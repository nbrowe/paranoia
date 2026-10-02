/*
 * E2E: a late joiner sees recent history rendered for them.
 * Scope: history in `welcome`, masked where the joiner was omitted. A raw
 * protocol client omits every Pokemon nick so that whichever nick the
 * late joiner draws, it is omitted. Limitations: relies on the global
 * WebSocket of Node 22+ and on the server accepting absent nicks in omit.
 */
import { readFileSync } from 'node:fs'
import { test, expect } from '@playwright/test'
import { WS_EFFECT_LOOP, WS_EFFECT_LOOP_REASON } from '../lib/known-bugs.js'
import { User, uniqueRoom } from '../lib/user.js'
import { SERVER_URL } from '../lib/stack.js'

const NICKS = readFileSync(
  process.env.E2E_POKEMON_FILE ||
    new URL('../../../../server/paranoia/data/pokemon.txt', import.meta.url),
  'utf8').split('\n').filter(Boolean)

/**
 * Open a raw protocol client and wait for its welcome frame.
 * @param {string} room room name
 * @returns {Promise<WebSocket>} open socket
 */
async function rawClient(room) {
  const ws = new WebSocket(`${SERVER_URL.replace('http', 'ws')}/ws?room=${room}`)
  await new Promise((resolve, reject) => {
    ws.onmessage = () => resolve()  // first frame is always welcome
    ws.onerror = reject
  })
  return ws
}

test('late joiner gets history masked per recipient', async ({ browser }) => {
  test.fixme(WS_EFFECT_LOOP, WS_EFFECT_LOOP_REASON)
  const room = uniqueRoom()
  const raw = await rawClient(room)
  raw.send(JSON.stringify({ type: 'say', text: 'for nobody else', omit: NICKS }))
  raw.send(JSON.stringify({ type: 'say', text: 'for everyone' }))

  const late = await User.join(browser, room)
  await expect(late.messages).toHaveCount(2)

  const hidden = late.messages.nth(0)
  await expect(hidden).toHaveClass(/fst-italic/)
  expect(await hidden.getByTestId('text').textContent())
    .toBe('for nobody else'.replace(/\S/g, '*'))
  await expect(hidden.getByTestId('omitted')).toHaveCount(0)

  const open = late.messages.nth(1)
  await expect(open).not.toHaveClass(/fst-italic/)
  await expect(open.getByTestId('text')).toHaveText('for everyone')
  // History precedes the greeting notice.
  await expect(late.timeline.locator('> *').last()).toHaveAttribute(
    'data-testid', 'notice')
  raw.close()
})
