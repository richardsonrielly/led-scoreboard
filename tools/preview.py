"""Save a picture of what the panel will look like, without any hardware.

    python3 tools/preview.py            -> preview.png with sample games
"""
import os
import sys

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scoreboard.espn import Game, Team  # noqa: E402
from scoreboard.render import render_game  # noqa: E402

SAMPLES = [
    Game("nfl", "in", "4:12 3RD", "", Team("GB", "Packers", "17", "204E32", "FFB612"),
         Team("CHI", "Bears", "14", "0B162A", "E64100")),
    Game("nhl", "pre", "11/18 7:00 PM", "", Team("NYR", "Rangers", "", "0038A8", "CE1126"),
         Team("NJ", "Devils", "", "CE1126", "000000")),
    Game("mens-college-basketball", "post", "FINAL", "", Team("MARQ", "Marquette", "78", "003366", "FFCC00", True),
         Team("SIE", "Siena", "65", "006B54", "FFC72C")),
]


def led_look(img, dot=10):
    """Scale up and draw each pixel as a round LED."""
    w, h = img.size
    out = Image.new("RGB", (w * dot, h * dot), (12, 12, 12))
    d = ImageDraw.Draw(out)
    px = img.load()
    for y in range(h):
        for x in range(w):
            c = px[x, y]
            if c == (0, 0, 0):
                c = (28, 28, 28)
            d.ellipse([x * dot + 1, y * dot + 1, x * dot + dot - 2, y * dot + dot - 2], fill=c)
    return out


if __name__ == "__main__":
    frames = [led_look(render_game(g)) for g in SAMPLES]
    sheet = Image.new("RGB", (frames[0].width, sum(f.height + 20 for f in frames)), (0, 0, 0))
    y = 0
    for f in frames:
        sheet.paste(f, (0, y))
        y += f.height + 20
    sheet.save("preview.png")
    print("Saved preview.png")
