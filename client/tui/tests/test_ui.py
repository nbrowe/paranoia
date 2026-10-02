"""Tests for the paranoia_tui.ui redraw scheduling (fake screen)."""

import curses
import queue

from paranoia_tui import ui


class FakeScreen:
    """Feeds scripted keys; None or a callable simulates a timeout."""

    def __init__(self, keys):
        """Store the key script."""
        self.keys = list(keys)

    def timeout(self, _ms):
        """Ignored."""

    def keypad(self, _flag):
        """Ignored."""

    def get_wch(self):
        """Return the next scripted key; timeouts raise curses.error."""
        key = self.keys.pop(0)
        if key is None or callable(key):
            if callable(key):
                key()
            raise curses.error
        return key


def run_counting(keys, frames):
    """Run App.run with draw() counted (ends on "Q"); returns the count."""
    count = []
    app = ui.App(FakeScreen(keys), None, frames)
    app.draw = lambda: count.append(1)
    app.on_key = lambda k: k == "Q"
    app.run()
    return len(count)


def test_idle_ticks_do_not_redraw():
    """Only the initial draw happens across idle timeouts."""
    assert run_counting([None, None, None, "Q"], queue.Queue()) == 1


def test_key_and_resize_redraw():
    """Any key, including KEY_RESIZE, marks the screen dirty."""
    keys = [None, curses.KEY_RESIZE, None, "Q"]
    assert run_counting(keys, queue.Queue()) == 2


def test_frame_redraws():
    """A frame arriving mid-run triggers exactly one more draw."""
    frames = queue.Queue()
    frame = {"type": "topic", "nick": "a", "text": "t"}
    keys = [None, lambda: frames.put(frame), None, None, "Q"]
    assert run_counting(keys, frames) == 2
