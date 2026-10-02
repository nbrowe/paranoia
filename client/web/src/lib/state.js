/*
 * Chat state reducer: applies server frames (docs/protocol.md) and UI
 * actions to an immutable state object. Pure JS, no Svelte or DOM.
 * Scope: welcome/join/leave/message/topic/kick/op/error frames,
 * connection status, the sticky omit list, the room topic and operator,
 * user ordering (own nick first). A disconnect clears identity, users and
 * omit but keeps the timeline. A kick naming our own nick marks the state
 * `kicked` (the caller must then stop reconnecting). Limitations: the
 * timeline is capped at MAX_ITEMS entries; unknown frame types are
 * ignored (protocol forward compat).
 */

export const MAX_ITEMS = 500

/**
 * Build the state for a fresh, not-yet-connected client.
 * @returns {object} initial state
 */
export function initialState() {
  return {
    status: 'connecting',  // connecting | open | disconnected
    nick: null,
    room: null,
    users: [],
    items: [],             // timeline: messages and notices, oldest first
    omit: [],              // sticky omit list (subset of users)
    topic: '',             // room topic, '' if unset
    op: null,              // current room operator's nick
    kicked: false,         // true once we were kicked: do not reconnect
    seq: 0,               // counter for notice keys
  }
}

/**
 * Append a timeline item, assigning it a unique key and enforcing the cap.
 * @param {object} state current state
 * @param {object} item message or notice fields (without key)
 * @returns {object} new state
 */
function addItem(state, item) {
  const key = item.kind === 'message' ? `m${item.id}` : `n${state.seq}`
  const items = [...state.items, { ...item, key }].slice(-MAX_ITEMS)
  return { ...state, items, seq: state.seq + 1 }
}

/**
 * Build a notice timeline item.
 * @param {string} level Bootstrap-ish level: info or error
 * @param {string} text notice text
 * @returns {object} notice item
 */
function notice(level, text) {
  return { kind: 'notice', level, text }
}

/**
 * Convert a wire Message (or history entry) to a timeline item.
 * @param {object} m wire message
 * @returns {object} message item
 */
function messageItem(m) {
  const { id, ts, sender, text, masked, omitted, action } = m
  return {
    kind: 'message', id, ts, sender, text, masked, omitted,
    action: action === true,
  }
}

/**
 * Append local (client-generated) notices, one per line.
 * @param {object} state current state
 * @param {string} level info or error
 * @param {string[]} lines notice texts
 * @returns {object} new state
 */
export function addNotices(state, level, lines) {
  return lines.reduce((s, l) => addItem(s, notice(level, l)), state)
}

/**
 * Keep only omit entries that are present in the user list.
 * @param {string[]} omit omit selection
 * @param {string[]} users present nicknames
 * @returns {string[]} pruned selection
 */
export function pruneOmit(omit, users) {
  return omit.filter((n) => users.includes(n))
}

/**
 * Order users for display: own nick first, the rest alphabetical.
 * @param {string[]} users nicknames
 * @param {string|null} nick own nick
 * @returns {string[]} sorted copy
 */
export function sortUsers(users, nick) {
  const rest = users.filter((n) => n !== nick).sort()
  return users.includes(nick) ? [nick, ...rest] : rest
}

