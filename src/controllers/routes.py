from datetime import date
from os import getenv
import re
import ssl as _ssl
import urllib.request as _urllib_req
try:
    import certifi as _certifi
    _SSL_CTX = _ssl.create_default_context(cafile=_certifi.where())
except ImportError:
    _SSL_CTX = None


from flask import Blueprint, Response, redirect, render_template, request, url_for
from src.data.FAQ import FAQ
from src.data.accommodations import hotel_options, travel_info
from src.data.artists import artists
from src.data.social_proof import social_proof
from src.data.speakers import speakers as speakers_data
from src.data.videos import videos as videos_data
from src.data.tickers import ticketer1, ticketers
from src.data.tickets import get_ticket_context
from src.data.background_text import background_1
from src.data.sponsors import sponsors
from src.data.about_smn import about_smn_conferences
from src.data.podcasts import podcasts as podcasts_data
from src.data.wives import wives as wives_data
from src.data.invite import invite as invite_data
from src.data.schedule import schedule as schedule_data
from src.data.the_play import the_play as the_play_data
from src.data.camping import camping as camping_data
from src.data.hotels import hotels as hotels_data
from src.data.trailers import trailers as trailers_data
from src.data.media_downloads import media_downloads

public_bp = Blueprint("public", __name__)
SITE_URL = "https://www.freedomcon26.com"
ASSET_BASE_URL = getenv("ASSET_BASE_URL", "").strip().rstrip("/")


def extract_youtube_id(url: str) -> str:
	if "watch?v=" in url:
		return url.split("watch?v=", 1)[1].split("&", 1)[0]
	if "youtu.be/" in url:
		return url.split("youtu.be/", 1)[1].split("?", 1)[0]
	if "/embed/" in url:
		return url.split("/embed/", 1)[1].split("?", 1)[0]
	return ""


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


@public_bp.app_context_processor
def inject_global_urgency() -> dict[str, object]:
	def asset_url(path: str) -> str:
		normalized = path.lstrip("/")
		if ASSET_BASE_URL and normalized.startswith(("pdfs/", "downloads/", "media/")):
			return f"{ASSET_BASE_URL}/{normalized}"
		return url_for("static", filename=normalized)

	return {
		"asset_url": asset_url,
		"asset_base_url": ASSET_BASE_URL,
	}


def build_seo(
	*,
	title: str,
	description: str,
	path: str,
	canonical_path: str | None = None,
	robots: str = "index,follow",
	og_type: str = "website",
	image_path: str = "/static/img/title_on_black.png?v=20260417",
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
# 			image_path="/static/img/title_on_black.png?v=20260417",
# 		),
# 	)

@public_bp.get("/alt")
def landing_alt() -> str:
	return redirect(url_for("public.landing"))
	context = {
		"speakers": speakers_data,
	}
	return render_template('public/landing_v7/index.html', **context)

@public_bp.get("/")
def landing() -> str:
	# return redirect(url_for("public.landing_alt"))
	"""Alt landing page — Customer-as-Hero / Story Brand variant."""
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
	ticket_ctx = get_ticket_context()

	visible_sponsors = {
		"businesses": [
			item for item in sponsors.get("businesses", []) if item.get("show_on_sponsor_page") is True
		],
		"ministries": [
			item for item in sponsors.get("ministries", []) if item.get("show_on_sponsor_page") is True
		],
		"churches": [
			item for item in sponsors.get("churches", []) if item.get("show_on_sponsor_page") is True
		],
	}
	return render_template(
		"public/landing copy/index.html",
		social_proof=social_proof,
		speakers=speakers_data,
		trailers=conference_trailers_section["items"],
		conference_trailers_section=conference_trailers_section,
		podcast_section=podcast_section,
		ticket_prices=ticket_ctx["ticket_prices"],
		ticket_meta=ticket_ctx["ticket_meta"],
		sponsors=visible_sponsors,
		seo=build_seo(
			title="FREEDOM CON 2026 — Father's Day Weekend at The Gorge",
			description="Two-day outdoor men's conference at The Gorge Amphitheatre, Father's Day Weekend June 19–20 2026. Worship, bold preaching, Crowder, camping, and the Columbia River.",
			path="/alt",
			image_path="/static/img/sharable.png?v=20260417",
		),
	)


@public_bp.get("/faqs")
def faqs() -> str:
	return render_template(
		"public/FAQs/index.html",
		faq_content=FAQ,
		structured_data=[build_faq_schema(FAQ)],
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
		speakers=speakers_data,
		seo=build_seo(
			title="FREEDOM CON Speakers | 2026 Conference Lineup",
			description="Meet the Freedom Con 2026 speaker lineup featuring pastors, veterans, leaders, and voices challenging men toward faith and statesmanship.",
			path="/speakers",
		),
	)


@public_bp.get("/artists")
def artists_page() -> str:
	return render_template(
		"public/artists/index.html",
		artists=artists,
		seo=build_seo(
			title="FREEDOM CON Artist | Live Worship and Concert",
			description="See the featured Freedom Con artist and live worship experience planned for Father’s Day weekend 2026.",
			path="/artists",
		),
	)


@public_bp.get("/about-smn")
def about_smn_page() -> str:
	conference_sections: list[dict[str, object]] = []

	for conference in about_smn_conferences:
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
			}
		)

	return render_template(
		"public/about_smn/index.html",
		conference_sections=conference_sections,
		seo=build_seo(
			title="Past SMN Conferences | The Road to The Gorge",
			description="Explore past Stronger Man Nation conferences and the Road to The Gorge journey leading into Freedom Con.",
			path="/about-smn",
		),
	)


