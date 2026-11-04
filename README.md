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
**Not supported yet.** The detector already has a Linux/X11 key table
(`LINUX_LAYOUT`, unit-tested), but there is no keyboard-capture backend or tray
app, and it has never been run on a Linux desktop. Wayland does not let normal
apps block the global keyboard, so X11 would come first. Help testing is welcome:
open an issue or a pull request.

## Layout

- `detector.py`: platform-independent cat detection (with unit tests in `tests/`).
- `pawpause.py`: macOS app. `pawpause_win.py`: Windows app.

## Acknowledgments

- **[Milad Safarzadeh](https://github.com/miladsafarzadeh1)** for
  [PawPause-mac](https://github.com/miladsafarzadeh1/PawPause-mac) (MIT). The cat
  detection (six weighted signals, 1.5 s window, auto-release, Esc override) is a
  Python port of his `CatDetector.swift`; this project would not exist without it.
  His copyright notice is kept in `LICENSE`.
- Other cat-proof keyboard tools worth a look:
  [JK-Tmux/PawPause](https://github.com/JK-Tmux/PawPause) (Windows) and the
  commercial macOS app *Cats Lock*.
- Built with [pyobjc](https://pyobjc.readthedocs.io/), [py2app](https://py2app.readthedocs.io/),
  [pystray](https://github.com/moses-palmer/pystray) and [Pillow](https://python-pillow.org/).
- Written with [Claude Code](https://claude.com/claude-code).
- And to the cat, for the field testing.

## License

MIT, see `LICENSE`. This is an independent project, not affiliated with the
projects above.
