"""Pure, UI-free client logic: input parsing, frame building, formatting.

Purpose: everything about the Paranoia protocol that needs no terminal or
socket, so it can be unit tested.
Scope: slash-command parsing, `say` frame construction, server frame
decoding, roster updates and one-line rendering of server events.
Limitations: no I/O; line wrapping is left to the curses layer.
"""

import json
import time
from typing import NamedTuple


USAGE = {
    "/me": "usage: /me <text>",
    "/kick": "usage: /kick <nick> [reason]",
}
HELP = [
    "/help                 this list",
    "/omit [nick ...]      hide your messages from nicks; bare clears",
    "/me <text>            send an action (* nick text)",
    "/kick <nick> [why]    remove a user (room operator only)",
    "/topic [text]         show the topic, or set it",
    "/quit                 exit",
    "//text                send a message starting with a literal /",
    "Tab after /omit or /kick completes nicks in the room",
]


class Command(NamedTuple):
    """Parsed user input.

    `kind` is quit/help/omit/me/kick/topic/say/usage/unknown/empty. `arg`
    is the payload: omit list, text, (nick, reason), topic text (None to
    show it) or a usage string.
    """

    kind: str
    arg: object = None


class Line(NamedTuple):
    """A renderable line: `style` is msg/own/masked/notice/error."""

    style: str
    text: str


def parse_input(raw):
    """Turn a typed line into a Command."""
    text = raw.strip()
    if not text:
        return Command("empty")
    if text.startswith("//"):
        return Command("say", text[1:])
    if not text.startswith("/"):
        return Command("say", text)
    cmd, _, rest = text.partition(" ")
    rest = rest.strip()
    if cmd == "/quit":
        return Command("quit")
    if cmd == "/help":
        return Command("help")
    if cmd == "/omit":
        return Command("omit", list(dict.fromkeys(rest.split())))
    if cmd == "/me":
        return Command("me", rest) if rest else Command("usage", USAGE[cmd])
    if cmd == "/topic":
        return Command("topic", rest or None)
    if cmd == "/kick":
        nick, _, reason = rest.partition(" ")
        if not nick:
            return Command("usage", USAGE[cmd])
        return Command("kick", (nick, reason.strip()))
    return Command("unknown", cmd)


class Completion(NamedTuple):
    """Tab-cycle state: buffer text before the word, candidates, index."""

    head: str
    matches: list
    index: int


def complete(buf, users, own_nick, state=None):
    """Tab-complete the last word of an /omit or /kick line.

    Returns (new_buf, state). Pass the previous state back on repeated Tab
    to cycle through the candidates; pass None for a fresh completion.
    Candidates are room users (minus ourselves, and minus nicks already
    listed for /omit) matching the word as a case-insensitive prefix.
    /kick only completes its first argument; the rest is a free reason.
    """
    if state:
        idx = (state.index + 1) % len(state.matches)
        return state.head + state.matches[idx], state._replace(index=idx)
    cmd, sep, rest = buf.partition(" ")
    if not sep or cmd not in ("/omit", "/kick"):
        return buf, None
    head, _, word = buf.rpartition(" ")
    head += " "
    done = rest.split()[:-1] if word else rest.split()
    if cmd == "/kick" and done:
        return buf, None
    skip = {own_nick, *done}
    found = [u for u in users
             if u not in skip and u.lower().startswith(word.lower())]
    if not found:
        return buf, None
    return head + found[0], Completion(head, found, 0)


def build_say(text, omit, action=False):
    """Build the JSON text of a `say` frame.

    `omit` is sent when non-empty; `action` marks a /me message.
    """
    frame = {"type": "say", "text": text}
    if omit:
        frame["omit"] = list(omit)
    if action:
        frame["action"] = True
    return json.dumps(frame)


def build_topic(text):
    """Build the JSON text of a `topic` frame."""
    return json.dumps({"type": "topic", "text": text})


