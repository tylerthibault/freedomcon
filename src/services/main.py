"""
Service layer — query the SQLite database and return data in the same shape
that templates have always expected (plain Python dicts/lists).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Speakers
# ---------------------------------------------------------------------------

def get_speakers() -> list[dict]:
    from src.models.main import Speaker, db
    rows = db.session.execute(
        db.select(Speaker).where(Speaker.is_gen_z == False, Speaker.is_visible == True).order_by(Speaker.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


def get_gen_z_speakers() -> list[dict]:
    from src.models.main import Speaker, db
    rows = db.session.execute(
        db.select(Speaker).where(Speaker.is_gen_z == True, Speaker.is_visible == True).order_by(Speaker.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


# ---------------------------------------------------------------------------
# Sponsors
# ---------------------------------------------------------------------------

def get_sponsors() -> dict:
    """Returns {'businesses': [...], 'ministries': [...], 'churches': [...]}"""
    from src.models.main import Sponsor, db
    result: dict = {"businesses": [], "ministries": [], "churches": []}
    rows = db.session.execute(
        db.select(Sponsor).order_by(Sponsor.category, Sponsor.sort_order)
    ).scalars().all()
    for row in rows:
        cat = row.category
        if cat in result:
            result[cat].append(row.to_dict())
        else:
            result[cat] = [row.to_dict()]
    return result


def get_visible_sponsors() -> dict:
    """Sponsors filtered to show_on_sponsor_page == True."""
    all_sponsors = get_sponsors()
    return {
        cat: [s for s in items if s.get("show_on_sponsor_page")]
        for cat, items in all_sponsors.items()
    }


# ---------------------------------------------------------------------------
# Artists
# ---------------------------------------------------------------------------

def get_artists() -> list[dict]:
    from src.models.main import Artist, db
    rows = db.session.execute(
        db.select(Artist).order_by(Artist.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


# ---------------------------------------------------------------------------
# Tickets
# ---------------------------------------------------------------------------

def get_ticket_prices() -> list[dict]:
    from src.models.main import TicketPrice, db
    rows = db.session.execute(
        db.select(TicketPrice).order_by(TicketPrice.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


def get_ticket_meta() -> dict:
    return _get_site_config("ticket_meta", {})


def get_ticket_context() -> dict:
    return {
        "ticket_meta": get_ticket_meta(),
        "ticket_prices": get_ticket_prices(),
    }


# ---------------------------------------------------------------------------
# Videos & Podcasts
# ---------------------------------------------------------------------------

def get_videos() -> list[dict]:
    from src.models.main import Video, db
    rows = db.session.execute(
        db.select(Video).order_by(Video.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


def get_podcasts() -> list[dict]:
    from src.models.main import Podcast, db
    rows = db.session.execute(
        db.select(Podcast).order_by(Podcast.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


# ---------------------------------------------------------------------------
# Social Proof
# ---------------------------------------------------------------------------

def get_social_proof() -> list[dict]:
    from src.models.main import SocialProof, db
    rows = db.session.execute(
        db.select(SocialProof).where(SocialProof.is_boys == False).order_by(SocialProof.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


def get_boys_social_proof() -> list[dict]:
    from src.models.main import SocialProof, db
    rows = db.session.execute(
        db.select(SocialProof).where(SocialProof.is_boys == True).order_by(SocialProof.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


# ---------------------------------------------------------------------------
# FAQs
# ---------------------------------------------------------------------------

def get_faq() -> dict:
    """Returns {'Category Name': [{'question': ..., 'answer': ...}, ...], ...}"""
    from src.models.main import FAQ, db
    rows = db.session.execute(
        db.select(FAQ).order_by(FAQ.category, FAQ.sort_order)
    ).scalars().all()
    result: dict = {}
    for row in rows:
        cat = row.category
        if cat not in result:
            result[cat] = []
        result[cat].append(row.to_dict())
    return result


# ---------------------------------------------------------------------------
# Hotels / Accommodations
# ---------------------------------------------------------------------------

def get_hotel_groups(source: str) -> list[dict]:
    from src.models.main import HotelGroup, db
    rows = db.session.execute(
        db.select(HotelGroup)
        .where(HotelGroup.source == source)
        .order_by(HotelGroup.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


def get_hotels_data() -> dict:
    """Rebuild the hotels dict expected by the hotels template."""
    meta = _get_site_config("hotels_meta", {})
    return {
        "hero": meta.get("hero", {}),
        "important_note": meta.get("important_note", ""),
        "options": get_hotel_groups("hotels"),
        "cta": meta.get("cta", {}),
    }


def get_travel_info() -> dict:
    """Rebuild travel_info dict (overview + airports list)."""
    from src.models.main import Airport, db
    meta = _get_site_config("travel_info_meta", {})
    airport_rows = db.session.execute(
        db.select(Airport).order_by(Airport.sort_order)
    ).scalars().all()
    return {
        "overview": meta.get("overview", ""),
        "airports": [r.to_dict() for r in airport_rows],
    }


# ---------------------------------------------------------------------------
# Site config blobs (camping / invite / the_play / wives)
# ---------------------------------------------------------------------------

def _get_site_config(key: str, default=None):
    from src.models.main import SiteConfig, db
    row = db.session.execute(
        db.select(SiteConfig).where(SiteConfig.key == key)
    ).scalar_one_or_none()
    if row is None:
        return default if default is not None else {}
    return row.get_value()


def get_camping() -> dict:
    return _get_site_config("camping", {})


def get_invite() -> dict:
    return _get_site_config("invite", {})


def get_the_play() -> dict:
    return _get_site_config("the_play", {})


def get_wives() -> dict:
    return _get_site_config("wives", {})


def get_schedule_pdf_url() -> str:
    cfg = _get_site_config("schedule_pdf", {})
    return cfg.get("url", "")


# ---------------------------------------------------------------------------
# Past Conferences
# ---------------------------------------------------------------------------

def get_past_conferences() -> list[dict]:
    from src.models.main import PastConference, db
    rows = db.session.execute(
        db.select(PastConference).order_by(PastConference.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


# ---------------------------------------------------------------------------
# Media Downloads
# ---------------------------------------------------------------------------

def get_media_downloads() -> list[dict]:
    from src.models.main import MediaDownload, db
    rows = db.session.execute(
        db.select(MediaDownload).order_by(MediaDownload.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]


# ---------------------------------------------------------------------------
# Tickers
# ---------------------------------------------------------------------------

def get_ticker(name: str = "ticketer1") -> list[str]:
    from src.models.main import Ticker, db
    rows = db.session.execute(
        db.select(Ticker)
        .where(Ticker.ticker_name == name)
        .order_by(Ticker.sort_order)
    ).scalars().all()
    return [r.text for r in rows]


def get_ticketers() -> dict:
    from src.models.main import Ticker, db
    rows = db.session.execute(
        db.select(Ticker).order_by(Ticker.ticker_name, Ticker.sort_order)
    ).scalars().all()
    result: dict = {}
    for row in rows:
        n = row.ticker_name
        result.setdefault(n, []).append(row.text)
    return result


# ---------------------------------------------------------------------------
# Background Text
# ---------------------------------------------------------------------------

def get_background_text(group: str = "background_1") -> list[str]:
    from src.models.main import BackgroundText, db
    rows = db.session.execute(
        db.select(BackgroundText)
        .where(BackgroundText.group_name == group)
        .order_by(BackgroundText.sort_order)
    ).scalars().all()
    return [r.text for r in rows]


# ---------------------------------------------------------------------------
# Churches
# ---------------------------------------------------------------------------

def get_churches() -> list[dict]:
    from src.models.main import Church, db
    rows = db.session.execute(
        db.select(Church)
        .where(Church.active == True)
        .order_by(Church.sort_order)
    ).scalars().all()
    return [r.to_dict() for r in rows]
