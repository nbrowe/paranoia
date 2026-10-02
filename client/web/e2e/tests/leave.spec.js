/*
 * E2E: a user leaving is removed from others' lists and omit selection.
 * Scope: user list, leave notice, omit bar pruning. Limitations: the
 * departed user's context is closed, not navigated away.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom } from '../lib/user.js'

test('leaving user is removed and pruned from omit', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const b = await User.join(browser, room)
  const c = await User.join(browser, room)
  await expect(a.userList).toContainText('Users (3)')

  await a.omit(b.nick)
  await a.omit(c.nick)
  await expect(a.omitBar).toContainText(b.nick)
  await expect(a.omitBar).toContainText(c.nick)

  await b.page.context().close()

  await expect(a.userList).toContainText('Users (2)')
  await expect(a.box(b.nick)).toHaveCount(0)
  await expect(a.notices.filter({ hasText: `${b.nick} left` })).toHaveCount(1)
  await expect(a.omitBar).not.toContainText(b.nick)
  await expect(a.omitBar).toContainText(c.nick)
  await expect(c.box(b.nick)).toHaveCount(0)
  await expect(c.notices.filter({ hasText: `${b.nick} left` })).toHaveCount(1)
})
