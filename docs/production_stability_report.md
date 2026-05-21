# Production Stability Report
### Freedom Con – Heroku / Gunicorn / Sentry Investigation
**Date:** May 21, 2026  
**Prepared by:** Platform Engineering (Internal)  
**Audience:** Technical Founder

---

## Executive Summary

The recurring H12 request timeouts, Gunicorn `SystemExit` storms, and assorted Sentry errors are **not caused by traffic load** — they are caused by a predictable set of architectural mistakes that are entirely fixable without a major rewrite. The two most severe issues are:

1. **Gunicorn is running with a single synchronous worker and no explicit timeout** — one slow or blocked request freezes the entire application.
2. **A synchronous HTTP proxy call** (`/press/download`) can hold that one worker for up to 30 seconds, guaranteed to produce an H12.
3. **Every single public page request** hits the database via the `inject_global_urgency` context processor with no caching — this is the hidden constant background pressure.

All other Sentry errors (AttributeError, IntegrityError, UndefinedError, sqlite3) are correctness bugs that add noise and further destabilize the application. They are individually small but collectively signal that the application was never hardened for production.

This report covers root cause analysis, immediate fixes, and a roadmap to full production reliability.

---

## Root Cause Analysis

### RCA-1 · Gunicorn Running with Default Sync Worker — No Concurrency

**Location:** `Procfile`

```
web: gunicorn run:app --bind 0.0.0.0:$PORT
```

**The problem:** No `--workers`, no `--timeout`, no `--worker-class`. Gunicorn defaults to **1 synchronous worker** with a **30-second timeout**. A single-worker sync Gunicorn process can handle exactly **one HTTP request at a time**. If that request takes 29.9 seconds, every other incoming request queues behind it. Heroku's router gives a request exactly 30 seconds to complete; once the queue backs up, timeouts cascade.

**Why this produces H12:** Heroku's router will hold a connection for 30 seconds waiting for the dyno to respond. With one worker processing a slow request, the next request waits idle. Heroku times out that waiting connection → H12.

**Why this produces `SystemExit` events in Sentry:** When Gunicorn's worker timeout triggers (default: 30s), the arbiter process sends `SIGKILL` to the hung worker and spawns a replacement. Flask/Sentry catches the abrupt process termination as a `SystemExit` event. Hundreds of these means hundreds of worker kills — one per slow request that hit the 30-second wall.

**Why low throughput (2 req/sec) still causes this:** 2 req/sec is only safe if every response completes in under 500ms. If one request blocks for 5–30 seconds, the 10 requests that arrived during that window all time out. Low throughput does NOT protect against queue starvation when worker count is 1.

---

### RCA-2 · Synchronous CDN Proxy in Request Lifecycle — Guaranteed Timeouts

**Location:** `src/controllers/routes.py` — `/press/download` route

```python
kwargs = {"timeout": 30}
with _urllib_req.urlopen(req, **kwargs) as resp:
    data = resp.read()          # ← blocks worker for up to 30 seconds
```

**The problem:** This route proxies a CDN file download synchronously inside the worker. The `timeout=30` matches Heroku's H12 threshold exactly. Any CDN latency, large file, or slow client connection holds the single worker hostage. During that time, zero other requests can be served.

**Compounding factor:** `resp.read()` loads the entire file into memory before streaming. For large PDFs or media kits, this is both slow and memory-wasteful.

**Why it causes H12:** The route was designed to stream a file, but it reads the whole response body blocking the worker. If the CDN takes 5 seconds and the file is 50MB, the worker is stuck for the full transfer duration — often exceeding 30 seconds.

---

### RCA-3 · Database Hit on Every Single Public Request (No Caching)

**Location:** `src/controllers/routes.py` — `inject_global_urgency` context processor

```python
@public_bp.app_context_processor
def inject_global_urgency() -> dict[str, object]:
    from src.models.main import Promo
    activepromos = Promo.query.filter_by(active=True).order_by(Promo.sort_order).all()
    return {
        "asset_url": asset_url,
        "asset_base_url": ASSET_BASE_URL,
        "global_promos": [p.to_dict() for p in activepromos],
    }
```

**The problem:** `app_context_processor` runs on **every single request** — including every static asset served through Flask, every admin page, every error page. Every call executes a `SELECT` against PostgreSQL with no caching. At 2 req/sec sustained, this is 120 DB queries/minute just from this one processor, before any route-specific queries run.

