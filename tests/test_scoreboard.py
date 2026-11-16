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
