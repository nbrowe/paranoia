"""Tests for room join/leave and broadcast, using fake connections."""
import asyncio

from paranoia.nicknames import NICKNAMES
from paranoia.room import Hub, Room
from paranoia.storage import MemoryHistoryStore


class FakeConn:
    """Records frames instead of sending them."""

    def __init__(self):
        """Start with no received frames."""
        self.frames = []

    async def send_json(self, frame):
        """Record the frame."""
        self.frames.append(frame)


def make_room():
    """Return a fresh room on an in-memory store."""
    return Room("lobby", MemoryHistoryStore())


def test_join_assigns_unique_nicks_and_notifies():
    """Joiners get distinct nicks, welcome first, and others see join."""
    async def go():
        room = make_room()
        a, b = FakeConn(), FakeConn()
        na = await room.join(a)
        nb = await room.join(b)
        assert na != nb
        assert a.frames[0]["type"] == "welcome"
        assert a.frames[0]["users"] == [na]
        assert b.frames[0]["users"] == sorted([na, nb])
        assert a.frames[1] == {"type": "join", "nick": nb}
        await room.leave(nb)
        assert a.frames[2] == {"type": "leave", "nick": nb}
    asyncio.run(go())


def test_room_full_returns_none():
    """A room with every nickname taken refuses new joiners."""
    async def go():
        room = make_room()
        room.users = {n: FakeConn() for n in NICKNAMES}
        assert await room.join(FakeConn()) is None
    asyncio.run(go())


def test_say_renders_per_recipient():
    """Sender, omitted and third party each get their own copy."""
    async def go():
        room = make_room()
        conns = {}
        for _ in range(3):
            c = FakeConn()
            conns[await room.join(c)] = c
        s, o, t = list(conns)
        await room.say(s, "hi you", {o, s})
        last = {n: c.frames[-1] for n, c in conns.items()}
        assert last[s]["omitted"] == [o] and last[s]["text"] == "hi you"
        assert last[o]["text"] == "** ***" and "omitted" not in last[o]
        assert last[t]["text"] == "hi you" and not last[t]["masked"]
    asyncio.run(go())


def test_hub_creates_rooms_once():
    """Hub returns the same Room for the same name."""
    hub = Hub(MemoryHistoryStore())
    assert hub.get("x") is hub.get("x")
    assert hub.get("x") is not hub.get("y")
