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

Start the server first: `./paranoia server` (wraps `podman-compose up -d
--build`, see [docs/deployment.md](docs/deployment.md)), or run it from a
local virtualenv per [server/README.md](server/README.md). It listens on
port 8000. Then pick a client:

```sh
./paranoia tui        # terminal client
./paranoia desktop    # desktop client (needs tkinter, see its README)

# web (Node runs in Podman; open http://localhost:5173)
cd client/web
./npmw install
./npmw run dev
```

On first run the launcher creates the client's `.venv` and installs its
`requirements.txt` (one "setting up..." line); it reinstalls only when
`requirements.txt` changes. Arguments pass through
(`./paranoia tui --room secret`). Set `PARANOIA_URL=ws://host:8000/ws` to
change the default server for both clients; an explicit `--url` wins. The
script works from any directory or through a symlink. It needs Python 3.9+
with `venv`; set `PARANOIA_PYTHON` to use another interpreter. Extra arguments to `server` replace the default compose
arguments (`./paranoia server config`). Manual setup is in the client
READMEs.

To omit people from a message: in the TUI and desktop clients type
`/omit alice bob` (`/omit` alone clears the list); the desktop and web
clients also let you select users in the user list.
