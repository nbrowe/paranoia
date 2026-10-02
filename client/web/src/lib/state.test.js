/*
 * Unit tests for the chat state reducer (state.js).
 * Scope: frame handling (incl. topic, kick, op, action messages), omit
 * list rules, status changes, timeline cap.
 * Limitations: no component or DOM tests.
 */
import { describe, it, expect } from 'vitest'
import {
  initialState, applyFrame, setStatus, sortUsers, toggleOmit, clearOmit,
  setOmit, addNotices, MAX_ITEMS,
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
    expect(s.users).toEqual(['pikachu', 'gengar', 'mew'])
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

describe('sortUsers', () => {
  it('pins own nick first and sorts the rest', () => {
    expect(sortUsers(['gengar', 'mew', 'abra', 'zubat'], 'mew'))
      .toEqual(['mew', 'abra', 'gengar', 'zubat'])
  })

  it('sorts alone when own nick is absent', () => {
    expect(sortUsers(['mew', 'abra'], null)).toEqual(['abra', 'mew'])
  })

  it('keeps own nick first through welcome and join', () => {
    let s = welcomed({ nick: 'mew', users: ['gengar', 'mew', 'abra'] })
    expect(s.users).toEqual(['mew', 'abra', 'gengar'])
    s = applyFrame(s, { type: 'join', nick: 'aerodactyl' })
    expect(s.users).toEqual(['mew', 'abra', 'aerodactyl', 'gengar'])
  })
})

describe('disconnect', () => {
  it('clears nick, users and omit but keeps the timeline', () => {
    let s = toggleOmit(welcomed({ history: [msg(1)] }), 'mew')
    const before = s.items.length
    s = setStatus(s, 'disconnected')
    expect(s.nick).toBeNull()
    expect(s.users).toEqual([])
    expect(s.omit).toEqual([])
    expect(s.items).toHaveLength(before + 1)  // plus the drop notice
    expect(s.items[0].kind).toBe('message')
  })

  it('stays cleared while reconnecting, welcome restores', () => {
    let s = setStatus(welcomed(), 'disconnected')
    s = setStatus(s, 'connecting')
    expect(s.users).toEqual([])
    s = applyFrame(s, {
      type: 'welcome', nick: 'abra', room: 'lobby', users: ['abra'],
      history: [],
    })
    expect(s.nick).toBe('abra')
  })
})

describe('topic', () => {
  it('welcome carries topic and op, defaults when absent', () => {
    const s = welcomed({ topic: 'be careful', op: 'gengar' })
    expect([s.topic, s.op]).toEqual(['be careful', 'gengar'])
    const old = welcomed()
    expect([old.topic, old.op]).toEqual(['', null])
  })

  it('topic frame updates the header topic and adds a notice', () => {
    let s = applyFrame(welcomed(), {
      type: 'topic', nick: 'gengar', text: 'cake',
    })
    expect(s.topic).toBe('cake')
    expect(s.items.at(-1).text).toBe('gengar set the topic to: cake')
    s = applyFrame(s, { type: 'topic', nick: 'mew', text: '' })
    expect(s.topic).toBe('')
    expect(s.items.at(-1).text).toBe('mew cleared the topic')
  })

  it('a disconnect clears the topic and op', () => {
    const s = setStatus(welcomed({ topic: 't', op: 'mew' }), 'disconnected')
    expect([s.topic, s.op]).toEqual(['', null])
  })
})

describe('kick', () => {
  it('removes another user, prunes omit, adds a notice', () => {
    let s = toggleOmit(welcomed(), 'gengar')
    s = applyFrame(s, {
      type: 'kick', nick: 'gengar', by: 'mew', reason: 'spam',
    })
    expect(s.users).not.toContain('gengar')
    expect(s.omit).toEqual([])
    expect(s.kicked).toBe(false)
    expect(s.items.at(-1).text).toBe('gengar was kicked by mew: spam')
  })

  it('omits the colon when the reason is empty', () => {
    const s = applyFrame(welcomed(), {
      type: 'kick', nick: 'gengar', by: 'mew', reason: '',
    })
    expect(s.items.at(-1).text).toBe('gengar was kicked by mew')
  })

  it('kicking us shows the reason and goes offline for good', () => {
    let s = applyFrame(welcomed(), {
      type: 'kick', nick: 'pikachu', by: 'mew', reason: 'bye',
    })
    expect(s.kicked).toBe(true)
    expect(s.status).toBe('disconnected')
    const last = s.items.at(-1)
    expect(last.level).toBe('error')
    expect(last.text).toBe('You were kicked by mew: bye')
    const n = s.items.length
    s = setStatus(s, 'disconnected')  // the socket close that follows
    s = setStatus(s, 'connecting')
    expect(s.items).toHaveLength(n)
    expect(s.status).toBe('disconnected')
  })
})

describe('op', () => {
  it('tracks the new operator without a notice', () => {
    const s0 = welcomed({ op: 'gengar' })
    const s = applyFrame(s0, { type: 'op', nick: 'mew' })
    expect(s.op).toBe('mew')
    expect(s.items).toHaveLength(s0.items.length)
  })
})

describe('action messages', () => {
  it('keeps the action flag, false when absent', () => {
    let s = welcomed()
    s = applyFrame(s, { type: 'message', ...msg(1, { action: true }) })
    s = applyFrame(s, { type: 'message', ...msg(2) })
    expect(s.items.at(-2).action).toBe(true)
    expect(s.items.at(-1).action).toBe(false)
  })
})

describe('setOmit and addNotices', () => {
  it('setOmit keeps present, non-self nicks, sorted and unique', () => {
    const s = setOmit(welcomed(), ['mew', 'pikachu', 'nobody', 'gengar', 'mew'])
    expect(s.omit).toEqual(['gengar', 'mew'])
  })

  it('addNotices appends one notice per line with unique keys', () => {
    const s = addNotices(welcomed(), 'error', ['a', 'b'])
    const [a, b] = s.items.slice(-2)
    expect([a.text, b.text, a.level]).toEqual(['a', 'b', 'error'])
    expect(a.key).not.toBe(b.key)
  })
})
