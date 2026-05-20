from os import getenv
from pathlib import Path
from secrets import token_urlsafe

from dotenv import load_dotenv
load_dotenv()

import sentry_sdk
from flask import Flask, redirect, request
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.middleware.proxy_fix import ProxyFix

from src.controllers.routes import public_bp
from src.controllers.admin_auth import admin_auth_bp, limiter
from src.controllers.admin_views import create_admin
from src.models.main import db, login_manager

def _env_bool(name: str, default: bool = False) -> bool:
	value = getenv(name)
	if value is None:
		return default
	return value.lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
	value = getenv(name)
	if value is None:
		return default
	try:
		return float(value)
	except ValueError:
		return default


sentry_dsn = getenv("SENTRY_DSN", "")
if sentry_dsn:
	sentry_sdk.init(
		dsn=sentry_dsn,
		integrations=[FlaskIntegration()],
		traces_sample_rate=_env_float("SENTRY_TRACES_SAMPLE_RATE", 0.2),
		send_default_pii=_env_bool("SENTRY_SEND_DEFAULT_PII", False),
	)


def create_app() -> Flask:
	base_dir = Path(__file__).resolve().parent
	is_debug = _env_bool("FLASK_DEBUG", False)
	secret_key = getenv("SECRET_KEY") or token_urlsafe(32)
	secure_cookies = _env_bool("SESSION_COOKIE_SECURE", not is_debug)
	enforce_https = _env_bool("FORCE_HTTPS", False)

	app = Flask(
		__name__,
		template_folder=str(base_dir / "src" / "templates"),
		static_folder=str(base_dir / "src" / "static"),
		static_url_path="/static",
	)

	app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

	# Heroku sets DATABASE_URL with legacy "postgres://" scheme; SQLAlchemy requires "postgresql://"
	_db_url = getenv("DATABASE_URL", f"sqlite:///{base_dir / 'freedomcon.db'}")
	if _db_url.startswith("postgres://"):
		_db_url = _db_url.replace("postgres://", "postgresql://", 1)

	app.config.update(
		SECRET_KEY=secret_key,
		SESSION_COOKIE_HTTPONLY=True,
		SESSION_COOKIE_SECURE=secure_cookies,
		SESSION_COOKIE_SAMESITE=getenv("SESSION_COOKIE_SAMESITE", "Lax"),
		PREFERRED_URL_SCHEME="https",
		SQLALCHEMY_DATABASE_URI=_db_url,
		SQLALCHEMY_TRACK_MODIFICATIONS=False,
	)

	@app.before_request
	def _redirect_to_https():
		if not enforce_https:
			return None
		if request.is_secure:
			return None
		host = (request.host or "").split(":")[0]
		if host in {"localhost", "127.0.0.1"}:
			return None
		return redirect(request.url.replace("http://", "https://", 1), code=301)

	@app.after_request
	def _set_security_headers(response):
		response.headers.setdefault("X-Content-Type-Options", "nosniff")
		response.headers.setdefault("X-Frame-Options", "DENY")
		response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
		response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
		response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
		if request.is_secure:
			response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
		return response

	app.register_blueprint(public_bp)
	app.register_blueprint(admin_auth_bp)

	# --- Database & auth ---
	db.init_app(app)
	limiter.init_app(app)
	login_manager.init_app(app)
	login_manager.login_view = "admin_auth.login_page"   # type: ignore[assignment]
	login_manager.login_message_category = "error"

	# --- Create tables if they don't exist yet ---
	with app.app_context():
		db.create_all()

	# --- Flask-Admin ---
	create_admin(app)

	return app


app = create_app()


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

@app.cli.command("seed")
def seed_command():
    """Seed the SQLite database from the legacy Python data files."""
    import click
    from seed_db import seed
    click.echo("Seeding database …")
    seed(app)
    click.echo("Done.")


@app.cli.command("create-admin")
def create_admin_user():
    """Create or reset an admin user. Usage: flask create-admin"""
    import click
    from src.models.main import AdminUser, db

    username = click.prompt("Username", default="admin")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    with app.app_context():
        user = db.session.execute(
            db.select(AdminUser).where(AdminUser.username == username)
        ).scalar_one_or_none()
        if user:
            user.set_password(password)
            click.echo(f"Updated password for '{username}'.")
        else:
            user = AdminUser(username=username)
            user.set_password(password)
            db.session.add(user)
            click.echo(f"Created admin user '{username}'.")
        db.session.commit()


if __name__ == "__main__":
	debug_mode = _env_bool("FLASK_DEBUG", True)
	host = getenv("FLASK_HOST", "0.0.0.0")

	if debug_mode:
		app.config.update(
			TEMPLATES_AUTO_RELOAD=True,
			SEND_FILE_MAX_AGE_DEFAULT=0,
		)

	app.run(
		debug=debug_mode,
		use_reloader=debug_mode,
		port=int(getenv("PORT", "5199")),
		host=host,
	)
