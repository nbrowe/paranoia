/*
 * Unit tests for the chat state reducer (state.js).
 * Scope: frame handling, omit list rules, status changes, timeline cap.
 * Limitations: no component or DOM tests.
 */
import { describe, it, expect } from 'vitest'
import {
  initialState, applyFrame, setStatus, toggleOmit, clearOmit, MAX_ITEMS,
} from './state.js'

const msg = (id, extra = {}) => ({
  id, ts: 1, sender: 'gengar', text: `t${id}`, masked: false, ...extra,
})

/**
 * Build a state that has received a welcome frame.
 * @param {object} [over] welcome field overrides
 * @returns {object} state
 */
function welcomed(over = {}) {
  return applyFrame(initialState(), {
    type: 'welcome', nick: 'pikachu', room: 'lobby',
    users: ['pikachu', 'gengar', 'mew'], history: [], ...over,
  })
}

describe('welcome', () => {
  it('sets identity, users and history', () => {
    const s = welcomed({ history: [msg(1), msg(2, { masked: true })] })
    expect(s.status).toBe('open')
    expect(s.nick).toBe('pikachu')
    expect(s.users).toEqual(['gengar', 'mew', 'pikachu'])
    const kinds = s.items.map((i) => i.kind)
    expect(kinds).toEqual(['message', 'message', 'notice'])
    expect(s.items[1].masked).toBe(true)
  })

  it('resets timeline and prunes omit on reconnect', () => {
    let s = welcomed()
    s = toggleOmit(s, 'gengar')
    s = toggleOmit(s, 'mew')
    s = applyFrame(s, { type: 'message', ...msg(5) })
    s = applyFrame(s, {
      type: 'welcome', nick: 'eevee', room: 'lobby',
      users: ['eevee', 'mew'], history: [],
    })
    expect(s.nick).toBe('eevee')
    expect(s.omit).toEqual(['mew'])
    expect(s.items.filter((i) => i.kind === 'message')).toHaveLength(0)
  })
})

describe('join and leave', () => {
  it('adds and removes users with notices', () => {
    let s = welcomed()
    s = applyFrame(s, { type: 'join', nick: 'abra' })
    expect(s.users).toContain('abra')
    expect(s.items.at(-1).text).toBe('abra joined')
    s = applyFrame(s, { type: 'leave', nick: 'abra' })
    expect(s.users).not.toContain('abra')
    expect(s.items.at(-1).text).toBe('abra left')
  })

  it('does not duplicate an already-listed user', () => {
    const s = applyFrame(welcomed(), { type: 'join', nick: 'mew' })
    expect(s.users.filter((n) => n === 'mew')).toHaveLength(1)
  })

  it('prunes a departed user from the omit list', () => {
    let s = toggleOmit(welcomed(), 'gengar')
    s = applyFrame(s, { type: 'leave', nick: 'gengar' })
    expect(s.omit).toEqual([])
  })
})

describe('message and error', () => {
  it('keeps masked flag and omitted list', () => {
    let s = welcomed()
    s = applyFrame(s, { type: 'message', ...msg(7, { masked: true }) })
    s = applyFrame(s, {
      type: 'message', ...msg(8, { sender: 'pikachu', omitted: ['mew'] }),
    })
    expect(s.items.at(-2).masked).toBe(true)
    expect(s.items.at(-1).omitted).toEqual(['mew'])
  })

  it('renders errors as error notices', () => {
    const s = applyFrame(welcomed(), {
      type: 'error', code: 'bad_text', message: 'too long',
    })
    expect(s.items.at(-1)).toMatchObject({
      kind: 'notice', level: 'error', text: 'bad_text: too long',
    })
  })

  it('ignores unknown frame types', () => {
    const s = welcomed()
    expect(applyFrame(s, { type: 'typing', nick: 'x' })).toBe(s)
  })

  it('caps the timeline and keeps keys unique', () => {
    let s = welcomed()
    for (let i = 1; i <= MAX_ITEMS + 20; i++) {
      s = applyFrame(s, { type: 'message', ...msg(i) })
    }
    expect(s.items).toHaveLength(MAX_ITEMS)
    expect(new Set(s.items.map((i) => i.key)).size).toBe(MAX_ITEMS)
  })
})

describe('omit list', () => {
  it('toggles users in sorted order', () => {
    let s = toggleOmit(welcomed(), 'mew')
    s = toggleOmit(s, 'gengar')
    expect(s.omit).toEqual(['gengar', 'mew'])
    s = toggleOmit(s, 'mew')
    expect(s.omit).toEqual(['gengar'])
  })

  it('ignores own nick and absent users', () => {
    const s = welcomed()
    expect(toggleOmit(s, 'pikachu').omit).toEqual([])
    expect(toggleOmit(s, 'ghost').omit).toEqual([])
  })

  it('clears', () => {
    const s = clearOmit(toggleOmit(welcomed(), 'mew'))
    expect(s.omit).toEqual([])
  })
})

describe('status', () => {
  it('announces a drop from open exactly once', () => {
    let s = setStatus(welcomed(), 'disconnected')
    const count = s.items.length
    s = setStatus(s, 'connecting')
    s = setStatus(s, 'disconnected')
    expect(s.items).toHaveLength(count)
    expect(s.items.at(-1).text).toMatch(/Disconnected/)
  })
})
