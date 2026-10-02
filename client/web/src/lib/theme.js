/*
 * Theme logic: the colour mode is light or dark. With no saved choice it
 * follows the local time of day (dark from DARK_FROM to DARK_TO); the
 * header button flips it and saves that explicit choice. Pure JS, no
 * Svelte or DOM; storage is passed in as a getter so tests can fake it.
 * Limitations: the time rule is applied once at load, not live. index.html
 * repeats the key, the hours and the rule in a tiny inline script (it must
 * run before the bundle to avoid a light flash); keep the two in sync.
 */

export const THEMES = ['light', 'dark']
export const STORAGE_KEY = 'paranoia-theme'
export const DARK_FROM = 18  // local hour (inclusive) dark mode starts
export const DARK_TO = 6     // local hour (exclusive) dark mode ends

/**
 * Pick the scheme for a local hour of the day.
 * @param {number} hour 0-23
 * @returns {string} light | dark
 */
export function themeForHour(hour) {
  return hour >= DARK_FROM || hour < DARK_TO ? 'dark' : 'light'
}

/**
 * The other scheme.
 * @param {string} theme light | dark
 * @returns {string} dark for light, light for dark
 */
export function otherTheme(theme) {
  return theme === 'dark' ? 'light' : 'dark'
}

/**
 * Read the saved choice; storage may be missing or throw.
 * @param {() => Storage} getStorage returns the storage object
 * @returns {string|null} light | dark, or null if none/invalid/unavailable
 */
export function loadChoice(getStorage) {
  try {
    const v = getStorage().getItem(STORAGE_KEY)
    return THEMES.includes(v) ? v : null
  } catch {
    return null
  }
}

/**
 * Choose the scheme to show at load: the saved choice, else by time.
 * @param {() => Storage} getStorage returns the storage object
 * @param {Date} [now] current time (for tests)
 * @returns {string} light | dark
 */
export function initialTheme(getStorage, now = new Date()) {
  return loadChoice(getStorage) ?? themeForHour(now.getHours())
}

/**
 * Save the choice; failures (private mode, blocked storage) are ignored.
 * @param {() => Storage} getStorage returns the storage object
 * @param {string} theme light | dark
 */
export function saveChoice(getStorage, theme) {
  if (!THEMES.includes(theme)) return
  try {
    getStorage().setItem(STORAGE_KEY, theme)
  } catch { /* storage is optional */ }
}
