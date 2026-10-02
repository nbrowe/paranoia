"""Curses front end: message pane, user sidebar, status line, input line.

Purpose: draw state and translate keystrokes into protocol actions.
Scope: single-room chat loop; all decisions delegate to logic.py.
Limitations: no scrollback (shows the newest lines), no cursor movement
inside the input line (type, backspace, enter), not unit tested.
"""

import curses
import queue

from websockets.exceptions import ConnectionClosed

from . import logic

SIDEBAR_WIDTH = 18
MIN_COLS_FOR_SIDEBAR = 60
MAX_LINES = 2000
ATTRS = {
    "msg": curses.A_NORMAL,
    "own": curses.A_BOLD,
    "masked": curses.A_DIM,
    "notice": curses.A_UNDERLINE,
    "error": curses.A_STANDOUT,
}


class App:
    """Chat state plus curses drawing for one connection."""

    def __init__(self, stdscr, ws, frames):
        """Bind to a curses screen, websocket and incoming frame queue."""
        self.scr = stdscr
        self.ws = ws
        self.frames = frames
        self.nick = "?"
        self.users = []
        self.omit = []
        self.lines = []
        self.buf = ""
        self.closed = False

    def add(self, line):
        """Append a Line to the scrollback, trimming old entries."""
        self.lines.append(line)
        del self.lines[:-MAX_LINES]

    def on_frame(self, frame):
        """Apply a server frame (or the synthetic _closed frame)."""
        if frame["type"] == "_closed":
            self.closed = True
            self.add(logic.Line("error", f"! disconnected: {frame['reason']}"))
            return
        if frame["type"] == "welcome":
            self.nick = frame["nick"]
        self.users = logic.update_users(self.users, frame)
        for line in logic.format_event(frame, self.nick):
            self.add(line)

    def submit(self):
        """Handle the Enter key; returns True when the app should exit."""
        cmd = logic.parse_input(self.buf)
        self.buf = ""
        if cmd.kind == "quit":
            return True
        if cmd.kind == "omit":
            self.omit = cmd.arg
        elif cmd.kind == "unknown":
            self.add(logic.Line("error", f"! unknown command {cmd.arg}"))
        elif cmd.kind == "say":
            self.send(cmd.arg)
        return False

    def send(self, text):
        """Send a say frame with the sticky omit list."""
        try:
            self.ws.send(logic.build_say(text, self.omit))
        except ConnectionClosed:
            pass  # reader thread reports the disconnect

    def on_key(self, key):
        """Handle one key; returns True when the app should exit."""
        if key in ("\n", "\r") or key == curses.KEY_ENTER:
            return self.submit()
        if key in ("\x7f", "\b") or key == curses.KEY_BACKSPACE:
            self.buf = self.buf[:-1]
        elif isinstance(key, str) and key.isprintable():
            self.buf += key
        return False

    def draw_pane(self, rows, cols):
        """Draw the newest wrapped message lines into rows x cols."""
        wrapped = []
        for line in self.lines[-rows:]:
            for chunk in logic.wrap(line.text, cols):
                wrapped.append((chunk, ATTRS[line.style]))
        for y, (chunk, attr) in enumerate(wrapped[-rows:]):
            self.scr.addstr(y, 0, chunk, attr)

    def draw_sidebar(self, rows, x):
        """Draw the user list at column x."""
        self.scr.addstr(0, x, "users", curses.A_BOLD)
        for y, user in enumerate(self.users[:rows - 1], start=1):
            attr = curses.A_BOLD if user == self.nick else curses.A_NORMAL
            self.scr.addstr(y, x, user[:SIDEBAR_WIDTH - 2], attr)
        for y in range(rows):
            self.scr.addch(y, x - 1, curses.ACS_VLINE)

    def draw(self):
        """Redraw the whole screen for the current terminal size."""
        self.scr.erase()
        height, width = self.scr.getmaxyx()
        rows = height - 2
        pane = width
        if width >= MIN_COLS_FOR_SIDEBAR:
            pane = width - SIDEBAR_WIDTH
            self.draw_sidebar(rows, pane + 1)
        self.draw_pane(rows, pane - 1)
        status = logic.status_text(self.nick, self.omit)
        self.scr.addstr(rows, 0, status[:width - 1].ljust(width - 1),
                        curses.A_REVERSE)
        prompt = "> " + self.buf
        shown = prompt[-(width - 1):]
        self.scr.addstr(rows + 1, 0, shown)
        self.scr.refresh()

    def drain(self):
        """Process every queued frame without blocking."""
        while True:
            try:
                self.on_frame(self.frames.get_nowait())
            except queue.Empty:
                return

    def run(self):
        """Main loop: poll keys every 100 ms, drain frames, redraw."""
        self.scr.timeout(100)
        self.scr.keypad(True)
        while True:
            self.drain()
            self.draw()
            try:
                key = self.scr.get_wch()
            except curses.error:
                key = None  # timeout; also fires after a disconnect
            if self.closed and key is not None:
                return
            if key is not None and self.on_key(key):
                return


def run(ws, frames):
    """Run the curses app on an open websocket; returns when finished."""
    def main(stdscr):
        """curses.wrapper callback."""
        curses.curs_set(1)
        app = App(stdscr, ws, frames)
        app.run()
        return app

    app = curses.wrapper(main)
    return app.lines[-1].text if app.closed else None