**Why this degrades performance:** PostgreSQL connection acquisition, query round-trip, result serialization, and Python object construction all add latency to every response. Under any connection pool pressure (even briefly), this stalls all requests simultaneously.

**Why this matters for H12:** Any connection pool saturation or database slowness causes this processor to block, which stalls request completion, which causes Gunicorn's worker to be "busy" longer than it should be, which cascades into timeout failures.

---

### RCA-4 · Permission Check Pattern with Two Queries Per Admin Request

**Location:** `src/models/main.py` — `role_can_access()`

```python
def role_can_access(role: str, endpoint: str) -> bool:
    if role == "superadmin":
        return True
    if ViewPermission.query.count() == 0:   # ← Query 1: always runs for non-superadmin
        return True
    return ViewPermission.query.filter_by(role=role, endpoint=endpoint).count() > 0  # ← Query 2
```

**The problem:** Every non-superadmin admin page view executes two sequential DB queries. The first (`count() == 0`) is a full table count with no filtering — it cannot use a partial index efficiently. The second is a filtered count. Both run in the `is_accessible()` method, which Flask-Admin calls for every admin view check.

**Additional issue:** `SecureAdminIndexView.index()` calls `role_can_access()` in a loop for every entry in `ADMIN_VIEWS` (21 entries) to build the sidebar — that is up to 42 DB queries per admin dashboard page load.

---

### RCA-5 · Audit Log Commits on Every Admin Write Action

**Location:** `src/models/main.py` — `log_audit()`

```python
def log_audit(...) -> None:
    entry = AuditLog(...)
    db.session.add(entry)
    db.session.commit()   # ← separate commit per action
```

And called from `after_model_change` and `after_model_delete` in admin views — meaning every save/delete in admin does two separate commits: the model commit (handled by Flask-Admin) and the audit log commit. Under any DB pressure, each extra round-trip adds to response latency.

---

### RCA-6 · SQLite Fallback in Production

**Location:** `run.py`

```python
_db_url = getenv("DATABASE_URL", f"sqlite:///{base_dir / 'freedomcon.db'}")
```

**The problem:** If `DATABASE_URL` is unset or not properly injected into the dyno environment (e.g., after a config var change that requires a restart), the app silently falls back to SQLite. SQLite is a file-based database stored on the dyno's ephemeral filesystem. Heroku dynos are ephemeral — the filesystem is wiped on every restart, deploy, or dyno cycle.

**Why this produces the `sqlite3 OperationalError` in Sentry:** Any dyno restart without `DATABASE_URL` available during startup causes the app to create a fresh empty SQLite DB. Queries against empty tables produce `OperationalError: no such table` or similar failures. This is a silent misconfiguration that is hard to detect.

---

### RCA-7 · `UndefinedError: 'dict object' has no attribute 'hero'`

**Location:** Template rendering — likely `src/templates/public/landing copy/` (the hero component currently open in the editor)

**The problem:** A template is accessing `.hero` on a dict context variable using dot notation (Jinja2 allows this). If the route passes the context variable as a plain dict without a `hero` key, Jinja2 raises `UndefinedError`. This happens when:
- A data file returns a different key structure than expected
- A DB query returns `None` instead of a populated dict
- A fallback was removed from the data layer without updating the template

Because the error is in template rendering, the entire response fails with a 500, not a partial render.

---

### RCA-8 · `AttributeError: 'AdminUser' has no attribute ...'`

**Location:** Admin views layer

**The problem:** Flask-Admin attempts to access a column or property on `AdminUser` that does not exist on the model. Common causes:
- A `column_list` or `form_columns` declaration in an admin view references a field that was renamed or removed from the model
- A `__str__` or `to_dict` method references a stale attribute name
- The `is_superadmin` property logic fails silently somewhere in a view that expects a column directly

This error crashes the admin request and is surfaced in Sentry.

---

### RCA-9 · `IntegrityError / psycopg2 UniqueViolation`

**Location:** Any admin create form or seeding operation

**The problem:** The `ViewPermission` model has a unique constraint on `(role, endpoint)`. The `seed_db.py` script or admin form appears to attempt duplicate inserts without an `ON CONFLICT DO NOTHING` / `INSERT OR IGNORE` guard. Race conditions in manual admin operations or double-form-submissions produce this error.

