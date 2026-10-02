/*
 * Unit tests for wire helpers (protocol.js).
 * Scope: URL derivation and say/topic/kick frame building. Limitations: none.
 */
import { describe, it, expect } from 'vitest'
import { wsUrl, buildSay, buildTopic, buildKick } from './protocol.js'

describe('wsUrl', () => {
  it('uses ws for http and defaults to the lobby', () => {
    const loc = { protocol: 'http:', host: 'localhost:5173', search: '' }
    expect(wsUrl(loc)).toBe('ws://localhost:5173/ws?room=lobby')
  })

  it('uses wss for https and honours ?room=', () => {
    const loc = { protocol: 'https:', host: 'chat.example', search: '?room=x' }
    expect(wsUrl(loc)).toBe('wss://chat.example/ws?room=x')
  })

  it('lets the env override replace the base', () => {
    const loc = { protocol: 'http:', host: 'a', search: '' }
    expect(wsUrl(loc, 'ws://srv:8000/ws'))
      .toBe('ws://srv:8000/ws?room=lobby')
  })
})

describe('buildSay', () => {
  it('trims text and includes the omit list', () => {
    const out = JSON.parse(buildSay('  hi  ', ['mew']))
    expect(out).toEqual({ type: 'say', text: 'hi', omit: ['mew'] })
  })

  it('returns null for blank text', () => {
    expect(buildSay('   ', [])).toBeNull()
  })
})

describe('action, topic and kick frames', () => {
  it('say adds action only when requested', () => {
    expect(JSON.parse(buildSay('hi', ['a'], true)))
      .toEqual({ type: 'say', text: 'hi', omit: ['a'], action: true })
    expect(JSON.parse(buildSay('hi', []))).not.toHaveProperty('action')
  })

  it('topic trims and allows empty', () => {
    expect(JSON.parse(buildTopic('  hello  ')))
      .toEqual({ type: 'topic', text: 'hello' })
    expect(JSON.parse(buildTopic(''))).toEqual({ type: 'topic', text: '' })
  })

  it('kick carries nick and trimmed reason, default empty', () => {
    expect(JSON.parse(buildKick('mew', ' spam ')))
      .toEqual({ type: 'kick', nick: 'mew', reason: 'spam' })
    expect(JSON.parse(buildKick('mew')).reason).toBe('')
  })
})
