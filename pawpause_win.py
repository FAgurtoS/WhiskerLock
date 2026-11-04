#!/usr/bin/env python3
"""Paw Pause (Windows): pauses the keyboard when a cat walks on it.

Detection lives in detector.py (ported from miladsafarzadeh1/PawPause-mac, MIT).
Esc always releases. Keystrokes are never stored or sent anywhere: only
key codes and timestamps from the last 1.5 s are kept in memory.

Needs: pip install pystray pillow   (tkinter ships with Python)
"""
import ctypes
import json
import os
import queue
import sys
import threading
import tkinter as tk
from ctypes import wintypes

import pystray
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from detector import CatDetector, WIN_LAYOUT  # noqa: E402

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WH_KEYBOARD_LL = 13
WM_KEYDOWN, WM_KEYUP, WM_SYSKEYDOWN, WM_SYSKEYUP = 0x100, 0x101, 0x104, 0x105
LLKHF_INJECTED = 0x10
ESCAPE = WIN_LAYOUT.escape


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("vkCode", wintypes.DWORD), ("scanCode", wintypes.DWORD),
                ("flags", wintypes.DWORD), ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_size_t)]


HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_ssize_t, ctypes.c_int,
                              wintypes.WPARAM, wintypes.LPARAM)
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, HOOKPROC, wintypes.HINSTANCE,
                                     wintypes.DWORD]
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int,
                                  wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_ssize_t
kernel32.GetModuleHandleW.restype = wintypes.HMODULE

# ---------------------------------------------------------------- settings
SETTINGS_PATH = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")),
                             "PawPause", "settings.json")
DEFAULTS = {"sensitivity": "balanced", "sound": True, "stay": False, "blur": True}
THRESHOLDS = {"high": 0.8, "balanced": 1.0, "relaxed": 1.3}


def load_settings():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            return {**DEFAULTS, **json.load(f)}
    except (OSError, ValueError):
        return dict(DEFAULTS)


def save_settings():
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f)
    except OSError:
        pass


settings = load_settings()
detector = CatDetector(WIN_LAYOUT, threshold=THRESHOLDS.get(settings["sensitivity"], 1.0),
                       stay_locked=bool(settings["stay"]))
lock = threading.Lock()                 # detector is used by hook + UI threads
events = queue.Queue()                  # hook thread -> UI thread
state = {"armed": True, "hook": None, "demo": False}

# ---------------------------------------------------------------- keyboard hook


def _hook(n_code, w_param, l_param):
    if n_code == 0 and state["armed"]:
        k = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        if not (k.flags & LLKHF_INJECTED):          # ignore software-sent keys
            vk = k.vkCode
            if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                with lock:
                    if vk == ESCAPE and detector.blocking:   # human override
                        detector.unlock()
                        events.put("changed")
                        return 1
                    was = detector.blocking
                    detector.feed_down(vk, detector.is_down(vk))
                    now = detector.blocking
                if now and not was:
                    events.put("blocked")
                if now:
                    return 1                        # swallow the key
            elif w_param in (WM_KEYUP, WM_SYSKEYUP):
                # Key-ups always pass, so a modifier can never get stuck down.
                with lock:
                    detector.feed_up(vk)
                    released = detector.tick_auto_release()
                if released:
                    events.put("changed")
    return user32.CallNextHookEx(None, n_code, w_param, l_param)


_hook_proc = HOOKPROC(_hook)            # keep a reference so it is not collected


def hook_thread():
    state["hook"] = user32.SetWindowsHookExW(
        WH_KEYBOARD_LL, _hook_proc, kernel32.GetModuleHandleW(None), 0)
    events.put("changed")
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))


# ---------------------------------------------------------------- tray icon


EMOJI_FONT = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "seguiemj.ttf")
CAT_EMOJI = "\U0001F431"                 # cat face
BADGES = {"blocked": (225, 60, 60, 255), "warn": (240, 170, 40, 255)}
_emoji_cache = []


