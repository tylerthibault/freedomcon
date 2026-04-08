from flask import Blueprint, render_template

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def landing() -> str:
	return render_template("public/landing/index.html")


@public_bp.get("/faqs")
def faqs() -> str:
    return render_template("public/FAQs/index.html")


@public_bp.get("/speakers")
def speakers() -> str:
	return render_template("public/speakers/index.html")