"""Draw a game (or a message) onto a small image that matches the LED panel.

Uses a hand-made 3x5 pixel font so every letter lands exactly on an LED.
Scores and team codes are drawn at 2x size.
"""
from PIL import Image

# Each character is 5 rows; "1" = LED on. Most are 3 pixels wide.
FONT = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "111", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "001", "010", "010"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"],
    "C": ["011", "100", "100", "100", "011"], "D": ["110", "101", "101", "101", "110"],
    "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"], "H": ["101", "101", "111", "101", "101"],
    "I": ["111", "010", "010", "010", "111"], "J": ["001", "001", "001", "101", "010"],
    "K": ["101", "101", "110", "101", "101"], "L": ["100", "100", "100", "100", "111"],
    "M": ["10001", "11011", "10101", "10001", "10001"],
    "N": ["1001", "1101", "1011", "1001", "1001"],
    "O": ["010", "101", "101", "101", "010"], "P": ["110", "101", "110", "100", "100"],
    "Q": ["010", "101", "101", "110", "011"], "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"],
    "U": ["101", "101", "101", "101", "111"], "V": ["101", "101", "101", "101", "010"],
    "W": ["10001", "10001", "10101", "11011", "10001"],
    "X": ["101", "101", "010", "101", "101"], "Y": ["101", "101", "010", "010", "010"],
    "Z": ["111", "001", "010", "100", "111"],
    " ": ["00", "00", "00", "00", "00"], ":": ["0", "1", "0", "1", "0"],
    ".": ["0", "0", "0", "0", "1"], "-": ["000", "000", "111", "000", "000"],
    "/": ["001", "001", "010", "100", "100"], "&": ["0100", "1010", "0100", "1011", "0110"],
    "'": ["1", "1", "0", "0", "0"], "(": ["01", "10", "10", "10", "01"],
    ")": ["10", "01", "01", "01", "10"], "@": ["111", "101", "111", "100", "011"],
}

WHITE = (255, 255, 255)
GRAY = (110, 110, 110)
YELLOW = (255, 200, 0)
GREEN = (0, 200, 60)


def text_width(text, scale=1):
    chars = [FONT[c] for c in text.upper() if c in FONT]
    if not chars:
        return 0
    return sum((len(g[0]) + 1) * scale for g in chars) - scale


def draw_text(img, x, y, text, color, scale=1):
    px = img.load()
    w, h = img.size
    for ch in text.upper():
        glyph = FONT.get(ch)
        if glyph is None:
            continue
        for row, bits in enumerate(glyph):
            for col, bit in enumerate(bits):
                if bit == "1":
                    for dy in range(scale):
                        for dx in range(scale):
                            X, Y = x + col * scale + dx, y + row * scale + dy
                            if 0 <= X < w and 0 <= Y < h:
                                px[X, Y] = color
        x += (len(glyph[0]) + 1) * scale
    return x


def hex_color(h):
    h = (h or "FFFFFF").lstrip("#")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return WHITE


def team_color(team):
    """Use the team's color, brightened so dark colors (navy, forest green) show up on LEDs."""
    for h in (team.color, team.alt_color):
        r, g, b = hex_color(h)
        peak = max(r, g, b)
        if peak < 40:            # basically black: try the alternate color
            continue
        if 0.299 * r + 0.587 * g + 0.114 * b < 90:
            r, g, b = (int(c * 255 / peak) for c in (r, g, b))
        return (r, g, b)
    return WHITE


def dim(color, factor=0.5):
    return tuple(int(c * factor) for c in color)


