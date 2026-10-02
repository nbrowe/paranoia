"""Client frame parsing and validation.

Purpose: turn a raw client frame into a validated (text, omit, action) triple or a
ProtocolError carrying a protocol error code.
Scope: the client -> server direction of docs/protocol.md.
Limitations: only the `say` type exists; an `omit` that is not a list of
strings is reported as bad_json (the protocol defines no code for it).
"""
import json


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


def parse_say(raw, max_text):
    """Validate a raw frame as `say`; return (text, omit set, action) or raise."""
    try:
        data = json.loads(raw) if raw is not None else None
    except ValueError:
        data = None
    if not isinstance(data, dict):
        raise ProtocolError("bad_json", "frame must be a JSON object")
    if data.get("type") != "say":
        raise ProtocolError("unknown_type", "unknown type")
    text = data.get("text")
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= max_text:
        raise ProtocolError("bad_text", f"text must be 1-{max_text} chars")
    omit = data.get("omit", [])
    if not isinstance(omit, list) or not all(isinstance(o, str) for o in omit):
        raise ProtocolError("bad_json", "omit must be a list of strings")
    action = data.get("action", False)
    if not isinstance(action, bool):
        raise ProtocolError("bad_json", "action must be a boolean")
    return text.strip(), set(omit), action
