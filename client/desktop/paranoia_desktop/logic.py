"""Pure (Tk-free, I/O-free) client logic for the Paranoia desktop client.

Purpose: input parsing, outgoing frame building, server frame handling and
message formatting and user-list markers, so all of it is unit-testable
without a display.
Scope: protocol v1 (docs/protocol.md) only.
Limitations: omit names absent from the user list are kept in the omit
list but cannot be shown as selected in the list widget.
"""

import time
from collections import namedtuple
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
    "/topic [text|-]       show the topic, set it, or clear it with -",
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
        return ("topic", "" if rest == "-" else rest or None)
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


Completion = namedtuple("Completion", "head cands idx")
Completion.line = property(lambda c: c.head + c.cands[c.idx])


def complete(line, users, own, prev=None):
    """TAB-complete the last word of `line` against room users.

    Applies to every /omit argument and the first /kick argument. Matching
    is a case-insensitive prefix; `own` is never offered. If `line` is the
    result of `prev` (a Completion), cycle to its next candidate instead.
    Returns a Completion (use `.line`) or None when nothing applies."""
    if prev and line == prev.line:
        nxt = (prev.idx + 1) % len(prev.cands)
        return Completion(prev.head, prev.cands, nxt)
    cut = line.rfind(" ") + 1
    head, word = line[:cut], line[cut:]
    words = head.split()
    if not words or words[0] not in ("/omit", "/kick"):
        return None
    if words[0] == "/kick" and len(words) > 1:
        return None
    cands = sorted(u for u in users
                   if u != own and u.lower().startswith(word.lower()))
    return Completion(head, cands, 0) if cands else None


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


def format_topic_label(topic):
    """Text for the topic label above the log; empty topics read (none)."""
    return f"Topic: {topic or '(none)'}"


def format_topic(topic):
    """Local line describing the current topic."""
    return f"* topic: {topic}" if topic else "* no topic set"


def format_ts(ts):
    """Format a server Unix timestamp as local HH:MM."""
    return time.strftime("%H:%M", time.localtime(ts))


def format_message(msg):
    """Return (tag, line) for a Message dict; tag is own/masked/normal."""
    who = f"* {msg['sender']} " if msg.get("action") else f"{msg['sender']}: "
    head = f"[{format_ts(msg['ts'])}] {who}{msg['text']}"
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
        state.topic, state.op = frame.get("topic", ""), frame.get("op", "")
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
    if kind == "topic":
        state.topic = frame["text"]
        return [("notice", _topic_line(frame))]
    if kind == "kick":
        return _apply_kick(state, frame)
    if kind == "op":
        state.op = frame["nick"]
        return [("notice", f"* {frame['nick']} is now the operator")]
    return []


def _topic_line(frame):
    """System line for a `topic` frame."""
    if frame["text"]:
        return f"* {frame['nick']} set the topic: {frame['text']}"
    return f"* {frame['nick']} cleared the topic"


def _apply_kick(state, frame):
    """Handle a `kick` frame; our own nick means we were removed."""
    why = f": {frame['reason']}" if frame.get("reason") else ""
    if frame["nick"] == state.nick:
        state.kicked = True
        return [("error", f"! you were kicked by {frame['by']}{why}")]
    state.users = [u for u in state.users if u != frame["nick"]]
    return [("notice", f"* {frame['nick']} was kicked by {frame['by']}{why}")]


def mark_user(nick, own_nick, op):
    """User-list label: `@` prefixes the operator, `*` follows our nick.

    Display only; always use the bare nick for omit/kick/completion."""
    lead = "@" if nick == op else ""
    return lead + nick + ("*" if nick == own_nick else "")


def format_status(state):
    """Status-bar text: own nick, room and current omit list."""
    omit = ", ".join(state.omit) or "none"
    return f"you: {state.nick or '?'}  room: {state.room or '?'}  omit: {omit}"
