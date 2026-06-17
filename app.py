"""WSGI entry point for Render (gunicorn app:app)."""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, Response, jsonify

from generate_heatmap import (
    DEFAULT_MAP_SUBTITLE,
    DEFAULT_MAP_TITLE,
    load_dataset,
    normalize_columns,
    render_map_html,
)

DATA_PATH = BASE_DIR / "data" / "cbe_burning_data.xlsx"
MAP_TITLE = os.environ.get("MAP_TITLE", DEFAULT_MAP_TITLE)
MAP_SUBTITLE = os.environ.get("MAP_SUBTITLE", DEFAULT_MAP_SUBTITLE)

app = Flask(__name__)
_df_cache = None
_html_cache = None


def get_dataframe():
    global _df_cache
    if _df_cache is None:
        if not DATA_PATH.is_file():
            raise FileNotFoundError(f"Data file not found: {DATA_PATH}")
        _df_cache = normalize_columns(load_dataset(DATA_PATH))
    return _df_cache


def reload_dataframe():
    global _df_cache, _html_cache
    _df_cache = normalize_columns(load_dataset(DATA_PATH))
    _html_cache = None
    return _df_cache


def get_map_html() -> str:
    global _html_cache
    if _html_cache is None:
        df = get_dataframe()
        _html_cache = render_map_html(df, MAP_TITLE, MAP_SUBTITLE)
    return _html_cache


@app.route("/")
def index():
    return Response(get_map_html(), mimetype="text/html; charset=utf-8")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "mode": "html"})


@app.route("/api/refresh", methods=["POST"])
def refresh():
    reload_dataframe()
    return jsonify({"status": "refreshed"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
