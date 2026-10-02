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
from paranoia.protocol import ProtocolError


class Room:
    """A named room; users maps nickname -> object with async send_json."""

    def __init__(self, name, store):
        """Create an empty room backed by the given HistoryStore."""
        self.name = name
        self.users = {}
        self.topic = ""
        self._store = store

    @property
    def op(self):
        """Nickname of the operator: the longest-connected user, or ""."""
        return next(iter(self.users), "")

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

    async def leave(self, nick, conn=None):
        """Remove nick, tell the others, and announce a new operator.

        A no-op if conn is given and no longer owns nick (it was kicked,
        and the nickname may already belong to a new connection).
        """
        if conn is not None and self.users.get(nick) is not conn:
            return
        was_op = nick == self.op
        del self.users[nick]
        await self._broadcast({"type": "leave", "nick": nick})
        if was_op and self.users:
            await self._broadcast({"type": "op", "nick": self.op})

    async def kick(self, nick, target, reason):
        """Operator nick removes target; raise ProtocolError if refused.

        Everyone (target included) gets a kick frame, then the target is
        dropped without a leave frame and its socket is closed.
        """
        if nick != self.op:
            raise ProtocolError("not_op", "only the operator can kick")
        if target == nick:
            raise ProtocolError("bad_target", "you cannot kick yourself")
        if target not in self.users:
            raise ProtocolError("no_such_nick", f"no such user: {target}")
        await self._broadcast(
            {"type": "kick", "nick": target, "by": nick, "reason": reason})
        conn = self.users.pop(target)
        await conn.close()

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
                "users": sorted(self.users), "topic": self.topic, "op": self.op,
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
