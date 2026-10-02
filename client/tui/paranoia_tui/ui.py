"""Curses front end: message pane, user sidebar, status line, input line.

Purpose: draw state and translate keystrokes into protocol actions.
Scope: single-room chat loop; all decisions delegate to logic.py.
Handles /help /omit /me /kick /topic /quit and Tab nick completion.
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
        self.topic = ""
        self.tab = None  # logic.Completion while cycling with Tab
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
        self.topic = logic.update_topic(self.topic, frame)
        for line in logic.format_event(frame, self.nick):
            self.add(line)
        if logic.is_self_kick(frame, self.nick):
            self.closed = True  # server closes the socket; no reconnect

    def submit(self):
        """Handle the Enter key; returns True when the app should exit."""
        cmd = logic.parse_input(self.buf)
        self.buf = ""
        if cmd.kind == "quit":
            return True
        self.run_command(cmd)
        return False

    def run_command(self, cmd):
        """Carry out a parsed non-quit Command."""
        kind, arg = cmd
        if kind == "omit":
            self.omit = arg
        elif kind == "help":
            for text in logic.HELP:
                self.add(logic.Line("notice", text))
        elif kind == "usage":
            self.add(logic.Line("error", f"! {arg}"))
        elif kind == "unknown":
            self.add(logic.Line("error", f"! unknown command {arg}"))
        elif kind == "topic" and arg is None:
            shown = self.topic or "(none)"
            self.add(logic.Line("notice", f"* topic: {shown}"))
        elif kind == "topic":
            self.transmit(logic.build_topic(arg))
        elif kind == "kick":
            self.transmit(logic.build_kick(*arg))
        elif kind in ("say", "me"):
            self.transmit(logic.build_say(arg, self.omit, kind == "me"))

    def transmit(self, raw):
        """Send a prebuilt frame, ignoring a closed socket."""
        try:
            self.ws.send(raw)
        except ConnectionClosed:
            pass  # reader thread reports the disconnect

    def on_key(self, key):
        """Handle one key; returns True when the app should exit."""
        if key == "\t":
            self.buf, self.tab = logic.complete(
                self.buf, self.users, self.nick, self.tab)
            return False
        self.tab = None
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
        status = logic.status_text(self.nick, self.omit, self.topic)
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
