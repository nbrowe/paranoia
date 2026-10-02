/*
 * E2E: a single user connects and sees the initial UI state.
 * Scope: nick (Pokemon slug), user list with self (pinned first), greeting
 * notice, no messages. Limitations: nick randomness is only checked against the pool.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom, isPokemon } from '../lib/user.js'

test('connects, shows nick, user list and greeting', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)

  expect(isPokemon(a.nick)).toBe(true)
  await expect(a.status).toHaveText('online')
  await expect(a.userList).toContainText('Users (1)')
  await expect(a.userList).toContainText(`${a.nick} (you)`)
  await expect(a.userList.getByRole('checkbox')).toHaveCount(0)

  await expect(a.notices).toHaveCount(1)
  await expect(a.notices.first())
    .toHaveText(`* Joined #${room} as ${a.nick}`)
  await expect(a.messages).toHaveCount(0)
  await expect(a.omitBar).toHaveText('Omitting nobody')
  await expect(a.input).toBeEnabled()
  await expect(a.input).toBeFocused()
})

test('own nick is first in the user list', async ({ browser }) => {
  const room = uniqueRoom()
  const users = []
  for (let i = 0; i < 3; i++) users.push(await User.join(browser, room))
  for (const u of users) {
    await expect(u.userList).toContainText('Users (3)')
    await expect(u.userList.locator('#user-list-body > :first-child'))
      .toHaveText(`${u.nick} (you)`)
  }
})
