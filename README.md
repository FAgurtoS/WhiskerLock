# Paw Pause 🐱

A macOS menu-bar app that pauses your keyboard when a cat walks on it, and blurs
the screen with a "Cat in keyboard" message until it is safe again.

- Detects cat-like typing (many keys at once, scattered bursts, adjacent-key paw rolls).
- **Esc always unlocks.** The mouse keeps working, so you can also unlock from the menu.
- Sensitivity slider, optional sound, "stay locked" mode. Settings are remembered.
- Runs locally. Keystrokes are never stored or sent anywhere: only key codes and
  timestamps from the last 1.5 s are kept in memory.

## Install

### macOS
Requires a Python 3 (`brew install python`). Xcode is **not** needed.

```
./install.sh
```

Then enable **Paw Pause** under System Settings > Privacy & Security >
**Accessibility** and **Input Monitoring**, and reopen the app.
Uninstall with `./uninstall.sh`.

### Windows (experimental, needs testing)
Requires Python 3.9+ ([python.org](https://www.python.org/downloads/)). In PowerShell:

```
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Open **Paw Pause** from the Start Menu; the paw icon lives in the system tray
(click the ^ arrow if hidden). No special permissions are needed.
The blur overlay uses an undocumented Windows API; if it does not look right,
untick "Blur overlay" in the tray menu for a plain dark tint.
Uninstall with `uninstall.ps1`.

### Linux
Not supported yet.

## Layout

- `detector.py`: platform-independent cat detection (with unit tests in `tests/`).
- `pawpause.py`: macOS app. `pawpause_win.py`: Windows app.

## Credits

The detection logic is a Python port of the detector in
[miladsafarzadeh1/PawPause-mac](https://github.com/miladsafarzadeh1/PawPause-mac)
(MIT, by Milad Safarzadeh). The menu-bar app, blur overlay and installer are new.