def render_game(game, width=64, height=32):
    img = Image.new("RGB", (width, height))
    rows = [(game.away, 1), (game.home, 12)]
    for team, y in rows:
        color = team_color(team)
        lost = game.state == "post" and not team.winner and (game.away.winner or game.home.winner)
        if lost:
            color = dim(color)
        draw_text(img, 1, y, team.abbr[:4], color, scale=2)
        if game.state != "pre":
            score_color = dim(WHITE) if lost else WHITE
            sw = text_width(team.score, scale=2)
            draw_text(img, width - sw - 1, y, team.score, score_color, scale=2)

    status_color = {"in": GREEN, "pre": YELLOW}.get(game.state, GRAY)
    status = game.status
    while status and text_width(status) > width - 2:   # trim to fit
        status = status[:-1]
    draw_text(img, (width - text_width(status)) // 2, height - 6, status, status_color)
    return img


def render_message(lines, width=64, height=32, color=WHITE):
    img = Image.new("RGB", (width, height))
    total = len(lines) * 7 - 2
    y = (height - total) // 2
    for line in lines:
        draw_text(img, (width - text_width(line)) // 2, y, line, color)
        y += 7
    return img


# ---------------------------------------------------------------------------
# Live-game detail pages. Each sport gets its own layout; the main loop flips
# between the score page and these. On a 128-wide panel they sit side by side.
# ---------------------------------------------------------------------------
from PIL import ImageDraw  # noqa: E402

from .config import detail_on  # noqa: E402
from .leagues import LEAGUES  # noqa: E402

RED = (230, 30, 30)
DIM = (45, 45, 45)
BROWN = (190, 95, 30)
FIELD = (0, 85, 20)
FIELD_LINE = (0, 140, 40)


def ordinal(n):
    n = int(n)
    suffix = "TH" if 10 <= n % 100 <= 20 else {1: "ST", 2: "ND", 3: "RD"}.get(n % 10, "TH")
    return f"{n}{suffix}"


def fit(text, width):
    text = (text or "").upper()
    while text and text_width(text) > width:
        text = text[:-1]
    return text


def _base(d, cx, cy, on, r=3):
    pts = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    d.polygon(pts, fill=YELLOW if on else None, outline=YELLOW if on else GRAY)


def _triangle(d, x, y, up, color):
    if up:
        d.polygon([(x + 2, y), (x + 4, y + 2), (x, y + 2)], fill=color)
    else:
        d.polygon([(x, y), (x + 4, y), (x + 2, y + 2)], fill=color)


def _baseball_icon(d, x, y):
    d.ellipse([x + 1, y, x + 4, y + 3], fill=WHITE)            # the ball
    d.point([(x + 2, y + 1)], fill=RED)                        # a stitch


def _score_row(img, d, game, icon_team=None, icon=None):
    """Top row shared by the full-screen layouts: AWAY 3 ........ 7 HOME."""
    width = img.size[0]
    edges = []
    for team, side in ((game.away, "left"), (game.home, "right")):
        abbr = team.abbr[:4]
        aw, sw = text_width(abbr), text_width(team.score, scale=2)
        if side == "left":
            ax, sx = 1, 1 + aw + 2
            edges.append(sx + sw)
        else:
            ax = width - 1 - aw
            sx = ax - 2 - sw
            edges.append(sx)
        draw_text(img, ax, 2, abbr, team_color(team))
        draw_text(img, sx, 1, team.score, WHITE, scale=2)
        if icon and team is icon_team:
            icon(d, ax + (aw - 7) // 2 + 1, 8)
    # A little dash between the scores so "10 12" never reads as "1012"
    gap_left, gap_right = edges
    if gap_right - gap_left >= 6:
        mid = (gap_left + gap_right) // 2
        d.line([mid - 1, 5, mid, 5], fill=GRAY)


def last_name(name):
    parts = (name or "").split()
    return parts[-1] if parts else ""


def baseball_pages(game, cfg, width=64, height=32):
    """Complete screens for a live baseball game: score, inning, count, outs,
    bases, and the batter (then the pitcher) on the bottom line."""
    s = game.situation
    on = lambda key: detail_on(cfg, game.league, key)  # noqa: E731
    half = s.get("half")
    batting = {"top": game.away, "bottom": game.home}.get(half)
    people = [k for k in ("batter", "pitcher") if on(k) and s.get(k)]

    def page(person_key):
        img = Image.new("RGB", (width, height))
        d = ImageDraw.Draw(img)
        _score_row(img, d, game, batting, _baseball_icon)

        # Inning (with an up/down arrow for top/bottom)
        if on("inning") and s.get("inning"):
            if half in ("top", "bottom"):
                _triangle(d, 2, 14, half == "top", WHITE)
                draw_text(img, 8, 13, ordinal(s["inning"]), WHITE)
            else:
                draw_text(img, 2, 13, f"{(half or '')[:3]} {s['inning']}".strip(), WHITE)
        # Balls-strikes and outs
        x = 2
        if on("count") and s.get("balls") is not None:
            x = draw_text(img, x, 19, str(s["balls"]), GREEN)
            x = draw_text(img, x, 19, "-", GRAY)
            x = draw_text(img, x, 19, str(s.get("strikes", 0)), RED) + 4
        if on("outs") and s.get("outs") is not None:
            for i in range(3):
                d.ellipse([x + i * 5, 19, x + i * 5 + 3, 22], fill=RED if i < s["outs"] else DIM)
        # Batter or pitcher
        if person_key:
            label = "AB " if person_key == "batter" else "P "
            nx = draw_text(img, 2, 26, label, GRAY)
            draw_text(img, nx, 26, fit(last_name(s[person_key]), width - 26 - nx), WHITE)
        # The diamond, bottom right
        if on("bases"):
            cx = width - 12
            _base(d, cx, 16, s.get("on_second"))
            _base(d, cx - 7, 23, s.get("on_third"))
            _base(d, cx + 7, 23, s.get("on_first"))
            d.rectangle([cx - 1, 29, cx + 1, 30], fill=WHITE)    # home plate
        return img

    return [page(p) for p in people] or [page(None)]


def _football_icon(d, x, y):
    d.ellipse([x, y, x + 6, y + 3], fill=BROWN)                 # the football
    d.line([x + 2, y + 1, x + 4, y + 1], fill=WHITE)           # its laces


def football_pages(game, cfg, width=64, height=32):
    """One complete screen for a live football game: score, clock, down, field."""
    s = game.situation
    on = lambda key: detail_on(cfg, game.league, key)  # noqa: E731
    offense = game.away if s["possession"] == "away" else game.home
    defense = game.home if offense is game.away else game.away
    img = Image.new("RGB", (width, height))
    d = ImageDraw.Draw(img)
    red_zone = on("redzone") and s.get("red_zone")
    if red_zone:                       # red stripes across the top and bottom
        d.line([0, 0, width - 1, 0], fill=RED)
        d.line([0, height - 1, width - 1, height - 1], fill=RED)

    # Top row: AWAY 3 ........ 7 HOME, with a football under whoever has the ball
    _score_row(img, d, game, offense if on("possession") else None, _football_icon)

    # Middle: quarter and clock on the left, ball spot on the right
    status = fit(game.status, width - 4)
    draw_text(img, 2, 13, status, GREEN)
    if on("down"):
        spot = s.get("spot_text", "").upper()
        if spot and text_width(status) + text_width(spot) + 4 <= width - 4:
            draw_text(img, width - 2 - text_width(spot), 13, spot, GRAY)
        draw_text(img, 2, 19, fit(s.get("down_text"), width - 4), RED if red_zone else WHITE)

    ytg = s.get("yards_to_goal")
    if on("field") and ytg is not None:
        left, right, top, bottom = 2, width - 3, 26, 29
        ez = 5
        d.rectangle([left, top, left + ez - 1, bottom], fill=dim(team_color(offense), 0.6))
        d.rectangle([right - ez + 1, top, right, bottom], fill=dim(team_color(defense), 0.6))
        f0, f1 = left + ez, right - ez + 1                      # the 100 yards
        d.rectangle([f0, top, f1 - 1, bottom], fill=FIELD)
        yard_x = lambda yards: f0 + round(yards * (f1 - f0) / 100)  # noqa: E731
        for yards in range(10, 100, 10):
            d.line([yard_x(yards), top, yard_x(yards), bottom], fill=FIELD_LINE)
        ball = 100 - ytg
        dist = s.get("distance")
        if dist and dist < ytg:
            d.line([yard_x(ball + dist), top - 1, yard_x(ball + dist), bottom + 1], fill=YELLOW)
        bx = yard_x(ball)
        d.rectangle([bx - 1, top, bx, bottom], fill=BROWN)
    return [img]


DETAIL_LAYOUTS = {"baseball": baseball_pages, "football": football_pages}
# Sports whose live layout already includes the score and clock, so it
# replaces the score page instead of alternating with it.
FULL_LAYOUTS = {"football", "baseball"}


def render_pages(game, cfg, width=64, height=32):
    """All the pages for one game: the score, then any live details."""
    detail = []
    sport = LEAGUES.get(game.league, {}).get("sport")
    layout = DETAIL_LAYOUTS.get(sport)
    if sport in FULL_LAYOUTS and game.state == "in" and game.situation:
        return layout(game, cfg, width, height)
    if layout and game.state == "in" and game.situation:
        panel_w = 64 if width >= 128 else width
        detail = layout(game, cfg, panel_w, height)
    if detail and width >= 128:
        # Wide panel: score on the left, details on the right
        pages = []
        for page in detail:
            img = Image.new("RGB", (width, height))
            img.paste(render_game(game, 64, height), (0, 0))
            img.paste(page, (64, 0))
            pages.append(img)
        return pages
    return [render_game(game, width, height)] + detail


def led_look(img, dot=10):
    """Scale up and draw each pixel as a round LED (for previews)."""
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
