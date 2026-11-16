"""Download scores from ESPN's public scoreboard feed and turn them into Game objects."""
import logging
import re
from dataclasses import dataclass

import requests

from .leagues import BASE_URL, LEAGUES, TEAMS_URL

log = logging.getLogger(__name__)
HEADERS = {"User-Agent": "led-scoreboard/1.0"}


@dataclass
class Team:
    abbr: str
    name: str
    score: str
    color: str        # hex like "203731"
    alt_color: str
    winner: bool = False


@dataclass
class Game:
    league: str       # key from LEAGUES, e.g. "nfl"
    state: str        # "pre", "in" or "post"
    status: str       # short text for the bottom line, e.g. "Q3 4:12"
    start: str        # ISO start time, used for sorting
    away: Team
    home: Team


def _team(c):
    t = c.get("team", {})
    return Team(
        abbr=t.get("abbreviation", "???"),
        name=t.get("displayName") or t.get("shortDisplayName") or t.get("name", ""),
        score=str(c.get("score", "") or ""),
        color=t.get("color") or "FFFFFF",
        alt_color=t.get("alternateColor") or "FFFFFF",
        winner=bool(c.get("winner")),
    )


def short_status(state, detail):
    """Squeeze ESPN's status text into ~16 characters for a 64-pixel-wide panel."""
    detail = (detail or "").strip()
    if state == "pre":
        # "11/16 - 8:15 PM EST" -> "11/16 8:15 PM"
        detail = re.sub(r"\s+[A-Z]{2,4}$", "", detail)  # drop time zone
        detail = detail.replace(" - ", " ")
    elif state == "post":
        detail = detail.replace("Final/", "F/")
    else:
        detail = detail.replace(" - ", " ").replace("Quarter", "Q").replace("Period", "P")
    return detail.upper()


def parse_scoreboard(data, league):
    games = []
    for event in data.get("events", []):
        comp = (event.get("competitions") or [{}])[0]
        competitors = comp.get("competitors", [])
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        if not away or not home:
            continue
        stype = (comp.get("status") or event.get("status") or {}).get("type", {})
        state = stype.get("state", "pre")
        games.append(Game(
            league=league,
            state=state,
            status=short_status(state, stype.get("shortDetail") or stype.get("detail")),
            start=event.get("date", ""),
            away=_team(away),
            home=_team(home),
        ))
    return games


def fetch_league(league, timeout=10):
    info = LEAGUES[league]
    games = []
    for path in info["paths"]:
        try:
            r = requests.get(BASE_URL.format(path=path), params=info.get("params"),
                             headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            games += parse_scoreboard(r.json(), league)
        except (requests.RequestException, ValueError) as e:
            log.warning("Could not load %s (%s): %s", league, path, e)
    return games


def fetch_teams(league, timeout=10):
    """List of (abbreviation, name) for the web page's team picker."""
    teams = {}
    for path in LEAGUES[league]["paths"]:
        try:
            r = requests.get(TEAMS_URL.format(path=path), params={"limit": "1000"},
                             headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            for sport in r.json().get("sports", []):
                for lg in sport.get("leagues", []):
                    for t in lg.get("teams", []):
                        t = t.get("team", {})
                        if t.get("abbreviation"):
                            teams[t["abbreviation"]] = t.get("displayName", t["abbreviation"])
        except (requests.RequestException, ValueError) as e:
            log.warning("Could not load teams for %s: %s", league, e)
    return sorted(teams.items(), key=lambda kv: kv[1])


def matches(team, wanted):
    """True if a favorites entry matches this team (by code, or part of the name)."""
    w = wanted.strip().lower()
    if not w:
        return False
    if w == team.abbr.lower():
        return True
    # Only match on names for longer words, so "NY" doesn't match "Albany"
    return len(w) >= 4 and w in team.name.lower()


def select_games(games, cfg):
    """Apply mode (favorites/all) and the show_upcoming / show_final switches."""
    out = []
    for g in games:
        if g.state == "pre" and not cfg.get("show_upcoming", True):
            continue
        if g.state == "post" and not cfg.get("show_final", True):
            continue
        if cfg.get("mode") == "favorites":
            wanted = cfg.get("favorites", {}).get(g.league, [])
            if not any(matches(t, w) for t in (g.away, g.home) for w in wanted):
                continue
        out.append(g)
    # Live games first, then upcoming, then finished; by start time within each
    order = {"in": 0, "pre": 1, "post": 2}
    return sorted(out, key=lambda g: (order.get(g.state, 3), g.start))
