import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from detector import CatDetector, MAC_LAYOUT, WIN_LAYOUT, LINUX_LAYOUT  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def keys(layout):
    """Return (home row of 5 keys, human 'hello world' sequence) per layout."""
    if layout is MAC_LAYOUT:
        return [0, 1, 2, 3, 5], [4, 14, 37, 37, 31, 49, 13, 31, 15, 37, 2]
    if layout is WIN_LAYOUT:
        return [ord(c) for c in "ASDFG"], [ord(c) for c in "HELLO"] + [0x20] + [ord(c) for c in "WORLD"]
    return [38, 39, 40, 41, 42], [43, 26, 46, 46, 32, 65, 25, 32, 27, 46, 40]


class DetectorTests(unittest.TestCase):
    def check(self, layout):
        chord, human = keys(layout)

        clk = Clock()
        d = CatDetector(layout, clock=clk)
        for c in human:                       # normal typing never blocks
            clk.t += 0.2
            d.feed_down(c)
            clk.t += 0.05
            d.feed_up(c)
        self.assertFalse(d.blocking)

        d = CatDetector(layout, clock=clk)    # cat sits: 5 keys at once
        for c in chord:
            clk.t += 0.02
            d.feed_down(c)
        self.assertTrue(d.blocking)
        for c in chord:
            d.feed_up(c)
        clk.t += 1.2
        self.assertTrue(d.tick_auto_release())
        self.assertFalse(d.blocking)

        d = CatDetector(layout, stay_locked=True, clock=clk)
        for c in chord:
            clk.t += 0.02
            d.feed_down(c)
            d.feed_up(c)
        for c in chord:
            d.feed_down(c)
        for c in chord:
            d.feed_up(c)
        clk.t += 5
        self.assertFalse(d.tick_auto_release())  # stays locked until unlock
        d.unlock()
        self.assertFalse(d.blocking)

    def test_mac(self):
        self.check(MAC_LAYOUT)

    def test_windows(self):
        self.check(WIN_LAYOUT)

    def test_linux(self):
        self.check(LINUX_LAYOUT)

    def test_adjacency_symmetric(self):
        for layout in (MAC_LAYOUT, WIN_LAYOUT, LINUX_LAYOUT):
            for a, ns in layout.adjacency.items():
                for b in ns:
                    self.assertIn(a, layout.adjacency[b])


if __name__ == "__main__":
    unittest.main()
