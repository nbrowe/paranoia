/*
 * Display-only user markers for the user list, IRC style: `@` before the
 * room operator's nick, `*` after your own (`@nick*` for both), plus a
 * spoken description for tooltips and assistive tech. Pure JS, no Svelte
 * or DOM. Limitations: markers are never part of any nick used for logic
 * (omit, toggling); callers keep passing the bare nick around.
 */

/**
 * Markers to print around a nick.
 * @param {string} u bare nick
 * @param {string|null} me our own nick
 * @param {string|null} op the room operator's nick
 * @returns {{pre: string, post: string}} `@` before for the operator, `*`
 *   after for ourselves; empty strings otherwise
 */
export function marks(u, me, op) {
  return { pre: u === op ? '@' : '', post: u === me ? '*' : '' }
}

/**
 * Full description of a user for tooltips and assistive tech.
 * @param {string} u bare nick
 * @param {string|null} me our own nick
 * @param {string|null} op the room operator's nick
 * @returns {string} e.g. "pikachu (you, operator)", or the bare nick
 */
export function describe(u, me, op) {
  const words = [u === me && 'you', u === op && 'operator'].filter(Boolean)
  return words.length ? `${u} (${words.join(', ')})` : u
}
