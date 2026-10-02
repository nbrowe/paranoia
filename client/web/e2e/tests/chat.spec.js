/*
 * E2E: two users see each other and exchange plaintext messages.
 * Scope: user lists on both sides, join notice, message delivery in both
 * directions, input cleared after send. Limitations: no omit here.
 */
import { test, expect } from '@playwright/test'
import { WS_EFFECT_LOOP, WS_EFFECT_LOOP_REASON } from '../lib/known-bugs.js'
import { User, uniqueRoom } from '../lib/user.js'

test('two users see each other and read plaintext', async ({ browser }) => {
  test.fixme(WS_EFFECT_LOOP, WS_EFFECT_LOOP_REASON)
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const b = await User.join(browser, room)

  await expect(a.userList).toContainText('Users (2)')
  await expect(a.box(b.nick)).toBeVisible()
  await expect(b.userList).toContainText('Users (2)')
  await expect(b.box(a.nick)).toBeVisible()
  await expect(a.notices.filter({ hasText: `${b.nick} joined` })).toHaveCount(1)

  await a.say('hello from a')
  await expect(a.input).toHaveValue('')
  await expect(b.message(a.nick, 'hello from a')).toHaveCount(1)
  await expect(a.message(a.nick, 'hello from a')).toHaveCount(1)

  await b.say('hi back')
  await expect(a.message(b.nick, 'hi back')).toHaveCount(1)
  await expect(b.message(b.nick, 'hi back')).toHaveCount(1)
  await expect(a.messages).toHaveCount(2)
  await expect(b.messages.first()).not.toHaveClass(/fst-italic/)
})
