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


def test_parse_commands():
    """/help, /me, /kick, /topic and the // escape."""
    assert logic.parse_input("/help") == ("help", None)
    assert logic.parse_input("/me waves  ") == ("action", "waves")
    assert logic.parse_input("/me")[0] == "error"
    assert logic.parse_input("/kick bob") == ("kick", ("bob", ""))
    assert logic.parse_input("/kick bob be  nice") == (
        "kick", ("bob", "be  nice"))
    assert logic.parse_input("/kick")[0] == "error"
    assert logic.parse_input("/topic") == ("topic", None)
    assert logic.parse_input("/topic a b") == ("topic", "a b")
    assert logic.parse_input("/topic -") == ("topic", "")
    assert logic.parse_input("//omit x") == ("say", "/omit x")


def test_build_frames():
    """Action flag only present when set; topic and kick frames."""
    assert "action" not in logic.build_say("x", [])
    assert logic.build_say("x", [], action=True)["action"] is True
    assert logic.build_topic("t") == {"type": "topic", "text": "t"}
    assert logic.build_kick("b", "r") == {
        "type": "kick", "nick": "b", "reason": "r"}


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


def test_format_topic():
    """Set and unset topics."""
    assert logic.format_topic("hi") == "* topic: hi"
    assert logic.format_topic("") == "* no topic set"
    assert logic.format_topic_label("hi") == "Topic: hi"
    assert logic.format_topic_label("") == "Topic: (none)"


def test_action_message():
    """/me messages render as '* nick text', masked too."""
    line = logic.format_message(_msg(action=True))[1]
    assert line.endswith("* pikachu hello")
    tag, line = logic.format_message(_msg(action=True, text="**", masked=True))
    assert tag == "masked" and line.endswith("* pikachu **")


def test_welcome_topic_and_topic_frame():
    """Welcome seeds topic/op; topic and op frames update them."""
    st = ChatState()
    logic.apply_frame(st, {"type": "welcome", "nick": "me", "room": "r",
                           "users": ["me"], "history": [], "topic": "hi",
                           "op": "me"})
    assert (st.topic, st.op) == ("hi", "me")
    out = logic.apply_frame(st, {"type": "topic", "nick": "a", "text": "yo"})
    assert st.topic == "yo" and "a set the topic: yo" in out[0][1]
    out = logic.apply_frame(st, {"type": "topic", "nick": "a", "text": ""})
    assert st.topic == "" and "cleared" in out[0][1]
    logic.apply_frame(st, {"type": "op", "nick": "a"})
    assert st.op == "a"


def test_kick_other_and_self():
    """Kicking someone drops them; kicking us flags the session."""
    st = ChatState(nick="me", users=["bob", "me"])
    out = logic.apply_frame(st, {"type": "kick", "nick": "bob", "by": "me",
                                 "reason": "spam"})
    assert st.users == ["me"] and not st.kicked
    assert out == [("notice", "* bob was kicked by me: spam")]
    out = logic.apply_frame(st, {"type": "kick", "nick": "me", "by": "x",
                                 "reason": ""})
    assert st.kicked and out == [("error", "! you were kicked by x")]


USERS = ["abe", "Abby", "bob", "me"]


def test_complete_prefix_and_cycle():
    """Case-insensitive prefix, own nick excluded, repeated TAB cycles."""
    c = logic.complete("/omit a", USERS, "me")
    assert c.line == "/omit Abby"  # sorted: "Abby" < "abe"
    c = logic.complete(c.line, USERS, "me", c)
    assert c.line == "/omit abe"
    c = logic.complete(c.line, USERS, "me", c)
    assert c.line == "/omit Abby"
    assert logic.complete("/omit m", USERS, "me") is None


def test_complete_scope():
    """Empty word lists all; /kick only completes its first argument."""
    assert logic.complete("/omit abe ", USERS, "me").cands == [
        "Abby", "abe", "bob"]
    assert logic.complete("/omit abe b", USERS, "me").line == "/omit abe bob"
    assert logic.complete("/kick b", USERS, "me").line == "/kick bob"
    assert logic.complete("/kick bob b", USERS, "me") is None
    assert logic.complete("/me b", USERS, "me") is None
    assert logic.complete("hello b", USERS, "me") is None


def test_mark_user_and_op_tracking():
    """`@` prefixes the operator, `*` marks self; op follows frames."""
    assert logic.mark_user("a", "a", "b") == "a*"
    assert logic.mark_user("b", "a", "b") == "@b"
    assert logic.mark_user("a", "a", "a") == "@a*"
    st = logic.ChatState()
    welcome = {"type": "welcome", "nick": "a", "room": "r",
               "users": ["a", "b"], "topic": "", "op": "b", "history": []}
    logic.apply_frame(st, welcome)
    assert st.op == "b"
    logic.apply_frame(st, {"type": "leave", "nick": "b"})
    logic.apply_frame(st, {"type": "op", "nick": "a"})
    assert (st.op, st.users) == ("a", ["a"])


def test_changes_user_list():
    """Only membership/op frames force a user list rebuild."""
    for kind in ("welcome", "join", "leave", "kick", "op"):
        assert logic.changes_user_list({"type": kind})
    for kind in ("message", "topic", "error", "bogus"):
        assert not logic.changes_user_list({"type": kind})
