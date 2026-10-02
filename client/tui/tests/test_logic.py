"""Unit tests for paranoia_tui.logic (pure functions only)."""

import json

from paranoia_tui import logic


def test_parse_input_kinds():
    """Commands and plain text are classified."""
    assert logic.parse_input("  ").kind == "empty"
    assert logic.parse_input("hi there") == ("say", "hi there")
    assert logic.parse_input("/quit").kind == "quit"
    assert logic.parse_input("/nope").kind == "unknown"


def test_parse_omit_sets_clears_dedups():
    """/omit takes names, dedups, and clears when bare."""
    assert logic.parse_input("/omit a b a") == ("omit", ["a", "b"])
    assert logic.parse_input("/omit") == ("omit", [])


def test_parse_new_commands():
    """/help, /me, /topic, /kick and the // escape parse as specified."""
    assert logic.parse_input("/help").kind == "help"
    assert logic.parse_input("/me waves  hi") == ("me", "waves  hi")
    assert logic.parse_input("/me").kind == "usage"
    assert logic.parse_input("/topic") == ("topic", None)
    assert logic.parse_input("/topic new  title") == ("topic", "new  title")
    assert logic.parse_input("/kick bob") == ("kick", ("bob", ""))
    assert logic.parse_input("/kick bob be  nice") == (
        "kick", ("bob", "be  nice"))
    assert logic.parse_input("/kick").kind == "usage"
    assert logic.parse_input("//shrug") == ("say", "/shrug")


def test_build_say_includes_omit_only_when_set():
    """The omit key is absent for an empty list."""
    assert json.loads(logic.build_say("x", [])) == {"type": "say", "text": "x"}
    assert json.loads(logic.build_say("x", ["a"]))["omit"] == ["a"]


def test_parse_frame_rejects_garbage():
    """Non-JSON and untyped frames yield None."""
    assert logic.parse_frame("nope") is None
    assert logic.parse_frame("[1]") is None
    assert logic.parse_frame('{"a": 1}') is None
    assert logic.parse_frame('{"type": "join"}') == {"type": "join"}


def test_update_users():
    """Roster follows welcome, join, leave; other frames are no-ops."""
    users = logic.update_users([], {"type": "welcome", "users": ["b", "a"]})
    assert users == ["a", "b"]
    users = logic.update_users(users, {"type": "join", "nick": "c"})
    assert users == ["a", "b", "c"]
    users = logic.update_users(users, {"type": "leave", "nick": "a"})
    assert users == ["b", "c"]
    assert logic.update_users(users, {"type": "message"}) == users


def test_format_message_styles():
    """Masked, own (with omitted list) and other messages differ."""
    base = {"ts": 0, "sender": "ash", "text": "hello"}
    assert logic.format_message(base, "me").style == "msg"
    own = logic.format_message(
        {**base, "sender": "me", "omitted": ["x", "y"]}, "me")
    assert own.style == "own" and "hidden from: x, y" in own.text
    masked = logic.format_message({**base, "text": "*****", "masked": True},
                                  "me")
    assert masked.style == "masked" and "*****" in masked.text


def test_format_event():
    """Welcome expands history; unknown types render nothing."""
    welcome = {"type": "welcome", "nick": "me", "room": "lobby",
               "users": ["me"],
               "history": [{"ts": 0, "sender": "a", "text": "old"}]}
    lines = logic.format_event(welcome, "me")
    assert len(lines) == 2 and "lobby" in lines[0].text
    assert logic.format_event({"type": "leave", "nick": "a"}, "me")[0].text \
        == "* a left"
    err = logic.format_event(
        {"type": "error", "code": "bad_text", "message": "no"}, "me")
    assert err[0].style == "error"
    assert logic.format_event({"type": "future"}, "me") == []


def test_status_and_wrap():
    """Status shows nick and omit list; wrap chunks by width."""
    assert "me" in logic.status_text("me", []) and "(none)" in \
        logic.status_text("me", [])
    assert "a, b" in logic.status_text("me", ["a", "b"])
    assert logic.wrap("abcde", 2) == ["ab", "cd", "e"]
    assert logic.wrap("", 5) == [""]
