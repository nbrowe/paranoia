/*
 * Unit tests for slash-command parsing and handling (commands.js).
 * Scope: parseInput cases, and handleInput's state changes and frames for
 * each command. Limitations: no DOM; server permission errors untested.
 */
import { describe, it, expect } from 'vitest'
import { parseInput, handleInput, HELP_LINES } from './commands.js'
import { initialState, applyFrame, toggleOmit } from './state.js'

/**
 * Build a connected state with a few users and a topic.
 * @returns {object} state
 */
function room() {
  return applyFrame(initialState(), {
    type: 'welcome', nick: 'pikachu', room: 'lobby', topic: 'cake',
    op: 'mew', users: ['pikachu', 'gengar', 'mew'], history: [],
  })
}

/**
 * Parse the frames of a handleInput result.
 * @param {{frames: string[]}} r result
 * @returns {object[]} frame objects
 */
const frames = (r) => r.frames.map((f) => JSON.parse(f))

/**
 * Newest timeline item of a handleInput result.
 * @param {{state: object}} r result
 * @returns {object} item
 */
const last = (r) => r.state.items.at(-1)

describe('parseInput', () => {
  it('plain text is a say', () => {
    expect(parseInput('hello /me')).toEqual({ cmd: 'say', args: 'hello /me' })
  })

  it('// sends a literal slash', () => {
    expect(parseInput('//shrug')).toEqual({ cmd: 'say', args: '/shrug' })
    expect(parseInput('//')).toEqual({ cmd: 'say', args: '/' })
  })

  it('splits command and arguments, lowercasing the command', () => {
    expect(parseInput('/ME  waves  hello ')).toEqual(
      { cmd: 'me', args: 'waves  hello' })
    expect(parseInput('/help')).toEqual({ cmd: 'help', args: '' })
  })

  it('a bare slash is an empty (unknown) command', () => {
    expect(parseInput('/')).toEqual({ cmd: '', args: '' })
    expect(parseInput('/ x').cmd).toBe('')
  })
})

describe('say', () => {
  it('sends text with the current omit list', () => {
    const s = toggleOmit(room(), 'gengar')
    const r = handleInput(s, '  hi there ')
    expect(frames(r)).toEqual([
      { type: 'say', text: 'hi there', omit: ['gengar'] }])
  })

  it('// sends the text with one slash', () => {
    const r = handleInput(room(), '//omit me')
    expect(frames(r)[0].text).toBe('/omit me')
  })

  it('blank input sends nothing', () => {
    expect(handleInput(room(), '   ').frames).toEqual([])
  })
})

describe('/help', () => {
  it('lists the commands as local notices, sending nothing', () => {
    const s = room()
    const r = handleInput(s, '/help')
    expect(r.frames).toEqual([])
    const added = r.state.items.slice(s.items.length).map((i) => i.text)
    expect(added).toEqual(HELP_LINES)
    for (const c of ['/omit', '/me', '/kick', '/topic', '//']) {
      expect(added.join('\n')).toContain(c)
    }
  })
})

describe('/omit', () => {
  it('sets the list to the named users', () => {
    const r = handleInput(room(), '/omit mew gengar')
    expect(r.state.omit).toEqual(['gengar', 'mew'])
    expect(r.frames).toEqual([])
  })

  it('replaces the previous selection', () => {
    const s = toggleOmit(room(), 'gengar')
    expect(handleInput(s, '/omit mew').state.omit).toEqual(['mew'])
  })

  it('alone clears it', () => {
    const s = toggleOmit(room(), 'gengar')
    const r = handleInput(s, '/omit')
    expect(r.state.omit).toEqual([])
    expect(r.state.items).toHaveLength(s.items.length)
  })

  it('reports unknown nicks and yourself', () => {
    const r = handleInput(room(), '/omit mew nobody pikachu')
    expect(r.state.omit).toEqual(['mew'])
    expect(last(r).level).toBe('error')
    expect(last(r).text).toContain('nobody, pikachu')
  })
})

describe('/me', () => {
  it('sends an action say with the omit list', () => {
    const s = toggleOmit(room(), 'mew')
    expect(frames(handleInput(s, '/me waves  hi'))).toEqual([
      { type: 'say', text: 'waves  hi', omit: ['mew'], action: true }])
  })

  it('needs text', () => {
    const r = handleInput(room(), '/me')
    expect(r.frames).toEqual([])
    expect(last(r).text).toBe('Usage: /me <text>')
  })
})

describe('/kick', () => {
  it('sends nick and reason', () => {
    expect(frames(handleInput(room(), '/kick gengar being rude'))).toEqual([
      { type: 'kick', nick: 'gengar', reason: 'being rude' }])
  })

  it('reason is optional, nick required', () => {
    expect(frames(handleInput(room(), '/kick gengar'))[0].reason).toBe('')
    const r = handleInput(room(), '/kick')
    expect(r.frames).toEqual([])
    expect(last(r).level).toBe('error')
  })
})

describe('/topic', () => {
  it('with text sends a topic frame', () => {
    expect(frames(handleInput(room(), '/topic new  plan'))).toEqual([
      { type: 'topic', text: 'new  plan' }])
  })

  it('alone shows the current topic locally', () => {
    const r = handleInput(room(), '/topic')
    expect(r.frames).toEqual([])
    expect(last(r).text).toBe('Topic: cake')
    const none = applyFrame(room(), { type: 'topic', nick: 'mew', text: '' })
    expect(last(handleInput(none, '/topic')).text).toBe('No topic is set')
  })
})

describe('unknown commands', () => {
  it('are reported locally and not sent', () => {
    const r = handleInput(room(), '/dance now')
    expect(r.frames).toEqual([])
    expect(last(r)).toMatchObject({
      level: 'error', text: 'Unknown command: /dance (try /help)' })
  })
})
