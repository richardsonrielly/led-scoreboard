"""Download scores from ESPN's public scoreboard feed and turn them into Game objects."""
import logging
import re
from dataclasses import dataclass, field

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
    id: str = ""
    logo: str = ""


@dataclass
class Game:
    league: str       # key from LEAGUES, e.g. "nfl"
    state: str        # "pre", "in" or "post"
    status: str       # short text for the bottom line, e.g. "Q3 4:12"
    start: str        # ISO start time, used for sorting
    away: Team
    home: Team
    # Live-game details (only filled in for sports that have them):
    # baseball: half ("top"/"bottom"/"middle"/"end"), inning, balls, strikes, outs,
    #           on_first, on_second, on_third, batter, pitcher
    # football: possession ("home"/"away"), down_text, spot_text, yards_to_goal,
    #           distance, red_zone
    situation: dict = field(default_factory=dict)


def _team(c):
    t = c.get("team", {})
    return Team(
        abbr=t.get("abbreviation", "???"),
        name=t.get("displayName") or t.get("shortDisplayName") or t.get("name", ""),
        score=str(c.get("score", "") or ""),
        color=t.get("color") or "FFFFFF",
        alt_color=t.get("alternateColor") or "FFFFFF",
        winner=bool(c.get("winner")),
        id=str(t.get("id", "")),
        logo=t.get("logo", ""),
    )


def _athlete_name(entry):
    if not isinstance(entry, dict):
        return ""
    a = entry.get("athlete", entry)
    return a.get("shortName") or a.get("displayName") or ""


def parse_situation(sport, state, sit, stype, period, away, home):
    """Pull the extra live-game info out of ESPN's "situation" block."""
    if state != "in":
        return {}
    sit = sit or {}
    if sport == "baseball":
        detail = (stype.get("shortDetail") or stype.get("detail") or "").lower()
        half = next((h for h, words in (("top", ("top",)), ("bottom", ("bot",)),
                                         ("middle", ("mid",)), ("end", ("end",)))
                     if detail.startswith(words)), "")
        return {
            "half": half,
            "inning": period,
            "balls": sit.get("balls"),
            "strikes": sit.get("strikes"),
            "outs": sit.get("outs"),
            "on_first": bool(sit.get("onFirst")),
            "on_second": bool(sit.get("onSecond")),
            "on_third": bool(sit.get("onThird")),
            "batter": _athlete_name(sit.get("batter")),
            "pitcher": _athlete_name(sit.get("pitcher")),
        }
    if sport == "football":
        pos = str(sit.get("possession", ""))
        side = "away" if pos and pos == away.id else "home" if pos and pos == home.id else ""
        if not side:
            return {}
        offense = away if side == "away" else home
        spot = sit.get("possessionText") or ""        # e.g. "MIA 20" or "50"
        yards_to_goal = None
        parts = spot.split()
        try:
            yard = int(parts[-1])
            if len(parts) == 1:               # midfield
                yards_to_goal = 50
            elif parts[0] == offense.abbr:     # on our own side of the field
                yards_to_goal = 100 - yard
            else:
                yards_to_goal = yard
        except (ValueError, IndexError):
            pass
        return {
            "possession": side,
            "down_text": sit.get("shortDownDistanceText") or "",
            "spot_text": spot,
            "yards_to_goal": yards_to_goal,
            "distance": sit.get("distance"),
            "red_zone": bool(sit.get("isRedZone")),
        }
    return {}


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
        status = comp.get("status") or event.get("status") or {}
        stype = status.get("type", {})
        state = stype.get("state", "pre")
        away_t, home_t = _team(away), _team(home)
        games.append(Game(
            league=league,
            state=state,
            status=short_status(state, stype.get("shortDetail") or stype.get("detail")),
            start=event.get("date", ""),
            away=away_t,
            home=home_t,
            situation=parse_situation(LEAGUES.get(league, {}).get("sport"), state,
                                      comp.get("situation"), stype, status.get("period"),
                                      away_t, home_t),
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
    """Teams for the settings page's logo picker, sorted by name."""
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
                            logos = t.get("logos") or [{}]
                            teams[t["abbreviation"]] = {
                                "abbr": t["abbreviation"],
                                "name": t.get("displayName", t["abbreviation"]),
                                "short": t.get("shortDisplayName") or t.get("name") or "",
                                "logo": logos[0].get("href", ""),
                                "color": t.get("color") or "444444",
                            }
        except (requests.RequestException, ValueError) as e:
            log.warning("Could not load teams for %s: %s", league, e)
    return sorted(teams.values(), key=lambda t: t["name"])


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
