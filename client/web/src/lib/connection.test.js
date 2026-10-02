/*
 * Unit tests for the reconnecting connection (connection.js) using a
 * fake WebSocket and fake timers. Scope: backoff, reconnect, send gating.
 * Limitations: does not exercise a real network socket.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { connect, backoffDelay } from './connection.js'

let sockets

/** Minimal controllable WebSocket stand-in. */
class FakeWS {
  /** Register the instance so tests can drive it. */
  constructor(url) {
    this.url = url
    this.readyState = 0
    this.sent = []
    sockets.push(this)
  }

  /** Record an outgoing frame. */
  send(text) { this.sent.push(text) }

  /** Mark closed without firing onclose (caller-initiated). */
  close() { this.readyState = 3 }

  /** Simulate the handshake completing. */
  open() { this.readyState = 1; this.onopen() }

  /** Simulate a server frame. */
  recv(frame) { this.onmessage({ data: JSON.stringify(frame) }) }

  /** Simulate the server dropping the link. */
  drop() { this.readyState = 3; this.onclose() }
}

beforeEach(() => {
  sockets = []
  vi.useFakeTimers()
})

describe('backoffDelay', () => {
  it('doubles from 500ms up to a 10s cap', () => {
    expect([0, 1, 2].map(backoffDelay)).toEqual([500, 1000, 2000])
    expect(backoffDelay(20)).toBe(10000)
  })
})

describe('connect', () => {
  it('reconnects after a drop with increasing delay', () => {
    const status = []
    connect({ url: 'u', onFrame() {}, onStatus: (s) => status.push(s),
      WS: FakeWS })
    sockets[0].open()
    sockets[0].drop()
    vi.advanceTimersByTime(499)
    expect(sockets).toHaveLength(1)
    vi.advanceTimersByTime(1)
    expect(sockets).toHaveLength(2)
    sockets[1].drop()
    vi.advanceTimersByTime(999)
    expect(sockets).toHaveLength(2)
    vi.advanceTimersByTime(1)
    expect(sockets).toHaveLength(3)
    expect(status).toEqual([
      'connecting', 'open', 'disconnected', 'connecting', 'disconnected',
      'connecting',
    ])
  })

  it('resets backoff on welcome and forwards frames', () => {
    const frames = []
    connect({ url: 'u', onFrame: (f) => frames.push(f), onStatus() {},
      WS: FakeWS })
    sockets[0].drop()
    vi.advanceTimersByTime(500)
    sockets[1].open()
    sockets[1].recv({ type: 'welcome' })
    sockets[1].drop()
    vi.advanceTimersByTime(500)
    expect(sockets).toHaveLength(3)
    expect(frames).toEqual([{ type: 'welcome' }])
  })

  it('sends only while open and stops reconnecting once closed', () => {
    const c = connect({ url: 'u', onFrame() {}, onStatus() {}, WS: FakeWS })
    expect(c.send('x')).toBe(false)
    sockets[0].open()
    expect(c.send('x')).toBe(true)
    expect(sockets[0].sent).toEqual(['x'])
    c.close()
    sockets[0].drop()
    vi.advanceTimersByTime(60000)
    expect(sockets).toHaveLength(1)
  })
})
