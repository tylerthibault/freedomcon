from datetime import date
from os import getenv
import re
import ssl as _ssl
import time as _time
import urllib.request as _urllib_req
try:
    import certifi as _certifi
    _SSL_CTX = _ssl.create_default_context(cafile=_certifi.where())
except ImportError:
    _SSL_CTX = None


from flask import Blueprint, Response, redirect, render_template, request, stream_with_context, url_for
from src.services.main import (
    get_artists,
    get_background_text,
    get_boys_social_proof,
    get_camping,
    get_faq,
    get_gen_z_speakers,
    get_hotels_data,
    get_hotel_groups,
    get_invite,
    get_media_downloads,
    get_past_conferences,
    get_podcasts,
    get_social_proof,
    get_speakers,
    get_the_play,
    get_ticket_context,
    get_ticketers,
    get_ticker,
    get_travel_info,
    get_videos,
    get_visible_sponsors,
    get_wives,
    get_churches,
)

public_bp = Blueprint("public", __name__)
SITE_URL = "https://www.freedomcon26.com"
ASSET_BASE_URL = getenv("ASSET_BASE_URL", "").strip().rstrip("/")
R2_PUBLIC_URL   = getenv("R2_PUBLIC_URL",   "").strip().rstrip("/")


def extract_youtube_id(url: str) -> str:
	if "watch?v=" in url:
		return url.split("watch?v=", 1)[1].split("&", 1)[0]
	if "youtu.be/" in url:
		return url.split("youtu.be/", 1)[1].split("?", 1)[0]
	if "/embed/" in url:
		return url.split("/embed/", 1)[1].split("?", 1)[0]
	return ""


def extract_youtube_start(url: str) -> int:
	"""Return the t= or start= timestamp (in seconds) from a YouTube URL, or 0."""
	for param in ("t=", "start="):
		if param in url:
			raw = url.split(param, 1)[1].split("&", 1)[0].split("#", 1)[0]
			try:
				return max(0, int(raw))
			except ValueError:
				pass
	return 0


def normalize_video_thumbnail_path(path: str) -> str:
	trimmed = str(path).strip().lstrip("/")
	if not trimmed:
		return "img/TheGuys-WithLogoNoFeet.avif"
	if trimmed.startswith(("img/", "videos/")):
		return trimmed
	if "/" not in trimmed:
		return f"videos/{trimmed}"
	return trimmed


def normalize_optional_thumbnail_path(path: str | None) -> str | None:
	raw = str(path or "").strip()
	if not raw:
		return None
	if raw.startswith(("http://", "https://")):
		return raw
	return normalize_video_thumbnail_path(raw)


def build_youtube_thumbnail_urls(youtube_id: str) -> dict[str, str]:
	base_url = f"https://i.ytimg.com/vi/{youtube_id}"
	return {
		"desktop": f"{base_url}/maxresdefault.jpg",
		"desktop_fallback": f"{base_url}/hqdefault.jpg",
	}


def build_media_section(
	*,
	section_id: str,
	eyebrow: str,
	title: str,
	aria_label: str,
	items: list[dict[str, object]],
	initial_count: int = 4,
	reveal_count: int = 6,
	play_label: str = "Play Video",
	show_more_label: str = "Show More",
	show_all_label: str = "Show All",
) -> dict[str, object]:
	normalized_items: list[dict[str, object]] = []

	for index, item in enumerate(items, start=1):
		video_url = str(item.get("url", "")).strip()
		youtube_id = str(item.get("youtube_id") or extract_youtube_id(video_url)).strip()
		if not youtube_id:
			continue

		youtube_thumbnails = build_youtube_thumbnail_urls(youtube_id)
		normalized_items.append(
			{
				"title": item.get("title") or f"{title} {index}",
				"youtube_id": youtube_id,
				"start": item.get("start") or extract_youtube_start(video_url),
				"alt": item.get("alt") or f"{title} thumbnail {index}",
				"thumbnail_mobile": normalize_optional_thumbnail_path(
					item.get("thumbnail_mobile") or item.get("thumbnail")
				),
				"mobile_image_x": item.get("mobile_image_x"),
				"thumbnail_desktop": youtube_thumbnails["desktop"],
				"thumbnail_desktop_fallback": youtube_thumbnails["desktop_fallback"],
				"play_label": item.get("play_label") or play_label,
			}
		)

	return {
		"section_id": section_id,
		"eyebrow": eyebrow,
		"title": title,
		"aria_label": aria_label,
		"initial_count": max(0, int(initial_count)),
		"reveal_count": max(0, int(reveal_count)),
		"show_more_label": show_more_label,
		"show_all_label": show_all_label,
		"play_label": play_label,
		"items": normalized_items,
	}


