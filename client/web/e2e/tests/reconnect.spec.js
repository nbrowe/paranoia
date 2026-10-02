/*
 * E2E: the client survives a server restart.
 * Scope: disconnected state (badge, notice, disabled input), automatic
 * recovery with a fresh nick from `welcome`, and chatting again.
 * Limitations: restarts the shared server container, so it must not run
 * in parallel with other tests (the config uses a single worker).
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom, isPokemon } from '../lib/user.js'
import { restartServer } from '../lib/stack.js'

test('shows disconnected, recovers and works again', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  await a.say('before restart')
  await expect(a.messages).toHaveCount(1)

  await restartServer()
  await expect(a.status).toHaveText('online', { timeout: 20000 })

  // A restart wipes state, so the welcome frame resets the timeline.
  const nick = (await a.page.getByTestId('nick').textContent()).trim()
  expect(isPokemon(nick)).toBe(true)
  await expect(a.messages).toHaveCount(0)
  await expect(a.userList).toContainText(`${nick} (you)`)
  await expect(a.userList).toContainText('Users (1)')
  await expect(a.input).toBeEnabled()

  const b = await User.join(browser, room)
  await a.say('after restart')
  await expect(b.message(nick, 'after restart')).toHaveCount(1)
})

test('shows a disconnected state while the server is down',
  async ({ browser }) => {
    const room = uniqueRoom()
    const a = await User.join(browser, room)
    const b = await User.join(browser, room)
    await a.box(b.nick).check()
    await a.say('kept while down')
    await expect(a.messages).toHaveCount(1)
    const down = expect(a.status).toHaveText('offline')
    await restartServer()
    await down

    // Stale identity is cleared, history stays readable.
    const nick = a.page.getByTestId('nick')
    await expect(nick).toHaveText('—')
    await expect(a.userList).toContainText('Users (0)')
    await expect(a.userList.getByRole('checkbox')).toHaveCount(0)
    await expect(a.omitBar).toHaveText('Omitting nobody')
    await expect(a.message(a.nick, 'kept while down')).toHaveCount(1)

    await expect(a.status).toHaveText('online', { timeout: 20000 })
    await expect(nick).not.toHaveText('—')
    await expect(a.notices.filter({ hasText: 'Disconnected' })).toHaveCount(0)
  })
