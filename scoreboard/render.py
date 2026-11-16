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
    "/": ["001", "001", "010", "100", "100"], "&": ["010", "101", "010", "101", "011"],
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