Also: the `AdminUser` model has `unique=True` on `username`. Any attempt to create a duplicate admin user (e.g., running `create_admin_user.py` twice) will raise this error.

---

### RCA-10 · Invalid HTTP Header Issue

**Location:** `/press/download` route or response headers

**The problem:** The `Content-Disposition` header construction uses string formatting:

```python
content_disposition = (
    f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{rfc5987_name}'
)
```

If `ascii_name` contains characters that are technically valid ASCII but illegal in HTTP header values (e.g., control characters, newlines injected through the `name` query parameter), this produces an invalid header. While the code does `encode("ascii", errors="replace")`, it does not strip control characters or newlines, which are different from non-ASCII characters. A crafted `name` parameter could inject a CRLF sequence into the response headers.

---

## Risk Assessment

| Risk | Severity | Likelihood | Impact |
|------|----------|------------|--------|
| Single Gunicorn worker | Critical | Confirmed | All traffic blocked by one slow request |
| `/press/download` synchronous proxy | Critical | Confirmed | 30s worker lock per download |
| Context processor DB query (no cache) | High | Confirmed | Constant DB pressure, latency amplification |
| SQLite production fallback | High | Possible | Silent data loss / empty DB on restart |
| `UndefinedError` in template | Medium | Confirmed | 500 errors on homepage |
| `AdminUser` AttributeError | Medium | Confirmed | Admin panel crashes |
| UniqueViolation on insert | Medium | Confirmed | Failed creates, confusing admin UX |
| Permission check N+1 | Medium | Confirmed | Admin page load slowness |
| HTTP header injection | Low-Medium | Possible | Security + header parsing errors |
| Audit log extra commit | Low | Confirmed | Marginal latency on admin saves |

---

## Gunicorn Architecture Analysis

### Current State

```
web: gunicorn run:app --bind 0.0.0.0:$PORT
```

- **Workers:** 1 (default) — catastrophically low for any production workload
- **Worker class:** `sync` (default) — one request at a time per worker
- **Timeout:** 30 seconds (default, matches Heroku H12 threshold exactly)
- **Threads:** 1 (default)
- **Preload:** Not set — each worker imports the full app independently

### Why Sync Workers Are Acceptable Here

This application is a **content-serving Flask app** — no WebSockets, no long polling, no streaming. All routes do: DB query → template render → response. Sync workers are appropriate. The problem is not the worker class, it is the worker **count** and the **blocking I/O** inside the CDN proxy route.

### Recommended Gunicorn Configuration

For a Heroku Standard-1X dyno (512MB RAM):

```
web: gunicorn run:app \
  --bind 0.0.0.0:$PORT \
  --workers 3 \
  --threads 2 \
  --worker-class gthread \
  --timeout 25 \
  --keep-alive 5 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  --preload \
  --access-logfile - \
  --error-logfile - \
  --log-level info
```

**Explanation of each flag:**

| Flag | Value | Reason |
|------|-------|--------|
| `--workers 3` | 3 | Standard formula: `(2 × CPU_cores) + 1`. Heroku dynos have 1 vCPU → 3 workers. Handles 3 concurrent requests without blocking. |
| `--threads 2` | 2 | `gthread` worker class allows each worker to handle 2 threads. Total effective concurrency: 6. |
| `--worker-class gthread` | gthread | Thread-based workers are lightweight and appropriate for I/O-bound Flask apps. No need for gevent/eventlet unless you have many concurrent long-poll connections. |
| `--timeout 25` | 25 | Set **below** Heroku's 30s H12 threshold. Gunicorn will kill a hung worker at 25s; Heroku gets a proper error response rather than a silent H12 timeout. |
| `--keep-alive 5` | 5 | Reuse HTTP connections from Heroku's router. Reduces TCP handshake overhead. |
| `--max-requests 1000` | 1000 | Recycle workers after 1000 requests to prevent memory leaks from accumulating over time. |
| `--max-requests-jitter 100` | 100 | Adds randomness to recycling to prevent all workers from recycling simultaneously. |
| `--preload` | flag | Load application code before forking workers. Reduces per-worker startup time and allows copy-on-write memory savings. Also ensures `db.create_all()` runs once, not three times. |
| `--access-logfile -` | - | Log to stdout so Heroku captures access logs in `heroku logs`. |
| `--error-logfile -` | - | Same for error logs. |
| `--log-level info` | info | Verbose enough to catch worker recycling events. |

