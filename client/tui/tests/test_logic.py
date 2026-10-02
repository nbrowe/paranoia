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
    assert logic.parse_input("/topic -") == ("topic", "")
    assert logic.parse_input("/kick bob") == ("kick", ("bob", ""))
    assert logic.parse_input("/kick bob be  nice") == (
        "kick", ("bob", "be  nice"))
    assert logic.parse_input("/kick").kind == "usage"
    assert logic.parse_input("//shrug") == ("say", "/shrug")


def test_build_say_includes_omit_only_when_set():
    """The omit key is absent for an empty list."""
    assert json.loads(logic.build_say("x", [])) == {"type": "say", "text": "x"}
    assert json.loads(logic.build_say("x", ["a"]))["omit"] == ["a"]


def test_build_action_topic_kick():
    """New client frames carry only the documented fields."""
    assert json.loads(logic.build_say("x", [], action=True))["action"] is True
    assert json.loads(logic.build_topic("hi")) == {"type": "topic",
                                                   "text": "hi"}
    assert json.loads(logic.build_kick("a")) == {"type": "kick", "nick": "a"}
    assert json.loads(logic.build_kick("a", "why"))["reason"] == "why"


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


def test_new_frames_render():
    """Action, topic, kick and op frames render; kick prunes the roster."""
    act = {"ts": 0, "sender": "ash", "text": "waves", "action": True}
    assert " * ash waves" in logic.format_message(act, "me").text
    top = {"type": "topic", "nick": "a", "text": "hi"}
    assert logic.format_event(top, "me")[0].text == "* a set the topic: hi"
    assert "cleared" in logic.format_event({**top, "text": ""}, "me")[0].text
    kick = {"type": "kick", "nick": "b", "by": "a", "reason": "spam"}
    assert logic.format_event(kick, "me")[0].text == \
        "* b was kicked by a: spam"
    assert logic.format_event({**kick, "nick": "me"}, "me")[0].style == "error"
    assert logic.is_self_kick({**kick, "nick": "me"}, "me")
    assert not logic.is_self_kick(kick, "me")
    assert logic.update_users(["a", "b"], kick) == ["a"]
    assert "operator" in logic.format_event(
        {"type": "op", "nick": "c"}, "me")[0].text


def test_topic_state():
    """welcome and topic frames set the stored topic; others keep it."""
    assert logic.update_topic("", {"type": "welcome", "topic": "t"}) == "t"
    assert logic.update_topic("t", {"type": "topic", "text": "u"}) == "u"
    assert logic.update_topic("t", {"type": "join"}) == "t"
    welcome = {"type": "welcome", "nick": "me", "room": "r", "users": [],
               "topic": "t", "history": []}
    assert "topic: t" in logic.format_event(welcome, "me")[1].text
    assert "topic: t" in logic.status_text("me", [], "t")
    assert "topic" not in logic.status_text("me", [], "")


def test_complete_prefix_and_cycle():
    """Tab completes case-insensitively, then cycles on repeats."""
    users = ["Bob", "bill", "me", "zed"]
    buf, st = logic.complete("/omit b", users, "me")
    assert buf == "/omit Bob"
    buf, st = logic.complete(buf, users, "me", st)
    assert buf == "/omit bill"
    buf, st = logic.complete(buf, users, "me", st)
    assert buf == "/omit Bob"


def test_complete_scope_and_exclusions():
    """Empty word lists everyone else; used and own nicks are skipped."""
    users = ["a", "b", "me"]
    assert logic.complete("/omit ", users, "me")[0] == "/omit a"
    assert logic.complete("/omit a ", users, "me")[0] == "/omit a b"
    assert logic.complete("/omit q", users, "me") == ("/omit q", None)
    assert logic.complete("/omit m", users, "me") == ("/omit m", None)
    assert logic.complete("hello b", users, "me") == ("hello b", None)
    assert logic.complete("/kick b", users, "me")[0] == "/kick b"
    assert logic.complete("/kick a rude b", users, "me")[1] is None
