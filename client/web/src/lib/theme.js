/*
 * Theme logic: validates a stored theme choice, resolves it (plus the OS
 * preference) to the concrete Bootstrap colour mode, and reads/writes
 * the choice in storage. Pure JS, no Svelte or DOM; storage is passed in
 * as a getter so tests can fake it. Scope: choices light | dark | auto.
 * Limitations: index.html repeats the key and the resolve rule in a tiny
 * inline script (it must run before the bundle to avoid a light flash);
 * keep the two in sync.
 */

export const THEMES = ['light', 'dark', 'auto']
export const DEFAULT_THEME = 'auto'
export const STORAGE_KEY = 'paranoia-theme'

/**
 * Validate a theme choice; anything unknown becomes the default.
 * @param {unknown} value candidate choice (e.g. read from storage)
 * @returns {string} light | dark | auto
 */
export function normalizeChoice(value) {
  return THEMES.includes(value) ? value : DEFAULT_THEME
}

/**
 * Resolve a choice to the concrete colour mode.
 * @param {string} choice light | dark | auto (validated first)
 * @param {boolean} systemDark true if the OS prefers a dark scheme
 * @returns {string} light | dark
 */
export function resolveTheme(choice, systemDark) {
  const c = normalizeChoice(choice)
  if (c === 'auto') return systemDark ? 'dark' : 'light'
  return c
}

/**
 * Read the saved choice; storage may be missing or throw.
 * @param {() => Storage} getStorage returns the storage object
 * @returns {string} validated choice, default if unavailable
 */
export function loadChoice(getStorage) {
  try {
    return normalizeChoice(getStorage().getItem(STORAGE_KEY))
  } catch {
    return DEFAULT_THEME
  }
}

/**
 * Save the choice; failures (private mode, blocked storage) are ignored.
 * @param {() => Storage} getStorage returns the storage object
 * @param {string} choice light | dark | auto
 */
export function saveChoice(getStorage, choice) {
  try {
    getStorage().setItem(STORAGE_KEY, normalizeChoice(choice))
  } catch { /* storage is optional */ }
}