def _cat_emoji():
    """The cat emoji as a 64x64 RGBA image, or None if the font is unavailable."""
    if not _emoji_cache:
        try:
            font = ImageFont.truetype(EMOJI_FONT, 109)
            big = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
            ImageDraw.Draw(big).text((0, 0), CAT_EMOJI, font=font, embedded_color=True)
            box = big.getbbox()
            glyph = big.crop(box)
            glyph.thumbnail((60, 60), Image.LANCZOS)
            img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
            img.paste(glyph, ((64 - glyph.width) // 2, (64 - glyph.height) // 2), glyph)
            _emoji_cache.append(img)
        except (OSError, ValueError, TypeError):
            _emoji_cache.append(None)
    return _emoji_cache[0]


def _paw_image(kind):
    """Fallback icon: drawn paw on a coloured tile."""
    colors = {"ok": (250, 200, 115), "blocked": (225, 80, 80),
              "off": (160, 160, 160), "warn": (240, 170, 40)}
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 62, 62), 14, fill=colors[kind])
    ink = (60, 40, 20, 255)
    d.ellipse((20, 30, 44, 54), fill=ink)                     # pad
    for x, y in ((11, 24), (23, 12), (37, 12), (49, 24)):     # toes
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=ink)
    return img


def make_image(kind):
    cat = _cat_emoji()
    if cat is None:
        return _paw_image(kind)
    img = cat.copy()
    if kind == "off":                                          # grey cat = not armed
        alpha = img.getchannel("A")
        img = Image.merge("RGBA", (*(img.convert("L"),) * 3, alpha))
    elif kind in BADGES:                                       # dot: blocked / warning
        d = ImageDraw.Draw(img)
        d.ellipse((38, 38, 62, 62), fill=BADGES[kind], outline=(255, 255, 255, 255), width=3)
    return img


def status_kind():
    if not state["hook"]:
        return "warn"
    if not state["armed"]:
        return "off"
    return "blocked" if detector.blocking else "ok"


def status_text(_item=None):
    return {"warn": "Hook not installed", "off": "Off",
            "blocked": "Paused: cat detected (Esc to override)",
            "ok": "Armed: watching"}[status_kind()]


def toggle_armed(icon, item):
    state["armed"] = not state["armed"]
    if not state["armed"]:
        with lock:
            detector.reset()
    events.put("changed")


def toggle_stay(icon, item):
    with lock:
        detector.stay_locked = not detector.stay_locked
    settings["stay"] = detector.stay_locked
    save_settings()


def toggle_sound(icon, item):
    settings["sound"] = not settings["sound"]
    save_settings()


def toggle_blur(icon, item):
    settings["blur"] = not settings["blur"]
    save_settings()


def set_sensitivity(name):
    def action(icon, item):
        settings["sensitivity"] = name
        with lock:
            detector.threshold = THRESHOLDS[name]
        save_settings()
    return action


def unlock(icon, item):
    with lock:
        detector.unlock()
    events.put("changed")


def test_overlay(icon, item):
    state["demo"] = True
    events.put("changed")
    threading.Timer(3.0, lambda: (state.update(demo=False), events.put("changed"))).start()


def quit_app(icon, item):
    events.put("quit")


WM_LBUTTONUP, WM_RBUTTONUP = 0x0202, 0x0205


class TrayIcon(pystray.Icon):
    """Tray icon whose menu opens on left click as well as right click.

    pystray only shows the menu on right click; custom shells (e.g. MyDockFinder)
    and most people expect the primary button to work too.
    """

    def _on_notify(self, wparam, lparam):
        if lparam == WM_LBUTTONUP:
            lparam = WM_RBUTTONUP
        super()._on_notify(wparam, lparam)


def build_tray():
    def sens(name):
        return pystray.MenuItem(name.capitalize(), set_sensitivity(name),
                                checked=lambda i, n=name: settings["sensitivity"] == n,
                                radio=True)
    return TrayIcon("pawpause", make_image("ok"), "Paw Pause", pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.MenuItem("Armed", toggle_armed, checked=lambda i: state["armed"]),
        pystray.MenuItem("Stay locked until I unlock", toggle_stay,
                         checked=lambda i: detector.stay_locked),
        pystray.MenuItem("Play sound when paused", toggle_sound,
                         checked=lambda i: settings["sound"]),
        pystray.MenuItem("Blur overlay (experimental)", toggle_blur,
                         checked=lambda i: settings["blur"]),
        pystray.MenuItem("Sensitivity", pystray.Menu(sens("high"), sens("balanced"),
                                                     sens("relaxed"))),
        pystray.MenuItem("Unlock keyboard", unlock),
        pystray.MenuItem("Test overlay (3 s)", test_overlay),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit Paw Pause", quit_app),
    ))


# ---------------------------------------------------------------- overlay