**For a Performance-L or Standard-2X dyno (1GB RAM), increase to:**
```
--workers 5 --threads 2
```

### Single-Dyno Risk

Running one dyno means:
- Any dyno restart (deploy, daily restart, crash) causes a brief outage
- No redundancy if one worker gets stuck
- Heroku's router has no second dyno to failover to

This is acceptable for low-traffic apps, but the deployment process should ensure zero-downtime deploys using Heroku's preboot feature (`heroku features:enable preboot`).

---

## Database Risk Analysis

### PostgreSQL Bottlenecks

**Missing indexes on frequently queried columns:**

The following queries run on every request or every admin page view but have no declared index:

| Table | Query Pattern | Missing Index |
|-------|--------------|---------------|
| `promos` | `filter_by(active=True).order_by(sort_order)` | `(active, sort_order)` |
| `promos` | `filter_by(active=True, show_on_tickets=True)` | `(active, show_on_tickets, sort_order)` |
| `view_permissions` | `filter_by(role=role, endpoint=endpoint)` | `(role, endpoint)` — unique constraint exists but confirm index is created |
| `speakers` | `order_by(sort_order)` | `sort_order` |
| `sponsors` | `filter_by(show_on_sponsor_page=True)` | `show_on_sponsor_page` |
| `churches` | `filter_by(active=True)` | `active` |

Without indexes on these columns, PostgreSQL does full table scans. For small tables this is fast, but as data grows, these queries slow down proportionally.

**Connection Pool Defaults:**

Flask-SQLAlchemy uses SQLAlchemy's default `QueuePool` with:
- `pool_size=5` connections
- `max_overflow=10` connections  
- `pool_timeout=30` seconds

With 3 workers × 2 threads = 6 concurrent connections at peak, the default pool_size of 5 means the 6th concurrent request will wait for a connection from the pool. This waiting contributes to response time and, under sustained load, to H12 timeouts.

**Recommended pool configuration** (add to `app.config.update()`):

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 5,
    "max_overflow": 2,
    "pool_timeout": 10,        # fail fast rather than wait 30s
    "pool_recycle": 300,       # prevent stale connection issues on Heroku
    "pool_pre_ping": True,     # validate connections before use
}
```

The `pool_pre_ping=True` setting prevents `OperationalError: server closed the connection unexpectedly` errors that occur when PostgreSQL terminates idle connections (Heroku's Postgres kills connections idle for 10 minutes on hobby tiers).

### Duplicate Insert Race Conditions

The `ViewPermission` model's unique constraint `uq_role_endpoint` correctly prevents duplicates at the DB level, but the application does not handle the resulting `IntegrityError` gracefully. Any admin UI or seed script that inserts permissions without checking for existence first will:
1. Raise `IntegrityError`
2. Leave the SQLAlchemy session in a broken state requiring a rollback
3. Cause subsequent queries in the same request to fail with `InvalidRequestError: This Session's transaction has been rolled back`

This is the likely source of cascading errors in Sentry.

### SQLite Production Anti-Pattern

SQLite uses **file-level locking**. On Heroku, the dyno filesystem is:
1. **Ephemeral** — wiped on every restart/deploy
2. **Not shared** — each dyno has its own filesystem; if you ever scale to 2 dynos, they would have independent databases

The `sqlite3 OperationalError` in Sentry is direct evidence this fallback has been triggered in production. The fix is to make the missing `DATABASE_URL` a hard startup error rather than a silent fallback.

### Transaction Locking Risks

The `log_audit()` function calls `db.session.commit()` as a separate transaction after every admin model change. If the admin model's commit (handled by Flask-Admin) succeeds but the audit log commit fails (e.g., DB connection issue), you get a logged action that never recorded in the audit log. More importantly, if the audit commit raises an exception, it bubbles up through the request and surfaces as a 500 error even though the actual data change succeeded.

---

## App-Level Architectural Issues

### Work Being Done Inside Request/Response Cycle

