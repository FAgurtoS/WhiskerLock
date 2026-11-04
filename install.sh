#!/bin/bash
# Installs Paw Pause.app. Needs a real Python 3 (e.g. `brew install python`),
# but NOT Xcode or the Command Line Tools.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
PREFIX="${PAWPAUSE_HOME:-$HOME/.pawpause}"
APP_DIR="${PAWPAUSE_APP_DIR:-/Applications}"

# Find a working Python 3 (skip the /usr/bin stub, it triggers an Xcode dialog).
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    [ -x "$c" ] && PY="$c" && break
  done
fi
if [ -z "$PY" ]; then
  echo "No Python 3 found. Install one with: brew install python" >&2
  exit 1
fi
"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 9))' \
  || { echo "Python 3.9+ required ($PY)" >&2; exit 1; }

echo "==> Installing into $PREFIX"
mkdir -p "$PREFIX"
cp "$HERE/pawpause.py" "$HERE/detector.py" "$HERE/make_icon.py" "$HERE/setup.py" "$PREFIX/"
cd "$PREFIX"

echo "==> Creating Python environment"
"$PY" -m venv venv
venv/bin/pip install --quiet --upgrade pip
venv/bin/pip install --quiet pyobjc-framework-Quartz pyobjc-framework-Cocoa py2app

echo "==> Making icon"
venv/bin/python make_icon.py
rm -rf PawPause.iconset && mkdir PawPause.iconset
for s in 16 32 128 256 512; do
  sips -z $s $s icon1024.png --out PawPause.iconset/icon_${s}x${s}.png >/dev/null
  sips -z $((s*2)) $((s*2)) icon1024.png --out PawPause.iconset/icon_${s}x${s}@2x.png >/dev/null
done
iconutil -c icns PawPause.iconset -o PawPause.icns

echo "==> Building app"
rm -rf build dist
venv/bin/python setup.py py2app -A >/dev/null

echo "==> Copying to $APP_DIR"
rm -rf "$APP_DIR/Paw Pause.app"
cp -R "dist/Paw Pause.app" "$APP_DIR/"

cat <<MSG

Done: $APP_DIR/Paw Pause.app
Next:
  1. Open it (a cat icon appears in the menu bar; a warning sign means permissions are missing).
  2. System Settings > Privacy & Security: enable Paw Pause under
     Accessibility and Input Monitoring, then reopen the app.
  3. Optional: add it under General > Login Items to start automatically.
Keep $PREFIX: the app runs from it.
MSG
