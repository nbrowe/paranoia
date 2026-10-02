"""WebSocket connection running in a background reader thread.

Purpose: decouple blocking network I/O from the Tk loop. The reader thread
only puts events on a thread-safe queue; the UI drains it via `poll()`.
Scope: one connection, text JSON frames per docs/protocol.md.
Limitations: no reconnect; `send` after close raises OSError-family errors.
"""

import json
import queue
import threading
from urllib.parse import urlencode

from websockets.sync.client import connect


def build_url(url, room):
    """Append the `room` query parameter to a ws:// URL."""
    sep = "&" if "?" in url else "?"
    return url + sep + urlencode({"room": room})


class Connection:
    """Chat connection. Events are ("frame", dict) and ("closed", reason)."""

    def __init__(self, url, room):
        """Remember the target; call `start()` to connect."""
        self.url = build_url(url, room)
        self.events = queue.Queue()
        self._ws = None
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        """Start the reader thread (connects inside the thread)."""
        self._thread.start()

    def _run(self):
        """Thread body: connect, then enqueue every frame until closed."""
        try:
            self._ws = connect(self.url)
            for raw in self._ws:
                self.events.put(("frame", json.loads(raw)))
            reason = "connection closed by server"
        except Exception as exc:  # reported to the UI, never raised
            reason = f"connection lost: {exc}"
        self.events.put(("closed", reason))

    def send(self, frame):
        """Send a frame (safe to call from the UI thread)."""
        self._ws.send(json.dumps(frame))

    def poll(self):
        """Return all queued events without blocking."""
        out = []
        while True:
            try:
                out.append(self.events.get_nowait())
            except queue.Empty:
                return out

    def close(self):
        """Close the socket, which ends the reader thread."""
        if self._ws is not None:
            self._ws.close()
