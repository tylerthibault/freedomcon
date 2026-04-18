from datetime import date
from os import getenv
import re

from flask import Blueprint, Response, redirect, render_template, url_for
from src.data.FAQ import FAQ
from src.data.accommodations import hotel_options, travel_info
from src.data.artists import artists
from src.data.social_proof import social_proof
from src.data.speakers import speakers as speakers_data
from src.data.videos import videos as videos_data
from src.data.tickers import ticketer1, ticketers
from src.data.tickets import get_ticket_context
from src.data.background_text import background_1

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
	image_path: str = "/static/img/sharing_pic.png?v=20260413",
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


@public_bp.get("/")
def landing() -> str:
	trailers_data = []
	for index, video in enumerate(videos_data, start=1):
		video_url = str(video.get("url", "")).strip()
		youtube_id = extract_youtube_id(video_url)
		if not youtube_id:
			continue
		thumbnail_mobile = normalize_video_thumbnail_path(
			video.get("thumbnail_mobile") or video.get("thumbnail") or ""
		)
		thumbnail_desktop = f"https://i.ytimg.com/vi/{youtube_id}/hqdefault.jpg"
		trailers_data.append(
			{
				"title": video.get("title") or f"Freedom Con Trailer {index}",
				"youtube_id": youtube_id,
				"thumbnail_mobile": thumbnail_mobile,
				"thumbnail_desktop": thumbnail_desktop,
				"alt": video.get("alt") or f"Freedom Con trailer thumbnail {index}",
			}
		)
	cta_2 = {
		"image": "img/TheGuysFadeFeet.avif",
	}
	crowder_audio = {
		"src": getenv("CROWDER_AUDIO_URL", "").strip() or "https://pub-fc470c82f793409f9e6c126deeb0387d.r2.dev/02_Grave%20Robber.wav",
		"title": "02_Grave Robber",
	}
	event_schema = {
		"@context": "https://schema.org",
		"@type": "Event",
		"name": "Freedom Con 2026",
		"description": "Join Freedom Con 2026 at The Gorge Amphitheatre in George, WA for two days of speakers, worship, brotherhood, and leadership challenge.",
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
		"public/landing/index.html",
		social_proof=social_proof,
		ticketer1=ticketer1,
		ticketers=ticketers,
		background_text=background_1,
		speakers=speakers_data,
		trailers=trailers_data,
		cta_2=cta_2,
		crowder_audio=crowder_audio,
		structured_data=[event_schema],
		seo=build_seo(
			title="A Congress of Christian Men at The Gorge Amphitheatre",
			description="Join Freedom Con 2026 at The Gorge Amphitheatre in George, WA for two days of speakers, worship, brotherhood, and leadership challenge.",
			path="/",
			image_path="/static/img/title_on_black.png?v=20260417",
		),
	)


@public_bp.get("/faqs")
def faqs() -> str:
	return render_template(
		"public/FAQs/index.html",
		faq_content=FAQ,
		structured_data=[build_faq_schema(FAQ)],
		seo=build_seo(
			title="Freedom Con FAQs | Event, Travel, and Camping Questions",
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
			title="Freedom Con Speakers | 2026 Conference Lineup",
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
			title="Freedom Con Artist | Live Worship and Concert",
			description="See the featured Freedom Con artist and live worship experience planned for Father’s Day weekend 2026.",
			path="/artists",
		),
	)


@public_bp.get("/about-smn")
def about_smn_page() -> str:
	return render_template(
		"public/about_smn/index.html",
		seo=build_seo(
			title="About SMN | The Road to The Gorge",
			description="Learn more about Stronger Man Nation and the Road to The Gorge journey leading into Freedom Con.",
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
			title="Freedom Con Accommodations | Travel, Camping, and Lodging",
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
			title="Freedom Con Vendors | Information Coming Soon",
			description="Vendor information for Freedom Con is coming soon. Check back for details on participating partners and on-site offerings.",
			path="/vendors",
		),
	)


@public_bp.get("/press")
def press_page() -> str:
	return redirect(url_for("public.landing"))
	media_kit_download_url = getenv("MEDIA_KIT_DOWNLOAD_URL", "").strip()
	media_kit_image_url = getenv("MEDIA_KIT_IMAGE_URL", "").strip() or url_for(
		"static", filename="img/freedom_con_media_kit_flyer.jpg"
	)
	men_picture_url = getenv("PRESS_MEN_PICTURE_URL", "").strip() or url_for(
		"static", filename="img/TheGuys-WithLogoNoFeet.avif"
	)
	formsubmit_action = getenv("PRESS_FORMSUBMIT_ACTION", "").strip()
	formsubmit_next = getenv("PRESS_FORMSUBMIT_NEXT", "").strip() or f"{SITE_URL}/press?submitted=1"

	return render_template(
		"public/press/index.html",
		media_kit_download_url=media_kit_download_url,
		media_kit_image_url=media_kit_image_url,
		men_picture_url=men_picture_url,
		formsubmit_action=formsubmit_action,
		formsubmit_next=formsubmit_next,
		seo=build_seo(
			title="Freedom Con Press & Media Kit",
			description="Download the Freedom Con media kit and connect with us for sponsor interviews, press requests, and partnership details.",
			path="/press",
		),
	)


@public_bp.get("/worship")
def worship_page() -> str:
	return render_template(
		"public/worship/index.html",
		seo=build_seo(
			title="Freedom Con Worship | Information Coming Soon",
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
			title="Freedom Con Tickets | 2026 Pricing and Registration",
			description="View Freedom Con 2026 ticket options, pricing tiers, and secure your spot for Father’s Day weekend at The Gorge.",
			path="/tickets",
		),
	)


# @public_bp.get("/venue-map")
# def venue_map_page() -> str:
# 	return render_template(
# 		"public/venue_map_svg/index.html",
# 		seo=build_seo(
# 			title="Freedom Con Venue Map | The Gorge Amphitheatre",
# 			description="Explore the Freedom Con venue diagram for gates, stage area, parking, camping zones, and key amenities at The Gorge Amphitheatre.",
# 			path="/venue-map",
# 		),
# 	)


@public_bp.get("/vision")
def vision_page() -> str:
	return redirect(url_for("public.landing"))
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
	return redirect(url_for("public.landing"))
	return render_template(
		"public/experience/index.html",
		seo=build_seo(
			title="The Experience | Freedom Con 2026",
			description="Explore the full Freedom Con experience — competitions, side stage, schedule, and everything happening at The Gorge.",
			path="/experience",
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
		"/the-venue",
		"/tickets",
	]
	urls = [{"loc": f"{SITE_URL}{path}", "lastmod": lastmod} for path in pages]
	xml = render_template("sitemap.xml", urls=urls)
	return Response(xml, mimetype="application/xml")