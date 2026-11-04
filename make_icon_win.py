#!/usr/bin/env python3
"""Writes the WhiskerLock tray image as a Windows .ico (used by install.ps1).

Usage: python make_icon_win.py <output.ico>
"""
import sys

from whiskerlock_win import make_image

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "whiskerlock.ico"
    make_image("ok").save(out, format="ICO",
                          sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])
