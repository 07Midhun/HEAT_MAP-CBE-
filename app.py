"""WSGI entry point for Render (gunicorn app:app)."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify, send_from_directory

from generate_heatmap import (
    DEFAULT_MAP_SUBTITLE,
    DEFAULT_MAP_TITLE,
    build_api_payload,
    load_dataset,
    normalize_columns,
)

DATA_PATH = BASE_DIR / "data" / "cbe_burning_data.xlsx"
FRONTEND_DIST = BASE_DIR / "frontend" / "dist"
MAP_TITLE = os.environ.get("MAP_TITLE", DEFAULT_MAP_TITLE)
MAP_SUBTITLE = os.environ.get("MAP_SUBTITLE", DEFAULT_MAP_SUBTITLE)

app = Flask(__name__, static_folder=None)
_df_cache = None


def get_dataframe():
    global _df_cache
    if _df_cache is None:
        if not DATA_PATH.is_file():
            raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
        _df_cache = normalize_columns(load_dataset(DATA_PATH))
    return _df_cache


def reload_dataframe():
    global _df_cache
    _df_cache = normalize_columns(load_dataset(DATA_PATH))
    return _df_cache


@app.route("/api/map-data")
def map_data():
    df = get_dataframe()
    return jsonify(build_api_payload(df, MAP_TITLE, MAP_SUBTITLE))


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "frontend": FRONTEND_DIST.is_dir()})


@app.route("/api/refresh", methods=["POST"])
def refresh():
    reload_dataframe()
    return jsonify({"status": "refreshed"})


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if not FRONTEND_DIST.is_dir():
        return (
            "React frontend not built. Run: cd frontend && npm install && npm run build",
            503,
        )
    asset = FRONTEND_DIST / path
    if path and asset.is_file():
        return send_from_directory(FRONTEND_DIST, path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