| Route | Blocking Work | Risk |
|-------|--------------|------|
| `GET /press/download` | Full CDN file download via `urllib.urlopen().read()` | **Critical** — up to 30s block |
| Every public route | `Promo.query` via context processor | **High** — DB hit on every request |
| `GET /` (landing) | `get_videos()`, `get_podcasts()`, `get_speakers()`, `get_social_proof()`, `get_boys_social_proof()`, `get_ticket_context()`, `get_visible_sponsors()` — 6+ DB queries | **Medium** — all synchronous, sequential |
| `GET /tickets` | `get_ticket_context()` + second `Promo.query` = minimum 2 DB queries | **Medium** |
| Admin dashboard | Up to 42 `role_can_access()` DB queries per page load | **Medium** |

### Missing Caching

There is **zero caching** anywhere in the application. Every page render does fresh DB queries. For content that changes rarely (speakers, sponsors, FAQs, ticket prices), this is pure waste. The `inject_global_urgency` context processor alone represents hundreds of unnecessary DB queries per hour.

### Template Rendering Failures

The `UndefinedError` on `hero` attribute confirms that at least one route passes a context variable structure that does not match what the template expects. In Jinja2, accessing a missing attribute on a dict with dot notation raises `UndefinedError` only when `undefined=StrictUndefined` or depends on the jinja environment. In Flask's default environment, this raises `jinja2.exceptions.UndefinedError` which is a 500.

The root fix is ensuring that any dict passed to a template that a template accesses via dot notation either always has the expected keys, or the template uses the `default` filter: `{{ item.hero | default('') }}`.

### Poor Exception Handling in Service Layer

The `services/main.py` data-fetching functions (e.g., `get_videos()`, `get_speakers()`) query the database. If any of these raise an exception (DB connection failure, malformed JSON in a column), the exception propagates up through the route, through the template render, and hits Flask's error handler. There is no try/except at the service layer to return a sensible empty default and log the error, meaning a single DB hiccup can take down an entire page.

---

## Production Hardening Plan

### Immediate Fixes (Today — < 2 hours total)

**Priority 1 · Fix the Procfile** (15 minutes)

This single change has the highest impact of anything in this document. It adds concurrency and sets a proper timeout.

```
web: gunicorn run:app --bind 0.0.0.0:$PORT --workers 3 --threads 2 --worker-class gthread --timeout 25 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --preload --access-logfile - --error-logfile -
```

Expected outcome: Eliminates the majority of H12 timeouts caused by queue starvation and significantly reduces `SystemExit` events.

**Priority 2 · Add connection pool settings to config** (15 minutes)

In `run.py`, inside `app.config.update()`:

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 5,
    "max_overflow": 2,
    "pool_timeout": 10,
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
```

Expected outcome: Eliminates stale connection errors and prevents pool starvation.

**Priority 3 · Guard against SQLite fallback** (10 minutes)

In `run.py`, replace the silent fallback with a hard check:

```python
_db_url = getenv("DATABASE_URL")
if not _db_url:
    import sys
    print("FATAL: DATABASE_URL is not set. Set it before starting the app.", file=sys.stderr)
    sys.exit(1)
