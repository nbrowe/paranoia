"""Tests for the in-memory history store."""
from paranoia.storage import MemoryHistoryStore


def test_ids_monotonic_per_room():
    """Each room counts independently from 1."""
    s = MemoryHistoryStore()
    assert [s.append("a", "x", "t", []).id for _ in range(3)] == [1, 2, 3]
    assert s.append("b", "x", "t", []).id == 1


def test_history_bounded_and_ordered():
    """Only the newest `limit` messages survive; ids keep increasing."""
    s = MemoryHistoryStore(limit=100)
    for i in range(130):
        s.append("a", "x", str(i), [])
    got = s.recent("a")
    assert len(got) == 100
    assert [m.id for m in got] == list(range(31, 131))


def test_unknown_room_is_empty():
    """Reading a room with no messages returns an empty list."""
    assert MemoryHistoryStore().recent("nope") == []