def strip_html_tags(value: str) -> str:
	return re.sub(r"<[^>]+>", "", value).strip()


def build_faq_schema(faq_content: dict[str, list[dict[str, object]]]) -> dict[str, object]:
	main_entities: list[dict[str, object]] = []

	for entries in faq_content.values():
		for item in entries:
			question = str(item.get("question", "")).strip()
			if not question:
				continue

			answer_text = ""
			if item.get("answer"):
				answer_text = str(item.get("answer", "")).strip()
			elif item.get("answer_html"):
				answer_text = strip_html_tags(str(item.get("answer_html", "")))
			elif item.get("answer_list"):
				answer_list = item.get("answer_list", [])
				if isinstance(answer_list, list):
					answer_text = " ".join(str(entry).strip() for entry in answer_list if str(entry).strip())

			if not answer_text:
				continue

			main_entities.append(
				{
					"@type": "Question",
					"name": question,
					"acceptedAnswer": {
						"@type": "Answer",
						"text": answer_text,
					},
				}
			)

	return {
		"@context": "https://schema.org",
		"@type": "FAQPage",
		"mainEntity": main_entities,
	}


# ---------------------------------------------------------------------------
# Simple module-level TTL cache for global promos (avoids a DB hit on every
# single request). TTL is intentionally short so admin changes surface
# quickly. Call invalidate_promo_cache() from admin views after any save.
# ---------------------------------------------------------------------------
_PROMO_CACHE_TTL = 60  # seconds
_promo_cache: list | None = None
_promo_cache_at: float = 0.0


def invalidate_promo_cache() -> None:
	"""Force the next request to re-query promos from the database."""
	global _promo_cache, _promo_cache_at
	_promo_cache = None
	_promo_cache_at = 0.0


@public_bp.app_context_processor
def inject_global_urgency() -> dict[str, object]:
	global _promo_cache, _promo_cache_at

	def asset_url(path: str) -> str:
		# Already an absolute URL (e.g. full CDN URL stored in DB) — return as-is.
		if path.startswith("http://") or path.startswith("https://"):
			return path
		normalized = path.lstrip("/")
		# Images served from Cloudflare R2 when R2_PUBLIC_URL is set.
		if R2_PUBLIC_URL and normalized.startswith("img/"):
			return f"{R2_PUBLIC_URL}/{normalized}"
		if ASSET_BASE_URL and normalized.startswith(("pdfs/", "downloads/", "media/")):
			return f"{ASSET_BASE_URL}/{normalized}"
		return url_for("static", filename=normalized)

	now = _time.monotonic()
	if _promo_cache is None or (now - _promo_cache_at) > _PROMO_CACHE_TTL:
		from src.models.main import Promo
		activepromos = Promo.query.filter_by(active=True).order_by(Promo.sort_order).all()
		_promo_cache = [p.to_dict() for p in activepromos]
		_promo_cache_at = now

	return {
		"asset_url": asset_url,
		"asset_base_url": ASSET_BASE_URL,
		"r2_public_url": R2_PUBLIC_URL,
		"global_promos": _promo_cache,
	}


def build_seo(
	*,
	title: str,
	description: str,
	path: str,
	canonical_path: str | None = None,
	robots: str = "index,follow",
	og_type: str = "website",
	image_path: str = "/static/img/Freedom_con_front_on_black.webp?v=20260417",
) -> dict[str, str]:
	resolved_canonical = canonical_path or path
	resolved_image = image_path if image_path.startswith("http") else f"{SITE_URL}{image_path}"

	return {
		"title": title,
		"description": description,
		"canonical_url": f"{SITE_URL}{resolved_canonical}",
		"robots": robots,
		"og_type": og_type,
		"og_image_url": resolved_image,
		"site_name": "Freedom Con",
		"twitter_card": "summary_large_image",
	}


