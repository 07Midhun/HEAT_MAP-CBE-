"""WSGI entry point for Render (gunicorn app:app)."""

import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = "cbe_burning_heatmap.html"

app = Flask(__name__, static_folder=None)


@app.route("/")
def index():
    if not (OUTPUT_DIR / OUTPUT_FILE).is_file():
        return (
            "Heat map HTML not found. Run: python generate_heatmap.py --no-open",
            503,
        )
    return send_from_directory(OUTPUT_DIR, OUTPUT_FILE)


@app.route("/api/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "mode": "static-html",
            "html_exists": (OUTPUT_DIR / OUTPUT_FILE).is_file(),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
