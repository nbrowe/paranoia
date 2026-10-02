/*
 * E2E: slash commands the current server already supports end to end.
 * Scope: /help (local lines, nothing sent), /omit (sets and clears the
 * sticky list, masks for the omitted user), unknown commands (local
 * error, nothing sent), `//` (literal slash). Limitations: /me, /topic
 * and /kick need the commands server and are covered by Vitest only.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom } from '../lib/user.js'

test('/help lists commands locally, others see nothing',
  async ({ browser }) => {
    const room = uniqueRoom()
    const a = await User.join(browser, room)
    const b = await User.join(browser, room)
    await a.say('/help')
    await expect(a.notices.filter({ hasText: '/omit [nick...]' }))
      .toHaveCount(1)
    await expect(a.notices.filter({ hasText: '/kick <nick>' })).toHaveCount(1)
    await expect(a.input).toHaveValue('')
    await expect(a.messages).toHaveCount(0)
    await a.say('ping')
    await expect(b.messages).toHaveCount(1)  // only "ping" arrived
    await expect(b.message(a.nick, 'ping')).toHaveCount(1)
  })

test('/omit sets and clears the sticky list', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const b = await User.join(browser, room)
  await expect(a.userList).toContainText('Users (2)')

  await a.say(`/omit ${b.nick}`)
  await expect(a.box(b.nick)).toHaveAttribute('aria-pressed', 'true')
  await expect(a.omitBar).toContainText(b.nick)
  await a.say('hush')
  await expect(b.messages.first().getByTestId('text')).toHaveText('****')

  await a.say('/omit')
  await expect(a.box(b.nick)).toHaveAttribute('aria-pressed', 'false')
  await expect(a.omitBar).toHaveText('Omitting nobody')
})

test('/omit with an absent nick reports it', async ({ browser }) => {
  const a = await User.join(browser, uniqueRoom())
  await a.say('/omit nobody-here')
  await expect(a.notices.filter({ hasText: 'nobody-here' })).toHaveCount(1)
  await expect(a.omitBar).toHaveText('Omitting nobody')
})

test('unknown command is a local error', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const b = await User.join(browser, room)
  await a.say('/dance now')
  await expect(a.notices.filter({ hasText: 'Unknown command: /dance' }))
    .toHaveCount(1)
  await a.say('after')
  await expect(b.messages).toHaveCount(1)  // the command was not sent
  await expect(b.message(a.nick, 'after')).toHaveCount(1)
})

test('// sends a literal slash', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const b = await User.join(browser, room)
  await a.say('//help me')
  await expect(b.message(a.nick, '/help me')).toHaveCount(1)
})