# @public_bp.get("/alt")
# def landing_alt() -> str:
# 	trailers_data = []
# 	for index, video in enumerate(videos_data, start=1):
# 		video_url = str(video.get("url", "")).strip()
# 		youtube_id = extract_youtube_id(video_url)
# 		if not youtube_id:
# 			continue
# 		thumbnail_mobile = normalize_video_thumbnail_path(
# 			video.get("thumbnail_mobile") or video.get("thumbnail") or ""
# 		)
# 		thumbnail_desktop = f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg"
# 		trailers_data.append(
# 			{
# 				"title": video.get("title") or f"Freedom Con Trailer {index}",
# 				"youtube_id": youtube_id,
# 				"thumbnail_mobile": thumbnail_mobile,
# 				"thumbnail_desktop": thumbnail_desktop,
# 				"alt": video.get("alt") or f"Freedom Con trailer thumbnail {index}",
# 			}
# 		)
# 	cta_2 = {
# 		"image": "img/TheGuysFadeFeet.avif",
# 	}
# 	crowder_audio = {
# 		"src": getenv("CROWDER_AUDIO_URL", "").strip() or "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/02_Grave%20Robber.wav",
# 		"title": "02_Grave Robber",
# 	}
# 	event_schema = {
# 		"@context": "https://schema.org",
# 		"@type": "Event",
# 		"name": "Freedom Con 2026",
# 		"description": "Join Freedom Con 2026 at The Gorge Amphitheatre in George, WA for two days of speakers, worship, brotherhood, and leadership challenge.",
# 		"startDate": "2026-06-19T17:00:00-07:00",
# 		"endDate": "2026-06-20T22:00:00-07:00",
# 		"eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
# 		"eventStatus": "https://schema.org/EventScheduled",
# 		"image": [f"{SITE_URL}/static/img/TheGuys-WithLogoNoFeet.avif"],
# 		"location": {
# 			"@type": "Place",
# 			"name": "The Gorge Amphitheatre",
# 			"address": {
# 				"@type": "PostalAddress",
# 				"streetAddress": "754 Silica Rd NW",
# 				"addressLocality": "Quincy",
# 				"addressRegion": "WA",
# 				"postalCode": "98848",
# 				"addressCountry": "US",
# 			},
# 		},
# 		"organizer": {
# 			"@type": "Organization",
# 			"name": "Stronger Man Nation",
# 			"url": SITE_URL,
# 		},
# 		"offers": {
# 			"@type": "Offer",
# 			"url": f"{SITE_URL}/tickets",
# 			"priceCurrency": "USD",
# 			"availability": "https://schema.org/InStock",
# 		},
# 	}
# 	return render_template(
# 		"public/landing/index.html",
# 		social_proof=social_proof,
# 		ticketer1=ticketer1,
# 		ticketers=ticketers,
# 		background_text=background_1,
# 		speakers=speakers_data,
# 		trailers=trailers_data,
# 		cta_2=cta_2,
# 		crowder_audio=crowder_audio,
# 		structured_data=[event_schema],
# 		seo=build_seo(
# 			title="A Congress of Christian Men at The Gorge Amphitheatre",
# 			description="Join Freedom Con 2026 at The Gorge Amphitheatre in George, WA for two days of speakers, worship, brotherhood, and leadership challenge.",
# 			path="/",
# 			image_path="/static/img/title_on_black.webp?v=20260417",
# 		),
# 	)

@public_bp.get("/alt")
def landing_alt() -> str:
	return redirect(url_for("public.landing"))
	context = {
		"speakers": speakers_data,
	}
	return render_template('public/archived/landing_v7/index.html', **context)

