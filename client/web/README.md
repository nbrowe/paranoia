# Paranoia web client

Svelte 5 + Vite single-page app with Bootstrap, speaking the protocol in
[docs/protocol.md](../../docs/protocol.md). Node is not installed on the
host: every command runs in a rootless Podman container via `./npmw`.

## Commands

`./npmw <args>` is `npm <args>` inside `docker.io/library/node:24-alpine`
with `client/web` mounted at `/app` (`NODE_IMAGE` overrides the image).

```sh
cd client/web
./npmw install        # first time; node_modules lands here (gitignored)
./npmw run dev        # dev server on http://localhost:5173
./npmw run build      # production bundle in dist/
./npmw test           # Vitest, one-shot, non-interactive
```

Raw equivalent (e.g. for GitLab CI with a `node:24-alpine` image, just run
`npm ci && npm test`):

```sh
podman run --rm -v "$PWD":/app:z -w /app docker.io/library/node:24-alpine \
  sh -c 'npm ci && npm test'
```

## Dev server and the backend

Vite always listens on port 5000 inside the container. `./npmw run dev`
(and `run preview`) publish it on `127.0.0.1:5173` of the host; other
npmw commands publish nothing, so `./npmw test` works while a dev server
is running. The dev server proxies `/ws` (with upgrade) and `/healthz` to
the Paranoia server on the host, `http://host.containers.internal:8000`
by default. Start the server as in [server/README.md](../../server/README.md);
it must listen on `0.0.0.0` (the compose setup and the README command
do), because a server bound to `127.0.0.1` is not reachable from the
container.

## Configuration

| Variable            | Default                      | Meaning                  |
|---------------------|------------------------------|--------------------------|
| `VITE_PROXY_TARGET` | `http://host.containers.internal:8000` | dev-server proxy target (npmw) |
| `NPMW_PORT`         | `5173`                       | host port for `run dev` / `run preview` |
| `NPMW_BIND`         | `127.0.0.1`                  | host address; `0.0.0.0` exposes it to the LAN |
| `VITE_WS_URL`       | derived from `location`      | override, e.g. `ws://h:8000/ws` |

`VITE_WS_URL` is baked in at build time. By default the client connects
to `ws(s)://<page host>/ws?room=<room>`, where the room is the page's
`?room=` query parameter (default `lobby`).

## Serving `dist/`

`dist/` is plain static files (`index.html` plus hashed assets). Serve it
from any static server; the reverse proxy must forward `/ws` (WebSocket
upgrade) and optionally `/healthz` to the Paranoia server on the same
origin, so no build-time URL is needed. Quick local check:

```sh
./npmw run preview
```

## Layout

| Path                      | Role                                       |
|---------------------------|--------------------------------------------|
| `src/lib/state.js`        | reducer: frames and omit list -> state     |
| `src/lib/protocol.js`     | ws URL derivation, `say` frame             |
| `src/lib/connection.js`   | WebSocket with backoff reconnect           |
| `src/lib/theme.js`        | theme choice (light/dark/auto) logic       |
| `src/lib/*.test.js`       | Vitest unit tests (core logic only)        |
| `src/App.svelte`, `src/components/` | UI wiring and presentation       |

The header has a Light / Dark / Auto theme selector (`data-bs-theme` on
`<html>`; Auto follows the OS, the choice is kept in `localStorage` and
applied by an inline script in `index.html` before first paint).

On reconnect the server assigns a new nickname and replays history, so
each `welcome` fully resets the timeline; the omit selection is kept only
for users still present.
