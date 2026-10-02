"""Tkinter window for the Paranoia desktop client.

Purpose: render chat state and turn user actions into protocol frames.
Scope: widgets and event wiring only; all decisions live in logic.py and
all socket work in net.py (Tk widgets are touched only on the Tk thread).
Limitations: no reconnect, no scrollback limit, minimal styling.
"""

import tkinter as tk
from tkinter import ttk

from . import logic
from .logic import ChatState

POLL_MS = 100


class App:
    """Main window: message log, user list, entry box and status bar."""

    def __init__(self, root, conn):
        """Build the widgets and start polling the connection."""
        self.root, self.conn = root, conn
        self.state = ChatState()
        self.connected = True
        root.title("Paranoia")
        self._build_widgets()
        root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._refresh_status()
        root.after(POLL_MS, self._poll)

    def _build_widgets(self):
        """Create and lay out all widgets."""
        self.topic = ttk.Label(self.root, anchor="w", relief="groove")
        self.topic.pack(fill="x")
        top = ttk.Frame(self.root)
        top.pack(fill="both", expand=True)
        self.log = tk.Text(top, state="disabled", wrap="word", width=70,
                           height=24)
        self.log.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(top, command=self.log.yview)
        scroll.pack(side="left", fill="y")
        self.log.configure(yscrollcommand=scroll.set)
        self.log.tag_configure("masked", foreground="#888888",
                               font=("TkFixedFont", 10, "italic"))
        self.log.tag_configure("own", foreground="#1a5fb4")
        self.log.tag_configure("notice", foreground="#26a269")
        self.log.tag_configure("error", foreground="#c01c28")
        side = ttk.Frame(top)
        side.pack(side="left", fill="y")
        ttk.Label(side, text="Users (select = omit)").pack()
        self.users = tk.Listbox(side, selectmode="multiple", width=20,
                                exportselection=False)
        self.users.pack(fill="y", expand=True)
        self.users.bind("<<ListboxSelect>>", self._on_select)
        self.entry = ttk.Entry(self.root)
        self.entry.pack(fill="x")
        self.entry.bind("<Return>", self._on_enter)
        self.entry.bind("<Tab>", self._on_tab)
        self.completion = None
        self.entry.focus_set()
        self.status = ttk.Label(self.root, anchor="w", relief="sunken")
        self.status.pack(fill="x")

    def show(self, tag, line):
        """Append one line to the read-only log and scroll to the end."""
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n", tag)
        self.log.configure(state="disabled")
        self.log.see("end")

    def _refresh_status(self):
        """Redraw the status bar."""
        self.status.configure(text=logic.format_status(self.state))
        self.topic.configure(text=logic.format_topic_label(self.state.topic))

    def _refresh_users(self):
        """Redraw the user list and restore selection from the omit list."""
        self.users.delete(0, "end")
        for i, nick in enumerate(self.state.users):
            label = nick + (" (you)" if nick == self.state.nick else "")
            self.users.insert("end", label)
            if nick in self.state.omit:
                self.users.selection_set(i)

    def _selected_nicks(self):
        """Nicks currently selected in the list."""
        return {self.state.users[i] for i in self.users.curselection()}

    def _on_select(self, _event):
        """Selection changed: it becomes the sticky omit list."""
        omit = logic.merge_selection(
            self.state.omit, self.state.users, self._selected_nicks())
        self.state.omit = logic.normalize_omit(omit, self.state.nick)
        self._refresh_status()

    def _on_enter(self, _event):
        """Handle the entry box: send a message or run a slash command."""
        parsed = logic.parse_input(self.entry.get())
        if parsed is None:
            return
        self.entry.delete(0, "end")
        kind, arg = parsed
        if kind == "say":
            self._send(logic.build_say(arg, self.state.omit))
        elif kind == "action":
            self._send(logic.build_say(arg, self.state.omit, action=True))
        elif kind == "omit":
            self.state.omit = logic.normalize_omit(arg, self.state.nick)
            self._refresh_users()
            self._refresh_status()
        elif kind == "kick":
            self._send(logic.build_kick(*arg))
        elif kind == "topic":
            self._do_topic(arg)
        elif kind == "help":
            for line in logic.HELP:
                self.show("notice", line)
        else:
            self.show("error", "! " + arg)

    def _on_tab(self, _event):
        """TAB: complete or cycle a nick; never move keyboard focus."""
        line = self.entry.get()
        comp = logic.complete(line, self.state.users, self.state.nick,
                              self.completion)
        if comp:
            self.completion = comp
            self.entry.delete(0, "end")
            self.entry.insert(0, comp.line)
            self.entry.icursor("end")
        return "break"

    def _do_topic(self, text):
        """/topic: show the current topic, or send a new one."""
        if text is None:
            self.show("notice", logic.format_topic(self.state.topic))
        else:
            self._send(logic.build_topic(text))

    def _send(self, frame):
        """Send a frame, or complain if the connection is gone."""
        if not self.connected:
            self.show("error", "! not connected")
            return
        try:
            self.conn.send(frame)
        except Exception as exc:  # socket died between poll ticks
            self.show("error", f"! send failed: {exc}")

    def _poll(self):
        """Drain network events on the Tk thread, then reschedule."""
        for kind, payload in self.conn.poll():
            if kind == "frame":
                for tag, line in logic.apply_frame(self.state, payload):
                    self.show(tag, line)
                self._refresh_users()
            else:
                self.connected = False
                if not self.state.kicked:  # a kick is final, say no more
                    self.show("error", f"! {payload} (restart to reconnect)")
        self._refresh_status()
        self.root.after(POLL_MS, self._poll)

    def on_close(self):
        """Close the connection and the window."""
        self.conn.close()
        self.root.destroy()
