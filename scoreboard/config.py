"""Load and save the scoreboard settings (config.json).

The display loop and the web page both use this module, so a change made
from the web page is picked up by the scoreboard within a second or two.
"""
import copy
import json
import os
import threading

CONFIG_PATH = os.environ.get(
    "SCOREBOARD_CONFIG",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"),
)

DEFAULTS = {
    # "favorites" = only the teams listed below; "all" = every game in the leagues below
    "mode": "favorites",
    # Leagues to check. Keys must exist in scoreboard/leagues.py
    "leagues": ["nfl", "mlb", "nba", "nhl", "mens-college-basketball", "usmnt"],
    # Teams to show in favorites mode. Each entry can be an ESPN code ("NYJ")
    # or part of the team name ("Siena").
    "favorites": {
        "nfl": ["GB", "NYJ"],
        "mlb": ["NYM"],
        "nba": ["NY"],
        "nhl": ["NYR"],
        "mens-college-basketball": ["Siena", "Marquette"],
        "usmnt": ["USA"],
    },
    # Extra live-game info per league, e.g. {"mlb": {"batter": false}}.
    # Anything not listed is on.
    "details": {},
    # Name shown at the top of the settings page
    "title": "My Scoreboard",
    "brightness": 60,            # 1-100
    "seconds_per_game": 6,       # how long each score stays on screen
    "refresh_seconds": 60,       # how often to download new scores
    "show_upcoming": True,       # include games that haven't started yet
    "show_final": True,          # include finished games
    "web_port": 8080,
    # Panel hardware (only used on the Pi)
    "panel": {
        "rows": 32,
        "cols": 64,
        "chain_length": 1,
        "hardware_mapping": "adafruit-hat",  # Bonnet uses the same mapping
        "gpio_slowdown": 2,                  # 2 works well on a Pi Zero 2W
    },
}

_lock = threading.Lock()


def _merge(defaults, overrides):
    result = copy.deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict) and key != "favorites":
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load(path=CONFIG_PATH):
    with _lock:
        if not os.path.exists(path):
            return copy.deepcopy(DEFAULTS)
        with open(path) as f:
            return _merge(DEFAULTS, json.load(f))


def save(cfg, path=CONFIG_PATH):
    """Write atomically so the display never reads a half-written file."""
    with _lock:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(cfg, f, indent=2)
        os.replace(tmp, path)


def mtime(path=CONFIG_PATH):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0


def detail_on(cfg, league, key):
    return bool(cfg.get("details", {}).get(league, {}).get(key, True))
