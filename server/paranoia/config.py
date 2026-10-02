"""Runtime settings, read from PARANOIA_* environment variables.

Purpose: one frozen Settings object passed into the app factory.
Scope: protocol limits and defaults only; host/port are uvicorn's job.
Limitations: values are read once at construction, not reloaded.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Server tunables; defaults match docs/protocol.md."""

    history_size: int = 100
    max_text: int = 500
    default_room: str = "lobby"

    @classmethod
    def from_env(cls, env=os.environ):
        """Build Settings from PARANOIA_* variables, defaulting the rest."""
        return cls(
            history_size=int(env.get("PARANOIA_HISTORY_SIZE", cls.history_size)),
            max_text=int(env.get("PARANOIA_MAX_TEXT", cls.max_text)),
            default_room=env.get("PARANOIA_DEFAULT_ROOM", cls.default_room),
        )
