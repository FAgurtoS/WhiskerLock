"""Cat detection engine, shared by every platform.

Python port of CatDetector.swift from miladsafarzadeh1/PawPause-mac (MIT).
It only knows about key codes and time. Each platform passes its own
`Layout` (escape key, "human structure" keys, QWERTY neighbours).
"""
import time

WINDOW = 1.5           # seconds of history
RELEASE_SILENCE = 1.0  # quiet time before auto-release

# Signal weights
W_CONCURRENT, W_CONCURRENT_HI, W_BURST = 0.7, 0.7, 0.4
W_CLUSTER, W_REPEAT, W_NOSTRUCT = 0.4, 0.3, 0.2


def build_adjacency(rows):
    """Keys next to each other (same row +-1, rows above/below +-1)."""
    adj = {}
    for r, row in enumerate(rows):
        for c, key in enumerate(row):
            n = set()
            if c > 0:
                n.add(row[c - 1])
            if c < len(row) - 1:
                n.add(row[c + 1])
            for dr in (r - 1, r + 1):
                if 0 <= dr < len(rows):
                    for oc in (c - 1, c, c + 1):
                        if 0 <= oc < len(rows[dr]):
                            n.add(rows[dr][oc])
            adj.setdefault(key, set()).update(n)
    return adj


class Layout:
    def __init__(self, escape, structural, rows):
        self.escape = escape
        self.structural = set(structural)  # space, return, delete, tab, ...
        self.adjacency = build_adjacency(rows)


# macOS CGKeyCodes (US layout)
MAC_LAYOUT = Layout(
    escape=53,
    structural={49, 36, 51, 48, 76},
    rows=[
        [12, 13, 14, 15, 17, 16, 32, 34, 31, 35],  # q w e r t y u i o p
        [0, 1, 2, 3, 5, 4, 38, 40, 37],            # a s d f g h j k l
        [6, 7, 8, 9, 11, 45, 46, 43, 47],          # z x c v b n m , .
    ],
)

# Windows virtual-key codes
WIN_LAYOUT = Layout(
    escape=0x1B,
    structural={0x20, 0x0D, 0x08, 0x09},  # space, enter, backspace, tab
    rows=[
        [ord(c) for c in "QWERTYUIOP"],
        [ord(c) for c in "ASDFGHJKL"],
        [ord(c) for c in "ZXCVBNM"] + [0xBC, 0xBE],  # , .
    ],
)

# Linux / X11 keycodes (evdev code + 8)
LINUX_LAYOUT = Layout(
    escape=9,
    structural={65, 36, 22, 23, 104},  # space, return, backspace, tab, kp enter
    rows=[
        list(range(24, 34)),  # q w e r t y u i o p
        list(range(38, 47)),  # a s d f g h j k l
        list(range(52, 61)),  # z x c v b n m , .
    ],
)


class CatDetector:
    def __init__(self, layout=MAC_LAYOUT, threshold=1.0, stay_locked=False,
                 clock=time.monotonic):
        self.layout = layout
        self.threshold = threshold
        self.stay_locked = stay_locked
        self.blocking = False
        self._clock = clock
        self._window = []      # (code, time)
        self._down = set()
        self._last = 0.0

    def reset(self):
        self._window.clear()
        self._down.clear()
        self.blocking = False

    unlock = reset

    def is_down(self, code):
        return code in self._down

    def feed_down(self, code, repeating=False):
        t = self._clock()
        self._last = t
        if not repeating:
            self._down.add(code)
        self._window.append((code, t))
        self._window = [s for s in self._window if t - s[1] <= WINDOW]
        if self._score() >= self.threshold:
            self.blocking = True
        return self.blocking

    def feed_up(self, code):
        self._down.discard(code)

    def tick_auto_release(self):
        """True on the tick that releases the lock."""
        if self.blocking and not self.stay_locked:
            if not self._down and self._clock() - self._last >= RELEASE_SILENCE:
                self.reset()
                return True
        return False

    def _score(self):
        s = 0.0
        held = len(self._down)
        if held >= 3:
            s += W_CONCURRENT
        if held >= 5:
            s += W_CONCURRENT_HI
        if len(self._window) / WINDOW >= 8:
            s += W_BURST
        codes = [c for c, _ in self._window]
        adj = self.layout.adjacency
        run = sum(1 for a, b in zip(codes, codes[1:]) if a != b and b in adj.get(a, ()))
        if run >= 3:
            s += W_CLUSTER
        counts = {}
        for c in codes:
            counts[c] = counts.get(c, 0) + 1
        if any(v >= 6 for v in counts.values()):
            s += W_REPEAT
        if len(codes) >= 6 and not any(c in self.layout.structural for c in codes):
            s += W_NOSTRUCT
        return s
