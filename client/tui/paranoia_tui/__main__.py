"""Entrypoint: `python -m paranoia_tui [--url URL] [--room NAME]`.

Purpose: parse arguments, connect, run the curses UI, report exit status.
Scope: one connection per process.
Limitations: no reconnect; exit code 1 if the server could not be reached
or the connection dropped.
"""

import argparse
import sys

from websockets.exceptions import WebSocketException

from . import net, ui


def main(argv=None):
    """Parse args, connect and run the UI; returns a process exit code."""
    parser = argparse.ArgumentParser(prog="paranoia_tui")
    parser.add_argument("--url", default="ws://localhost:8000/ws")
    parser.add_argument("--room", default="lobby")
    args = parser.parse_args(argv)
    try:
        ws = net.open_connection(args.url, args.room)
    except (OSError, WebSocketException) as exc:
        print(f"cannot connect to {args.url}: {exc}", file=sys.stderr)
        return 1
    frames = net.start_reader(ws)
    dropped = ui.run(ws, frames)
    ws.close()
    if dropped:
        print(dropped, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
