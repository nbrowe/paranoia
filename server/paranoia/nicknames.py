"""Nickname pool and random assignment.

Purpose: load the 821 Pokemon slugs and pick one not already in use.
Scope: pure helpers; the caller tracks which nicknames are taken.
Limitations: picking is O(pool size), fine for 821 names.
"""
import random
from pathlib import Path

_DATA = Path(__file__).parent / "data" / "pokemon.txt"


def load_nicknames(path=_DATA):
    """Return the nickname slugs in file order, skipping blank lines."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip()]


NICKNAMES = tuple(load_nicknames())


def pick_nickname(used, pool=NICKNAMES, rng=random):
    """Return a random nickname from pool not in used, or None if none."""
    free = [n for n in pool if n not in used]
    return rng.choice(free) if free else None