@public_bp.get("/")
def landing() -> str:
	"""Homepage — Customer-as-Hero / Story Brand variant."""
	videos_data = get_videos()
	podcasts_data = get_podcasts()
	social_proof = get_social_proof()
	boys_social_proof = get_boys_social_proof()
	speakers_data = get_speakers()
	ticket_ctx = get_ticket_context()
	conference_trailers_section = build_media_section(
		section_id="conference-trailers",
		eyebrow="Watch",
		title="FREEDOM CON Trailers",
		aria_label="Freedom Con trailers",
		items=videos_data,
		initial_count=4,
		reveal_count=6,
		play_label="Play Video",
		show_more_label="Show More",
		show_all_label="Show All",
	)
	podcast_section = build_media_section(
		section_id="podcasts",
		eyebrow="Listen",
		title="FREEDOM CON Podcasts",
		aria_label="Freedom Con podcasts",
		items=podcasts_data,
		initial_count=4,
		reveal_count=6,
		play_label="Play Podcast",
		show_more_label="Show More",
		show_all_label="Show All",
	)
	visible_sponsors = get_visible_sponsors()
	event_schema = {
		"@context": "https://schema.org",
		"@type": "Event",
		"name": "Freedom Con 2026",
		"description": "A two-day outdoor men's conference at The Gorge Amphitheatre. Speakers, worship, bold preaching, Crowder, camping, and the Columbia River.",
		"startDate": "2026-06-19T17:00:00-07:00",
		"endDate": "2026-06-20T22:00:00-07:00",
		"eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
		"eventStatus": "https://schema.org/EventScheduled",
		"image": [f"{SITE_URL}/static/img/TheGuys-WithLogoNoFeet.avif"],
		"location": {
			"@type": "Place",
			"name": "The Gorge Amphitheatre",
			"address": {
				"@type": "PostalAddress",
				"streetAddress": "754 Silica Rd NW",
				"addressLocality": "Quincy",
				"addressRegion": "WA",
				"postalCode": "98848",
				"addressCountry": "US",
			},
		},
		"organizer": {
			"@type": "Organization",
			"name": "Stronger Man Nation",
			"url": SITE_URL,
		},
		"offers": {
			"@type": "Offer",
			"url": f"{SITE_URL}/tickets",
			"priceCurrency": "USD",
			"availability": "https://schema.org/InStock",
		},
	}
	return render_template(
		"public/landing copy/index.html",
		social_proof=social_proof,
		boys_social_proof=boys_social_proof,
		speakers=speakers_data,
		trailers=conference_trailers_section["items"],
		conference_trailers_section=conference_trailers_section,
		podcast_section=podcast_section,
		ticket_prices=ticket_ctx["ticket_prices"],
		ticket_meta=ticket_ctx["ticket_meta"],
		sponsors=visible_sponsors,
		structured_data=[event_schema],
		seo=build_seo(
			title="Freedom Con 2026 | A Congress of Christian Men at The Gorge Amphitheatre",
			description="Two-day outdoor men's conference at The Gorge Amphitheatre, Father's Day Weekend June 19–20 2026. Worship, bold preaching, Crowder, camping, and the Columbia River.",
			path="/",
		),
	)


@public_bp.get("/faq")
def faq_redirect() -> str:
	return redirect(url_for("public.faqs"), 301)


@public_bp.get("/faqs")
def faqs() -> str:
	faq_content = get_faq()
	return render_template(
		"public/FAQs/index.html",
		faq_content=faq_content,
		structured_data=[build_faq_schema(faq_content)],
		seo=build_seo(
			title="FREEDOM CON FAQs | Event, Travel, and Camping Questions",
			description="Get answers to common Freedom Con questions including event details, what to bring, travel guidance, and camping information.",
			path="/faqs",
		),
	)


@public_bp.get("/speakers")
def speakers() -> str:
	return render_template(
		"public/speakers/index.html",
		speakers=get_speakers(),
		seo=build_seo(
			title="FREEDOM CON Speakers | 2026 Conference Lineup",
			description="Meet the Freedom Con 2026 speaker lineup featuring pastors, veterans, leaders, and voices challenging men toward faith and statesmanship.",
			path="/speakers",
		),
	)


@public_bp.get("/speakers/gen-z")
def gen_z_speakers_page() -> str:
	return render_template(
		"public/speakers/gen_z.html",
		speakers=get_gen_z_speakers(),
		seo=build_seo(
			title="FREEDOM CON Gen Z Speakers | 2026 Conference Lineup",
			description="Meet the Gen Z speaker lineup for Freedom Con 2026.",
			path="/speakers/gen-z",
		),
	)


@public_bp.get("/artists")
def artists_page() -> str:
	return render_template(
		"public/artists/index.html",
		artists=get_artists(),
		seo=build_seo(
			title="FREEDOM CON Artist | Live Worship and Concert",
			description="See the featured Freedom Con artist and live worship experience planned for Father’s Day weekend 2026.",
			path="/artists",
		),
	)


@public_bp.get("/past-conferences")
def past_conferences_page() -> str:
	conference_sections: list[dict[str, object]] = []

	for conference in get_past_conferences():
		year = conference.get("year")
		conference_name = str(conference.get("name") or f"Stronger Man Conference {year}").strip()
		conference_theme = str(conference.get("theme") or "").strip()
		conference_summary = str(conference.get("summary") or "").strip()
		conference_videos = conference.get("videos") if isinstance(conference.get("videos"), list) else []

		media_section = build_media_section(
			section_id=f"smn-{year}",
			eyebrow=f"{year} Conference",
			title=f"{conference_name} Videos",
			aria_label=f"{conference_name} videos",
			items=conference_videos,
			initial_count=4,
			reveal_count=6,
			play_label="Play Video",
			show_more_label="Show More",
			show_all_label="Show All",
		)

		conference_sections.append(
			{
				"year": year,
				"name": conference_name,
				"theme": conference_theme,
				"summary": conference_summary,
				"media_section": media_section,
				"has_videos": bool(media_section.get("items")),
				"empty_message": conference.get("empty_message", ""),
			}
		)

	return render_template(
		"public/about_smn/index.html",
		conference_sections=conference_sections,
		seo=build_seo(
			title="Past SMN Conferences | The Road to The Gorge",
			description="Explore past Stronger Man Nation conferences and the Road to The Gorge journey leading into Freedom Con.",
			path="/past-conferences",
		),
	)


