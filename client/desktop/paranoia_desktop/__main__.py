"""Entry point: `python -m paranoia_desktop [--url URL] [--room NAME]`.

Purpose: parse arguments, start the connection thread, run the Tk loop.
Scope: argument handling only.
Limitations: none beyond those of ui.py.
"""

import argparse
import tkinter as tk

from .net import Connection
from .ui import App


def main():
    """Parse arguments and run the client."""
    p = argparse.ArgumentParser(prog="paranoia_desktop")
    p.add_argument("--url", default="ws://localhost:8000/ws")
    p.add_argument("--room", default="lobby")
    args = p.parse_args()
    conn = Connection(args.url, args.room)
    conn.start()
    root = tk.Tk()
    App(root, conn)
    root.mainloop()


if __name__ == "__main__":
    main()
