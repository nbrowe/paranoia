/*
 * WebSocket connection with automatic reconnect and exponential backoff.
 * Scope: open/close lifecycle, JSON frame decoding, status callbacks.
 * Limitations: no heartbeat; the server assigns a new nick on every
 * connection, so callers must treat each `welcome` as a full reset.
 */

/**
 * Reconnect delay for the given attempt number (0-based).
 * @param {number} attempt consecutive failed attempts so far
 * @returns {number} delay in milliseconds, capped at 10 seconds
 */
export function backoffDelay(attempt) {
  return Math.min(10000, 500 * 2 ** attempt)
}

/**
 * Open a self-reconnecting connection.
 * @param {object} opts
 * @param {string} opts.url WebSocket URL
 * @param {(frame: object) => void} opts.onFrame called per server frame
 * @param {(status: string) => void} opts.onStatus connecting|open|disconnected
 * @param {typeof WebSocket} [opts.WS] WebSocket constructor (for tests)
 * @returns {{send: (text: string) => boolean, close: () => void}} handle
 */
export function connect({ url, onFrame, onStatus, WS = WebSocket }) {
  let ws = null
  let timer = null
  let attempt = 0
  let closed = false

  /** Create the socket and wire its handlers. */
  function open() {
    onStatus('connecting')
    ws = new WS(url)
    ws.onopen = () => onStatus('open')
    ws.onmessage = (e) => {
      const frame = JSON.parse(e.data)
      // Reset only on welcome so a room_full close loop keeps backing off.
      if (frame.type === 'welcome') attempt = 0
      onFrame(frame)
    }
    ws.onclose = () => {
      if (closed) return
      onStatus('disconnected')
      timer = setTimeout(open, backoffDelay(attempt++))
    }
  }

  open()
  return {
    /** Send a text frame; false if the socket is not open. */
    send(text) {
      if (ws.readyState !== 1) return false  // 1 = OPEN
      ws.send(text)
      return true
    },
    /** Close for good and stop reconnecting. */
    close() {
      closed = true
      clearTimeout(timer)
      ws.close()
    },
  }
}
