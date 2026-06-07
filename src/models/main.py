"""
SQLAlchemy models for the Freedom Con site.

All nested / array fields are stored as JSON text columns so Flask-Admin
can display them in a simple <textarea> without complex inline forms.
"""

import json
from datetime import datetime

from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()
login_manager = LoginManager()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_load(raw: str | None, default):
    try:
        return json.loads(raw) if raw else default
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

class AdminUser(db.Model, UserMixin):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # "superadmin" has full access including Admin Users page; "admin" is everything else
    role = db.Column(db.String(20), nullable=False, default="admin")

    @property
    def is_superadmin(self) -> bool:
        return self.role == "superadmin"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __str__(self) -> str:
        return self.username


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(AdminUser, int(user_id))


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class AuditLog(db.Model):
    """Immutable record of every significant admin action."""
    __tablename__ = "audit_log"

    id         = db.Column(db.Integer, primary_key=True)
    timestamp  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    username   = db.Column(db.String(100), nullable=False)
    # LOGIN | LOGOUT | CREATE | EDIT | DELETE | PASSWORD_CHANGE
    action     = db.Column(db.String(30), nullable=False)
    # Model class name or page name (nullable for auth events)
    resource   = db.Column(db.String(100))
    # Primary key of the affected record (nullable)
    record_id  = db.Column(db.Integer)
    # Human-readable summary
    detail     = db.Column(db.Text)
    # IP address of the request
    ip_address = db.Column(db.String(64))

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by {self.username} at {self.timestamp}>"


class ViewPermission(db.Model):
    """Stores which endpoints each non-superadmin role may access.

    When the table is empty (fresh install) every authenticated user is allowed
    everywhere — this prevents accidental lockout on first deploy.
    Once any row exists the table is authoritative.
    """
    __tablename__ = "view_permissions"

    id       = db.Column(db.Integer, primary_key=True)
    role     = db.Column(db.String(50), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)

    __table_args__ = (db.UniqueConstraint("role", "endpoint", name="uq_role_endpoint"),)

    def __repr__(self) -> str:
        return f"<ViewPermission {self.role} → {self.endpoint}>"


def role_can_access(role: str, endpoint: str) -> bool:
    """Return True if *role* may access *endpoint*.

    Superadmin always passes.  If no permissions have been configured yet
    (empty table) every authenticated user passes so a fresh install is not
    accidentally locked.
    """
    if role == "superadmin":
        return True
    if ViewPermission.query.count() == 0:
        return True
    return ViewPermission.query.filter_by(role=role, endpoint=endpoint).count() > 0


def log_audit(username: str, action: str, resource: str | None = None,
              record_id: int | None = None, detail: str | None = None,
              ip_address: str | None = None) -> None:
    """Write an audit entry and commit it immediately."""
    try:
        from flask import request as _req
        ip = ip_address or _req.remote_addr
    except RuntimeError:
        ip = ip_address
    entry = AuditLog(
        username=username,
        action=action,
        resource=resource,
        record_id=record_id,
        detail=detail,
        ip_address=ip,
    )
    db.session.add(entry)
    db.session.commit()


# ---------------------------------------------------------------------------
# Generic site config (key → JSON blob)
# ---------------------------------------------------------------------------

class SiteConfig(db.Model):
    """Stores complex page-config blobs (camping, invite, the_play, wives, etc.)"""
    __tablename__ = "site_config"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value_json = db.Column(db.Text, default="{}")

    def get_value(self):
        return _json_load(self.value_json, {})

    def set_value(self, value) -> None:
        self.value_json = json.dumps(value, ensure_ascii=False, indent=2)

    def __str__(self) -> str:
        return self.key


# ---------------------------------------------------------------------------
# Speakers
# ---------------------------------------------------------------------------

class Speaker(db.Model):
    __tablename__ = "speakers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(500), default="")
    alt = db.Column(db.String(300), default="")
    bio = db.Column(db.Text, default="")
    shrink = db.Column(db.Float, nullable=True)
    image_x = db.Column(db.Integer, nullable=True)
    image_y = db.Column(db.Integer, nullable=True)
    # JSON list of strings e.g. ["Lead Pastor, Grace City Church"]
    titles_json = db.Column(db.Text, default="[]")
    # JSON list of dicts e.g. [{"icon":"church","name":"...","subtitle":"..."}]
    orgs_json = db.Column(db.Text, default="[]")
    is_gen_z = db.Column(db.Boolean, default=False, nullable=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.name,
            "image": self.image,
            "alt": self.alt,
            "bio": self.bio,
            "titles": _json_load(self.titles_json, []),
            "orgs": _json_load(self.orgs_json, []),
        }
        if self.shrink is not None:
            d["shrink"] = self.shrink
        if self.image_x is not None:
            d["image_x"] = self.image_x
        if self.image_y is not None:
            d["image_y"] = self.image_y
        return d

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Sponsors
# ---------------------------------------------------------------------------