@public_bp.get("/accommodations")
def accommodations_page() -> str:
	return render_template(
		"public/accomodations/index.html",
		travel_info=travel_info,
		hotel_options=hotel_options,
		seo=build_seo(
			title="FREEDOM CON Accommodations | Travel, Camping, and Lodging",
			description="Plan your Freedom Con stay with travel routes, camping options, and nearby hotel listings around The Gorge Amphitheatre.",
			path="/accommodations",
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
	visible_sponsors = {
		"businesses": [
			item for item in sponsors.get("businesses", []) if item.get("show_on_sponsor_page") is True
		],
		"ministries": [
			item for item in sponsors.get("ministries", []) if item.get("show_on_sponsor_page") is True
		],
		"churches": [
			item for item in sponsors.get("churches", []) if item.get("show_on_sponsor_page") is True
		],
	}

	return render_template(
		"public/sponsor/index.html",
		sponsors=visible_sponsors,
		seo=build_seo(
			title="Sponsor Freedom Con 2026 | Partner With Us",
			description="Partner with Freedom Con 2026 and reach thousands of Christian men at The Gorge Amphitheater. Explore sponsorship opportunities.",
			path="/sponsor",
		),
	)


_TRUSTED_CDN = "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/"

@public_bp.get("/press/download")
def press_download() -> Response:
	"""Proxy a CDN asset so the browser receives Content-Disposition: attachment."""
	url  = request.args.get("url",  "").strip()
	name = request.args.get("name", "download").strip()

	if not url.startswith(_TRUSTED_CDN):
		return Response("Forbidden", status=403)

	try:
		req = _urllib_req.Request(url, headers={"User-Agent": "Mozilla/5.0"})
		kwargs = {"timeout": 30}
		if _SSL_CTX:
			kwargs["context"] = _SSL_CTX
		with _urllib_req.urlopen(req, **kwargs) as resp:
			content_type = resp.headers.get("Content-Type", "application/octet-stream")
			data = resp.read()
	except Exception as e:
		return Response(f"Failed: {e}", status=502)

	# Build filename: use label + extension extracted from URL
	url_path = url.split("?")[0]
	last_seg = url_path.rsplit("/", 1)[-1]
	try:
		last_seg = _urllib_req.urllib.parse.unquote(last_seg)
	except Exception:
		pass
	dot_idx = last_seg.rfind(".")
	ext = last_seg[dot_idx:] if dot_idx != -1 else ""
	safe_name = name.replace('"', "").strip()
	if ext and not safe_name.lower().endswith(ext.lower()):
		safe_name += ext

	return Response(data, headers={
		"Content-Disposition": f'attachment; filename="{safe_name}"',
		"Content-Type": content_type,
		"Cache-Control": "public, max-age=3600",
	})


@public_bp.get("/press")
def press_page() -> str:
	# return redirect(url_for("public.landing"))
	media_kit_download_url = getenv("MEDIA_KIT_DOWNLOAD_URL", "").strip() or url_for(
		"static", filename="pdfs/FreedomCon-Media-Kit-v1.zip"
	)
	media_kit_image_url = getenv("MEDIA_KIT_IMAGE_URL", "").strip() or url_for(
		"static", filename="img/freedom_con_media_kit_flyer.jpg"
	)
	men_picture_url = getenv("PRESS_MEN_PICTURE_URL", "").strip() or url_for(
		"static", filename="img/TheGuys-WithLogoNoFeet.avif"
	)
	formsubmit_action = getenv("PRESS_FORMSUBMIT_ACTION", "").strip() or "https://formsubmit.co/info@strongermannation.com"
	formsubmit_next = f"{SITE_URL}/thankyou"

	press_assets = media_downloads

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
	ticket_context = get_ticket_context()
	return render_template(
		"public/tickets/index.html",
		ticket_meta=ticket_context["ticket_meta"],
		ticket_prices=ticket_context["ticket_prices"],
		seo=build_seo(
			title="FREEDOM CON Tickets | 2026 Pricing and Registration",
			description="View Freedom Con 2026 ticket options, pricing tiers, and secure your spot for Father’s Day weekend at The Gorge.",
			path="/tickets",
		),
	)


# @public_bp.get("/venue-map")
# def venue_map_page() -> str:
# 	return render_template(
# 		"public/venue_map_svg/index.html",
# 		seo=build_seo(
# 			title="FREEDOM CON Venue Map | The Gorge Amphitheatre",
# 			description="Explore the Freedom Con venue diagram for gates, stage area, parking, camping zones, and key amenities at The Gorge Amphitheatre.",
# 			path="/venue-map",
# 		),
# 	)


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


@public_bp.get("/podcasts")
def podcasts_page() -> str:
	podcast_section = build_media_section(
		section_id="podcasts",
		eyebrow="Listen",
		title="FREEDOM CON odcasts",
		aria_label="Freedom Con podcasts",
		items=podcasts_data,
		initial_count=4,
		reveal_count=4,
		play_label="Play Podcast",
		show_more_label="Show More",
		show_all_label="Show All",
	)
	return render_template(
		"public/podcasts/index.html",
		podcast_section=podcast_section,
		seo=build_seo(
			title="FREEDOM CON Podcasts | Freedom Con 2026",
			description="Listen to Freedom Con podcast episodes from Stronger Man Nation — faith, freedom, and men leading well.",
			path="/podcasts",
		),
	)


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
	return redirect(url_for("public.the_venue_page"), code=301)


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
		"/camping",
		"/hotels",
		"/the-venue",
		"/tickets",
		"/schedule",
		"/the-play",
		"/invite",
		"/wives",
	]
	urls = [{"loc": f"{SITE_URL}{path}", "lastmod": lastmod} for path in pages]
	xml = render_template("sitemap.xml", urls=urls)
	return Response(xml, mimetype="application/xml")



@public_bp.get("/wives")
def wives_page() -> str:
	return render_template(
		"public/wives/index.html",
		wives=wives_data,
		seo=build_seo(
			title="For the Wives | Freedom Con 2026",
			description="A personal message from Sharon McPherson to the wives and families supporting the men of Freedom Con.",
			path="/wives",
		),
	)


@public_bp.get("/invite")
def invite_page() -> str:
	return render_template(
		"public/invite/index.html",
		invite=invite_data,
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
		schedule=schedule_data,
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
		the_play=the_play_data,
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
		camping=camping_data,
		seo=build_seo(
			title="Camping at The Gorge | Freedom Con 2026",
			description="Stay on-site at The Gorge Amphitheatre. Camping details, check-in times, RV info, and what to bring for Freedom Con 2026.",
			path="/camping",
		),
	)


@public_bp.get("/hotels")
def hotels_page() -> str:
	return render_template(
		"public/hotels/index.html",
		hotels=hotels_data,
		seo=build_seo(
			title="Hotels Near The Gorge | Freedom Con 2026",
			description="Hotel and lodging options near The Gorge Amphitheatre for Freedom Con 2026. George, Quincy, Ephrata, and Moses Lake.",
			path="/hotels",
		),
	)


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
