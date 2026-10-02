/*
 * Unit tests for lib/theme.js: the time-of-day default, flipping, and
 * storage access that may fail.
 * Scope: pure logic with fake storage. Limitations: no DOM.
 */
import { describe, it, expect } from 'vitest'
import {
  themeForHour, otherTheme, loadChoice, initialTheme, saveChoice,
  STORAGE_KEY, DARK_FROM, DARK_TO,
} from './theme.js'

/**
 * Build an in-memory Storage stand-in.
 * @param {object} data initial entries
 * @returns {object} getItem/setItem fake
 */
function fakeStorage(data = {}) {
  return {
    getItem: (k) => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v) },
    data,
  }
}

/**
 * Build a Date at a local hour.
 * @param {number} h hour 0-23
 * @returns {Date} 15 Jan 2026 at h:30 local
 */
const at = (h) => new Date(2026, 0, 15, h, 30)

describe('themeForHour', () => {
  it('is dark from 18:00 to 06:00 and light otherwise', () => {
    expect([DARK_FROM, DARK_TO]).toEqual([18, 6])
    for (const h of [18, 23, 0, 5]) expect(themeForHour(h)).toBe('dark')
    for (const h of [6, 12, 17]) expect(themeForHour(h)).toBe('light')
  })
})

describe('otherTheme', () => {
  it('flips', () => {
    expect(otherTheme('light')).toBe('dark')
    expect(otherTheme('dark')).toBe('light')
  })
})

describe('initialTheme', () => {
  it('follows the clock with nothing saved', () => {
    expect(initialTheme(() => fakeStorage(), at(20))).toBe('dark')
    expect(initialTheme(() => fakeStorage(), at(9))).toBe('light')
  })

  it('a saved choice beats the clock', () => {
    const st = fakeStorage({ [STORAGE_KEY]: 'light' })
    expect(initialTheme(() => st, at(23))).toBe('light')
  })
})

describe('storage', () => {
  it('round-trips a choice', () => {
    const st = fakeStorage()
    saveChoice(() => st, 'dark')
    expect(st.data[STORAGE_KEY]).toBe('dark')
    expect(loadChoice(() => st)).toBe('dark')
  })

  it('ignores invalid stored values and invalid saves', () => {
    expect(loadChoice(() => fakeStorage({ [STORAGE_KEY]: 'auto' })))
      .toBeNull()
    const st = fakeStorage()
    saveChoice(() => st, 'auto')
    expect(st.data).toEqual({})
  })

  it('survives storage that throws', () => {
    const boom = () => { throw new Error('denied') }
    expect(loadChoice(boom)).toBeNull()
    expect(() => saveChoice(boom, 'dark')).not.toThrow()
    const bad = { getItem: boom, setItem: boom }
    expect(initialTheme(() => bad, at(20))).toBe('dark')
    expect(() => saveChoice(() => bad, 'light')).not.toThrow()
  })
})
