from datetime import date
from os import getenv

from flask import Blueprint, Response, redirect, render_template, url_for
from src.data.FAQ import FAQ
from src.data.accommodations import camping_options, hotel_options, travel_info
from src.data.artists import artists
from src.data.social_proof import social_proof
from src.data.speakers import speakers as speakers_data
from src.data.tickers import ticketer1, ticketers
from src.data.tickets import get_ticket_context

public_bp = Blueprint("public", __name__)
SITE_URL = "https://www.freedomcon26.com"
ASSET_BASE_URL = getenv("ASSET_BASE_URL", "").strip().rstrip("/")


@public_bp.app_context_processor
def inject_global_urgency() -> dict[str, object]:
	def asset_url(path: str) -> str:
		normalized = path.lstrip("/")
		if ASSET_BASE_URL and normalized.startswith(("pdfs/", "downloads/", "media/")):
			return f"{ASSET_BASE_URL}/{normalized}"
		return url_for("static", filename=normalized)

	return {
		"urgency": get_ticket_context()["urgency"],
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
	image_path: str = "/static/img/TheGuys-WithLogoNoFeet.avif",
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
	ticket_context = get_ticket_context()
	return render_template(
		"public/landing/index.html",
		social_proof=social_proof,
		ticketer1=ticketer1,
		ticketers=ticketers,
		speakers=speakers_data,
		urgency=ticket_context["urgency"],
		seo=build_seo(
			title="Freedom Con 2026 | Christian Men's Conference at The Gorge",
			description="Join Freedom Con 2026 at The Gorge Amphitheatre in George, WA for two days of speakers, worship, brotherhood, and leadership challenge.",
			path="/",
		),
	)


@public_bp.get("/faqs")
def faqs() -> str:
	return render_template(
		"public/FAQs/index.html",
		faq_content=FAQ,
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


@public_bp.get("/accommodations")
def accommodations_page() -> str:
	return render_template(
		"public/accomodations/index.html",
		travel_info=travel_info,
		camping_options=camping_options,
		hotel_options=hotel_options,
		seo=build_seo(
			title="Freedom Con Accommodations | Travel, Camping, and Lodging",
			description="Plan your Freedom Con stay with travel routes, camping options, and nearby hotel listings around The Gorge Amphitheatre.",
			path="/accommodations",
		),
	)


@public_bp.get("/where")
def where_page() -> str:
	return render_template(
		"public/where/index.html",
		seo=build_seo(
			title="Where is Freedom Con? | The Gorge Amphitheatre, Washington",
			description="Find Freedom Con at The Gorge Amphitheatre in George, Washington, with map details and location information.",
			path="/where",
		),
	)


@public_bp.get("/tickets")
def tickets_page() -> str:
	ticket_context = get_ticket_context()
	return render_template(
		"public/tickets/index.html",
		ticket_meta=ticket_context["ticket_meta"],
		ticket_prices=ticket_context["ticket_prices"],
		urgency=ticket_context["urgency"],
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


@public_bp.get("/venue-map-svg")
def venue_map_svg_page() -> str:
	return redirect(url_for("public.venue_map_page"))


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
		"/faqs",
		"/speakers",
		"/artists",
		"/accommodations",
		"/where",
		"/tickets",
		"/venue-map",
	]
	urls = [{"loc": f"{SITE_URL}{path}", "lastmod": lastmod} for path in pages]
	xml = render_template("sitemap.xml", urls=urls)
	return Response(xml, mimetype="application/xml")