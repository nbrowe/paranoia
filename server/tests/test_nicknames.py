"""Tests for nickname loading and assignment."""
from paranoia.nicknames import NICKNAMES, pick_nickname


def test_pool_has_821_unique_slugs():
    """The packaged list loads fully with no duplicates."""
    assert len(NICKNAMES) == 821
    assert len(set(NICKNAMES)) == 821
    assert "mr-mime" in NICKNAMES


def test_pick_skips_used():
    """A pick never returns a nickname already in use."""
    used = set(NICKNAMES[:-1])
    assert pick_nickname(used) == NICKNAMES[-1]


def test_pick_exhausted_returns_none():
    """When every nickname is taken, pick returns None."""
    assert pick_nickname(set(NICKNAMES)) is None


def test_picks_are_unique_when_accumulated():
    """Repeatedly picking with a growing used set yields no repeats."""
    used = set()
    for _ in range(len(NICKNAMES)):
        used.add(pick_nickname(used))
    assert used == set(NICKNAMES)