class Overlay:
    """Full-screen message over all monitors. Click-through, so the mouse works."""

    GWL_EXSTYLE = -20
    EX_TRANSPARENT, EX_TOOLWINDOW, EX_NOACTIVATE, EX_LAYERED = 0x20, 0x80, 0x08000000, 0x80000

    def __init__(self, root):
        self.root = root
        self.win = None

    def show(self):
        if self.win:
            return
        x, y = user32.GetSystemMetrics(76), user32.GetSystemMetrics(77)    # virtual screen
        w, h = user32.GetSystemMetrics(78), user32.GetSystemMetrics(79)
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.configure(bg="black")
        win.attributes("-topmost", True)
        for text, size, dy in (("\U0001F431 Cat in keyboard", 54, -30),
                               ("Press Esc to unlock", 20, 40)):
            tk.Label(win, text=text, bg="black", fg="white",
                     font=("Segoe UI Emoji", size, "bold")).place(relx=0.5, rely=0.5, y=dy,
                                                                  anchor="center")
        win.update_idletasks()
        hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
        blurred = settings["blur"] and self._acrylic(hwnd)
        if not blurred:
            win.attributes("-alpha", 0.82)       # plain dark tint instead of blur
        self._click_through(hwnd, layered=not blurred)
        self.win = win

    def hide(self):
        if self.win:
            self.win.destroy()
            self.win = None

    def _acrylic(self, hwnd):
        """Windows 10/11 acrylic blur-behind. Undocumented API; may fail."""
        class AccentPolicy(ctypes.Structure):
            _fields_ = [("AccentState", ctypes.c_int), ("AccentFlags", ctypes.c_int),
                        ("GradientColor", ctypes.c_uint), ("AnimationId", ctypes.c_int)]

        class WinCompAttrData(ctypes.Structure):
            _fields_ = [("Attribute", ctypes.c_int), ("Data", ctypes.c_void_p),
                        ("SizeOfData", ctypes.c_size_t)]
        try:
            accent = AccentPolicy(4, 2, 0xB0202020, 0)       # ACRYLICBLURBEHIND, AABBGGRR
            data = WinCompAttrData(19, ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p),
                                   ctypes.sizeof(accent))
            return bool(user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data)))
        except (AttributeError, OSError):
            return False

    def _click_through(self, hwnd, layered):
        try:
            get = user32.GetWindowLongPtrW
            set_ = user32.SetWindowLongPtrW
            get.restype = ctypes.c_ssize_t
            set_.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_ssize_t]
            style = get(hwnd, self.GWL_EXSTYLE)
            style |= self.EX_TRANSPARENT | self.EX_TOOLWINDOW | self.EX_NOACTIVATE
            if layered:
                style |= self.EX_LAYERED
            set_(hwnd, self.GWL_EXSTYLE, style)
        except (AttributeError, OSError):
            pass


# ---------------------------------------------------------------- main


def beep():
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass


def already_running():
    """True if another Paw Pause owns the named mutex (single-instance guard)."""
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    state["mutex"] = kernel32.CreateMutexW(None, False, "Local\\PawPauseSingleInstance")
    return ctypes.get_last_error() == 183       # ERROR_ALREADY_EXISTS


def main():
    if already_running():
        sys.exit(0)                             # a second copy would double-hook the keyboard
    root = tk.Tk()
    root.withdraw()
    overlay = Overlay(root)
    tray = build_tray()
    tray.run_detached()
    threading.Thread(target=hook_thread, daemon=True).start()

    def refresh():
        tray.icon = make_image(status_kind())
        tray.update_menu()
        if detector.blocking or state["demo"]:
            overlay.show()
        else:
            overlay.hide()

    def poll():
        with lock:
            if detector.tick_auto_release():
                events.put("changed")
        try:
            while True:
                ev = events.get_nowait()
                if ev == "quit":
                    if state["hook"]:
                        user32.UnhookWindowsHookEx(ctypes.c_void_p(state["hook"]))
                    tray.stop()
                    root.destroy()
                    return
                if ev == "blocked" and settings["sound"]:
                    beep()
                refresh()
        except queue.Empty:
            pass
        root.after(100, poll)

    root.after(100, poll)
    root.mainloop()


if __name__ == "__main__":
    if sys.platform != "win32":
        sys.exit("pawpause_win.py only runs on Windows.")
    main()