def build_kick(nick, reason=""):
    """Build the JSON text of a `kick` frame (reason omitted if empty)."""
    frame = {"type": "kick", "nick": nick}
    if reason:
        frame["reason"] = reason
    return json.dumps(frame)


def parse_frame(raw):
    """Decode a server frame; return None if it is not a typed object."""
    try:
        frame = json.loads(raw)
    except ValueError:
        return None
    if isinstance(frame, dict) and isinstance(frame.get("type"), str):
        return frame
    return None


def update_users(users, frame):
    """Return the sorted roster after applying welcome/join/leave."""
    kind = frame["type"]
    if kind == "welcome":
        return sorted(frame.get("users", []))
    if kind == "join":
        return sorted(set(users) | {frame["nick"]})
    if kind in ("leave", "kick"):
        return sorted(set(users) - {frame["nick"]})
    return list(users)


def update_topic(topic, frame):
    """Return the room topic after applying welcome/topic."""
    if frame["type"] in ("welcome", "topic"):
        return frame.get("topic", frame.get("text", ""))
    return topic


def is_self_kick(frame, own_nick):
    """True if `frame` is a kick naming our own nickname."""
    return frame["type"] == "kick" and frame.get("nick") == own_nick


def format_message(msg, own_nick):
    """Render a Message dict (live or history) as a Line."""
    stamp = time.strftime("%H:%M", time.localtime(msg.get("ts", 0)))
    sender, text = msg["sender"], msg["text"]
    who = f"* {sender}" if msg.get("action") else f"<{sender}>"
    if msg.get("masked"):
        return Line("masked", f"{stamp} {who} {text}  [masked]")
    omitted = msg.get("omitted")
    suffix = f"  [hidden from: {', '.join(omitted)}]" if omitted else ""
    style = "own" if sender == own_nick else "msg"
    return Line(style, f"{stamp} {who} {text}{suffix}")


def _topic_text(frame):
    """Describe a `topic` frame as a notice string."""
    if frame["text"]:
        return f"* {frame['nick']} set the topic: {frame['text']}"
    return f"* {frame['nick']} cleared the topic"


def _kick_line(frame, own_nick):
    """Render a `kick` frame; louder when we are the target."""
    why = f": {frame['reason']}" if frame.get("reason") else ""
    if frame["nick"] == own_nick:
        return Line("error", f"! kicked by {frame['by']}{why}")
    return Line("notice", f"* {frame['nick']} was kicked by {frame['by']}{why}")


def format_event(frame, own_nick):
    """Render a server frame as a list of Lines (empty if not shown)."""
    kind = frame["type"]
    if kind == "welcome":
        head = [Line("notice",
                     f"* joined #{frame['room']} as {frame['nick']}")]
        if frame.get("topic"):
            head.append(Line("notice", f"* topic: {frame['topic']}"))
        return head + [format_message(m, own_nick)
                       for m in frame.get("history", [])]
    if kind == "message":
        return [format_message(frame, own_nick)]
    if kind == "join":
        return [Line("notice", f"* {frame['nick']} joined")]
    if kind == "leave":
        return [Line("notice", f"* {frame['nick']} left")]
    if kind == "topic":
        return [Line("notice", _topic_text(frame))]
    if kind == "kick":
        return [_kick_line(frame, own_nick)]
    if kind == "op":
        return [Line("notice", f"* {frame['nick']} is now the operator")]
    if kind == "error":
        return [Line("error", f"! {frame['code']}: {frame['message']}")]
    return []


def status_text(nick, omit, topic=""):
    """Status line: own nick, sticky omit list, topic and a help hint."""
    hidden = ", ".join(omit) if omit else "(none)"
    shown = f" | topic: {topic}" if topic else ""
    return f" {nick} | omit: {hidden}{shown} | /help"


def wrap(text, width):
    """Split text into chunks of at most `width` columns."""
    width = max(width, 1)
    return [text[i:i + width] for i in range(0, len(text), width)] or [""]
