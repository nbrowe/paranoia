"""Pure (Tk-free, I/O-free) client logic for the Paranoia desktop client.

Purpose: input parsing, outgoing frame building, server frame handling and
message formatting, so all of it is unit-testable without a display.
Scope: protocol v1 (docs/protocol.md) only.
Limitations: omit names absent from the user list are kept in the omit
list but cannot be shown as selected in the list widget.
"""

import time
from dataclasses import dataclass, field


@dataclass
class ChatState:
    """Mutable view of the session: identity, room members, sticky omits."""

    nick: str = ""
    room: str = ""
    users: list = field(default_factory=list)
    omit: list = field(default_factory=list)
    topic: str = ""
    op: str = ""
    kicked: bool = False


HELP = [
    "/help                 show this list",
    "/omit [nick ...]      set the omit list; alone clears it",
    "/me <text>            send an action (* nick text)",
    "/kick <nick> [why]    remove a user (room operator only)",
    "/topic [text]         show the topic, or set it",
    "//text                send a literal /text",
]


def parse_input(line):
    """Parse an entry-box line into (kind, arg), or None for blank input.

    Kinds: say/action (arg text), omit (names), kick ((nick, reason)),
    topic (text or None to show), help (None), error (message)."""
    line = line.strip()
    if not line:
        return None
    if not line.startswith("/") or line.startswith("//"):
        return ("say", line[1:] if line.startswith("//") else line)
    cmd, _, rest = line.partition(" ")
    rest = rest.strip()
    if cmd == "/omit":
        return ("omit", rest.split())
    if cmd == "/help":
        return ("help", None)
    if cmd == "/topic":
        return ("topic", rest or None)
    if cmd == "/me":
        return ("action", rest) if rest else ("error", "usage: /me <text>")
    if cmd == "/kick":
        nick, _, reason = rest.partition(" ")
        if not nick:
            return ("error", "usage: /kick <nick> [reason]")
        return ("kick", (nick, reason.strip()))
    return ("error", f"unknown command {cmd} (try /help)")


def build_say(text, omit, action=False):
    """Build a `say` frame carrying the sticky omit list."""
    frame = {"type": "say", "text": text, "omit": list(omit)}
    if action:
        frame["action"] = True
    return frame


def build_topic(text):
    """Build a `topic` frame (empty text clears the topic)."""
    return {"type": "topic", "text": text}


def build_kick(nick, reason=""):
    """Build a `kick` frame."""
    return {"type": "kick", "nick": nick, "reason": reason}


def normalize_omit(names, own_nick):
    """Drop own nick and duplicates, keeping order."""
    out = []
    for n in names:
        if n != own_nick and n not in out:
            out.append(n)
    return out


def merge_selection(omit, users, selected):
    """New omit list after the user changes the list selection.

    Names not in `users` (not selectable) are kept; present names follow
    the selection."""
    kept = [n for n in omit if n not in users]
    return kept + [n for n in users if n in selected]


def format_topic(topic):
    """Local line describing the current topic."""
    return f"* topic: {topic}" if topic else "* no topic set"


def format_ts(ts):
    """Format a server Unix timestamp as local HH:MM."""
    return time.strftime("%H:%M", time.localtime(ts))


def format_message(msg):
    """Return (tag, line) for a Message dict; tag is own/masked/normal."""
    head = f"[{format_ts(msg['ts'])}] {msg['sender']}: {msg['text']}"
    if msg.get("masked"):
        return "masked", head
    if "omitted" in msg:
        who = ", ".join(msg["omitted"]) or "nobody"
        return "own", f"{head}  (omitted: {who})"
    return "normal", head


def apply_frame(state, frame):
    """Update `state` from a server frame; return [(tag, line), ...] to show.

    Unknown frame types are ignored per the protocol."""
    kind = frame.get("type")
    if kind == "welcome":
        state.nick, state.room = frame["nick"], frame["room"]
        state.users = sorted(frame["users"])
        lines = [format_message(m) for m in frame["history"]]
        lines.append(("notice", f"* joined #{state.room} as {state.nick}"))
        return lines
    if kind == "join":
        if frame["nick"] not in state.users:
            state.users = sorted(state.users + [frame["nick"]])
        return [("notice", f"* {frame['nick']} joined")]
    if kind == "leave":
        state.users = [u for u in state.users if u != frame["nick"]]
        return [("notice", f"* {frame['nick']} left")]
    if kind == "message":
        return [format_message(frame)]
    if kind == "error":
        return [("error", f"! {frame['code']}: {frame['message']}")]
    return []


def format_status(state):
    """Status-bar text: own nick, room and current omit list."""
    omit = ", ".join(state.omit) or "none"
    return f"you: {state.nick or '?'}  room: {state.room or '?'}  omit: {omit}"