@public_bp.get("/accommodations")
def accommodations_page() -> str:
	return render_template(
		"public/accomodations/index.html",
		travel_info=get_travel_info(),
		hotel_options=get_hotel_groups("accommodations"),
		seo=build_seo(
			title="FREEDOM CON Accommodations | Travel, Camping, and Lodging",
			description="Plan your Freedom Con stay with travel routes, camping options, and nearby hotel listings around The Gorge Amphitheatre.",
			path="/accommodations",
		),
	)


@public_bp.get("/travel")
def travel_page() -> str:
	return render_template(
		"public/traveling/index.html",
		travel_info=get_travel_info(),
		seo=build_seo(
			title="FREEDOM CON Travel Guide | Getting to The Gorge Amphitheatre",
			description="Plan your drive to The Gorge Amphitheatre for Freedom Con. Airport routes, drive times, and travel tips from Seattle and Spokane.",
			path="/travel",
		),
	)


@public_bp.get("/the-venue")
def the_venue_page() -> str:
	return render_template(
		"public/the_venue/index.html",
		seo=build_seo(
			title="The Venue | The Gorge Amphitheatre, Washington",
			description="Find Freedom Con at The Gorge Amphitheatre in George, Washington, with map details and location information.",
			path="/the-venue",
		),
	)


@public_bp.get("/vendors")
def vendors_page() -> str:
	return render_template(
		"public/vendors/index.html",
		seo=build_seo(
			title="FREEDOM CON Vendors | Information Coming Soon",
			description="Vendor information for Freedom Con is coming soon. Check back for details on participating partners and on-site offerings.",
			path="/vendors",
		),
	)


@public_bp.get("/sponsor")
def sponsors_page() -> str:
	return render_template(
		"public/sponsor/index.html",
		sponsors=get_visible_sponsors(),
		seo=build_seo(
			title="Sponsor Freedom Con 2026 | Partner With Us",
			description="Partner with Freedom Con 2026 and reach thousands of Christian men at The Gorge Amphitheater. Explore sponsorship opportunities.",
			path="/sponsor",
		),
	)


_TRUSTED_CDN = "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/"

@public_bp.get("/press/download")
def press_download() -> Response:
	"""Stream a trusted CDN asset to the browser as an attachment.

	Previous implementation called resp.read() which buffered the entire file
	into worker memory and blocked the Gunicorn worker for up to 30 seconds,
	guaranteeing H12 timeouts on large files. This version:
	  - Opens the CDN connection with a 10-second timeout (fail fast)
	  - Streams 64 KB chunks directly to the client without buffering
	  - Releases the worker incrementally so Gunicorn's 25-second timeout
	    is not hit unless the CDN itself is genuinely unresponsive
	"""
	url  = request.args.get("url",  "").strip()
	name = request.args.get("name", "download").strip()

	if not url.startswith(_TRUSTED_CDN):
		return Response("Forbidden", status=403)

	# Build safe filename before opening the network connection.
	import re as _re
	from urllib.parse import quote as _urlquote, unquote as _urlunquote
	url_path = url.split("?")[0]
	last_seg = url_path.rsplit("/", 1)[-1]
	try:
		last_seg = _urlunquote(last_seg)
	except Exception:
		pass
	dot_idx = last_seg.rfind(".")
	ext = last_seg[dot_idx:] if dot_idx != -1 else ""
	# Strip control characters (including CR/LF) and quotes from user-supplied name.
	safe_name = _re.sub(r'[\x00-\x1f\x7f\r\n"]', "", name).strip()
	if ext and not safe_name.lower().endswith(ext.lower()):
		safe_name += ext
	ascii_name = safe_name.encode("ascii", errors="replace").decode("ascii").replace("?", "_")
	rfc5987_name = _urlquote(safe_name, safe=" !#$&+-.^_`|~")
	content_disposition = (
		f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{rfc5987_name}'
	)

	try:
		req = _urllib_req.Request(url, headers={"User-Agent": "Mozilla/5.0"})
		kwargs: dict = {"timeout": 10}  # fail fast — don't hold the worker indefinitely
		if _SSL_CTX:
			kwargs["context"] = _SSL_CTX
		# Open the connection now to read Content-Type; body is streamed lazily below.
		cdn_resp = _urllib_req.urlopen(req, **kwargs)
		content_type = cdn_resp.headers.get("Content-Type", "application/octet-stream")
	except Exception as e:
		return Response(f"Failed to reach CDN: {e}", status=502)

	_CHUNK = 64 * 1024  # 64 KB

	@stream_with_context
	def _generate():
		try:
			while True:
				chunk = cdn_resp.read(_CHUNK)
				if not chunk:
					break
				yield chunk
		finally:
			cdn_resp.close()

	return Response(
		_generate(),
		headers={
			"Content-Disposition": content_disposition,
			"Content-Type": content_type,
			"Cache-Control": "public, max-age=3600",
		},
	)


