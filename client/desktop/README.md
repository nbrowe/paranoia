# Paranoia desktop client (Tkinter)

Implements [docs/protocol.md](../../docs/protocol.md). Needs a Python with
`tkinter` (usually a separate system package, e.g. `tk` or
`python3-tkinter`; check with `python3 -c 'import tkinter'`).

## Run

From the repo root (any directory works):

```sh
./paranoia desktop [--url ws://localhost:8000/ws] [--room lobby]
```

The launcher creates `client/desktop/.venv` and installs `requirements.txt` on
first run (and again whenever it changes), then execs the client.
`PARANOIA_URL` sets the default `--url`.

## Manual setup

```sh
cd client/desktop
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime only: requirements.txt
.venv/bin/python -m paranoia_desktop [--url ws://localhost:8000/ws] [--room lobby]
```

## Usage

- Type a message and press Enter to send it.
- Omit users by selecting them in the user list (click, ctrl-click for
  several). The selection is the sticky omit list sent with every message;
  the status bar shows it. Omitted users see your text as `*`.
- `/omit alice bob` sets the omit list (selection follows), `/omit` clears it.
- Masked messages (you were omitted) are grey italic; your own messages
  show `(omitted: ...)`. Join/leave notices are green, errors red.
- On disconnect a red message appears; restart the client to reconnect.
- Omit names not currently in the room are kept but cannot be shown as
  selected in the list.

## Test

```sh
.venv/bin/pytest   # pure logic only
```

## Layout

| Module     | Role                                             |
|------------|--------------------------------------------------|
| `logic.py` | pure: parsing, frames, formatting, state         |
| `net.py`   | websocket reader thread + event queue            |
| `ui.py`    | Tk widgets; polls the queue with `after()`       |
| `__main__.py` | argument parsing and startup                  |
