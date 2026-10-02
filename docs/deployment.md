# Deployment

The server ships as a container image built from `server/Containerfile`
(Python 3.12 slim, non-root user `paranoia`, uvicorn on `0.0.0.0:8000`).
State is in memory, so restarting the container clears all rooms.

## Build

Run from the repo root. Use `--format docker` with Podman, otherwise the
default OCI format silently drops the `HEALTHCHECK`.

```sh
podman build --format docker -t paranoia-server -f server/Containerfile server
docker build -t paranoia-server -f server/Containerfile server
```

## Run

```sh
podman run -d --name paranoia -p 8000:8000 paranoia-server
docker run -d --name paranoia -p 8000:8000 paranoia-server
```

Or with Compose (`podman-compose` or `docker compose`), which builds and
starts the server on port 8000:

```sh
podman-compose up -d --build
docker compose up -d --build
```

Clients connect to `ws://<host>:8000/ws?room=lobby`; see
[protocol.md](protocol.md).

## Health check

`GET /healthz` returns `200 {"status": "ok"}`. The image's `HEALTHCHECK`
calls it every 30 s using the Python stdlib (no curl in the image).

```sh
podman healthcheck run paranoia    # exit 0 when healthy
podman ps                          # STATUS shows (healthy)
docker inspect --format '{{.State.Health.Status}}' paranoia
```

## Environment variables

Pass with `-e NAME=value` or the `environment:` block in `compose.yaml`.

| Variable                 | Default | Meaning                           |
|--------------------------|---------|-----------------------------------|
| `PARANOIA_HISTORY_SIZE`  | `100`   | messages retained per room        |
| `PARANOIA_MAX_TEXT`      | `500`   | max characters per message        |
| `PARANOIA_DEFAULT_ROOM`  | `lobby` | room used when `?room=` is absent |

The listen address is fixed at `0.0.0.0:8000` inside the container; change
the published port instead (`-p 9000:8000`). Rootless Podman needs no
extra privileges for ports above 1023.

## Notes

- There is no TLS, auth or rate limiting; put a reverse proxy in front for
  anything beyond a trusted network.
- The web client is not containerized yet.
