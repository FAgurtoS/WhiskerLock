#!/bin/bash
# Removes Paw Pause. Also remove it from Login Items and the privacy lists by hand.
set -euo pipefail
PREFIX="${PAWPAUSE_HOME:-$HOME/.pawpause}"
APP_DIR="${PAWPAUSE_APP_DIR:-/Applications}"
pkill -f "Paw Pause.app/Contents/MacOS" 2>/dev/null || true
rm -rf "$APP_DIR/Paw Pause.app" "$PREFIX"
defaults delete local.felipe.pawpause 2>/dev/null || true
echo "Paw Pause removed."