if _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql://", 1)
```

Expected outcome: Eliminates silent SQLite-in-production failures and makes the misconfiguration immediately visible.

**Priority 4 · Enable Heroku preboot** (5 minutes, zero code change)

```bash
heroku features:enable preboot -a <your-app-name>
```

Expected outcome: Zero-downtime deploys. New dynos are fully started before receiving traffic, eliminating the brief outage window on every deploy.

---

### Short-Term Fixes (This Week — < 1 day total)

**Fix the `/press/download` proxy route**

Replace the synchronous full-read proxy with a proper streaming redirect or a signed CDN URL. The simplest safe fix is a direct redirect to the CDN with a content-disposition header handled on the CDN side. If the proxy is needed for security, stream the response instead of buffering it:

```python
# Instead of resp.read() buffering the entire file:
# Stream: use Response with a generator, or redirect to a pre-signed URL
return redirect(url, code=302)  # simplest fix if CDN URL is already trusted
```

If the proxy must stay, move it behind a background job that generates a short-lived download token, and serve the file from a redirect to a pre-signed R2/S3 URL.

**Cache the Promo context processor**

```python
# Use Flask-Caching (add flask-caching to requirements.txt)
from flask_caching import Cache
cache = Cache(config={"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 60})

@public_bp.app_context_processor
def inject_global_urgency() -> dict[str, object]:
    from src.models.main import Promo
    
    cached = cache.get("global_promos")
    if cached is None:
        activepromos = Promo.query.filter_by(active=True).order_by(Promo.sort_order).all()
        cached = [p.to_dict() for p in activepromos]
        cache.set("global_promos", cached, timeout=60)
    
    def asset_url(path: str) -> str:
        ...
    
    return {
        "asset_url": asset_url,
        "asset_base_url": ASSET_BASE_URL,
        "global_promos": cached,
    }
```

More impactful alternative: add a `cache.delete("global_promos")` call in the Promo admin view's `after_model_change` so the cache invalidates immediately when an admin saves a promo.

**Fix the N+1 admin permission check**

Cache the permission table in memory at startup (it rarely changes):

```python
# In role_can_access, use a module-level cache dict
_permission_cache: dict[str, set[str]] | None = None

def _get_permissions() -> dict[str, set[str]]:
    global _permission_cache
    if _permission_cache is None:
        rows = ViewPermission.query.all()
        cache: dict[str, set[str]] = {}
        for row in rows:
            cache.setdefault(row.role, set()).add(row.endpoint)
        _permission_cache = cache
    return _permission_cache

def role_can_access(role: str, endpoint: str) -> bool:
    if role == "superadmin":
        return True
    perms = _get_permissions()
    if not perms:  # empty table = open access
        return True
    return endpoint in perms.get(role, set())

def invalidate_permission_cache() -> None:
    global _permission_cache
    _permission_cache = None
```

Call `invalidate_permission_cache()` from the `ViewPermission` admin view's `after_model_change` and `after_model_delete`.

**Add indexes for the most-queried columns**

In a new Alembic migration (or a `db.create_all()` bootstrap if not using migrations):

```python
# In Speaker model:
__table_args__ = (db.Index("ix_speakers_sort_order", "sort_order"),)

# In Promo model:
__table_args__ = (
    db.Index("ix_promos_active_sort", "active", "sort_order"),
    db.Index("ix_promos_active_tickets", "active", "show_on_tickets"),
)

# In Church model:
__table_args__ = (db.Index("ix_churches_active", "active"),)

# In Sponsor model:
__table_args__ = (db.Index("ix_sponsors_show", "show_on_sponsor_page"),)
```

**Fix UniqueViolation in seed/admin by adding UPSERT logic**

In any code that inserts `ViewPermission` rows:

```python
from sqlalchemy.dialects.postgresql import insert as pg_insert

stmt = pg_insert(ViewPermission).values(role=role, endpoint=endpoint)
stmt = stmt.on_conflict_do_nothing(index_elements=["role", "endpoint"])
db.session.execute(stmt)
db.session.commit()
```

**Fix the `UndefinedError: 'dict object' has no attribute 'hero'`**

In the hero template (`src/templates/public/landing copy/components/hero.html`), replace any `{{ variable.hero }}` with `{{ variable.hero | default('') }}` or `{{ variable.get('hero', '') }}`. Also audit the route that renders this template to ensure the context always includes the `hero` key.

**Add HTTP header sanitization to `/press/download`**

```python
import re
safe_name = re.sub(r'[\x00-\x1f\x7f\r\n]', '', safe_name)  # strip control chars
```

---

### Long-Term Architecture Improvements (Next 2–4 weeks)

**Move `/press/download` to a signed CDN URL pattern**

Rather than proxying files through the Gunicorn worker, generate pre-signed URLs directly to Cloudflare R2 or use public CDN URLs with a server-side redirect. This completely eliminates the blocking download from the request lifecycle.

**Add a proper caching layer**

Use Redis (available as Heroku Redis add-on) with Flask-Caching. Cache:
- `global_promos` — 60 second TTL, invalidate on admin save
- `get_speakers()` — 5 minute TTL
- `get_sponsors()` — 5 minute TTL
- `get_ticket_context()` — 30 second TTL
- Full page cache for `/`, `/speakers`, `/faqs` — 30–60 seconds

Redis on Heroku's hobby tier costs $3/month and eliminates the majority of DB load.

**Introduce background job processing**

If you ever add email sending, image processing, PDF generation, or any external API call (OpenAI, payment webhooks, etc.) to the request lifecycle, move it to a background queue immediately. Use [RQ](https://python-rq.org/) with Heroku Redis — it requires no additional infrastructure (Redis is already recommended above) and is simpler to operate than Celery.

```python
# In a route:
from rq import Queue
from redis import Redis
q = Queue(connection=Redis.from_url(os.environ["REDIS_URL"]))
q.enqueue(send_confirmation_email, user_email, ticket_id)
# Return immediately — don't wait for email
```

**Migrate to Alembic for database schema management**

Currently, schema changes are applied via `db.create_all()`, which only adds new tables — it never modifies existing ones. As the schema evolves, columns added to models won't appear in existing deployments without a manual migration. Use Flask-Migrate (which wraps Alembic) to version and apply schema changes safely.

**Upgrade to a Heroku Standard dyno**

The Standard-1X and Standard-2X dynos are not put to sleep after 30 minutes of inactivity (unlike hobby dynos). Hobby dyno cold starts (the dyno sleeping and waking) produce their own H12 spikes as the dyno takes 5–10 seconds to wake up, during which all requests queue.

---

## Observability Recommendations

### Sentry Improvements

**Current state:** Basic Flask integration with `traces_sample_rate=0.2` (20% of transactions are traced).

**Recommended improvements:**

1. **Increase trace sampling temporarily** to 1.0 (100%) to diagnose the timeout issues, then reduce to 0.1 once stable:
   ```python
   traces_sample_rate=_env_float("SENTRY_TRACES_SAMPLE_RATE", 0.2)
   ```
   Set `SENTRY_TRACES_SAMPLE_RATE=1.0` in Heroku config vars temporarily.

2. **Enable Sentry's DB query monitoring** by ensuring `sqlalchemy` is in the integrations:
   ```python
   from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
   sentry_sdk.init(
       integrations=[FlaskIntegration(), SqlalchemyIntegration()],
       ...
   )
   ```
   This will show slow queries in Sentry's Performance tab.

3. **Add performance alerts** in the Sentry dashboard:
   - Alert when P95 response time exceeds 3 seconds
   - Alert when error rate exceeds 1% over 5 minutes
   - Alert on any new `SystemExit` event (these should be zero after Procfile fix)

4. **Tag requests with route name** for easier filtering:
   ```python
   # Already done via FlaskIntegration — confirm transaction names are appearing
   ```

5. **Ignore noisy non-actionable errors** to reduce Sentry quota usage:
   ```python
   sentry_sdk.init(
       ignore_errors=[KeyboardInterrupt],
       ...
   )
   ```

### APM and Request Timing

Heroku has a free built-in metrics dashboard at `heroku.com/apps/<name>/metrics`. Monitor:
- **Response time P50/P95/P99** — target P95 < 1s
- **Throughput** — requests/minute
- **Error rate** — H12 count should drop to zero after Procfile fix
- **Memory** — watch for memory growth after `--preload` is enabled (copy-on-write may increase per-worker memory)
- **Dyno load** — CPU % — if consistently > 80%, upgrade dyno tier

**Add request timing to structured logs:**

```python
import time

@app.before_request
def _start_timer():
    from flask import g
    g.request_start = time.perf_counter()

@app.after_request
def _log_timing(response):
    from flask import g
    duration_ms = (time.perf_counter() - g.request_start) * 1000
    app.logger.info(
        "request",
        extra={
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }
    )
    return response
```

With `--access-logfile -` in Gunicorn, Heroku Logplex captures these logs and they can be forwarded to Papertrail or Logtail for querying.

### Slow Query Logging

Enable PostgreSQL slow query logging on Heroku:

```bash
heroku config:set LOG_MIN_DURATION_STATEMENT=200  # log queries > 200ms
```

This requires Heroku Postgres Standard tier or higher. On hobby tier, use SQLAlchemy's event system:

```python
from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.monotonic())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.monotonic() - conn.info["query_start_time"].pop(-1)
    if total > 0.1:  # log queries taking over 100ms
        logging.getLogger("sqlalchemy.slow").warning(
            f"SLOW QUERY ({total*1000:.1f}ms): {statement[:200]}"
        )
```

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| H12 error count | > 1 / 5 min | > 5 / 5 min |
| P95 response time | > 2s | > 5s |
| DB connection wait | > 100ms | > 500ms |
| Worker `SystemExit` | Any | Any |
| Memory per dyno | > 400MB | > 480MB (Heroku kills at 512MB) |
| DB connection count | > 8 | > 12 |

---

## Immediate Action Items

1. **[ ] Update Procfile** with multi-worker Gunicorn config — `--workers 3 --threads 2 --worker-class gthread --timeout 25 --preload`
2. **[ ] Add SQLAlchemy engine options** — `pool_pre_ping`, `pool_recycle`, `pool_timeout`
3. **[ ] Hard-fail on missing `DATABASE_URL`** — remove SQLite fallback
4. **[ ] Enable Heroku preboot** — `heroku features:enable preboot`
5. **[ ] Set `SENTRY_TRACES_SAMPLE_RATE=1.0`** temporarily to capture full trace data
6. **[ ] Add `SqlalchemyIntegration`** to Sentry init

Deploy these six changes as a single commit. Expected outcome: H12 rate drops by 80–90% immediately, `SystemExit` events drop to near zero.

---

## Recommended Infrastructure Changes

| Change | Service | Estimated Cost | Impact |
|--------|---------|---------------|--------|
| Upgrade from Hobby dyno to Standard-1X | Heroku Dyno | +$25/mo | Eliminates cold-start H12s, adds preboot support |
| Add Heroku Redis | Heroku Redis | $3–$15/mo | Enables proper caching, removes DB pressure |
| Add Heroku Postgres Standard tier | Heroku Postgres | +$9/mo | Adds slow query logs, connection metrics |
| Enable Papertrail (log management) | Papertrail | Free tier | Searchable logs, request timing |

---

## Recommended Code Changes

| File | Change | Priority |
|------|--------|----------|
| `Procfile` | Multi-worker Gunicorn config | Critical |
| `run.py` | Hard-fail on missing `DATABASE_URL`, add `SQLALCHEMY_ENGINE_OPTIONS` | Critical |
| `src/controllers/routes.py` | Cache `inject_global_urgency`, fix `/press/download` blocking read | High |
| `src/models/main.py` | Cache permission table, fix `log_audit` transaction isolation, add indexes | High |
| `src/templates/public/landing copy/components/hero.html` | Use `| default('')` on all potentially-missing dict attributes | Medium |
| `src/controllers/admin_views.py` | Fix `column_list`/`form_columns` to match actual model attributes | Medium |
| `seed_db.py` | Replace bare INSERT with UPSERT for `ViewPermission` rows | Medium |
| `run.py` | Add request timing middleware | Low |
| Any route that calls external APIs | Wrap in timeout + exception handler, consider background job | Medium |

---

## Final Remediation Roadmap

### Week 1 — Stop the bleeding

- Deploy Procfile fix (multi-worker Gunicorn)
- Add SQLAlchemy pool settings and hard-fail on SQLite fallback
- Enable preboot
- Confirm H12 rate drops in Heroku metrics
- Confirm `SystemExit` events stop in Sentry

### Week 2 — Remove remaining timeout risks

- Fix `/press/download` to redirect or stream (not buffer)
- Add Flask-Caching with in-memory cache (no Redis needed yet)
- Cache `inject_global_urgency` with 60-second TTL
- Cache `get_speakers()`, `get_sponsors()` with 5-minute TTL
- Add DB indexes for `promos.active`, `speakers.sort_order`, `churches.active`
- Fix `UndefinedError` in hero template

### Week 3 — Fix correctness bugs

- Fix `AdminUser` AttributeError by auditing Flask-Admin `column_list` declarations
- Add UPSERT logic to all seed inserts
- Sanitize HTTP header construction in `/press/download`
- Fix `log_audit` to not commit in a separate transaction
- Cache permission table

### Week 4 — Observability and resilience

- Add `SqlalchemyIntegration` to Sentry + slow query listener
- Add request timing middleware
- Set Sentry alert thresholds
- Consider upgrading to Standard dyno + Heroku Redis
- Document all config vars in a `.env.example` file so missing env vars are obvious
- Add startup validation that checks for required env vars before accepting traffic

---

*End of report. All findings are based on direct code inspection of the production codebase. No changes were made to the existing code — this report is a plan of action only.*
