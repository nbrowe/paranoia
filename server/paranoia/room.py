"""Rooms: connected users, join/leave, and per-recipient broadcast.

Purpose: hold who is in a room and fan messages out so each recipient
gets only the copy render() allows.
Scope: in-process rooms keyed by name, created on first use.
Limitations: rooms (and their history) are never evicted; a slow client
delays only its own send, but is not disconnected for being slow.
"""
import asyncio

from paranoia.messages import render
from paranoia.nicknames import pick_nickname


class Room:
    """A named room; users maps nickname -> object with async send_json."""

    def __init__(self, name, store):
        """Create an empty room backed by the given HistoryStore."""
        self.name = name
        self.users = {}
        self.topic = ""
        self._store = store

    async def join(self, conn):
        """Admit conn; return its nickname, or None if the room is full.

        On success the welcome frame is sent first and others are told.
        """
        nick = pick_nickname(self.users)
        if nick is None:
            return None
        self.users[nick] = conn
        await conn.send_json(self._welcome(nick))
        await self._broadcast({"type": "join", "nick": nick}, skip=nick)
        return nick

    async def leave(self, nick):
        """Remove nick and tell the remaining users."""
        del self.users[nick]
        await self._broadcast({"type": "leave", "nick": nick})

    async def set_topic(self, nick, text):
        """Set the room topic and tell everyone, including the setter."""
        self.topic = text
        await self._broadcast({"type": "topic", "nick": nick, "text": text})

    async def say(self, sender, text, omit, action=False):
        """Store a message and send each user their rendered copy."""
        msg = self._store.append(
            self.name, sender, text, omit - {sender}, action)
        await self._send_each(
            {n: {"type": "message", **render(msg, n)} for n in self.users}
        )

    def _welcome(self, nick):
        """Build the welcome frame with history rendered for nick."""
        history = [render(m, nick) for m in self._store.recent(self.name)]
        return {"type": "welcome", "nick": nick, "room": self.name,
                "users": sorted(self.users), "topic": self.topic,
                "history": history}

    async def _broadcast(self, frame, skip=None):
        """Send the same frame to every user except skip."""
        await self._send_each({n: frame for n in self.users if n != skip})

    async def _send_each(self, frames):
        """Send frames[nick] to each nick concurrently, ignoring failures."""
        conns = [self.users[n] for n in frames]
        await asyncio.gather(
            *(c.send_json(f) for c, f in zip(conns, frames.values())),
            return_exceptions=True,
        )


class Hub:
    """Registry of rooms sharing one history store."""

    def __init__(self, store):
        """Create an empty registry using store for all rooms."""
        self._store = store
        self._rooms = {}

    def get(self, name):
        """Return the room called name, creating it on first use."""
        if name not in self._rooms:
            self._rooms[name] = Room(name, self._store)
        return self._rooms[name]
