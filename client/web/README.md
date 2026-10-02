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
podman run --rm -v "$PWD":/app:Z -w /app docker.io/library/node:24-alpine \
  sh -c 'npm ci && npm test'
```

## Dev server and the backend

The dev server proxies `/ws` (with upgrade) and `/healthz` to
`VITE_PROXY_TARGET` (default `http://localhost:8000`). Start the server
as in [server/README.md](../../server/README.md). Because `localhost`
inside the container is the container itself, share the host network:

```sh
PODMAN_ARGS="--network host" ./npmw run dev
```

or keep the default networking and point at the host instead:

```sh
VITE_PROXY_TARGET=http://host.containers.internal:8000 ./npmw run dev
```

(the server must then listen on `0.0.0.0`, as in its README).

## Configuration

| Variable            | Default                      | Meaning                  |
|---------------------|------------------------------|--------------------------|
| `VITE_PROXY_TARGET` | `http://localhost:8000`      | dev-server proxy target  |
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
| `src/lib/*.test.js`       | Vitest unit tests (core logic only)        |
| `src/App.svelte`, `src/components/` | UI wiring and presentation       |

On reconnect the server assigns a new nickname and replays history, so
each `welcome` fully resets the timeline; the omit selection is kept only
for users still present.
