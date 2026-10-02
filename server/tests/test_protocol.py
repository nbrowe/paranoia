"""Tests for client frame parsing."""
import json

import pytest

from paranoia.protocol import ProtocolError, parse_frame


def code(raw):
    """Return the error code parse_frame raises for raw."""
    with pytest.raises(ProtocolError) as e:
        parse_frame(raw, 500)
    return e.value.code


def test_valid_say_strips_text_and_dedups_omit():
    """Text is stripped and omit becomes a set."""
    raw = json.dumps({"type": "say", "text": " hi ", "omit": ["a", "a"]})
    assert parse_frame(raw, 500) == ("say", ("hi", {"a"}, False))


def test_error_codes():
    """Each malformed frame maps to its protocol error code."""
    assert code("{nope") == "bad_json"
    assert code("[1]") == "bad_json"
    assert code(None) == "bad_json"
    assert code('{"type": "dance"}') == "unknown_type"
    assert code('{"type": "say", "text": "   "}') == "bad_text"
    assert code('{"type": "say", "text": 5}') == "bad_text"
    assert code(json.dumps({"type": "say", "text": "x" * 501})) == "bad_text"
    assert code('{"type": "say", "text": "x", "omit": "a"}') == "bad_json"


def test_max_length_boundary():
    """Exactly 500 characters after stripping is accepted."""
    raw = json.dumps({"type": "say", "text": " " + "x" * 500 + " "})
    assert len(parse_frame(raw, 500)[1][0]) == 500


def test_action_flag():
    """action must be a boolean and defaults to False."""
    raw = json.dumps({"type": "say", "text": "waves", "action": True})
    assert parse_frame(raw, 500) == ("say", ("waves", set(), True))
    assert code('{"type": "say", "text": "x", "action": "yes"}') == "bad_json"


def test_topic_frame():
    """Topic is stripped, may be empty, and is limited to 200 chars."""
    assert parse_frame('{"type": "topic", "text": " hi "}', 500) == (
        "topic", ("hi",))
    assert parse_frame('{"type": "topic", "text": "  "}', 500)[1] == ("",)
    assert parse_frame(json.dumps({"type": "topic", "text": "x" * 200}),
                       500)[1] == ("x" * 200,)
    assert code(json.dumps({"type": "topic", "text": "x" * 201})) == "bad_text"
    assert code('{"type": "topic"}') == "bad_text"
