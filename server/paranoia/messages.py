"""Stored message model and per-recipient rendering.

Purpose: define the canonical message record and pure functions that
turn it into the wire dict each recipient is allowed to see.
Scope: masking and omit semantics from docs/protocol.md only.
Limitations: no I/O; callers add the "type" key for live frames.
"""
import re
from dataclasses import dataclass

_NON_SPACE = re.compile(r"\S")


@dataclass(frozen=True)
class Message:
    """A stored message with its real text and effective omit set."""

    id: int
    ts: float
    sender: str
    text: str
    omitted: frozenset


def mask(text):
    """Replace every non-whitespace character with '*', keeping layout."""
    return _NON_SPACE.sub("*", text)


def render(msg, recipient):
    """Return the wire dict (no "type") of msg as recipient may see it."""
    out = {"id": msg.id, "ts": msg.ts, "sender": msg.sender}
    if recipient == msg.sender:
        out.update(text=msg.text, masked=False, omitted=sorted(msg.omitted))
    elif recipient in msg.omitted:
        out.update(text=mask(msg.text), masked=True)
    else:
        out.update(text=msg.text, masked=False)
    return out
