/*
 * Test helper: a chat user driven through its own browser context.
 * Scope: joins a room, exposes locators for the main UI parts and actions
 * to send messages and toggle omit checkboxes. Selectors are the
 * data-testid hooks in client/web/src plus ARIA roles.
 * Limitations: one page per user; no multi-room support.
 */
import { expect } from '@playwright/test'
import { readFileSync } from 'node:fs'

const POKEMON_FILE = process.env.E2E_POKEMON_FILE ||
  new URL('../../../../server/paranoia/data/pokemon.txt', import.meta.url)

const POKEMON = new Set(
  readFileSync(POKEMON_FILE, 'utf8').split('\n').filter(Boolean))

/**
 * Create a room name unique to one test.
 * @returns {string} room name
 */
export function uniqueRoom() {
  return `e2e-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

/**
 * Check that a nick is a known Pokemon slug.
 * @param {string} nick nickname to check
 * @returns {boolean} true if it is in the server's pool
 */
export function isPokemon(nick) {
  return POKEMON.has(nick)
}

/**
 * Join extra silent users by opening raw WebSockets from inside a page
 * (same origin, so the web server's /ws proxy is used). The sockets live
 * until the page's context closes.
 * @param {import('@playwright/test').Page} page any loaded app page
 * @param {string} room room name
 * @param {number} count how many users to add
 * @returns {Promise<void>}
 */
export async function addLurkers(page, room, count) {
  await page.evaluate(({ room, count }) => {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    window.lurkers = Array.from({ length: count }, () =>
      new WebSocket(`${proto}://${location.host}/ws?room=${room}`))
  }, { room, count })
}

export class User {
  /**
   * @param {import('@playwright/test').Page} page page in its own context
   */
  constructor(page) {
    this.page = page
    this.nick = ''
    this.status = page.getByTestId('status')
    this.timeline = page.getByTestId('timeline')
    this.messages = this.timeline.getByTestId('message')
    this.notices = this.timeline.getByTestId('notice')
    this.userList = page.getByTestId('user-list')
    this.omitBar = page.getByTestId('omit-bar')
    this.input = page.getByPlaceholder('Message')
  }

  /**
   * Open a new browser context, load the app in a room and wait for the
   * welcome frame (status open and a nick shown).
   * @param {import('@playwright/test').Browser} browser browser
   * @param {string} room room name
   * @returns {Promise<User>} the connected user
   */
  static async join(browser, room) {
    const context = await browser.newContext()
    const user = new User(await context.newPage())
    await user.page.goto(`/?room=${room}`)
    await expect(user.status).toHaveText('online')
    user.nick = (await user.page.getByTestId('nick').textContent()).trim()
    return user
  }

  /**
   * Send a message through the input field.
   * @param {string} text message text
   * @returns {Promise<void>}
   */
  async say(text) {
    await this.input.fill(text)
    await this.input.press('Enter')
  }

  /**
   * Checkbox for another user in the user list.
   * @param {string} nick other user's nick
   * @returns {import('@playwright/test').Locator} checkbox locator
   */
  box(nick) {
    return this.userList.getByRole('checkbox', { name: nick, exact: true })
  }

  /**
   * Message rows from a given sender with exact text.
   * @param {string} sender sender nick
   * @param {string|RegExp} text expected text
   * @returns {import('@playwright/test').Locator} message row locator
   */
  message(sender, text) {
    return this.messages
      .filter({ has: this.page.getByTestId('sender').getByText(sender) })
      .filter({
        has: this.page.getByTestId('text').getByText(text, { exact: true }),
      })
  }
}
