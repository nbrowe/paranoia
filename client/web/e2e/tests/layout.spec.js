/*
 * E2E: the page fits a phone-width viewport.
 * Scope: no horizontal page overflow at 390px and 320px (header incl.), the collapsed "Users (N)"
 * toggle that expands the list inline, and a long user list scrolling in
 * its own bounded box (phone and desktop) while the timeline and input
 * stay reachable. Limitations: two widths only; no visual diffs.
 */
import { test, expect } from '@playwright/test'
import { User, uniqueRoom, addLurkers } from '../lib/user.js'

/**
 * Open the app in a phone-width context.
 * @param {import('@playwright/test').Browser} browser browser
 * @param {string} room room name
 * @param {number} [width] viewport width in px
 * @returns {Promise<import('@playwright/test').Page>} loaded page
 */
async function phone(browser, room, width = 390) {
  const context = await browser.newContext({
    viewport: { width, height: 844 },
  })
  const page = await context.newPage()
  await page.goto(`/?room=${room}`)
  await expect(page.getByTestId('status')).toHaveAttribute('title', 'online')
  return page
}

test('no overflow at 390px, toggle button usable', async ({ browser }) => {
  const room = uniqueRoom()
  const a = await User.join(browser, room)
  const page = await phone(browser, room)
  const toggle = page.getByTestId('user-toggle')
  const box = page.getByRole('button', { name: a.nick, exact: true })
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

test('many users: list scrolls in its own box, rest reachable',
  async ({ browser }) => {
    const room = uniqueRoom()
    const page = await phone(browser, room)
    await addLurkers(page, room, 60)
    const toggle = page.getByTestId('user-toggle')
    await expect(toggle).toHaveText(/Users \(61\)/)
    await toggle.click()

    const body = page.locator('#user-list-body')
    const box = await body.evaluate((el) => ({
      scrolls: el.scrollHeight > el.clientHeight + 1,
      overflowY: getComputedStyle(el).overflowY,
      height: el.clientHeight,
    }))
    expect(box.scrolls).toBe(true)
    expect(box.overflowY).toBe('auto')
    expect(box.height).toBeLessThanOrEqual(844 * 0.4 + 1)

    const timeline = await page.getByTestId('timeline').boundingBox()
    expect(timeline.height).toBeGreaterThanOrEqual(200)
    const last = body.getByRole('button').last()
    await last.scrollIntoViewIfNeeded()
    await expect(last).toBeInViewport()
    await expect(page.getByPlaceholder('Message')).toBeInViewport()
    await page.context().close()
  })

test('desktop: long list scrolls inside the side column',
  async ({ browser }) => {
    const room = uniqueRoom()
    const a = await User.join(browser, room)
    await addLurkers(a.page, room, 120)
    await expect(a.userList).toContainText('Users (121)')

    const body = a.page.locator('#user-list-body')
    const scrolls = await body.evaluate((el) =>
      el.scrollHeight > el.clientHeight + 1 &&
      getComputedStyle(el).overflowY === 'auto')
    expect(scrolls).toBe(true)
    const page = await a.page.evaluate(() => ({
      over: document.documentElement.scrollHeight - innerHeight,
      width: document.documentElement.scrollWidth - innerWidth,
    }))
    expect(page).toEqual({ over: 0, width: 0 })
    await expect(a.input).toBeInViewport()
    const last = body.getByRole('button').last()
    await last.scrollIntoViewIfNeeded()
    await expect(last).toBeInViewport()
  })

for (const width of [320, 390]) {
  test(`header fits at ${width}px, long nick`, async ({ browser }) => {
    const page = await phone(browser, uniqueRoom(), width)
    // Force the worst case: a long nick and a long room name.
    await page.evaluate(() => {
      document.querySelector('[data-testid="nick"]').textContent =
        'landorus-incarnate'
    })
    const m = await page.evaluate(() => {
      const el = document.documentElement
      const h = document.querySelector('header')
      const r = (e) => e.getBoundingClientRect()
      const logo = r(h.querySelector('img'))
      return {
        overflow: el.scrollWidth - el.clientWidth,
        headerOverflow: h.scrollWidth - h.clientWidth,
        logoRight: logo.right,
        logoVisible: logo.width > 0,
        themeRight: r(h.querySelector("[data-testid=theme]")).right,
      }
    })
    expect(m.overflow).toBe(0)
    expect(m.headerOverflow).toBe(0)
    expect(m.logoVisible).toBe(true)
    expect(m.themeRight).toBeLessThanOrEqual(width)
    await page.context().close()
  })
}
