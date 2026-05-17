#!/usr/bin/env bash
# launch_applycraft.sh — Bootstrap the venv if missing, then start the GUI.
# Works on macOS and Linux. (Windows users: use launch_applycraft.bat.)

set -euo pipefail

cd "$(dirname "$0")"

if [[ ! -x "venv/bin/python" ]]; then
  echo "No venv detected. Running first-run setup..."
  python3 setup_applycraft.py
fi

exec "venv/bin/python" core/cv_generator_gui.py
