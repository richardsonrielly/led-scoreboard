"""Main loop: download scores, then cycle through them on the panel.

Run on the Pi:        sudo python3 -m scoreboard.main
Preview on a laptop:  python3 -m scoreboard.main --console
"""
import argparse
import logging
import threading
import time
from datetime import datetime

from . import config, web
from .display import make_display
from .espn import fetch_league, select_games
from .leagues import LEAGUES
from .render import render_game, render_message

log = logging.getLogger("scoreboard")


class Scoreboard:
    def __init__(self, display):
        self.display = display
        self.cfg = config.load()
        self.cfg_mtime = config.mtime()
        self.games = []
        self.last_fetch = 0

    def reload_config_if_changed(self):
        m = config.mtime()
        if m != self.cfg_mtime:
            self.cfg_mtime = m
            old = self.cfg
            self.cfg = config.load()
            self.display.set_brightness(self.cfg["brightness"])
            if old["leagues"] != self.cfg["leagues"]:
                self.last_fetch = 0       # new leagues: fetch right away
            log.info("Settings changed")
            return True
        return False

    def refresh_if_due(self):
        if time.time() - self.last_fetch < self.cfg["refresh_seconds"]:
            return
        games = []
        for league in self.cfg["leagues"]:
            if league in LEAGUES:
                games += fetch_league(league)
        self.games = games
        self.last_fetch = time.time()
        log.info("Loaded %d games", len(games))

    def wait(self, seconds):
        """Sleep, but wake early if the settings change so the board feels responsive."""
        end = time.time() + seconds
        while time.time() < end:
            if self.reload_config_if_changed():
                return True
            time.sleep(0.25)
        return False

    def run(self):
        w, h = self.display.width, self.display.height
        self.display.show(render_message(["LOADING", "SCORES..."], w, h))
        while True:
            self.reload_config_if_changed()
            self.refresh_if_due()
            shown = select_games(self.games, self.cfg)
            if not shown:
                now = datetime.now().strftime("%-I:%M")
                self.display.show(render_message([now, "NO GAMES"], w, h))
                self.wait(10)
                continue
            for game in shown:
                self.display.show(render_game(game, w, h))
                changed = self.wait(self.cfg["seconds_per_game"])
                if changed or time.time() - self.last_fetch >= self.cfg["refresh_seconds"]:
                    break  # start over with fresh settings or scores


def main():
    parser = argparse.ArgumentParser(description="LED sports scoreboard")
    parser.add_argument("--console", action="store_true", help="draw in the terminal instead of the LED panel")
    parser.add_argument("--no-web", action="store_true", help="don't start the settings web page")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s: %(message)s")

    cfg = config.load()
    if not args.no_web:
        threading.Thread(target=web.run, args=(cfg["web_port"],), daemon=True).start()
        log.info("Settings page on port %s", cfg["web_port"])

    display = make_display(cfg, force_console=args.console)
    try:
        Scoreboard(display).run()
    except KeyboardInterrupt:
        display.clear()


if __name__ == "__main__":
    main()
