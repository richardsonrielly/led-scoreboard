"""Save a picture of what the panel will look like, without any hardware.

    python3 tools/preview.py            -> preview.png with sample games (64x32 panel)
    python3 tools/preview.py 128        -> same, for two chained panels (128x32)
"""
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scoreboard.espn import Game, Team  # noqa: E402
from scoreboard.render import led_look, render_pages  # noqa: E402

SAMPLES = [
    Game("nfl", "in", "4:12 3RD", "", Team("GB", "Packers", "17", "204E32", "FFB612"),
         Team("CHI", "Bears", "14", "0B162A", "E64100")),
    Game("mlb", "in", "BOT 5TH", "", Team("ATL", "Braves", "3", "0C2340", "CE1141"),
         Team("NYM", "Mets", "4", "002D72", "FF5910"),
         situation={"half": "bottom", "inning": 5, "balls": 2, "strikes": 1, "outs": 1,
                    "on_first": True, "on_second": False, "on_third": True,
                    "batter": "F. Lindor", "pitcher": "S. Strider"}),
    Game("nfl", "in", "4:12 3RD", "", Team("MIA", "Dolphins", "3", "008E97", "FC4C02", id="15"),
         Team("NYJ", "Jets", "7", "125740", "FFFFFF", id="20"),
         situation={"possession": "home", "down_text": "2nd & 7", "spot_text": "MIA 18",
                    "yards_to_goal": 18, "distance": 7, "red_zone": True}),
    Game("nhl", "pre", "11/18 7:00 PM", "", Team("NYR", "Rangers", "", "0038A8", "CE1126"),
         Team("NJ", "Devils", "", "CE1126", "000000")),
    Game("mens-college-basketball", "post", "FINAL", "", Team("MARQ", "Marquette", "78", "003366", "FFCC00", True),
         Team("SIE", "Siena", "65", "006B54", "FFC72C")),
]




if __name__ == "__main__":
    width = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    cfg = {"details": {}}
    rows = [[led_look(p) for p in render_pages(g, cfg, width, 32)] for g in SAMPLES]
    cols = max(len(r) for r in rows)
    fw, fh = rows[0][0].size
    sheet = Image.new("RGB", (cols * (fw + 20) - 20, len(rows) * (fh + 20) - 20), (0, 0, 0))
    for i, row in enumerate(rows):
        for j, frame in enumerate(row):
            sheet.paste(frame, (j * (fw + 20), i * (fh + 20)))
    sheet.save("preview.png")
    print("Saved preview.png")
