"""Unit tests for paranoia_desktop.logic (pure functions only)."""

from paranoia_desktop import logic
from paranoia_desktop.logic import ChatState


def test_parse_input():
    """Plain text, /omit forms, unknown commands and blanks."""
    assert logic.parse_input("  ") is None
    assert logic.parse_input(" hi there ") == ("say", "hi there")
    assert logic.parse_input("/omit a  b") == ("omit", ["a", "b"])
    assert logic.parse_input("/omit") == ("omit", [])
    assert logic.parse_input("/nope")[0] == "error"


def test_build_say_copies_omit():
    """The frame carries a copy of the omit list."""
    omit = ["a"]
    frame = logic.build_say("x", omit)
    omit.append("b")
    assert frame == {"type": "say", "text": "x", "omit": ["a"]}


def test_normalize_omit():
    """Own nick and duplicates are dropped."""
    assert logic.normalize_omit(["me", "a", "a", "b"], "me") == ["a", "b"]


def test_merge_selection_keeps_absent_names():
    """Absent omitted names survive; present ones follow the selection."""
    out = logic.merge_selection(["ghost", "a"], ["a", "b", "c"], {"b", "c"})
    assert out == ["ghost", "b", "c"]


def _msg(**kw):
    """Build a Message dict with defaults."""
    base = {"ts": 0, "sender": "pikachu", "text": "hello"}
    return {**base, **kw}


def test_format_message_variants():
    """Normal, masked and own-with-omitted messages get distinct tags."""
    assert logic.format_message(_msg())[0] == "normal"
    tag, line = logic.format_message(_msg(text="*****", masked=True))
    assert tag == "masked" and line.endswith("pikachu: *****")
    tag, line = logic.format_message(_msg(omitted=["b", "a"]))
    assert tag == "own" and line.endswith("(omitted: b, a)")
    assert logic.format_message(_msg(omitted=[]))[1].endswith("nobody)")


def test_apply_welcome_join_leave():
    """Welcome sets identity/users and renders history; join/leave update."""
    st = ChatState()
    lines = logic.apply_frame(st, {
        "type": "welcome", "nick": "me", "room": "lobby",
        "users": ["zed", "me"], "history": [_msg()],
    })
    assert (st.nick, st.room, st.users) == ("me", "lobby", ["me", "zed"])
    assert [t for t, _ in lines] == ["normal", "notice"]
    logic.apply_frame(st, {"type": "join", "nick": "abe"})
    assert st.users == ["abe", "me", "zed"]
    logic.apply_frame(st, {"type": "leave", "nick": "zed"})
    assert st.users == ["abe", "me"]


def test_apply_error_and_unknown():
    """Errors are shown; unknown types are ignored."""
    st = ChatState()
    out = logic.apply_frame(st, {"type": "error", "code": "bad_text",
                                 "message": "too long"})
    assert out == [("error", "! bad_text: too long")]
    assert logic.apply_frame(st, {"type": "future"}) == []


def test_format_status():
    """Status shows nick, room and omit list."""
    st = ChatState(nick="me", room="r", omit=["a", "b"])
    assert logic.format_status(st) == "you: me  room: r  omit: a, b"
    assert "omit: none" in logic.format_status(ChatState())
