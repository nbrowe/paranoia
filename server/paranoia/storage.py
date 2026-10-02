"""History storage interface and in-memory implementation.

Purpose: own per-room message history and id assignment behind a small
interface so a persistent backend (e.g. SQLite) can be swapped in.
Scope: append and recent-read only.
Limitations: the in-memory store loses everything on restart; ids are
per-room counters starting at 1 and never reused while the process lives.
"""
import time
from abc import ABC, abstractmethod
from collections import deque

from paranoia.messages import Message


class HistoryStore(ABC):
    """Interface every storage backend implements (sync, called inline)."""

    @abstractmethod
    def append(self, room, sender, text, omitted):
        """Persist a new message for room and return the stored Message."""

    @abstractmethod
    def recent(self, room):
        """Return the room's retained messages, oldest first."""


class MemoryHistoryStore(HistoryStore):
    """Bounded per-room deque history with monotonic ids."""

    def __init__(self, limit=100, clock=time.time):
        """Keep at most limit messages per room; clock supplies ts."""
        self._limit = limit
        self._clock = clock
        self._history = {}
        self._last_id = {}

    def append(self, room, sender, text, omitted):
        """Assign the next id and timestamp, store, and return the message."""
        mid = self._last_id.get(room, 0) + 1
        self._last_id[room] = mid
        msg = Message(mid, self._clock(), sender, text, frozenset(omitted))
        self._history.setdefault(room, deque(maxlen=self._limit)).append(msg)
        return msg

    def recent(self, room):
        """Return retained messages for room, oldest first."""
        return list(self._history.get(room, ()))
