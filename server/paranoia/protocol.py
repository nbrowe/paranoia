"""Client frame parsing and validation.

Purpose: turn a raw client frame into a (type, args) pair of validated
values, or raise a ProtocolError carrying a protocol error code.
Scope: the client -> server direction of docs/protocol.md.
Limitations: an `omit` that is not a list of
strings is reported as bad_json (the protocol defines no code for it).
"""
import json

MAX_FIELD = 200  # topic and kick reason length limit


class ProtocolError(Exception):
    """A client mistake that maps to an `error` frame."""

    def __init__(self, code, message):
        """Store the protocol error code and human-readable message."""
        super().__init__(message)
        self.code = code
        self.message = message


def error_frame(code, message):
    """Return the wire dict for an error frame."""
    return {"type": "error", "code": code, "message": message}


def parse_frame(raw, max_text):
    """Validate a raw client frame; return (type, args tuple) or raise."""
    try:
        data = json.loads(raw) if raw is not None else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise ProtocolError("bad_json", "frame must be a JSON object")
    kind = data.get("type")
    if kind == "say":
        return kind, _say(data, max_text)
    if kind == "topic":
        return kind, (_text(data, 0, MAX_FIELD),)
    if kind == "kick":
        return kind, _kick(data)
    raise ProtocolError("unknown_type", "unknown type")


def _text(data, low, high):
    """Return data["text"] stripped, or raise bad_text if out of range."""
    text = data.get("text")
    if not isinstance(text, str) or not low <= len(text.strip()) <= high:
        raise ProtocolError("bad_text", f"text must be {low}-{high} chars")
    return text.strip()


def _kick(data):
    """Validate a `kick` frame; return (nick, reason)."""
    nick = data.get("nick")
    if not isinstance(nick, str) or not nick:
        raise ProtocolError("bad_json", "nick must be a non-empty string")
    reason = data.get("reason", "")
    if not isinstance(reason, str) or len(reason.strip()) > MAX_FIELD:
        raise ProtocolError("bad_text", f"reason must be 0-{MAX_FIELD} chars")
    return nick, reason.strip()


def _say(data, max_text):
    """Validate a `say` frame; return (text, omit set, action)."""
    text = _text(data, 1, max_text)
    omit = data.get("omit", [])
    if not isinstance(omit, list) or not all(isinstance(o, str) for o in omit):
        raise ProtocolError("bad_json", "omit must be a list of strings")
    action = data.get("action", False)
    if not isinstance(action, bool):
        raise ProtocolError("bad_json", "action must be a boolean")
    return text, set(omit), action
