"""Which ESPN scoreboards to read for each league.

To add a league, add an entry here. "paths" is a list because some teams
(like the USMNT) play in several competitions.
"""

LEAGUES = {
    "nfl": {"name": "NFL", "paths": ["football/nfl"]},
    "mlb": {"name": "MLB", "paths": ["baseball/mlb"]},
    "nba": {"name": "NBA", "paths": ["basketball/nba"]},
    "nhl": {"name": "NHL", "paths": ["hockey/nhl"]},
    "wnba": {"name": "WNBA", "paths": ["basketball/wnba"]},
    "college-football": {
        "name": "College Football",
        "paths": ["football/college-football"],
        "params": {"groups": "80"},  # all FBS games, not just ranked ones
    },
    "mens-college-basketball": {
        "name": "Men's College Basketball",
        "paths": ["basketball/mens-college-basketball"],
        "params": {"groups": "50", "limit": "400"},  # all Division I games
    },
    "mls": {"name": "MLS", "paths": ["soccer/usa.1"]},
    "epl": {"name": "Premier League", "paths": ["soccer/eng.1"]},
    "usmnt": {
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
