# Paranoia

Paranoia is a small group chat where every message can be hidden from
chosen people. Senders list who must not read a message, and the server
masks the text for those recipients, so the real content never reaches
them. There are no accounts: each connection gets a random Pokemon
nickname. Clients (terminal, desktop, web) all speak the same WebSocket
protocol to one in-memory server.

## Layout

| Path             | Contents                                         |
|------------------|--------------------------------------------------|
| `server/`        | FastAPI + uvicorn backend ([README](server/README.md)) |
| `client/tui`     | curses terminal client ([README](client/tui/README.md)) |
| `client/desktop` | Tkinter desktop client ([README](client/desktop/README.md)) |
| `client/web`     | Svelte web client ([README](client/web/README.md)) |
| `docs/`          | [protocol](docs/protocol.md), [deployment](docs/deployment.md) |

## Quick start

Start the server first: `podman-compose up -d --build` from the repo root
(see [docs/deployment.md](docs/deployment.md)), or run it from a local
virtualenv per [server/README.md](server/README.md). It listens on
port 8000. Then pick a client. Each block below is the full sequence from
a fresh clone; after the first time, only the last line is needed.

```sh
# terminal
cd client/tui
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m paranoia_tui

# desktop (needs tkinter, see its README)
cd client/desktop
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m paranoia_desktop

# web (Node runs in Podman; open http://localhost:5173)
cd client/web
./npmw install
PODMAN_ARGS="--network host" ./npmw run dev
```

To omit people from a message: in the TUI and desktop clients type
`/omit alice bob` (`/omit` alone clears the list); the desktop and web
clients also let you select users in the user list.
