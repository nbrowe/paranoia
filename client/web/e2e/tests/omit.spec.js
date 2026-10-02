/*
 * E2E: omitting users via the user-list checkboxes (sticky omit list).
 * Scope: masked text for the omitted user, plaintext for others, the
 * sender's omitted badge, the omit bar, and unticking. Limitations: masked
 * whitespace is checked on the DOM text plus its pre-wrap style.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom } from '../lib/user.js'

test('omitted user sees asterisks, others plaintext', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const b = await User.join(browser, room)
  const c = await User.join(browser, room)
  await expect(a.userList).toContainText('Users (3)')

  await a.box(b.nick).check()
  await expect(a.omitBar).toContainText('Omitting:')
  await expect(a.omitBar).toContainText(b.nick)

  const text = 'top secret  plan'
  const masked = text.replace(/\S/g, '*')
  await a.say(text)

  const own = a.message(a.nick, text)
  await expect(own).toHaveCount(1)
  await expect(own.getByTestId('omitted'))
    .toHaveText(`hidden from ${b.nick}`)
  await expect(a.box(b.nick)).toBeChecked()  // sticky after sending

  const plain = c.message(a.nick, text)
  await expect(plain).toHaveCount(1)
  await expect(plain.getByTestId('omitted')).toHaveCount(0)
  await expect(plain).not.toHaveClass(/fst-italic/)

  await expect(b.messages).toHaveCount(1)
  const hidden = b.messages.first()
  expect(await hidden.getByTestId('text').textContent()).toBe(masked)
  await expect(hidden).toHaveClass(/fst-italic/)
  await expect(hidden.getByTestId('text'))
    .toHaveCSS('white-space', 'pre-wrap')
  await expect(hidden.getByTestId('omitted')).toHaveCount(0)
  await expect(b.page.getByText('secret')).toHaveCount(0)

  await a.box(b.nick).uncheck()
  await expect(a.omitBar).toHaveText('Omitting nobody')
  await a.say('second note')
  await expect(b.message(a.nick, 'second note')).toHaveCount(1)
  await expect(b.message(a.nick, 'second note')).not.toHaveClass(/fst-italic/)
})