const frameHandlers = {
  /** Reset everything from the server's snapshot (new nick on reconnect). */
  welcome(state, f) {
    const base = {
      ...state,
      status: 'open',
      nick: f.nick,
      room: f.room,
      users: sortUsers(f.users, f.nick),
      omit: pruneOmit(state.omit, f.users),
      topic: f.topic ?? '',
      op: f.op ?? null,
      items: [],
      seq: 0,
    }
    const withHistory = f.history.reduce(
      (s, m) => addItem(s, messageItem(m)), base)
    return addItem(withHistory,
      notice('info', `Joined #${f.room} as ${f.nick}`))
  },

  /** Add a user and a notice. */
  join(state, f) {
    const users = state.users.includes(f.nick)
      ? state.users : sortUsers([...state.users, f.nick], state.nick)
    return addItem({ ...state, users }, notice('info', `${f.nick} joined`))
  },

  /** Remove a user, prune the omit list, add a notice. */
  leave(state, f) {
    const users = state.users.filter((n) => n !== f.nick)
    const omit = pruneOmit(state.omit, users)
    return addItem({ ...state, users, omit }, notice('info', `${f.nick} left`))
  },

  /** Append a chat message. */
  message(state, f) {
    return addItem(state, messageItem(f))
  },

  /** Store the new topic and announce who set it. */
  topic(state, f) {
    const text = f.text ?? ''
    const what = text ? `set the topic to: ${text}` : 'cleared the topic'
    return addItem({ ...state, topic: text },
      notice('info', `${f.nick} ${what}`))
  },

  /**
   * Announce a kick. The target leaves the user list; if that is us we go
   * offline for good (kicked) and show the reason.
   */
  kick(state, f) {
    const why = f.reason ? `: ${f.reason}` : ''
    if (f.nick === state.nick) {
      const gone = {
        ...state, status: 'disconnected', kicked: true, users: [], omit: [],
      }
      return addItem(gone,
        notice('error', `You were kicked by ${f.by}${why}`))
    }
    const users = state.users.filter((n) => n !== f.nick)
    const next = { ...state, users, omit: pruneOmit(state.omit, users) }
    return addItem(next,
      notice('info', `${f.nick} was kicked by ${f.by}${why}`))
  },

  /** Track the new room operator. */
  op(state, f) {
    return { ...state, op: f.nick }
  },

  /** Show a server error as a notice. */
  error(state, f) {
    return addItem(state, notice('error', `${f.code}: ${f.message}`))
  },
}

/**
 * Apply a server frame; unknown types leave the state unchanged.
 * @param {object} state current state
 * @param {object} frame parsed server frame
 * @returns {object} new state
 */
export function applyFrame(state, frame) {
  const handler = frameHandlers[frame.type]
  return handler ? handler(state, frame) : state
}

/**
 * Record a connection status change; announces an unexpected drop once.
 * Going disconnected clears nick, users and omit (they are stale until
 * the next welcome) but keeps the timeline readable.
 * @param {object} state current state
 * @param {string} status connecting | open | disconnected
 * @returns {object} new state
 */
export function setStatus(state, status) {
  if (status === state.status || state.kicked) return state
  const next = { ...state, status }
  if (status === 'disconnected') {
    Object.assign(next,
      { nick: null, users: [], omit: [], topic: '', op: null })
  }
  if (status === 'disconnected' && state.status === 'open') {
    return addItem(next, notice('error', 'Disconnected. Reconnecting...'))
  }
  return next
}

/**
 * Toggle a user in the sticky omit list (own nick and absent users ignored).
 * @param {object} state current state
 * @param {string} nick user to toggle
 * @returns {object} new state
 */
export function toggleOmit(state, nick) {
  if (nick === state.nick || !state.users.includes(nick)) return state
  const omit = state.omit.includes(nick)
    ? state.omit.filter((n) => n !== nick)
    : [...state.omit, nick].sort()
  return { ...state, omit }
}

/**
 * Replace the sticky omit list (own nick, absent users, duplicates dropped).
 * @param {object} state current state
 * @param {string[]} nicks wanted omit list
 * @returns {object} new state
 */
export function setOmit(state, nicks) {
  const wanted = new Set(nicks)
  const omit = state.users.filter((n) => n !== state.nick && wanted.has(n))
  return { ...state, omit: omit.sort() }
}

/**
 * Empty the sticky omit list.
 * @param {object} state current state
 * @returns {object} new state
 */
export function clearOmit(state) {
  return state.omit.length ? { ...state, omit: [] } : state
}
