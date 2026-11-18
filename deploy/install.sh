#!/bin/bash
# One-time setup on the Raspberry Pi. Run from inside the repo:
#   bash deploy/install.sh
#
# What it does:
#   1. Installs system packages
#   2. Makes a Python virtual environment in .venv (newer Raspberry Pi OS
#      versions require one for Python packages)
#   3. Sets up a service so the scoreboard starts whenever the Pi boots
#   4. Runs Adafruit's installer for the LED matrix library (this step asks a
#      few questions, takes up to ~15 minutes, and ends by offering to reboot)
set -e
cd "$(dirname "$0")/.."
REPO_DIR="$(pwd)"
VENV="$REPO_DIR/.venv"

echo "== 1/4 Installing system packages =="
sudo apt-get update
sudo apt-get install -y git wget python3-venv python3-dev python3-pil python3-requests python3-flask

echo "== 2/4 Making the Python virtual environment =="
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV" --system-site-packages
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install --quiet adafruit-python-shell

echo "== 3/4 Setting up the scoreboard service =="
sed -e "s#/home/pi/led-scoreboard#${REPO_DIR}#g" deploy/scoreboard.service \
  | sudo tee /etc/systemd/system/scoreboard.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable scoreboard

if python -c "import rgbmatrix" 2>/dev/null; then
  echo "== 4/4 LED matrix library already installed =="
  sudo systemctl restart scoreboard
  echo "Done! The scoreboard is starting. Its settings address will show on the panel."
  exit 0
fi

echo "== 4/4 Installing the LED matrix library (up to ~15 minutes on a Pi Zero) =="
echo "Adafruit's installer will ask:"
echo "  - Interface board:   choose 'Adafruit RGB Matrix Bonnet'"
echo "  - Quality/Convenience: choose 'Convenience' (Quality needs a soldered jumper)"
echo "  - Reboot at the end: choose YES. The scoreboard starts by itself after the reboot."
echo
cd /tmp
wget -q -O rgb-matrix.py https://github.com/adafruit/Raspberry-Pi-Installer-Scripts/raw/main/rgb-matrix.py
sudo -E env PATH="$PATH" python3 rgb-matrix.py
