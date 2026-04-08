from flask import Blueprint, render_template
from src.data.accommodations import camping_options, hotel_options, travel_info
from src.data.artists import artists
from src.data.social_proof import social_proof
from src.data.speakers import speakers as speakers_data
from src.data.tickets import ticket_meta, ticket_prices

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def landing() -> str:
	return render_template("public/landing/index1.html", social_proof=social_proof)


@public_bp.get("/landing-2")
def landing_2() -> str:
	return render_template("public/landing/index2.html", social_proof=social_proof)


@public_bp.get("/landing-3")
def landing_3() -> str:
	return render_template("public/landing/index3.html", social_proof=social_proof)


@public_bp.get("/landing-4")
def landing_4() -> str:
	return render_template("public/landing/index4.html", social_proof=social_proof)


@public_bp.get("/landing-5")
def landing_5() -> str:
	return render_template("public/landing/index5.html", social_proof=social_proof)


@public_bp.get("/faqs")
def faqs() -> str:
    return render_template("public/FAQs/index.html")


@public_bp.get("/speakers")
def speakers() -> str:
	return render_template("public/speakers/index.html", speakers=speakers_data)


@public_bp.get("/artists")
def artists_page() -> str:
	return render_template("public/artists/index.html", artists=artists)


@public_bp.get("/accommodations")
def accommodations_page() -> str:
	return render_template(
		"public/accomodations/index.html",
		travel_info=travel_info,
		camping_options=camping_options,
		hotel_options=hotel_options,
	)


@public_bp.get("/tickets")
def tickets_page() -> str:
	return render_template("public/tickets/index.html", ticket_meta=ticket_meta, ticket_prices=ticket_prices)


@public_bp.get("/venue-map")
def venue_map_page() -> str:
	return render_template("public/venue_map/index.html")