#!/bin/bash
# One-time setup on the Raspberry Pi. Run from inside the repo:
#   bash deploy/install.sh
set -e
cd "$(dirname "$0")/.."
REPO_DIR="$(pwd)"

echo "== Installing Python packages =="
sudo apt-get update
sudo apt-get install -y python3-pil python3-requests python3-flask git

if ! python3 -c "import rgbmatrix" 2>/dev/null; then
  echo "== Installing the LED matrix library (takes a while on a Pi Zero) =="
  echo "Adafruit's installer will ask a few questions:"
  echo "  - Interface board: pick 'Adafruit RGB Matrix Bonnet' (or HAT)"
  echo "  - Quality vs convenience: 'convenience' is fine to start"
  curl -fsSL https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/main/rgb-matrix.sh -o /tmp/rgb-matrix.sh
  sudo bash /tmp/rgb-matrix.sh
fi

echo "== Setting up the service so it starts on boot =="
sed "s#/home/pi/led-scoreboard#${REPO_DIR}#" deploy/scoreboard.service | sudo tee /etc/systemd/system/scoreboard.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now scoreboard

echo
echo "Done! Settings page: http://$(hostname).local:8080"
