"""The settings page, served by the Pi. Open http://<pi-address>:8080 on a phone or tablet.

The page itself is scoreboard/static/index.html. It talks to these small
JSON endpoints:
    GET  /api/config          current settings + the list of leagues
    POST /api/config          change some settings (only the keys you send)
    GET  /api/teams/<league>  teams with logos, for the team picker
    GET  /now.png             a picture of what the board is showing right now
"""
import io
import os
import threading

from flask import Flask, jsonify, request, send_file, send_from_directory

from . import config
from .espn import fetch_teams
from .leagues import LEAGUES, details_for
from .render import led_look, render_message

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app = Flask(__name__, static_folder=None)
_team_cache = {}

# The main loop puts each picture it shows here, so the page can show it too.
current_image = None
_image_lock = threading.Lock()


def set_current_image(img):
    global current_image
    with _image_lock:
        current_image = img


@app.route("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.route("/api/config", methods=["GET"])
def get_config():
    leagues = [{"key": k, "name": v["name"], "emoji": v["emoji"], "sport": v["sport"],
                "details": [{"key": dk, "label": label, "emoji": e} for dk, label, e in details_for(k)]}
               for k, v in LEAGUES.items()]
    return jsonify({"config": config.load(), "leagues": leagues})


def _clamp_int(value, lo, hi):
    return max(lo, min(hi, int(value)))


@app.route("/api/config", methods=["POST"])
def update_config():
    """Only the keys we know about are accepted, and numbers are kept in range."""
    data = request.get_json(force=True, silent=True) or {}
    cfg = config.load()
    try:
        if data.get("mode") in ("favorites", "all"):
            cfg["mode"] = data["mode"]
        if isinstance(data.get("leagues"), list):
            cfg["leagues"] = [k for k in LEAGUES if k in data["leagues"]]
        if isinstance(data.get("favorites"), dict):
            for k, teams in data["favorites"].items():
                if k in LEAGUES and isinstance(teams, list):
                    cfg["favorites"][k] = [str(t).strip()[:40] for t in teams if str(t).strip()]
        if isinstance(data.get("details"), dict):
            for k, opts in data["details"].items():
                if k in LEAGUES and isinstance(opts, dict):
                    known = {dk for dk, _, _ in details_for(k)}
                    cfg.setdefault("details", {}).setdefault(k, {}).update(
                        {dk: bool(v) for dk, v in opts.items() if dk in known})
        for key, lo, hi in (("brightness", 1, 100), ("seconds_per_game", 2, 30),
                            ("refresh_seconds", 15, 300)):
            if key in data:
                cfg[key] = _clamp_int(data[key], lo, hi)
        for key in ("show_upcoming", "show_final"):
            if key in data:
                cfg[key] = bool(data[key])
        if isinstance(data.get("title"), str) and data["title"].strip():
            cfg["title"] = data["title"].strip()[:30]
    except (TypeError, ValueError):
        return jsonify({"error": "bad value"}), 400
    config.save(cfg)
    return jsonify({"config": cfg})


@app.route("/api/teams/<league>")
def teams(league):
    if league not in LEAGUES:
        return jsonify([]), 404
    if not _team_cache.get(league):
        _team_cache[league] = fetch_teams(league)
    return jsonify(_team_cache[league])


@app.route("/now.png")
def now_png():
    with _image_lock:
        img = current_image
    if img is None:
        img = render_message(["STARTING..."])
    buf = io.BytesIO()
    led_look(img, dot=6).save(buf, "PNG")
    buf.seek(0)
    resp = send_file(buf, mimetype="image/png")
    resp.headers["Cache-Control"] = "no-store"
    return resp


def run(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)
