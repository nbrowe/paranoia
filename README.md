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
| `client/tui`     | terminal client                                  |
| `client/desktop` | desktop client                                   |
| `client/web`     | web client                                       |
| `docs/`          | [protocol](docs/protocol.md), [deployment](docs/deployment.md) |

Not every client directory exists on every branch yet; as clients land,
each will carry its own README.

## Running the server

See [docs/deployment.md](docs/deployment.md) for container builds, or
[server/README.md](server/README.md) for a local virtualenv setup.
