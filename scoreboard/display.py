"""Send images to the LED panel, or to the terminal when testing on a laptop."""
import logging
import sys

log = logging.getLogger(__name__)


class MatrixDisplay:
    """The real Adafruit panel, via the rpi-rgb-led-matrix library."""

    def __init__(self, panel, brightness):
        from rgbmatrix import RGBMatrix, RGBMatrixOptions  # only installed on the Pi

        opts = RGBMatrixOptions()
        opts.rows = panel["rows"]
        opts.cols = panel["cols"]
        opts.chain_length = panel["chain_length"]
        opts.hardware_mapping = panel["hardware_mapping"]
        opts.gpio_slowdown = panel["gpio_slowdown"]
        opts.brightness = brightness
        # The library normally drops root after starting, which would stop us
        # saving config.json from the web page. Keep root.
        opts.drop_privileges = False
        self.matrix = RGBMatrix(options=opts)
        self.width = self.matrix.width
        self.height = self.matrix.height

    def set_brightness(self, value):
        self.matrix.brightness = max(1, min(100, int(value)))

    def show(self, img):
        self.matrix.SetImage(img.convert("RGB"))

    def clear(self):
        self.matrix.Clear()


class ConsoleDisplay:
    """Draws the panel in the terminal with colored blocks, for testing off the Pi."""

    def __init__(self, panel, brightness):
        self.width = panel["cols"] * panel["chain_length"]
        self.height = panel["rows"]
        self.brightness = brightness

    def set_brightness(self, value):
        self.brightness = value

    def show(self, img):
        px = img.load()
        out = ["\033[H\033[2J"]  # clear screen
        for y in range(self.height):
            row = []
            for x in range(self.width):
                r, g, b = px[x, y]
                row.append(f"\033[38;2;{r};{g};{b}m█" if (r or g or b) else " ")
            out.append("".join(row) + "\033[0m")
        sys.stdout.write("\n".join(out) + "\n")
        sys.stdout.flush()

    def clear(self):
        pass


def make_display(cfg, force_console=False):
    if not force_console:
        try:
            return MatrixDisplay(cfg["panel"], cfg["brightness"])
        except ImportError:
            log.info("rgbmatrix not installed; using the terminal preview instead")
    return ConsoleDisplay(cfg["panel"], cfg["brightness"])
