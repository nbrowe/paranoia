/*
 * Slash commands for the single message input (docs/protocol.md, "Client
 * UX conventions"): /help, /omit, /me, /kick, /topic; `//` sends a literal
 * `/`; unknown commands are reported locally. parseInput is pure text
 * parsing; handleInput applies the result to the chat state and returns
 * the wire frames to send. Pure JS, no Svelte or DOM.
 * Limitations: `/topic -` clears the topic, so a topic that is just "-"
 * cannot be set; permission checks (/kick needs the operator) are left to
 * the server's error frames.
 */
import { buildSay, buildTopic, buildKick } from './protocol.js'
import { addNotices, setOmit } from './state.js'

export const HELP_LINES = [
  'Commands:',
  '/help - show this list',
  '/omit [nick...] - hide your messages from these users; alone, clear',
  '/me <text> - send an action ("* nick text")',
  '/kick <nick> [reason] - remove a user (room operator only)',
  '/topic [text] - set the topic; alone, show it; "-", clear it',
  '//text - send a message that starts with a slash',
]

/**
 * Parse one line of input.
 * @param {string} input raw input text
 * @returns {{cmd: string, args: string}} cmd is 'say' for plain text
 *   (args is the text to send, `//` unescaped) or the lowercased command
 *   name; args is everything after the command, trimmed
 */
export function parseInput(input) {
  if (input.startsWith('//')) return { cmd: 'say', args: input.slice(1) }
  if (!input.startsWith('/')) return { cmd: 'say', args: input }
  const [, cmd, args] = /^\/(\S*)\s*(.*)$/s.exec(input)
  return { cmd: cmd.toLowerCase(), args: args.trim() }
}

/**
 * Split "first rest of it" into the first word and the remainder.
 * @param {string} args argument string
 * @returns {string[]} first word, trimmed remainder
 */
function splitFirst(args) {
  const [, first, rest] = /^(\S*)\s*(.*)$/s.exec(args)
  return [first, rest]
}

/**
 * Report a local usage error.
 * @param {object} state chat state
 * @param {string} text message
 * @returns {{state: object, frames: string[]}} result as for handleInput
 */
function fail(state, text) {
  return { state: addNotices(state, 'error', [text]), frames: [] }
}

/**
 * Apply /omit: set the sticky list, reporting nicks that are not here.
 * @param {object} state chat state
 * @param {string} args space-separated nicks (empty clears)
 * @returns {{state: object, frames: string[]}} result as for handleInput
 */
function runOmit(state, args) {
  const nicks = args.split(/\s+/).filter(Boolean)
  const next = setOmit(state, nicks)
  const missing = nicks.filter((n) => !next.omit.includes(n))
  if (!missing.length) return { state: next, frames: [] }
  return fail(next, `Not omitted (absent, or you): ${missing.join(', ')}`)
}

/**
 * Apply /topic: show the topic locally, clear it (`-`), or set it.
 * @param {object} state chat state
 * @param {string} args new topic, `-` to clear, or empty to show
 * @returns {{state: object, frames: string[]}} result as for handleInput
 */
function runTopic(state, args) {
  if (args === '-') return { state, frames: [buildTopic('')] }
  if (args) return { state, frames: [buildTopic(args)] }
  const line = state.topic ? `Topic: ${state.topic}` : 'No topic is set'
  return { state: addNotices(state, 'info', [line]), frames: [] }
}

/**
 * Run one line of input against the state.
 * @param {object} state chat state
 * @param {string} input raw input text
 * @returns {{state: object, frames: string[]}} new state (local notices,
 *   omit list) and the JSON frames to send, in order
 */
export function handleInput(state, input) {
  const { cmd, args } = parseInput(input)
  switch (cmd) {
    case 'say': {
      const f = buildSay(args, state.omit)
      return { state, frames: f ? [f] : [] }
    }
    case 'help':
      return { state: addNotices(state, 'info', HELP_LINES), frames: [] }
    case 'omit':
      return runOmit(state, args)
    case 'me':
      return args ? { state, frames: [buildSay(args, state.omit, true)] }
        : fail(state, 'Usage: /me <text>')
    case 'kick': {
      const [nick, reason] = splitFirst(args)
      return nick ? { state, frames: [buildKick(nick, reason)] }
        : fail(state, 'Usage: /kick <nick> [reason]')
    }
    case 'topic':
      return runTopic(state, args)
    default:
      return fail(state, `Unknown command: /${cmd} (try /help)`)
  }
}
