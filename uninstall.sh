#!/bin/bash
# Removes WhiskerLock. Also remove it from Login Items and the privacy lists by hand.
set -euo pipefail
PREFIX="${WHISKERLOCK_HOME:-$HOME/.whiskerlock}"
APP_DIR="${WHISKERLOCK_APP_DIR:-/Applications}"
pkill -f "WhiskerLock.app/Contents/MacOS" 2>/dev/null || true
rm -rf "$APP_DIR/WhiskerLock.app" "$PREFIX"
defaults delete local.felipe.whiskerlock 2>/dev/null || true
echo "WhiskerLock removed."
