"""DataForge Content Crew - Flask Application
Phase 2: Backend and Onboarding with SQLite Persistence
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded from .env in project root
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

from flask import Flask, render_template
from db import init_db
from routes.api import api_bp

app = Flask(__name__)

# Register Blueprints
app.register_blueprint(api_bp)

# Auto-initialize SQLite database tables on startup
with app.app_context():
    init_db()


# ---------------------------------------------------------------------------
# Page Routes
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    """Serves the DataForge Content Crew landing page."""
    return render_template("index.html")


@app.route("/workspace")
def workspace():
    """Serves the Content Crew blog workspace."""
    return render_template("workspace.html")


@app.route("/onboarding")
def onboarding():
    """Serves the company profile onboarding configuration page."""
    return render_template("onboarding.html")


@app.route("/blogs")
def blogs():
    """Serves the Content Crew published blogs catalog page."""
    return render_template("blogs.html")


if __name__ == "__main__":
    import socket

    def get_port(default_port=5000):
        if "PORT" in os.environ:
            return int(os.environ["PORT"])
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", default_port)) != 0:
                return default_port
        print(f"[Notice] Port {default_port} is in use by another process. Falling back to port 5001.")
        return 5001

    port = get_port(5000)
    print(f"Starting DataForge Content Crew on http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
