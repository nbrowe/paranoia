"""WebSocket transport: connect and pump server frames into a queue.

Purpose: isolate the sync `websockets` client and its reader thread.
Scope: one connection; frames are decoded via logic.parse_frame.
Limitations: no reconnect. On disconnect a synthetic
{"type": "_closed", "reason": ...} frame is queued, then the thread ends.
"""

import queue
import threading
from urllib.parse import quote

from websockets.exceptions import ConnectionClosed
from websockets.sync.client import connect

from . import logic


def open_connection(url, room):
    """Connect to `url` joining `room`; returns the websocket."""
    sep = "&" if "?" in url else "?"
    return connect(f"{url}{sep}room={quote(room)}")


def _pump(ws, frames):
    """Reader-thread body: queue decoded frames until the socket closes."""
    reason = "connection closed"
    try:
        for raw in ws:
            frame = logic.parse_frame(raw)
            if frame is not None:
                frames.put(frame)
    except ConnectionClosed as exc:
        reason = str(exc)
    frames.put({"type": "_closed", "reason": reason})


def start_reader(ws):
    """Start the reader thread; returns the queue frames arrive on."""
    frames = queue.Queue()
    threading.Thread(target=_pump, args=(ws, frames), daemon=True).start()
    return frames
