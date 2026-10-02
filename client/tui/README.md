# Paranoia TUI

Curses client for the Paranoia server ([protocol](../../docs/protocol.md)).

## Run

From the repo root (any directory works):

```sh
./paranoia tui [--url ws://localhost:8000/ws] [--room lobby]
```

The launcher creates `client/tui/.venv` and installs `requirements.txt` on
first run (and again whenever it changes), then execs the client.
`PARANOIA_URL` sets the default `--url`.

## Manual setup

```sh
cd client/tui
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt   # runtime only: requirements.txt
.venv/bin/python -m paranoia_tui [--url ws://localhost:8000/ws] [--room lobby]
```

Layout: message pane, user list (right, terminals 60+ columns wide), a
status line (own nick, active omit list) and the input line.

## Commands

| Input             | Effect                                              |
|-------------------|-----------------------------------------------------|
| `text`            | send as `say`, with the current omit list           |
| `/omit alice bob` | set the sticky omit list                            |
| `/omit`           | clear the omit list                                 |
| `/quit`           | exit                                                |

Masked messages are dimmed and tagged `[masked]`. Your own messages show
`[hidden from: ...]` when anyone was omitted. After a disconnect, press
any key to exit (the reason is printed and the exit code is 1).

## Test

```sh
.venv/bin/pytest
```

Only the pure logic in `paranoia_tui/logic.py` is tested.

## Layout

| Module     | Role                                            |
|------------|-------------------------------------------------|
| `logic.py` | pure: command parsing, frames, formatting       |
| `net.py`   | websocket connect and reader thread             |
| `ui.py`    | curses drawing and key handling                 |
| `__main__.py` | argument parsing and wiring                  |

## Limitations

No scrollback, no cursor movement within the input line, no reconnect.
