/*
 * E2E: the page fits a phone-width viewport.
 * Scope: no horizontal page overflow at 390px, the collapsed "Users (N)"
 * toggle that expands the list inline, and no nested scroll box with many
 * users. Limitations: one width only; no visual diffs.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom, addLurkers } from '../lib/user.js'

/**
 * Open the app in a 390px wide context.
 * @param {import('@playwright/test').Browser} browser browser
 * @param {string} room room name
 * @returns {Promise<import('@playwright/test').Page>} loaded page
 */
async function phone(browser, room) {
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
  })
  const page = await context.newPage()
  await page.goto(`/?room=${room}`)
  await expect(page.getByTestId('status')).toHaveText('online')
  return page
}

test('no overflow at 390px, checkbox usable', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const page = await phone(browser, room)
  const toggle = page.getByTestId('user-toggle')
  const box = page.getByRole('checkbox', { name: a.nick })
  await expect(toggle).toHaveText(/Users \(2\)/)
  await expect(box).toBeHidden()
  await toggle.click()
  await expect(toggle).toHaveAttribute('aria-expanded', 'true')
  await expect(box).toBeInViewport()

  const overflow = await page.evaluate(() => {
    const el = document.documentElement
    return el.scrollWidth - el.clientWidth
  })
  expect(overflow).toBe(0)
  const list = await page.getByTestId('user-list').boundingBox()
  expect(list.x + list.width).toBeLessThanOrEqual(390)
  await page.context().close()
})

test('many users: no nested scroll box, all reachable', async ({ browser }) => {
  const room = uniqueRoom()
  const page = await phone(browser, room)
  await addLurkers(page, room, 15)
  const toggle = page.getByTestId('user-toggle')
  await expect(toggle).toHaveText(/Users \(16\)/)
  await toggle.click()

  // The list must not be its own scroll container.
  const clipped = await page.getByTestId('user-list').evaluate(
    (el) => el.scrollHeight > el.clientHeight + 1 &&
      getComputedStyle(el).overflowY !== 'visible')
  expect(clipped).toBe(false)

  const timeline = await page.getByTestId('timeline').boundingBox()
  expect(timeline.height).toBeGreaterThanOrEqual(200)
  const last = page.getByRole('checkbox').last()
  await last.scrollIntoViewIfNeeded()
  await expect(last).toBeInViewport()
  await expect(page.getByPlaceholder('Message')).toBeInViewport()
  await page.context().close()
})
