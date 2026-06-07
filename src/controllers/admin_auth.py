"""Admin authentication routes (login / logout)."""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user, login_required, login_user, logout_user

from src.models.main import AdminUser, db, log_audit

admin_auth_bp = Blueprint("admin_auth", __name__, url_prefix="/admin")

# Rate limiter — init_app() is called in run.py create_app()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)


@admin_auth_bp.get("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("admin.index"))
    return render_template("admin/login.html")


@admin_auth_bp.post("/login")
@limiter.limit("10 per minute; 30 per hour")
def login_post():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    remember = bool(request.form.get("remember"))

    user = db.session.execute(
        db.select(AdminUser).where(AdminUser.username == username)
    ).scalar_one_or_none()

    if user is None or not user.check_password(password):
        # Log failed attempt (use username as typed, may not exist)
        log_audit(username=username or "<unknown>", action="LOGIN_FAILED",
                  detail=f"Failed login attempt from {request.remote_addr}")
        flash("Invalid username or password.", "error")
        return render_template("admin/login.html"), 401

    login_user(user, remember=remember)
    log_audit(username=user.username, action="LOGIN",
              detail=f"Logged in (remember={remember})")
    # Validate next is a relative path to prevent open redirect
    next_url = request.args.get("next", "")
    if not next_url or not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("admin.index")
    return redirect(next_url)


@admin_auth_bp.get("/logout")
@login_required
def logout():
    log_audit(username=current_user.username, action="LOGOUT")
    logout_user()
    return redirect(url_for("admin_auth.login_page"))


@admin_auth_bp.post("/reorder")
@login_required
def reorder():
    """AJAX – set sort_order for any sortable model.
    Body: {"model": "video", "ids": [3, 1, 2]}
    """
    from src.models.main import (
        Artist, BackgroundText, Church, FAQ, MediaDownload,
        PastConference, Podcast, SocialProof, Speaker, Sponsor,
        TicketPrice, Ticker, Video,
    )

    MODEL_MAP = {
        "artist":         Artist,
        "backgroundtext": BackgroundText,
        "church":         Church,
        "faq":            FAQ,
        "mediadownload":  MediaDownload,
        "pastconference": PastConference,
        "podcast":        Podcast,
        "socialproof":    SocialProof,
        "speaker":        Speaker,
        "sponsor":        Sponsor,
        "ticketprice":    TicketPrice,
        "ticker":         Ticker,
        "video":          Video,
    }

    data = request.get_json(silent=True) or {}
    model_name = (data.get("model") or "").lower().strip()
    ids = data.get("ids", [])

    ModelClass = MODEL_MAP.get(model_name)
    if ModelClass is None:
        return jsonify(ok=False, error=f"Unknown model: {model_name}"), 400
    if not isinstance(ids, list) or not ids:
        return jsonify(ok=False, error="ids must be a non-empty list"), 400

    try:
        for position, record_id in enumerate(ids):
            record = db.session.get(ModelClass, int(record_id))
            if record is not None:
                record.sort_order = position
        db.session.commit()
        log_audit(
            username=current_user.username,
            action="REORDER",
            resource=ModelClass.__name__,
            detail=f"New order: {ids}",
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify(ok=False, error=str(exc)), 500

    return jsonify(ok=True)
