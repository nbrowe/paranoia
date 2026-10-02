/*
 * E2E: the page fits a phone-width viewport.
 * Scope: no horizontal page overflow at 390px and a usable (visible, in
 * viewport) omit checkbox. Limitations: one width only; no visual diffs.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom } from '../lib/user.js'

test('no overflow at 390px, checkbox usable', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  })
  const page = await context.newPage()
  await page.goto(`/?room=${room}`)
  await expect(page.getByTestId('status')).toHaveText('open')
  await expect(page.getByRole('checkbox', { name: a.nick })).toBeInViewport()

  const overflow = await page.evaluate(() => {
    const el = document.documentElement
    return el.scrollWidth - el.clientWidth
  })
  expect(overflow).toBe(0)
  const list = await page.getByTestId('user-list').boundingBox()
  expect(list.x + list.width).toBeLessThanOrEqual(390)
  await context.close()
})
