/*
 * E2E: a single user connects and sees the initial UI state.
 * Scope: nick (Pokemon slug), user list with self, greeting notice, no
 * messages. Limitations: nick randomness is only checked against the pool.
 */
import { test, expect } from '@playwright/test'
import { WS_EFFECT_LOOP, WS_EFFECT_LOOP_REASON } from '../lib/known-bugs.js'
import { User, uniqueRoom, isPokemon } from '../lib/user.js'

test('connects, shows nick, user list and greeting', async ({ browser }) => {
  test.fixme(WS_EFFECT_LOOP, WS_EFFECT_LOOP_REASON)
  const room = uniqueRoom()
  const a = await User.join(browser, room)

  expect(isPokemon(a.nick)).toBe(true)
  await expect(a.status).toHaveText('open')
  await expect(a.userList).toContainText('Users (1)')
  await expect(a.userList).toContainText(`${a.nick} (you)`)
  await expect(a.userList.getByRole('checkbox')).toHaveCount(0)

  await expect(a.notices).toHaveCount(1)
  await expect(a.notices.first())
    .toHaveText(`* Joined #${room} as ${a.nick}`)
  await expect(a.messages).toHaveCount(0)
  await expect(a.omitBar).toHaveText('Omitting nobody')
  await expect(a.input).toBeEnabled()
})