@public_bp.get("/press")
def press_page() -> str:
	# return redirect(url_for("public.landing"))
	media_kit_download_url = getenv("MEDIA_KIT_DOWNLOAD_URL", "").strip() or url_for(
		"static", filename="pdfs/FreedomCon-Media-Kit-v1.zip"
	)
	media_kit_image_url = getenv("MEDIA_KIT_IMAGE_URL", "").strip() or url_for(
		"static", filename="img/freedom_con_media_kit_flyer.webp"
	)
	men_picture_url = getenv("PRESS_MEN_PICTURE_URL", "").strip() or url_for(
		"static", filename="img/TheGuys-WithLogoNoFeet.avif"
	)
	formsubmit_action = getenv("PRESS_FORMSUBMIT_ACTION", "").strip() or "https://formsubmit.co/info@strongermannation.com"
	formsubmit_next = f"{SITE_URL}/thankyou"

	press_assets = get_media_downloads()

	return render_template(
		"public/press/index.html",
		media_kit_download_url=media_kit_download_url,
		media_kit_image_url=media_kit_image_url,
		men_picture_url=men_picture_url,
		formsubmit_action=formsubmit_action,
		formsubmit_next=formsubmit_next,
		press_assets=press_assets,
		seo=build_seo(
			title="FREEDOM CON Press & Media Kit",
			description="Download the Freedom Con media kit and connect with us for sponsor interviews, press requests, and partnership details.",
			path="/press",
		),
	)


@public_bp.get("/worship")
def worship_page() -> str:
	return render_template(
		"public/worship/index.html",
		seo=build_seo(
			title="FREEDOM CON Worship | Information Coming Soon",
			description="More worship information for Freedom Con is coming soon. Check back for updates on worship experiences and schedule details.",
			path="/worship",
		),
	)


@public_bp.get("/tickets")
def tickets_page() -> str:
	from src.models.main import Promo
	ticket_context = get_ticket_context()  # queries DB
	ticket_promos = Promo.query.filter_by(active=True, show_on_tickets=True).order_by(Promo.sort_order).all()
	return render_template(
		"public/tickets/index.html",
		ticket_meta=ticket_context["ticket_meta"],
		ticket_prices=ticket_context["ticket_prices"],
		ticket_promos=[p.to_dict() for p in ticket_promos],
		seo=build_seo(
			title="FREEDOM CON Tickets | 2026 Pricing and Registration",
			description="View Freedom Con 2026 ticket options, pricing tiers, and secure your spot for Father’s Day weekend at The Gorge.",
			path="/tickets",
		),
	)


@public_bp.get("/venue-map")
def venue_map_page() -> str:
	return render_template(
		"public/venue_map/index.html",
		seo=build_seo(
			title="FREEDOM CON Venue Map | The Gorge Amphitheatre",
			description="View the Freedom Con venue map for entrances, stage area, parking, camping zones, and key amenities at The Gorge Amphitheatre.",
			path="/venue-map",
			image_path="/static/img/Map_v1.webp",
		),
	)


@public_bp.get("/pastors")
def pastors_page() -> str:
	return render_template(
		"public/pastors/index.html",
		seo=build_seo(
			title="Pastor VIP | Freedom Con 2026",
			description="Washington pastors are watching their congregations leave the state. Freedom Con is gathering shepherds to identify the problem, unite, and make a plan.",
			path="/pastors",
		),
	)


