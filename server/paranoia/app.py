"""FastAPI application: /healthz and the /ws chat endpoint.

Purpose: wire settings, storage, rooms and protocol parsing together.
Run with: uvicorn paranoia.app:app
Scope: the transport layer of docs/protocol.md; logic lives elsewhere.
Limitations: binary frames are answered with bad_json; there is no auth,
rate limiting or origin checking.
"""
from fastapi import FastAPI, WebSocket

from paranoia.config import Settings
from paranoia.protocol import ProtocolError, error_frame, parse_frame
from paranoia.room import Hub
from paranoia.storage import MemoryHistoryStore


def create_app(settings=None, store=None):
    """Build the app; pass a different HistoryStore to change backends."""
    settings = settings or Settings.from_env()
    store = store or MemoryHistoryStore(settings.history_size)
    hub = Hub(store)
    app = FastAPI()
    app.state.hub = hub

    @app.get("/healthz")
    async def healthz():
        """Liveness probe for container health checks."""
        return {"status": "ok"}

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket, room: str = settings.default_room):
        """Serve one chat connection until the client disconnects."""
        await ws.accept()
        chat = hub.get(room)
        nick = await chat.join(ws)
        if nick is None:
            await ws.send_json(error_frame("room_full", "room is full"))
            await ws.close()
            return
        try:
            await _serve(ws, chat, nick, settings.max_text)
        finally:
            await chat.leave(nick, ws)

    return app


async def _serve(ws, chat, nick, max_text):
    """Read frames from ws and act on them until it disconnects."""
    while True:
        event = await ws.receive()
        if event["type"] == "websocket.disconnect":
            return
        try:
            kind, args = parse_frame(event.get("text"), max_text)
            if kind == "say":
                await chat.say(nick, *args)
            elif kind == "topic":
                await chat.set_topic(nick, *args)
            elif kind == "kick":
                await chat.kick(nick, *args)
        except ProtocolError as e:
            await ws.send_json(error_frame(e.code, e.message))


app = create_app()
