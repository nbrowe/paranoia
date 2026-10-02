"""Tests for room join/leave and broadcast, using fake connections."""
import asyncio

import pytest

from paranoia.nicknames import NICKNAMES
from paranoia.protocol import ProtocolError
from paranoia.room import Hub, Room
from paranoia.storage import MemoryHistoryStore


class FakeConn:
    """Records frames instead of sending them."""

    def __init__(self):
        """Start with no received frames."""
        self.frames = []
        self.closed = False

    async def send_json(self, frame):
        """Record the frame."""
        self.frames.append(frame)

    async def close(self):
        """Record that the socket was closed."""
        self.closed = True


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


def test_first_user_is_op_and_op_passes_to_next_oldest():
    """Welcome names the op; when the op leaves the next oldest gets op."""
    async def go():
        room = make_room()
        a, b, c = FakeConn(), FakeConn(), FakeConn()
        na, nb, nc = [await room.join(x) for x in (a, b, c)]
        assert a.frames[0]["op"] == na
        assert b.frames[0]["op"] == na and c.frames[0]["op"] == na
        await room.leave(nb)  # non-op leaves: no op frame
        assert c.frames[-1] == {"type": "leave", "nick": nb}
        await room.leave(na)
        assert c.frames[-2:] == [{"type": "leave", "nick": na},
                                 {"type": "op", "nick": nc}]
        assert room.op == nc
        await room.leave(nc)
        assert room.op == ""
    asyncio.run(go())


def test_set_topic_broadcasts_and_shows_in_welcome():
    """Topic goes to everyone incl. setter; later joiners see it."""
    async def go():
        room = make_room()
        a, b = FakeConn(), FakeConn()
        na = await room.join(a)
        await room.join(b)
        assert a.frames[0]["topic"] == ""
        await room.set_topic(na, "plans")
        frame = {"type": "topic", "nick": na, "text": "plans"}
        assert a.frames[-1] == frame and b.frames[-1] == frame
        c = FakeConn()
        await room.join(c)
        assert c.frames[0]["topic"] == "plans"
        await room.set_topic(na, "")
        assert room.topic == "" and a.frames[-1]["text"] == ""
    asyncio.run(go())


def test_kick_notifies_all_and_closes_target_without_leave():
    """kick goes to everyone incl. target; target gets no leave."""
    async def go():
        room = make_room()
        a, b, c = FakeConn(), FakeConn(), FakeConn()
        na, nb, nc = [await room.join(x) for x in (a, b, c)]
        await room.kick(na, nb, "spam")
        frame = {"type": "kick", "nick": nb, "by": na, "reason": "spam"}
        assert a.frames[-1] == c.frames[-1] == b.frames[-1] == frame
        assert b.closed and not a.closed and nb not in room.users
        await room.leave(nb, b)  # the kicked handler's cleanup
        assert a.frames[-1] == frame and room.op == na
    asyncio.run(go())


@pytest.mark.parametrize("who,target,code", [
    (1, 0, "not_op"), (0, 0, "bad_target"), (0, None, "no_such_nick")])
def test_kick_errors(who, target, code):
    """Non-op, self-kick and unknown targets are refused untouched."""
    async def go():
        room = make_room()
        conns = [FakeConn(), FakeConn()]
        nicks = [await room.join(x) for x in conns]
        tgt = "ghost" if target is None else nicks[target]
        with pytest.raises(ProtocolError) as e:
            await room.kick(nicks[who], tgt, "")
        assert e.value.code == code and len(room.users) == 2
        assert not any(x.closed for x in conns)
    asyncio.run(go())


def test_stale_leave_does_not_evict_reused_nick():
    """A kicked connection's leave cannot remove a newer owner of nick."""
    async def go():
        room = make_room()
        old, new = FakeConn(), FakeConn()
        room.users = {"x": new}
        await room.leave("x", old)
        assert room.users == {"x": new}
    asyncio.run(go())