@public_bp.get("/vision")
def vision_page() -> str:
	return render_template(
		"public/vision/index.html",
		seo=build_seo(
			title="The Vision | Freedom Con 2026",
			description="Discover the vision and mission behind Freedom Con 2026 — a movement calling men to faith, statesmanship, and brotherhood.",
			path="/vision",
		),
	)


@public_bp.get("/experience")
def experience_page() -> str:
	return render_template(
		"public/experience/index.html",
		seo=build_seo(
			title="The Experience | Freedom Con 2026",
			description="Explore the full Freedom Con experience — competitions, side stage, schedule, and everything happening at The Gorge.",
			path="/experience",
		),
	)


@public_bp.get("/thankyou")
def thankyou_page() -> str:
	return render_template(
		"public/thankyou/index.html",
		seo=build_seo(
			title="Thank You | Freedom Con",
			description="Thank you for reaching out to Freedom Con. We'll be in touch shortly.",
			path="/thankyou",
			robots="noindex,follow",
		),
	)


@public_bp.get("/videos")
def videos_page() -> str:
	trailers_section = build_media_section(
		section_id="conference-trailers",
		eyebrow="Watch",
		title="FREEDOM CON Trailers",
		aria_label="Freedom Con trailers",
		items=get_videos(),
		initial_count=4,
		reveal_count=6,
		play_label="Play Video",
		show_more_label="Show More",
		show_all_label="Show All",
	)
	podcast_section = build_media_section(
		section_id="podcasts",
		eyebrow="Listen",
		title="FREEDOM CON Podcasts",
		aria_label="Freedom Con podcasts",
		items=get_podcasts(),
		initial_count=4,
		reveal_count=4,
		play_label="Play Podcast",
		show_more_label="Show More",
		show_all_label="Show All",
	)
	return render_template(
		"public/videos/index.html",
		trailers_section=trailers_section,
		podcast_section=podcast_section,
		seo=build_seo(
			title="Videos | Freedom Con 2026",
			description="Watch Freedom Con trailers and podcast episodes from Stronger Man Nation.",
			path="/videos",
		),
	)


# @public_bp.get("/podcasts")
# def podcasts_page() -> str:
# 	podcast_section = build_media_section(
# 		section_id="podcasts",
# 		eyebrow="Listen",
# 		title="FREEDOM CON odcasts",
# 		aria_label="Freedom Con podcasts",
# 		items=podcasts_data,
# 		initial_count=4,
# 		reveal_count=4,
# 		play_label="Play Podcast",
# 		show_more_label="Show More",
# 		show_all_label="Show All",
# 	)
# 	return render_template(
# 		"public/podcasts/index.html",
# 		podcast_section=podcast_section,
# 		seo=build_seo(
# 			title="FREEDOM CON Podcasts | Freedom Con 2026",
# 			description="Listen to Freedom Con podcast episodes from Stronger Man Nation — faith, freedom, and men leading well.",
# 			path="/podcasts",
# 		),
# 	)


@public_bp.get("/story")
def story_page() -> str:
	return render_template(
		"public/story/index.html",
		seo=build_seo(
			title="The Freedom Con Story | Long Form Videos, Podcasts & Media",
			description="Explore the Freedom Con story through long form videos, podcast episodes, and the official media kit.",
			path="/story",
		),
	)


@public_bp.get("/venue-map-svg")
def venue_map_svg_page() -> str:
	return redirect(url_for("public.venue_map_page"), code=301)


@public_bp.get("/robots.txt")
def robots_txt() -> Response:
	content = "\n".join(
		[
			"User-agent: *",
			"Allow: /",
			"Disallow: /venue-map-svg",
			f"Sitemap: {SITE_URL}/sitemap.xml",
		]
	)
	return Response(f"{content}\n", mimetype="text/plain")


@public_bp.get("/sitemap.xml")
def sitemap_xml() -> Response:
	lastmod = date.today().isoformat()
	pages = [
		"/",
		"/vision",
		"/experience",
		"/about-smn",
		"/story",
		"/faqs",
		"/speakers",
		"/artists",
		"/press",
		"/worship",
		"/vendors",
		"/accommodations",
		"/travel",
		"/camping",
		"/hotels",
		"/churches",
		"/food-and-drinks",
		"/venue-map",
		"/drinks",
		"/the-venue",
		"/tickets",
		"/invite",
		"/wives",
	]
	urls = [{"loc": f"{SITE_URL}{path}", "lastmod": lastmod} for path in pages]
	xml = render_template("sitemap.xml", urls=urls)
	return Response(xml, mimetype="application/xml")



