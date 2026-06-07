# SEO Audit Fixes

**Date:** May 20, 2026

---

## HIGH PRIORITY

### 1. `/faq` Returns Hard 404

**Issue:** Any inbound link or social post using `/faq` (singular) sent visitors to a dead end. The canonical URL is `/faqs`.

**Fix:** Added a permanent 301 redirect from `/faq` → `/faqs`.

- **File:** `src/controllers/routes.py` — new `faq_redirect()` route
- **File:** `tests/test_smoke.py` — added `/faq → /faqs` redirect assertion

---

### 2. Logo Not Visible on Initial Page Load

**Issue:** CSS rule `.landing12-nav.is-at-top .landing12-brand-logo { opacity: 0 }` hid the nav logo whenever the page was at scroll position 0 (i.e., every initial page load). The brand mark only appeared after the user scrolled past 24px.

**Fix:** Removed the `is-at-top` logo-hiding rule. The header background is already dark (`rgba(0,0,0,0.92)`) on load so the logo is fully legible without any transparency tricks.

- **File:** `src/static/css/components/freedom_con_shell.css`
- **File:** `src/static/css/components/freedom_con_shell.min.css`

---

## CRITICAL

### 1. Canonical URL Mismatch

**Issue:** Homepage `<link rel="canonical">` pointed to `/alt` instead of `/`, splitting SEO equity and misdirecting crawlers.

**Fix:** Updated `path` argument in `build_seo()` call inside the `landing()` route.

- **File:** `src/controllers/routes.py`
- **Change:** `path="/alt"` → `path="/"`

---

### 2. Nav "Home" Link Routing to `/alt`

**Issue:** The "Home" link in the Explore dropdown routed to `/alt` (via `url_for('public.landing_alt')`), reinforcing the canonical confusion and adding an unnecessary redirect hop.

**Fix:** Updated the href to point directly to the canonical homepage route.

- **File:** `src/templates/components/navigation.html`
- **Change:** `url_for('public.landing_alt')` → `url_for('public.landing')`

---

### 3. Removed `/alt` Route

**Issue:** The `/alt` route (a redirect stub to `/` and its large commented-out predecessor) was dead code that created a confusing redirect hop and cluttered the codebase.

**Fix:** Deleted the route entirely along with all commented-out legacy code.

- **File:** `src/controllers/routes.py`
- **File:** `tests/test_smoke.py` — removed the `/alt → /` redirect assertion

---

### 4. Missing Event JSON-LD (Rich Results Opportunity)

**Issue:** No `Event` schema on any page, so Google could not generate Event rich results (date, venue, ticket link) in search.

**Fix:** Added a `schema.org/Event` JSON-LD block to the homepage `render_template` call, passed via the existing `structured_data` pipeline that already renders `<script type="application/ld+json">` tags in the base template.

Schema covers: `name`, `description`, `startDate`/`endDate`, `eventAttendanceMode`, `eventStatus`, `image`, `location` (Place + PostalAddress), `organizer`, and `offers` (with ticket URL, currency, and `InStock` availability).

- **File:** `src/controllers/routes.py` — `event_schema` dict added to `landing()`, passed as `structured_data=[event_schema]`

---

## HIGH PRIORITY (continued)

### 3. Scroll-Triggered Animation Black Gaps

**Issue:** Large black dead zones appeared between sections during normal scrolling. Two compounding causes:
1. `main > section` was in the auto-reveal selector, so entire `<section>` elements started at `opacity: 0` — making whole content blocks invisible until the IntersectionObserver fired.
2. `rootMargin` of `-22%` (mobile) / `-10%` (desktop) delayed the trigger until the element was already well inside the viewport, extending how long sections stayed invisible.

**Fix:** Two changes to `src/static/js/main.js`:
- Removed `"main > section"` from `autoRevealSelector` — sections are never hidden; only inner elements (grid items, cards, FAQ items) animate in.
- Tightened `rootMargin` to `-5%` mobile / `-4%` desktop so the reveal fires as soon as the element is just barely inside the viewport.

---

### 4. Fathers & Sons Gallery — 3s+ Lazy-Load Delay & Dark Placeholders

**Issue:** Every gallery image was `loading="lazy" fetchpriority="low"`, including the first 8 that are immediately visible on scroll-in. The browser wouldn't start fetching them until the IntersectionObserver fired, causing 3+ second dark gaps. The `background: #1a1a1a` placeholder had no animation, making the wait feel like a broken page. The R2 CDN domain also had no preconnect hint, adding DNS + TLS overhead to every image request.

**Fix:**
- **First 8 images** set to `loading="eager" fetchpriority="auto"` in the template — browser fetches them immediately on page load regardless of scroll position.
- **Remaining images** stay `loading="lazy" fetchpriority="low"` (no change to bandwidth for the full set).
- **Shimmer skeleton** added to `.ft-ticker__item` via a `ft-shimmer` CSS keyframe animation — the `#1a1a1a → #2a2a2a → #1a1a1a` sweep makes placeholders look intentional while loading.
- **`preconnect` + `dns-prefetch`** hints added for `pub-fc470c82f793409f9e6c126deeb0387d.r2.dev` so the browser opens the CDN connection during HTML parse, before any image requests.

Files changed:
- `src/templates/public/landing copy/components/father_sons_scroller.html`
- `src/static/css/components/photo_ticker.css`
- `src/templates/public/landing copy/index.html`

---

### 5. Homepage `<title>` Missing Brand Name

**Issue:** Title was `"A Congress of Christian Men at The Gorge Amphitheatre"` — descriptive but omits "Freedom Con", reducing visibility in branded searches and making the browser tab unidentifiable.

**Fix:** Prepended the brand and year.

- **File:** `src/controllers/routes.py`
- **Change:** `"A Congress of Christian Men..."` → `"Freedom Con 2026 | A Congress of Christian Men at The Gorge Amphitheatre"`

---

### 6. No Reassurance Copy at Brushfire Checkout CTA

**Issue:** "Get Your Tickets" routes off-domain to brushfire.com with no explanation. New visitors have no signal that the transition is intentional and secure, increasing checkout abandonment risk.

**Fix:** Added a reassurance line beneath both CTA buttons on the tickets page:
> 🔒 Secure checkout powered by Brushfire — trusted by hundreds of faith-based events nationwide.

- **File:** `src/templates/public/tickets/index.html` — added to both CTA `<div>` blocks (ticket grid section and What's Included section)

**Action still required (cannot be done in code):**
Contact Brushfire support to confirm the Freedom Con Meta Pixel and GA4 purchase event tags are firing on the Brushfire order confirmation page. Without this, all paid ad attribution for completed ticket sales is broken — clicks will show in campaigns but zero purchases will be reported.

---

## STRATEGIC

### 1. Hero Has No Plain-Language Summary for Cold Paid Traffic

**Issue:** The hero right column showed "One Historic Event", a venue line, a date, and CTAs — nothing that told a first-time visitor what actually happens that weekend. Cold paid traffic had no context to evaluate the event before scrolling.

**Fix:** Added a one-sentence summary between the venue line and the date in the hero right column:

> *2 days of bold preaching, live worship, Crowder & Danny Gokey, and father‑son experiences — with a concrete plan you can act on.*

The copy slots into the natural read order: **what → where → when → action**, so it answers the cold-traffic question before the CTA appears.

- **File:** `src/templates/public/landing copy/components/hero.html`


