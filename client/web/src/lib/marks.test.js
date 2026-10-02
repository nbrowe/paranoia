/*
 * Vitest: user-list markers (lib/marks.js) and their reducer inputs.
 * Scope: `*` own, `@` operator, both, neither; descriptions; the op
 * moving on an `op` frame, a leave and a kick of the operator.
 * Limitations: the Svelte rendering is covered by the e2e suite.
 */
import { describe as suite, it, expect } from 'vitest'
import { marks, describe } from './marks.js'
import { initialState, applyFrame } from './state.js'

suite('marks', () => {
  it('marks self, operator, both and neither', () => {
    expect(marks('pikachu', 'pikachu', 'gengar')).toEqual({ pre: '', post: '*' })
    expect(marks('gengar', 'pikachu', 'gengar')).toEqual({ pre: '@', post: '' })
    expect(marks('pikachu', 'pikachu', 'pikachu'))
      .toEqual({ pre: '@', post: '*' })
    expect(marks('mew', 'pikachu', 'gengar')).toEqual({ pre: '', post: '' })
    expect(marks('mew', null, null)).toEqual({ pre: '', post: '' })
  })

  it('describes with words, bare nick when unmarked', () => {
    expect(describe('pikachu', 'pikachu', 'pikachu'))
      .toBe('pikachu (you, operator)')
    expect(describe('gengar', 'pikachu', 'gengar')).toBe('gengar (operator)')
    expect(describe('pikachu', 'pikachu', 'gengar')).toBe('pikachu (you)')
    expect(describe('mew', 'pikachu', 'gengar')).toBe('mew')
  })
})

suite('operator tracking', () => {
  const welcome = () => applyFrame(initialState(), {
    type: 'welcome', nick: 'pikachu', room: 'lobby', topic: '',
    users: ['pikachu', 'gengar', 'mew'], op: 'gengar', history: [],
  })

  it('follows op frames after the operator leaves or is kicked', () => {
    let s = welcome()
    expect(s.op).toBe('gengar')
    s = applyFrame(s, { type: 'leave', nick: 'gengar' })
    s = applyFrame(s, { type: 'op', nick: 'mew' })
    expect([s.op, s.users]).toEqual(['mew', ['pikachu', 'mew']])
    s = applyFrame(s, { type: 'kick', nick: 'mew', by: 'pikachu', reason: '' })
    s = applyFrame(s, { type: 'op', nick: 'pikachu' })
    expect(s.op).toBe('pikachu')
  })
})
