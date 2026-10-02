"""End-to-end tests over Starlette's TestClient WebSocket support."""
import json

from starlette.testclient import TestClient

from paranoia.app import create_app
from paranoia.config import Settings
from paranoia.nicknames import NICKNAMES


def client():
    """Return a TestClient on a fresh app (isolated rooms/history)."""
    return TestClient(create_app(Settings()))


def test_healthz():
    """GET /healthz returns the documented body."""
    r = client().get("/healthz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_join_leave_and_default_room():
    """Welcome lists users; join/leave are announced; default is lobby."""
    with client() as c:
        with c.websocket_connect("/ws") as a:
            wa = a.receive_json()
            assert wa["type"] == "welcome" and wa["room"] == "lobby"
            assert wa["users"] == [wa["nick"]] and wa["history"] == []
            with c.websocket_connect("/ws") as b:
                wb = b.receive_json()
                assert wb["nick"] != wa["nick"]
                assert a.receive_json() == {"type": "join", "nick": wb["nick"]}
            assert a.receive_json() == {"type": "leave", "nick": wb["nick"]}


def test_omit_flow_and_history():
    """Sender/omitted/third-party copies, then history per recipient."""
    with client() as c:
        with c.websocket_connect("/ws") as a, \
             c.websocket_connect("/ws") as b, \
             c.websocket_connect("/ws") as d:
            na = a.receive_json()["nick"]
            nb = b.receive_json()["nick"]
            nd = d.receive_json()["nick"]
            a.receive_json(); a.receive_json()  # joins of b, d
            b.receive_json()                    # join of d
            a.send_json({"type": "say", "text": " top  secret ",
                         "omit": [nb, na, nb, "ghost"]})
            ma, mb, md = a.receive_json(), b.receive_json(), d.receive_json()
            assert ma["text"] == "top  secret" and not ma["masked"]
            assert ma["omitted"] == sorted([nb, "ghost"])
            assert mb["text"] == "***  ******" and mb["masked"]
            assert "omitted" not in mb and "omitted" not in md
            assert md["text"] == "top  secret" and not md["masked"]
            assert ma["id"] == 1 and ma["sender"] == na
            with c.websocket_connect("/ws") as e:
                hist = e.receive_json()["history"]
                assert hist[0]["text"] == "top  secret" and "type" not in hist[0]
                assert "omitted" not in hist[0]


def test_history_masked_for_omitted_late_joiner():
    """Omitting every nickname masks the message in a joiner's history."""
    with client() as c:
        with c.websocket_connect("/ws") as a:
            a.receive_json()
            a.send_json({"type": "say", "text": "hi there",
                         "omit": list(NICKNAMES)})
            assert a.receive_json()["text"] == "hi there"
            with c.websocket_connect("/ws") as b:
                h = b.receive_json()["history"][0]
                assert h["text"] == "** *****" and h["masked"]
                assert "omitted" not in h


def test_errors_keep_connection_open():
    """bad_json, bad_text and unknown_type do not close the socket."""
    with client() as c, c.websocket_connect("/ws") as ws:
        ws.receive_json()
        ws.send_text("not json")
        assert ws.receive_json()["code"] == "bad_json"
        ws.send_text(json.dumps({"type": "say", "text": "   "}))
        assert ws.receive_json()["code"] == "bad_text"
        ws.send_text(json.dumps({"type": "nope"}))
        assert ws.receive_json()["code"] == "unknown_type"
        ws.send_json({"type": "say", "text": "still alive"})
        assert ws.receive_json()["text"] == "still alive"


def test_rooms_are_isolated_and_created_on_join():
    """Messages in one room are not seen in another."""
    with client() as c:
        with c.websocket_connect("/ws?room=r1") as a, \
             c.websocket_connect("/ws?room=r2") as b:
            assert a.receive_json()["room"] == "r1"
            assert b.receive_json()["users"] != []
            a.send_json({"type": "say", "text": "x"})
            a.receive_json()
        with c.websocket_connect("/ws?room=r2") as b2:
            assert b2.receive_json()["history"] == []


def test_room_full():
    """A full room gets room_full and the socket closes."""
    app = create_app(Settings())
    app.state.hub.get("lobby").users = {n: _Dead() for n in NICKNAMES}
    with TestClient(app) as c, c.websocket_connect("/ws") as ws:
        err = ws.receive_json()
        assert err["type"] == "error" and err["code"] == "room_full"


class _Dead:
    """Connection stub whose sends are ignored."""

    async def send_json(self, frame):
        """Discard the frame."""


def test_action_message_flag_and_masking():
    """/me messages carry action=true to all, with normal masking."""
    with client() as c:
        with c.websocket_connect("/ws") as a, c.websocket_connect("/ws") as b:
            a.receive_json()
            nb = b.receive_json()["nick"]
            a.receive_json()  # join of b
            a.send_json({"type": "say", "text": "waves", "action": True,
                         "omit": [nb]})
            ma, mb = a.receive_json(), b.receive_json()
            assert ma["action"] is True and ma["text"] == "waves"
            assert mb["action"] is True and mb["text"] == "*****"
            a.send_json({"type": "say", "text": "plain"})
            assert "action" not in a.receive_json()
            with c.websocket_connect("/ws") as d:
                hist = d.receive_json()["history"]
                assert hist[0]["action"] is True and "action" not in hist[1]


def test_topic_over_socket():
    """Topic frames reach everyone; bad_text for an oversized topic."""
    with client() as c:
        with c.websocket_connect("/ws") as a, c.websocket_connect("/ws") as b:
            na = a.receive_json()["nick"]
            b.receive_json()
            a.receive_json()  # join of b
            b.send_json({"type": "topic", "text": " new "})
            fa, fb = a.receive_json(), b.receive_json()
            assert fa == fb and fa["text"] == "new" and fa["nick"] != na
            b.send_json({"type": "topic", "text": "x" * 201})
            assert b.receive_json()["code"] == "bad_text"
            with c.websocket_connect("/ws") as d:
                assert d.receive_json()["topic"] == "new"
