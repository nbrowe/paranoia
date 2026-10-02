/*
 * Unit tests for lib/theme.js: choice validation, resolution against the
 * system preference, and storage access that may fail.
 * Scope: pure logic with fake storage. Limitations: no DOM.
 */
import { describe, it, expect } from 'vitest'
import {
  normalizeChoice, resolveTheme, loadChoice, saveChoice, STORAGE_KEY,
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

describe('normalizeChoice', () => {
  it('accepts the three choices', () => {
    for (const c of ['light', 'dark', 'auto']) {
      expect(normalizeChoice(c)).toBe(c)
    }
  })

  it('falls back to auto for anything else', () => {
    for (const v of [null, undefined, '', 'Dark', 'blue', 1, {}]) {
      expect(normalizeChoice(v)).toBe('auto')
    }
  })
})

describe('resolveTheme', () => {
  it('auto follows the system preference', () => {
    expect(resolveTheme('auto', true)).toBe('dark')
    expect(resolveTheme('auto', false)).toBe('light')
  })

  it('an explicit choice overrides the system', () => {
    expect(resolveTheme('light', true)).toBe('light')
    expect(resolveTheme('dark', false)).toBe('dark')
  })

  it('treats invalid choices as auto', () => {
    expect(resolveTheme('bogus', true)).toBe('dark')
  })
})

describe('storage', () => {
  it('round-trips a choice', () => {
    const st = fakeStorage()
    saveChoice(() => st, 'dark')
    expect(st.data[STORAGE_KEY]).toBe('dark')
    expect(loadChoice(() => st)).toBe('dark')
  })

  it('ignores invalid stored values', () => {
    expect(loadChoice(() => fakeStorage({ [STORAGE_KEY]: 'neon' })))
      .toBe('auto')
    expect(loadChoice(() => fakeStorage())).toBe('auto')
  })

  it('survives storage that throws', () => {
    const boom = () => { throw new Error('denied') }
    expect(loadChoice(boom)).toBe('auto')
    expect(() => saveChoice(boom, 'dark')).not.toThrow()
    const bad = { getItem: boom, setItem: boom }
    expect(loadChoice(() => bad)).toBe('auto')
    expect(() => saveChoice(() => bad, 'light')).not.toThrow()
  })
})
