"""Run with:  python3 -m unittest discover tests"""
import unittest

from scoreboard.espn import Game, Team, matches, parse_scoreboard, select_games, short_status
from scoreboard.render import render_game, text_width


def competitor(abbr, name, score, home_away, color="000000", winner=False):
    return {"homeAway": home_away, "score": score, "winner": winner,
            "team": {"abbreviation": abbr, "displayName": name, "color": color, "alternateColor": "FFFFFF"}}


SAMPLE = {"events": [
    {"date": "2026-11-16T18:00Z", "competitions": [{
        "status": {"type": {"state": "in", "shortDetail": "4:12 - 3rd"}},
        "competitors": [competitor("GB", "Green Bay Packers", "17", "away", "204E32"),
                        competitor("CHI", "Chicago Bears", "14", "home", "0B162A")]}]},
    {"date": "2026-11-16T23:00Z", "competitions": [{
        "status": {"type": {"state": "pre", "shortDetail": "11/16 - 8:15 PM EST"}},
        "competitors": [competitor("MIA", "Miami Dolphins", "0", "away"),
                        competitor("NYJ", "New York Jets", "0", "home", "125740")]}]},
    {"date": "2026-11-16T17:00Z", "competitions": [{
        "status": {"type": {"state": "post", "shortDetail": "Final"}},
        "competitors": [competitor("DAL", "Dallas Cowboys", "20", "away", winner=True),
                        competitor("PHI", "Philadelphia Eagles", "10", "home")]}]},
]}


class TestScoreboard(unittest.TestCase):
    def setUp(self):
        self.games = parse_scoreboard(SAMPLE, "nfl")

    def test_parse(self):
        self.assertEqual(len(self.games), 3)
        g = self.games[0]
        self.assertEqual((g.away.abbr, g.away.score, g.home.abbr), ("GB", "17", "CHI"))
        self.assertEqual(g.status, "4:12 3RD")

    def test_short_status_drops_time_zone(self):
        self.assertEqual(short_status("pre", "11/16 - 8:15 PM EST"), "11/16 8:15 PM")

    def test_favorites_mode(self):
        cfg = {"mode": "favorites", "favorites": {"nfl": ["GB", "Jets"]}}
        shown = select_games(self.games, cfg)
        self.assertEqual([g.away.abbr for g in shown], ["GB", "MIA"])  # live game first

    def test_all_mode(self):
        self.assertEqual(len(select_games(self.games, {"mode": "all"})), 3)

    def test_hide_finished(self):
        cfg = {"mode": "all", "show_final": False}
        self.assertEqual(len(select_games(self.games, cfg)), 2)

    def test_short_codes_dont_match_names(self):
        albany = Team("ALB", "Albany Great Danes", "", "", "")
        self.assertFalse(matches(albany, "NY"))
        siena = Team("SIE", "Siena Saints", "", "", "")
        self.assertTrue(matches(siena, "siena"))
        self.assertTrue(matches(siena, "SIE"))

    def test_render_fits_panel(self):
        img = render_game(self.games[0])
        self.assertEqual(img.size, (64, 32))
        self.assertLessEqual(text_width("MARQ", 2) + text_width("100", 2) + 3, 64)


if __name__ == "__main__":
    unittest.main()


class TestDetails(unittest.TestCase):
    def test_baseball_details_page(self):
        from scoreboard.render import render_pages
        g = Game("mlb", "in", "BOT 5TH", "", Team("ATL", "Braves", "3", "", ""), Team("NYM", "Mets", "4", "", ""),
                 situation={"half": "bottom", "inning": 5, "balls": 2, "strikes": 1, "outs": 1,
                            "on_first": True, "batter": "F. Lindor", "pitcher": "S. Strider"})
        self.assertEqual(len(render_pages(g, {"details": {}})), 3)       # score, batter, pitcher
        off = {"details": {"mlb": {"batter": False, "pitcher": False}}}
        self.assertEqual(len(render_pages(g, off)), 2)                    # score, diamond
        self.assertEqual(len(render_pages(g, {"details": {}}, width=128)), 2)  # side by side

    def test_football_spot_from_text(self):
        data = {"events": [{"competitions": [{
            "status": {"type": {"state": "in", "shortDetail": "4:12 - 3rd"}},
            "situation": {"possession": "20", "possessionText": "NYJ 35", "shortDownDistanceText": "2nd & 7"},
            "competitors": [competitor("MIA", "Miami Dolphins", "3", "away"),
                            competitor("NYJ", "New York Jets", "7", "home")]}]}]}
        data["events"][0]["competitions"][0]["competitors"][1]["team"]["id"] = "20"
        s = parse_scoreboard(data, "nfl")[0].situation
        self.assertEqual((s["possession"], s["yards_to_goal"]), ("home", 65))


class TestWeb(unittest.TestCase):
    def setUp(self):
        import os
        import tempfile
        from scoreboard import config
        self.path = os.path.join(tempfile.mkdtemp(), "config.json")
        self._orig = config.CONFIG_PATH
        config.load.__defaults__ = (self.path,)
        config.save.__defaults__ = (self.path,)
        from scoreboard import web
        self.client = web.app.test_client()

    def tearDown(self):
        from scoreboard import config
        config.load.__defaults__ = (self._orig,)
        config.save.__defaults__ = (self._orig,)

    def test_update_only_known_values(self):
        r = self.client.post("/api/config", json={"brightness": 500, "mode": "all", "hack": 1,
                                                   "details": {"mlb": {"batter": False, "nope": True}}})
        cfg = r.get_json()["config"]
        self.assertEqual((cfg["brightness"], cfg["mode"]), (100, "all"))
        self.assertNotIn("hack", cfg)
        self.assertEqual(cfg["details"]["mlb"], {"batter": False})

    def test_page_and_preview(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/now.png").mimetype, "image/png")
        leagues = self.client.get("/api/config").get_json()["leagues"]
        self.assertTrue(any(lg["key"] == "mlb" and lg["details"] for lg in leagues))
