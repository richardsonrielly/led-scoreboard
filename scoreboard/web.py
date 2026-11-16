"""A small settings page served by the Pi. Open http://<pi-name>.local:8080 on a phone."""
from flask import Flask, redirect, render_template_string, request

from . import config
from .espn import fetch_teams
from .leagues import LEAGUES

app = Flask(__name__)
_team_cache = {}

PAGE = """
<!doctype html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scoreboard settings</title>
<style>
 body{font-family:system-ui,sans-serif;max-width:640px;margin:auto;padding:16px;background:#111;color:#eee}
 h1{font-size:1.4em} fieldset{border:1px solid #333;border-radius:8px;margin:12px 0;padding:12px}
 legend{font-weight:600} label{display:block;margin:6px 0}
 input[type=text]{width:100%;padding:8px;background:#222;color:#eee;border:1px solid #444;border-radius:6px}
 input[type=range]{width:100%} .hint{color:#999;font-size:.85em}
 button{background:#2a7;color:#fff;border:0;padding:12px 20px;border-radius:8px;font-size:1em;width:100%}
 .saved{background:#264;padding:8px;border-radius:6px} a{color:#6cf}
</style></head><body>
<h1>🏟️ Scoreboard settings</h1>
{% if saved %}<p class="saved">Saved! The scoreboard will update in a moment.</p>{% endif %}
<form method="post">
<fieldset><legend>What to show</legend>
 <label><input type="radio" name="mode" value="favorites" {{'checked' if cfg.mode=='favorites'}}> Just my teams</label>
 <label><input type="radio" name="mode" value="all" {{'checked' if cfg.mode=='all'}}> Every game in the leagues below</label>
 <label><input type="checkbox" name="show_upcoming" {{'checked' if cfg.show_upcoming}}> Show games that haven't started</label>
 <label><input type="checkbox" name="show_final" {{'checked' if cfg.show_final}}> Show finished games</label>
</fieldset>
<fieldset><legend>Leagues and teams</legend>
 <p class="hint">Type team codes or names, separated by commas (e.g. <b>NYJ, GB</b> or <b>Siena</b>).</p>
 {% for key, info in leagues.items() %}
  <label><input type="checkbox" name="league_{{key}}" {{'checked' if key in cfg.leagues}}> <b>{{info.name}}</b>
   — <a href="/teams/{{key}}" target="_blank">team codes</a></label>
  <input type="text" name="fav_{{key}}" value="{{ ', '.join(cfg.favorites.get(key, [])) }}">
 {% endfor %}
</fieldset>
<fieldset><legend>Display</legend>
 <label>Brightness: <output id="b">{{cfg.brightness}}</output>%
  <input type="range" name="brightness" min="1" max="100" value="{{cfg.brightness}}" oninput="b.value=this.value"></label>
 <label>Seconds per game: <output id="s">{{cfg.seconds_per_game}}</output>
  <input type="range" name="seconds_per_game" min="2" max="30" value="{{cfg.seconds_per_game}}" oninput="s.value=this.value"></label>
 <label>Check for new scores every: <output id="r">{{cfg.refresh_seconds}}</output> seconds
  <input type="range" name="refresh_seconds" min="15" max="300" step="15" value="{{cfg.refresh_seconds}}" oninput="r.value=this.value"></label>
</fieldset>
<button type="submit">Save</button>
</form></body></html>
"""

TEAMS_PAGE = """
<!doctype html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:system-ui;background:#111;color:#eee;padding:16px} td{padding:3px 10px}</style>
</head><body><h2>{{name}} team codes</h2>
{% if not teams %}<p>Couldn't load the team list right now.</p>{% endif %}
<table>{% for code, n in teams %}<tr><td><b>{{code}}</b></td><td>{{n}}</td></tr>{% endfor %}</table>
</body></html>
"""


class _Attr(dict):
    __getattr__ = dict.get


@app.route("/", methods=["GET", "POST"])
def settings():
    cfg = config.load()
    saved = False
    if request.method == "POST":
        f = request.form
        cfg["mode"] = "all" if f.get("mode") == "all" else "favorites"
        cfg["show_upcoming"] = "show_upcoming" in f
        cfg["show_final"] = "show_final" in f
        cfg["leagues"] = [k for k in LEAGUES if f"league_{k}" in f]
        cfg["favorites"] = {
            k: [t.strip() for t in f.get(f"fav_{k}", "").split(",") if t.strip()]
            for k in LEAGUES
        }
        for key, lo, hi in (("brightness", 1, 100), ("seconds_per_game", 2, 30),
                            ("refresh_seconds", 15, 300)):
            try:
                cfg[key] = max(lo, min(hi, int(f.get(key, cfg[key]))))
            except ValueError:
                pass
        config.save(cfg)
        return redirect("/?saved=1")
    saved = request.args.get("saved") == "1"
    return render_template_string(PAGE, cfg=_Attr(cfg), leagues={k: _Attr(v) for k, v in LEAGUES.items()},
                                  saved=saved)


@app.route("/teams/<league>")
def teams(league):
    if league not in LEAGUES:
        return "Unknown league", 404
    if not _team_cache.get(league):
        _team_cache[league] = fetch_teams(league)
    return render_template_string(TEAMS_PAGE, name=LEAGUES[league]["name"], teams=_team_cache[league])


def run(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
