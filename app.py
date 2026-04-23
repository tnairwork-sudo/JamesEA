import os
import threading
import webbrowser

from dotenv import load_dotenv
from flask import Flask

from database import db
from modules.scheduler import start_scheduler
from routes.api import bp as api_bp
from routes.dashboard import bp as dashboard_bp
from routes.webhook import bp as webhook_bp


def create_app() -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///jamesea.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(webhook_bp)

    with app.app_context():
        from database import models  # noqa: F401

        db.create_all()
        start_scheduler()

    return app


def _open_browser() -> None:
    if os.getenv("AUTO_OPEN_BROWSER", "1") != "1":
        return
    if os.getenv("RAILWAY_ENVIRONMENT"):
        return
    url = f"http://localhost:{os.getenv('PORT', '5001')}"
    try:
        webbrowser.get("google-chrome").open_new(url)
    except Exception:
        webbrowser.open_new(url)


app = create_app()

if __name__ == "__main__":
    threading.Timer(1.2, _open_browser).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5001)), debug=False)
