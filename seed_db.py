"""
seed_db.py — Populate the SQLite database from the legacy Python data files.

Usage:
    flask seed          # via CLI command registered in run.py
    python seed_db.py   # run directly (creates app context automatically)
"""
from __future__ import annotations

import json
import sys


def seed(app=None):
    """Seed all tables. Pass in a Flask app instance or leave None to auto-create."""
    if app is None:
        from run import create_app
        app = create_app()

    with app.app_context():
        from src.models.main import (
            Airport,
            Artist,
            BackgroundText,
            Church,
            FAQ,
            HotelGroup,
            MediaDownload,
            PastConference,
            Podcast,
            SiteConfig,
            SocialProof,
            Speaker,
            Sponsor,
            TicketPrice,
            Ticker,
            Video,
            db,
        )

        # ------------------------------------------------------------------ #
        # Helpers
        # ------------------------------------------------------------------ #

        def _jdump(value) -> str:
            return json.dumps(value, ensure_ascii=False)

        def _clear_all():
            """Wipe all content tables before re-seeding."""
            for model in [
                Speaker, Sponsor, Artist, TicketPrice, Video, Podcast,
                SocialProof, FAQ, HotelGroup, Airport, PastConference,
                MediaDownload, Ticker, BackgroundText, SiteConfig, Church,
            ]:
                db.session.query(model).delete()
            db.session.commit()

        _clear_all()

        # ------------------------------------------------------------------ #
        # Speakers
        # ------------------------------------------------------------------ #
        from src.data.speakers import speakers as _speakers, gen_z_speakers as _gen_z_speakers

        for i, s in enumerate(_speakers):
            db.session.add(Speaker(
                sort_order=i,
                name=s.get("name", ""),
                image=s.get("image", ""),
                alt=s.get("alt", ""),
                bio=s.get("bio", ""),
                shrink=s.get("shrink"),
                image_x=s.get("image_x"),
                image_y=s.get("image_y"),
                titles_json=_jdump(s.get("titles", [])),
                orgs_json=_jdump(s.get("orgs", [])),
                is_gen_z=False,
            ))

        for i, s in enumerate(_gen_z_speakers):
            db.session.add(Speaker(
                sort_order=i,
                name=s.get("name", ""),
                image=s.get("image", ""),
                alt=s.get("alt", ""),
                bio=s.get("bio", ""),
                shrink=s.get("shrink"),
                image_x=s.get("image_x"),
                image_y=s.get("image_y"),
                titles_json=_jdump(s.get("titles", [])),
                orgs_json=_jdump(s.get("orgs", [])),
                is_gen_z=True,
            ))

        # ------------------------------------------------------------------ #
        # Sponsors
        # ------------------------------------------------------------------ #
        from src.data.sponsors import sponsors as _sponsors

        for category, items in _sponsors.items():
            for i, s in enumerate(items):
                db.session.add(Sponsor(
                    sort_order=i,
                    name=s.get("name", ""),
                    logo_url=s.get("logo_url", ""),
                    category=category,
                    show_on_sponsor_page=s.get("show_on_sponsor_page", True),
                    background_color=s.get("background_color"),
                    scale=s.get("scale"),
                ))

        # ------------------------------------------------------------------ #
        # Artists
        # ------------------------------------------------------------------ #
        from src.data.artists import artists as _artists

        for i, a in enumerate(_artists):
            db.session.add(Artist(
                sort_order=i,
                name=a.get("name", ""),
                image=a.get("image", ""),
                hero_image_x=str(a.get("hero_image_x", "50%")),
                hero_image_y=str(a.get("hero_image_y", "0%")),
                genre=a.get("genre", ""),
                bio=a.get("bio", ""),
                day=a.get("day", ""),
                stage=a.get("stage", ""),
            ))

        # ------------------------------------------------------------------ #
        # Ticket Prices & Meta
        # ------------------------------------------------------------------ #
        from src.data.tickets import ticket_prices as _ticket_prices, ticket_meta as _ticket_meta

        for i, t in enumerate(_ticket_prices):
            db.session.add(TicketPrice(
                sort_order=i,
                name=t.get("name", ""),
                price=t.get("price", ""),
                tax_total=t.get("tax_total"),
                notes_json=_jdump(t.get("notes", [])),
                highlight=t.get("highlight", False),
            ))

        db.session.add(SiteConfig(key="ticket_meta", value_json=_jdump(_ticket_meta)))

        # ------------------------------------------------------------------ #
        # Videos
        # ------------------------------------------------------------------ #
        from src.data.videos import videos as _videos

        for i, v in enumerate(_videos):
            db.session.add(Video(
                sort_order=i,
                url=v.get("url", ""),
                title=v.get("title", ""),
                thumbnail_mobile=v.get("thumbnail_mobile", ""),
            ))

        # ------------------------------------------------------------------ #
        # Podcasts
        # ------------------------------------------------------------------ #
        from src.data.podcasts import podcasts as _podcasts

        for i, p in enumerate(_podcasts):
            db.session.add(Podcast(
                sort_order=i,
                url=p.get("url", ""),
                title=p.get("title", ""),
                thumbnail_mobile=p.get("thumbnail_mobile", ""),
            ))

        # ------------------------------------------------------------------ #
        # Social Proof
        # ------------------------------------------------------------------ #
        from src.data.social_proof import social_proof as _sp, boys_social_proof as _boys_sp

        for i, s in enumerate(_sp):
            db.session.add(SocialProof(
                sort_order=i,
                name=s.get("name", ""),
                title=s.get("title", ""),
                quote=s.get("quote", ""),
                alt=s.get("alt", ""),
                img_json=_jdump(s.get("img", [])),
                is_boys=False,
            ))

        for i, s in enumerate(_boys_sp):
            db.session.add(SocialProof(
                sort_order=i,
                name=s.get("name", ""),
                title=s.get("title", ""),
                quote=s.get("quote", ""),
                alt=s.get("alt", ""),
                img_json=_jdump(s.get("img", [])),
                is_boys=True,
            ))

        # ------------------------------------------------------------------ #
        # FAQs
        # ------------------------------------------------------------------ #
        from src.data.FAQ import FAQ as _faq

        for category, items in _faq.items():
            for i, q in enumerate(items):
                answer_list = q.get("answer_list")
                db.session.add(FAQ(
                    sort_order=i,
                    category=category,
                    question=q.get("question", ""),
                    answer=q.get("answer"),
                    answer_html=q.get("answer_html"),
                    answer_list_json=_jdump(answer_list) if answer_list is not None else None,
                ))

        # ------------------------------------------------------------------ #
        # Hotel Groups  — hotels page
        # ------------------------------------------------------------------ #
        from src.data.hotels import hotels as _hotels_data

        # Store the meta (hero + important_note) as a SiteConfig
        db.session.add(SiteConfig(key="hotels_meta", value_json=_jdump({
            "hero": _hotels_data.get("hero", {}),
            "important_note": _hotels_data.get("important_note", ""),
            "cta": _hotels_data.get("cta", {}),
        })))

        for i, group in enumerate(_hotels_data.get("options", [])):
            db.session.add(HotelGroup(
                sort_order=i,
                name=group.get("name", ""),
                distance=group.get("distance", ""),
                details=group.get("details", ""),
                hotels_json=_jdump(group.get("hotels", [])),
                source="hotels",
            ))

        # ------------------------------------------------------------------ #
        # Accommodations (hotels + airports)
        # ------------------------------------------------------------------ #
        from src.data.accommodations import hotel_options as _hotel_options, travel_info as _travel_info

        db.session.add(SiteConfig(key="travel_info_meta", value_json=_jdump({
            "overview": _travel_info.get("overview", ""),
        })))

        for i, group in enumerate(_hotel_options):
            db.session.add(HotelGroup(
                sort_order=i,
                name=group.get("name", ""),
                distance=group.get("distance", ""),
                details=group.get("details", ""),
                hotels_json=_jdump(group.get("hotels", [])),
                source="accommodations",
            ))

        for i, airport in enumerate(_travel_info.get("airports", [])):
            db.session.add(Airport(
                sort_order=i,
                name=airport.get("name", ""),
                distance=airport.get("distance", ""),
                drive_time=airport.get("drive_time", ""),
                route_json=_jdump(airport.get("route", [])),
                notes=airport.get("notes", ""),
            ))

        # ------------------------------------------------------------------ #
        # Camping
        # ------------------------------------------------------------------ #
        from src.data.camping import camping as _camping
        db.session.add(SiteConfig(key="camping", value_json=_jdump(_camping)))

        # ------------------------------------------------------------------ #
        # Past Conferences
        # ------------------------------------------------------------------ #
        from src.data.about_smn import about_smn_conferences as _past_confs

        for i, conf in enumerate(_past_confs):
            db.session.add(PastConference(
                sort_order=i,
                year=conf.get("year", 0),
                name=conf.get("name", ""),
                summary=conf.get("summary", ""),
                videos_json=_jdump(conf.get("videos", [])),
            ))

        # ------------------------------------------------------------------ #
        # Invite
        # ------------------------------------------------------------------ #
        from src.data.invite import invite as _invite
        db.session.add(SiteConfig(key="invite", value_json=_jdump(_invite)))

        # ------------------------------------------------------------------ #
        # The Play
        # ------------------------------------------------------------------ #
        from src.data.the_play import the_play as _the_play
        db.session.add(SiteConfig(key="the_play", value_json=_jdump(_the_play)))

        # ------------------------------------------------------------------ #
        # Wives
        # ------------------------------------------------------------------ #
        from src.data.wives import wives as _wives
        db.session.add(SiteConfig(key="wives", value_json=_jdump(_wives)))

        # ------------------------------------------------------------------ #
        # Media Downloads
        # ------------------------------------------------------------------ #
        from src.data.media_downloads import media_downloads as _media_downloads

        for i, m in enumerate(_media_downloads):
            db.session.add(MediaDownload(
                sort_order=i,
                external_id=m.get("id", ""),
                label=m.get("label", ""),
                assets_json=_jdump(m.get("assets", [])),
            ))

        # ------------------------------------------------------------------ #
        # Tickers
        # ------------------------------------------------------------------ #
        from src.data.tickers import ticketers as _ticketers

        for ticker_name, texts in _ticketers.items():
            for i, text in enumerate(texts):
                db.session.add(Ticker(
                    sort_order=i,
                    ticker_name=ticker_name,
                    text=text,
                ))

        # ------------------------------------------------------------------ #
        # Background Text
        # ------------------------------------------------------------------ #
        from src.data.background_text import background_1 as _bg1

        for i, text in enumerate(_bg1):
            db.session.add(BackgroundText(
                sort_order=i,
                group_name="background_1",
                text=text,
            ))

        # ------------------------------------------------------------------ #
        # Churches
        # ------------------------------------------------------------------ #
        from src.data.churches import churches as _churches

        for i, c in enumerate(_churches):
            db.session.add(Church(
                sort_order=i,
                name=c["name"],
                logo_url=c.get("logo_url", ""),
                logo_bg=c.get("logo_bg", ""),
                background_color=c.get("background_color", ""),
                scale=c.get("scale", 1.0),
                active=True,
            ))

        # ------------------------------------------------------------------ #
        # Commit everything
        # ------------------------------------------------------------------ #
        db.session.commit()
        print("✓ Database seeded successfully.")


if __name__ == "__main__":
    seed()
