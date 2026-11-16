"""Which ESPN scoreboards to read for each league.

To add a league, add an entry here. "paths" is a list because some teams
(like the USMNT) play in several competitions.
"""

LEAGUES = {
    "nfl": {"emoji": "🏈", "sport": "football", "name": "NFL", "paths": ["football/nfl"]},
    "mlb": {"emoji": "⚾", "sport": "baseball", "name": "MLB", "paths": ["baseball/mlb"]},
    "nba": {"emoji": "🏀", "sport": "basketball", "name": "NBA", "paths": ["basketball/nba"]},
    "nhl": {"emoji": "🏒", "sport": "hockey", "name": "NHL", "paths": ["hockey/nhl"]},
    "wnba": {"emoji": "🏀", "sport": "basketball", "name": "WNBA", "paths": ["basketball/wnba"]},
    "college-football": {
        "emoji": "🏈",
        "sport": "football",
        "name": "College Football",
        "paths": ["football/college-football"],
        "params": {"groups": "80"},  # all FBS games, not just ranked ones
    },
    "mens-college-basketball": {
        "emoji": "🏀",
        "sport": "basketball",
        "name": "Men's College Basketball",
        "paths": ["basketball/mens-college-basketball"],
        "params": {"groups": "50", "limit": "400"},  # all Division I games
    },
    "mls": {"emoji": "⚽", "sport": "soccer", "name": "MLS", "paths": ["soccer/usa.1"]},
    "epl": {"emoji": "⚽", "sport": "soccer", "name": "Premier League", "paths": ["soccer/eng.1"]},
    "usmnt": {
        "emoji": "⚽",
        "sport": "soccer",
        "name": "USMNT",
        "paths": [
            "soccer/fifa.friendly",
            "soccer/concacaf.nations.league",
            "soccer/concacaf.gold",
            "soccer/fifa.worldq.concacaf",
            "soccer/fifa.world",
        ],
    },
}

BASE_URL = "https://site.api.espn.com/apis/site/v2/sports/{path}/scoreboard"
TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/{path}/teams"


# Extra things each sport can show during a live game. The settings page lists
# these as switches. Each entry: key, label, emoji.
DETAILS = {
    "baseball": [
        ("inning", "Top or bottom of the inning", "🔼"),
        ("count", "Balls and strikes", "🔢"),
        ("outs", "Outs", "❌"),
        ("bases", "Runners on base", "💎"),
        ("batter", "Who's batting", "🧢"),
        ("pitcher", "Who's pitching", "⚾"),
    ],
    "football": [
        ("possession", "Who has the ball", "🏈"),
        ("down", "Down and distance", "📏"),
        ("field", "Field map with the yellow line", "🟩"),
        ("redzone", "Red zone alert", "🚨"),
    ],
}


def details_for(league):
    return DETAILS.get(LEAGUES[league]["sport"], [])
