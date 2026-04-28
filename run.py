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

	app.config.update(
		SECRET_KEY=secret_key,
		SESSION_COOKIE_HTTPONLY=True,
		SESSION_COOKIE_SECURE=secure_cookies,
		SESSION_COOKIE_SAMESITE=getenv("SESSION_COOKIE_SAMESITE", "Lax"),
		PREFERRED_URL_SCHEME="https",
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

	return app


app = create_app()


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
