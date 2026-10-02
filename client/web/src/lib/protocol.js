/*
 * Wire helpers for docs/protocol.md: WebSocket URL derivation and
 * client frame construction. Pure JS, no Svelte or DOM.
 * Scope: URL building and the say, topic and kick frames. Limitations:
 * text length is validated by the server, not here.
 */

/**
 * Derive the WebSocket URL from the page location.
 * A Vite env override (VITE_WS_URL, e.g. ws://host:8000/ws) replaces the
 * scheme/host/path; the room comes from the page's ?room= (default lobby).
 * @param {{protocol: string, host: string, search: string}} loc location
 * @param {string} [override] value of VITE_WS_URL
 * @returns {string} ws:// or wss:// URL
 */
export function wsUrl(loc, override) {
  const scheme = loc.protocol === 'https:' ? 'wss:' : 'ws:'
  const url = new URL(override || `${scheme}//${loc.host}/ws`)
  const room = new URLSearchParams(loc.search).get('room') || 'lobby'
  url.searchParams.set('room', room)
  return url.toString()
}

/**
 * Build a `say` frame as a JSON string.
 * @param {string} text raw input text
 * @param {string[]} omit nicknames that must not read the message
 * @param {boolean} [action] true for a /me message
 * @returns {string|null} JSON text, or null if the text is blank
 */
export function buildSay(text, omit, action = false) {
  const trimmed = text.trim()
  if (!trimmed) return null
  const frame = { type: 'say', text: trimmed, omit }
  if (action) frame.action = true
  return JSON.stringify(frame)
}

/**
 * Build a `topic` frame; empty text clears the topic.
 * @param {string} text new topic
 * @returns {string} JSON text
 */
export function buildTopic(text) {
  return JSON.stringify({ type: 'topic', text: text.trim() })
}

/**
 * Build a `kick` frame.
 * @param {string} nick user to remove
 * @param {string} [reason] optional reason
 * @returns {string} JSON text
 */
export function buildKick(nick, reason = '') {
  return JSON.stringify({ type: 'kick', nick, reason: reason.trim() })
}