@public_bp.get("/wives")
def wives_page() -> str:
	formsubmit_action = getenv("WIVES_FORMSUBMIT_ACTION", "").strip() or "https://formsubmit.co/ladies.freedomcon26@strongermannation.com"
	formsubmit_next = f"{SITE_URL}/thankyou"
	return render_template(
		"public/wives/index.html",
		wives=get_wives(),
		formsubmit_action=formsubmit_action,
		formsubmit_next=formsubmit_next,
		seo=build_seo(
			title="For the Wives | Freedom Con 2026",
			description="A personal message from Sharon McPherson to the wives and families supporting the men of Freedom Con.",
			path="/wives",
		),
	)

@public_bp.get("/prayer_guide")
def prayer_guide_page() -> str:
	return render_template(
		"public/prayer_guide/index.html",
		# prayer_guide=prayer_guide_data,
		seo=build_seo(
			title="Prayer Guide | Freedom Con 2026",
			description="A prayer guide for attendees of Freedom Con 2026.",
			path="/prayer_guide",
		),
	)

@public_bp.get("/invite")
def invite_page() -> str:
	return render_template(
		"public/invite/index.html",
		invite=get_invite(),
		seo=build_seo(
			title="A Personal Invite | Freedom Con 2026",
			description="Personal invitations from Josh McPherson and his sons to the men of Washington for Freedom Con 2026.",
			path="/invite",
		),
	)


@public_bp.get("/schedule")
def schedule_page() -> str:
	return render_template(
		"public/schedule/index.html",
		seo=build_seo(
			title="Schedule | Freedom Con 2026",
			description="Full event schedule for Freedom Con 2026. Two days of speakers, worship, Danny Gokey, and Crowder at The Gorge Amphitheatre.",
			path="/schedule",
		),
	)


@public_bp.get("/the-play")
def the_play_page() -> str:
	return render_template(
		"public/the_play/index.html",
		the_play=get_the_play(),
		seo=build_seo(
			title="The Play | Freedom Con 2026",
			description="Three steps to Freedom Con: Register, Camp, Arrive. Your game plan for Father's Day Weekend at The Gorge.",
			path="/the-play",
		),
	)


@public_bp.get("/camping")
def camping_page() -> str:
	return render_template(
		"public/camping/index.html",
		seo=build_seo(
			title="Camping at The Gorge | Freedom Con 2026",
			description="Stay on-site at The Gorge Amphitheatre. Camping details, check-in times, RV info, and what to bring for Freedom Con 2026.",
			path="/camping",
		),
		camping=get_camping(),
	)


@public_bp.get("/hotels")
def hotels_page() -> str:
	return render_template(
		"public/hotels/index.html",
		hotels=get_hotels_data(),
		seo=build_seo(
			title="Hotels Near The Gorge | Freedom Con 2026",
			description="Hotel and lodging options near The Gorge Amphitheatre for Freedom Con 2026. George, Quincy, Ephrata, and Moses Lake.",
			path="/hotels",
		),
	)


@public_bp.get("/food-and-drinks")
def food_and_drinks_page() -> str:
	return render_template(
		"public/food_and_drinks/index.html",
		seo=build_seo(
			title="Food & Drinks | Freedom Con 2026",
			description="Food and beverage options at The Gorge Amphitheatre for Freedom Con attendees, plus a full drinks list.",
			path="/food-and-drinks",
		),
	)


@public_bp.get("/churches")
def churches_page() -> str:
	return render_template(
		"public/churches/index.html",
		churches=get_churches(),
		seo=build_seo(
			title="Churches | Freedom Con 2026",
			description="Partner churches represented at Freedom Con 2026 and their locations.",
			path="/churches",
		),
	)


@public_bp.get("/drinks")
def drinks_page() -> str:
	return redirect(url_for("public.food_and_drinks_page") + "#drinks", code=301)


#  404 handler
@public_bp.app_errorhandler(404)
def page_not_found(e) -> Response:
	return render_template(
		"public/errors/404.html",
		seo=build_seo(
			title="Page Not Found | Freedom Con",
			description="The page you are looking for cannot be found. Explore Freedom Con 2026 event details, speakers, tickets, and more.",
			path="/404",
			robots="noindex,follow",
		),
	), 404

# 500 handler
@public_bp.app_errorhandler(500)
def internal_server_error(e) -> Response:
	return render_template(
		"public/errors/500.html",
		seo=build_seo(
			title="Server Error | Freedom Con",
			description="An unexpected error occurred. Please try again later or contact support for assistance.",
			path="/500",
			robots="noindex,follow",
		),
	), 500
