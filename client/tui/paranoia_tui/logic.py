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


def build_say(text, omit):
    """Build the JSON text of a `say` frame; `omit` is sent when non-empty."""
    frame = {"type": "say", "text": text}
    if omit:
        frame["omit"] = list(omit)
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
    if kind == "leave":
        return sorted(set(users) - {frame["nick"]})
    return list(users)


def format_message(msg, own_nick):
    """Render a Message dict (live or history) as a Line."""
    stamp = time.strftime("%H:%M", time.localtime(msg.get("ts", 0)))
    sender, text = msg["sender"], msg["text"]
    if msg.get("masked"):
        return Line("masked", f"{stamp} <{sender}> {text}  [masked]")
    omitted = msg.get("omitted")
    suffix = f"  [hidden from: {', '.join(omitted)}]" if omitted else ""
    style = "own" if sender == own_nick else "msg"
    return Line(style, f"{stamp} <{sender}> {text}{suffix}")


def format_event(frame, own_nick):
    """Render a server frame as a list of Lines (empty if not shown)."""
    kind = frame["type"]
    if kind == "welcome":
        head = Line("notice", f"* joined #{frame['room']} as {frame['nick']}")
        return [head] + [format_message(m, own_nick)
                         for m in frame.get("history", [])]
    if kind == "message":
        return [format_message(frame, own_nick)]
    if kind == "join":
        return [Line("notice", f"* {frame['nick']} joined")]
    if kind == "leave":
        return [Line("notice", f"* {frame['nick']} left")]
    if kind == "error":
        return [Line("error", f"! {frame['code']}: {frame['message']}")]
    return []


def status_text(nick, omit):
    """Status line: own nick and the sticky omit list."""
    hidden = ", ".join(omit) if omit else "(none)"
    return f" {nick} | omit: {hidden} | /omit a b, /omit, /quit"


def wrap(text, width):
    """Split text into chunks of at most `width` columns."""
    width = max(width, 1)
    return [text[i:i + width] for i in range(0, len(text), width)] or [""]