class Sponsor(db.Model):
    __tablename__ = "sponsors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    logo_url = db.Column(db.String(500), default="")
    # 'businesses' | 'ministries' | 'churches'
    category = db.Column(db.String(50), default="businesses")
    show_on_sponsor_page = db.Column(db.Boolean, default=True)
    background_color = db.Column(db.String(20), nullable=True)
    scale = db.Column(db.Float, nullable=True)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.name,
            "logo_url": self.logo_url,
            "show_on_sponsor_page": self.show_on_sponsor_page,
        }
        if self.background_color:
            d["background_color"] = self.background_color
        if self.scale is not None:
            d["scale"] = self.scale
        return d

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Artists
# ---------------------------------------------------------------------------

class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(500), default="")
    hero_image_x = db.Column(db.String(20), default="50%")
    hero_image_y = db.Column(db.String(20), default="0%")
    genre = db.Column(db.String(100), default="")
    bio = db.Column(db.Text, default="")
    day = db.Column(db.String(50), default="")
    stage = db.Column(db.String(100), default="")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "image": self.image,
            "hero_image_x": self.hero_image_x,
            "hero_image_y": self.hero_image_y,
            "genre": self.genre,
            "bio": self.bio,
            "day": self.day,
            "stage": self.stage,
        }

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

class TicketPrice(db.Model):
    __tablename__ = "ticket_prices"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.String(100), default="")
    tax_total = db.Column(db.String(200), nullable=True)
    # JSON list of strings
    notes_json = db.Column(db.Text, default="[]")
    highlight = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "price": self.price,
            "tax_total": self.tax_total,
            "notes": _json_load(self.notes_json, []),
            "highlight": self.highlight,
        }

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Promos
# ---------------------------------------------------------------------------

class Promo(db.Model):
    """A promotional deal shown in the popup modal and on the tickets page."""
    __tablename__ = "promos"

    id         = db.Column(db.Integer, primary_key=True)
    # Short badge label, e.g. "50/50/50", "Group Rate", "VIP Pastor"
    badge      = db.Column(db.String(100), default="")
    # Badge colour variant: gold | green | navy | red
    badge_style = db.Column(db.String(30), default="gold")
    # One-liner shown in popup and as card title
    headline   = db.Column(db.String(300), nullable=False)
    # Full description paragraph (tickets page only, optional)
    description = db.Column(db.Text, default="")
    # Optional promo code snippet, e.g. "[STATE]50"
    promo_code  = db.Column(db.String(200), default="")
    # Examples text shown under the code, e.g. "e.g. WA50 · TX50"
    code_examples = db.Column(db.String(300), default="")
    # Additional hint / CTA text below the code block
    cta_hint   = db.Column(db.Text, default="")
    # URL anchor on the tickets page, e.g. "deal-fifty"
    anchor     = db.Column(db.String(100), default="")
    # Show in popup modal
    show_in_popup = db.Column(db.Boolean, default=True)
    # Show on tickets page
    show_on_tickets = db.Column(db.Boolean, default=True)
    active     = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "badge": self.badge,
            "badge_style": self.badge_style,
            "headline": self.headline,
            "description": self.description,
            "promo_code": self.promo_code,
            "code_examples": self.code_examples,
            "cta_hint": self.cta_hint,
            "anchor": self.anchor,
            "show_in_popup": self.show_in_popup,
            "show_on_tickets": self.show_on_tickets,
            "active": self.active,
        }

    def __str__(self) -> str:
        return self.headline or self.badge


# ---------------------------------------------------------------------------
# Videos & Podcasts
# ---------------------------------------------------------------------------

class Video(db.Model):
    __tablename__ = "videos"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500), default="")
    thumbnail_mobile = db.Column(db.String(500), default="")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "thumbnail_mobile": self.thumbnail_mobile,
        }

    def __str__(self) -> str:
        return self.title or self.url


class Podcast(db.Model):
    __tablename__ = "podcasts"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(500), default="")
    thumbnail_mobile = db.Column(db.String(500), default="")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "thumbnail_mobile": self.thumbnail_mobile,
        }

    def __str__(self) -> str:
        return self.title or self.url


# ---------------------------------------------------------------------------
# Social Proof
# ---------------------------------------------------------------------------

class SocialProof(db.Model):
    __tablename__ = "social_proof"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(300), default="")
    quote = db.Column(db.Text, default="")
    alt = db.Column(db.String(300), default="")
    # JSON list of image URL strings (may be empty)
    img_json = db.Column(db.Text, default="[]")
    # True = boys_social_proof list; False = social_proof list
    is_boys = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        d: dict = {
            "name": self.name,
            "title": self.title,
            "quote": self.quote,
            "alt": self.alt,
        }
        imgs = _json_load(self.img_json, [])
        if imgs:
            d["img"] = imgs
        return d

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# FAQ
# ---------------------------------------------------------------------------

