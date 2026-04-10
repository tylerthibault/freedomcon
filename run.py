from pathlib import Path

from flask import Flask

from src.controllers.routes import public_bp


def create_app() -> Flask:
	base_dir = Path(__file__).resolve().parent

	app = Flask(
		__name__,
		template_folder=str(base_dir / "src" / "templates"),
		static_folder=str(base_dir / "src" / "static"),
		static_url_path="/static",
	)

	app.register_blueprint(public_bp)

	return app


app = create_app()


if __name__ == "__main__":
	app.run(debug=True, port=5199, host="0.0.0.0")
