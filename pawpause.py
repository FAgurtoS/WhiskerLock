#!/usr/bin/env python3
"""Paw Pause (macOS): pauses the keyboard when a cat walks on it.

Detection lives in detector.py (ported from miladsafarzadeh1/PawPause-mac, MIT).
Esc always releases. Keystrokes are never stored or sent anywhere: only
key codes and timestamps from the last 1.5 s are kept in memory.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from detector import CatDetector, MAC_LAYOUT  # noqa: E402

ESCAPE = MAC_LAYOUT.escape


def main():
    import objc
    import Quartz
    from AppKit import (NSApplication, NSApplicationActivationPolicyAccessory,
                        NSBackingStoreBuffered, NSColor, NSFont, NSMenu,
                        NSMenuItem, NSScreen, NSSlider, NSStatusBar, NSSound,
                        NSTextField, NSView, NSVisualEffectView, NSWindow,
                        NSWorkspace)
    from Foundation import NSObject, NSTimer, NSURL, NSUserDefaults

    detector = CatDetector()
    state = {"armed": True, "tap": None}

    # Saved preferences. Sensitivity s in 0.6..1.6 (higher = more sensitive);
    # the detector threshold is 2.2 - s, so s=1.2 is the original threshold 1.0.
    prefs = NSUserDefaults.standardUserDefaults()
    prefs.registerDefaults_({"sensitivity": 1.2, "sound": True, "stay": False})
    state["sound"] = bool(prefs.boolForKey_("sound"))
    detector.threshold = 2.2 - float(prefs.doubleForKey_("sensitivity"))
    detector.stay_locked = bool(prefs.boolForKey_("stay"))

    def open_permissions():
        for pane in ("Privacy_ListenEvent", "Privacy_Accessibility"):
            NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(
                "x-apple.systempreferences:com.apple.preference.security?" + pane))

    def tap_callback(proxy, etype, event, refcon):
        if etype in (Quartz.kCGEventTapDisabledByTimeout,
                     Quartz.kCGEventTapDisabledByUserInput):
            if state["tap"] is not None:
                Quartz.CGEventTapEnable(state["tap"], True)
            return event
        if not state["armed"]:
            return event
        code = Quartz.CGEventGetIntegerValueField(
            event, Quartz.kCGKeyboardEventKeycode)
        if etype == Quartz.kCGEventKeyDown and code == ESCAPE:
            if detector.blocking:       # human override
                detector.unlock()
                state["ui"].refresh()
                return None
            return event
        if etype == Quartz.kCGEventKeyDown:
            rep = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGKeyboardEventAutorepeat) != 0
            was = detector.blocking
            detector.feed_down(code, rep)
            if detector.blocking and not was:
                if state["sound"]:
                    NSSound.soundNamed_("Funk").play()
                state["ui"].refresh()
            if detector.blocking:
                return None
        elif etype == Quartz.kCGEventKeyUp:
            detector.feed_up(code)
            if detector.tick_auto_release():
                state["ui"].refresh()
                return event
            if detector.blocking:
                return None
        elif etype == Quartz.kCGEventFlagsChanged and detector.blocking:
            return None
        return event

    def start_tap():
        mask = ((1 << Quartz.kCGEventKeyDown) | (1 << Quartz.kCGEventKeyUp)
                | (1 << Quartz.kCGEventFlagsChanged))
        tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap, Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionDefault, mask, tap_callback, None)
        if tap is None:
            state["tap"] = None
            return False
        src = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
        Quartz.CFRunLoopAddSource(Quartz.CFRunLoopGetCurrent(), src,
                                  Quartz.kCFRunLoopCommonModes)
        Quartz.CGEventTapEnable(tap, True)
        state["tap"] = tap
        return True

    class Delegate(NSObject):
        def applicationDidFinishLaunching_(self, _):
            self.item = NSStatusBar.systemStatusBar().statusItemWithLength_(-1)
            menu = NSMenu.alloc().init()
            self.status_line = menu.addItemWithTitle_action_keyEquivalent_("", None, "")
            self.status_line.setEnabled_(False)
            self.arm_item = menu.addItemWithTitle_action_keyEquivalent_(
                "Armed", "toggleArm:", "")
            self.arm_item.setTarget_(self)
            self.stay_item = menu.addItemWithTitle_action_keyEquivalent_(
                "Stay locked until I unlock", "toggleStay:", "")
            self.stay_item.setTarget_(self)
            unlock = menu.addItemWithTitle_action_keyEquivalent_(
                "Unlock keyboard", "unlock:", "")
            unlock.setTarget_(self)
            self.sound_item = menu.addItemWithTitle_action_keyEquivalent_(
                "Play sound when paused", "toggleSound:", "")
            self.sound_item.setTarget_(self)
            sens = float(prefs.doubleForKey_("sensitivity"))
            view = NSView.alloc().initWithFrame_(((0, 0), (240, 50)))
            self.sens_label = NSTextField.labelWithString_("")
            self.sens_label.setFont_(NSFont.systemFontOfSize_(12))
            self.sens_label.setFrame_(((14, 28), (212, 16)))
            slider = NSSlider.sliderWithValue_minValue_maxValue_target_action_(
                sens, 0.6, 1.6, self, "sensitivityChanged:")
            slider.setFrame_(((14, 6), (212, 20)))
            view.addSubview_(self.sens_label)
            view.addSubview_(slider)
            slider_item = NSMenuItem.alloc().init()
            slider_item.setView_(view)
            menu.addItem_(slider_item)
            self.updateSensLabel_(sens)
            test = menu.addItemWithTitle_action_keyEquivalent_(
                "Test overlay (3 s)", "testOverlay:", "")
            test.setTarget_(self)
            menu.addItem_(NSMenuItem.separatorItem())
            quit_item = menu.addItemWithTitle_action_keyEquivalent_(
                "Quit Paw Pause", "quit:", "q")
            quit_item.setTarget_(self)
            self.item.setMenu_(menu)
            self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.2, self, "poll:", None, True)
            if not start_tap():
                self.refresh()
                open_permissions()
            self.refresh()



        def showOverlay(self):
            if getattr(self, "windows", None):
                return
            self.windows = []
            for screen in NSScreen.screens():
                frame = screen.frame()
                win = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_screen_(
                    frame, 0, NSBackingStoreBuffered, False, screen)
                win.setLevel_(1000)
                win.setOpaque_(False)
                win.setBackgroundColor_(NSColor.clearColor())
                win.setIgnoresMouseEvents_(True)       # mouse keeps working
                win.setReleasedWhenClosed_(False)
                win.setCollectionBehavior_((1 << 0) | (1 << 4) | (1 << 8))
                blur = NSVisualEffectView.alloc().initWithFrame_(((0, 0), frame.size))
                blur.setMaterial_(13)                  # HUD window
                blur.setBlendingMode_(0)               # blur what is behind
                blur.setState_(1)                      # always active
                blur.setAutoresizingMask_(18)
                win.setContentView_(blur)
                for text, size, dy in (("\U0001F431 Cat in keyboard", 72, 0),
                                       ("Press Esc to unlock", 24, -90)):
                    label = NSTextField.labelWithString_(text)
                    label.setFont_(NSFont.boldSystemFontOfSize_(size))
                    label.setTextColor_(NSColor.labelColor())
                    label.setAlignment_(1)
                    label.setFrame_(((0, frame.size.height / 2 + dy - 50),
                                     (frame.size.width, 110)))
                    label.setAutoresizingMask_(2 | 16)
                    blur.addSubview_(label)
                win.orderFrontRegardless()
                self.windows.append(win)

        def hideOverlay(self):
            for win in getattr(self, "windows", None) or []:
                win.orderOut_(None)
                win.close()
            self.windows = []

        def poll_(self, _):
            if detector.tick_auto_release():
                self.refresh()

        def refresh(self):
            if state["tap"] is None:
                title, text = "⚠️", "Permissions needed (Input Monitoring + Accessibility)"
            elif not state["armed"]:
                title, text = "🐾", "Off"
            elif detector.blocking:
                title, text = "🔒", "Paused: cat detected (Esc to override)"
            else:
                title, text = "🐱", "Armed: watching"
            if detector.blocking or state.get("demo"):
                self.showOverlay()
            else:
                self.hideOverlay()
            self.item.button().setTitle_(title)
            self.status_line.setTitle_(text)
            self.arm_item.setState_(1 if state["armed"] else 0)
            self.stay_item.setState_(1 if detector.stay_locked else 0)
            self.sound_item.setState_(1 if state["sound"] else 0)

        def toggleArm_(self, _):
            state["armed"] = not state["armed"]
            if not state["armed"]:
                detector.reset()
            if state["tap"] is None:
                start_tap()
            self.refresh()

        def toggleStay_(self, _):
            detector.stay_locked = not detector.stay_locked
            prefs.setBool_forKey_(detector.stay_locked, "stay")
            self.refresh()

        def toggleSound_(self, _):
            state["sound"] = not state["sound"]
            prefs.setBool_forKey_(state["sound"], "sound")
            self.refresh()

        def updateSensLabel_(self, v):
            name = "High" if v >= 1.35 else "Balanced" if v >= 1.05 else "Relaxed"
            self.sens_label.setStringValue_("Sensitivity: " + name)

        def sensitivityChanged_(self, sender):
            v = round(float(sender.doubleValue()), 1)
            detector.threshold = 2.2 - v
            prefs.setDouble_forKey_(v, "sensitivity")
            self.updateSensLabel_(v)

        def testOverlay_(self, _):
            state["demo"] = True
            self.refresh()
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                3.0, self, "endDemo:", None, False)

        def endDemo_(self, _):
            state["demo"] = False
            self.refresh()

        def unlock_(self, _):
            detector.unlock()
            self.refresh()

        def quit_(self, _):
            NSApplication.sharedApplication().terminate_(None)

    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = Delegate.alloc().init()
    state["ui"] = delegate
    app.setDelegate_(delegate)
    app.run()


if __name__ == "__main__":
    main()