class FAQ(db.Model):
    __tablename__ = "faqs"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(200), nullable=False)
    question = db.Column(db.Text, nullable=False)
    # Exactly one of the three answer fields should be set:
    answer = db.Column(db.Text, nullable=True)
    answer_html = db.Column(db.Text, nullable=True)
    # JSON list of strings
    answer_list_json = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        d: dict = {"question": self.question}
        if self.answer:
            d["answer"] = self.answer
        elif self.answer_html:
            d["answer_html"] = self.answer_html
        elif self.answer_list_json:
            d["answer_list"] = _json_load(self.answer_list_json, [])
        return d

    def __str__(self) -> str:
        return self.question[:80]


# ---------------------------------------------------------------------------
# Hotels / Accommodations
# ---------------------------------------------------------------------------

class HotelGroup(db.Model):
    """One row = one geographic group with multiple hotel sub-items (stored as JSON)."""
    __tablename__ = "hotel_groups"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    distance = db.Column(db.String(100), default="")
    details = db.Column(db.Text, default="")
    # JSON list: [{"name":"...","link":"...","valid_link": true}]
    hotels_json = db.Column(db.Text, default="[]")
    # 'hotels' (hotels page) | 'accommodations' (accommodations page)
    source = db.Column(db.String(30), default="hotels")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "distance": self.distance,
            "details": self.details,
            "hotels": _json_load(self.hotels_json, []),
        }

    def __str__(self) -> str:
        return f"{self.name} ({self.source})"


# ---------------------------------------------------------------------------
# Airport / Travel
# ---------------------------------------------------------------------------

class Airport(db.Model):
    __tablename__ = "airports"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    distance = db.Column(db.String(200), default="")
    drive_time = db.Column(db.String(200), default="")
    # JSON list of step strings
    route_json = db.Column(db.Text, default="[]")
    notes = db.Column(db.Text, default="")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "distance": self.distance,
            "drive_time": self.drive_time,
            "route": _json_load(self.route_json, []),
            "notes": self.notes,
        }

    def __str__(self) -> str:
        return self.name


# ---------------------------------------------------------------------------
# Past Conferences
# ---------------------------------------------------------------------------

class PastConference(db.Model):
    __tablename__ = "past_conferences"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(200), default="")
    summary = db.Column(db.Text, default="")
    # JSON list of video dicts: [{"url":"...","title":"...","thumbnail_mobile":"..."}]
    videos_json = db.Column(db.Text, default="[]")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "year": self.year,
            "name": self.name,
            "summary": self.summary,
            "videos": _json_load(self.videos_json, []),
        }

    def __str__(self) -> str:
        return f"{self.year} – {self.name}"


# ---------------------------------------------------------------------------
# Media Downloads
# ---------------------------------------------------------------------------

class MediaDownload(db.Model):
    __tablename__ = "media_downloads"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), default="")
    label = db.Column(db.String(200), nullable=False)
    # JSON list of asset dicts: [{"label":"...","thumb":"...","download":"..."}]
    assets_json = db.Column(db.Text, default="[]")
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.external_id,
            "label": self.label,
            "assets": _json_load(self.assets_json, []),
        }

    def __str__(self) -> str:
        return self.label


# ---------------------------------------------------------------------------
# Tickers
# ---------------------------------------------------------------------------

class Ticker(db.Model):
    __tablename__ = "tickers"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    ticker_name = db.Column(db.String(100), default="ticketer1")
    sort_order = db.Column(db.Integer, default=0)

    def __str__(self) -> str:
        return self.text[:60]


# ---------------------------------------------------------------------------
# Background Text
# ---------------------------------------------------------------------------

class BackgroundText(db.Model):
    __tablename__ = "background_texts"

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    group_name = db.Column(db.String(100), default="background_1")
    sort_order = db.Column(db.Integer, default=0)

    def __str__(self) -> str:
        return self.text[:60]


# ---------------------------------------------------------------------------
# Partner Churches
# ---------------------------------------------------------------------------

class Church(db.Model):
    __tablename__ = "churches"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    # Relative URL e.g. /static/img/churches/foo.webp
    logo_url = db.Column(db.String(500), default="")
    # Card background colour: "white", "black", or "" (transparent/dark default)
    logo_bg = db.Column(db.String(20), default="")
    # Hex color for card background, e.g. "#ffffff". Takes precedence over logo_bg.
    background_color = db.Column(db.String(20), default="")
    # Scale multiplier for the logo image (1.0 = normal)
    scale = db.Column(db.Float, default=1.0)
    active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "logo_url": self.logo_url,
            "logo_bg": self.logo_bg,
            "background_color": self.background_color,
            "scale": self.scale,
            "active": self.active,
        }

    def __str__(self) -> str:
        return self.name
