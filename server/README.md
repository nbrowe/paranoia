# Paranoia server

FastAPI + uvicorn backend implementing [docs/protocol.md](../docs/protocol.md).
State is in memory only.

## Setup

```sh
cd server
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime only: requirements.txt
```

## Run

```sh
.venv/bin/uvicorn paranoia.app:app --host 0.0.0.0 --port 8000
```

- `GET /healthz` returns `{"status": "ok"}`.
- `ws://host:8000/ws?room=lobby` (room defaults to `lobby`).

## Test

```sh
.venv/bin/pytest
```

## Configuration

| Variable                 | Default | Meaning                          |
|--------------------------|---------|----------------------------------|
| `PARANOIA_HISTORY_SIZE`  | `100`   | messages retained per room       |
| `PARANOIA_MAX_TEXT`      | `500`   | max characters per message       |
| `PARANOIA_DEFAULT_ROOM`  | `lobby` | room used when `?room=` is absent|

Host and port are uvicorn options.

## Layout and extending

| Module            | Role                                              |
|-------------------|---------------------------------------------------|
| `config.py`       | `Settings` from environment                       |
| `nicknames.py`    | pool from `data/pokemon.txt`, random unused pick  |
| `messages.py`     | `Message`, `mask()`, `render()` (pure, per-recipient) |
| `protocol.py`     | client frame validation and error codes           |
| `storage.py`      | `HistoryStore` interface + in-memory backend      |
| `room.py`         | `Room` (users, broadcast) and `Hub` (room registry) |
| `app.py`          | FastAPI app factory and `/ws` transport           |

- New storage backend (e.g. SQLite): subclass `HistoryStore` in
  `storage.py` (`append` assigns the per-room id; `recent` returns the
  retained messages) and pass it to `create_app(store=...)`.
- New client message type: extend `protocol.py` parsing and dispatch in
  `app.py::_serve`, and document it in `docs/protocol.md`.
- Changes to who may read what belong in `messages.render()`.

## Known limitations

Rooms are never evicted once created, and there is no auth, rate limiting
or origin check.
