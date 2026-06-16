"""WSGI entry point for Render (gunicorn app:app)."""

import sys
from pathlib import Path

# Parentheses in folder names (e.g. HEAT_MAP(CBE)) can break sys.path on Windows.
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import os

from flask import Flask, send_from_directory

from generate_heatmap import generate_map

DATA_PATH = BASE_DIR / "data" / "cbe_burning_data.xlsx"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "cbe_burning_heatmap.html"
MAP_TITLE = os.environ.get("MAP_TITLE", "Coimbatore Burning Compliance Heat Map")

app = Flask(__name__)


def ensure_map() -> None:
    if not DATA_PATH.is_file():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
    if not OUTPUT_FILE.is_file() or os.environ.get("REGENERATE_ON_START"):
        generate_map(DATA_PATH, OUTPUT_FILE, MAP_TITLE)


ensure_map()


@app.route("/")
def index():
    return send_from_directory(OUTPUT_DIR, OUTPUT_FILE.name)


@app.route("/health")
def health():
    return {"status": "ok", "map": OUTPUT_FILE.name}


@app.route("/refresh", methods=["POST"])
def refresh():
    generate_map(DATA_PATH, OUTPUT_FILE, MAP_TITLE)
    return {"status": "refreshed", "map": OUTPUT_FILE.name}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
