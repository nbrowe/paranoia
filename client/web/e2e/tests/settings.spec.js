/*
 * E2E: the settings menu (gear button in the header).
 * Scope: opens/closes by click, outside click, Escape and (phone) backdrop
 * and close button; popover below and right-aligned on desktop, centred
 * dialog with a visible backdrop on a phone; the theme toggle works from
 * inside it; the build id line is present.
 * Limitations: Chromium only; positions are checked with a few px of slack.
 */
import { test, expect } from '@playwright/test'
import { uniqueRoom, openSettings } from '../lib/user.js'

/**
 * Open the app in a context of the given size.
 * @param {import('@playwright/test').Browser} browser browser
 * @param {number} width viewport width in px
 * @param {number} height viewport height in px
 * @returns {Promise<import('@playwright/test').Page>} loaded page
 */
async function open(browser, width, height) {
  const context = await browser.newContext({
    viewport: { width, height }, timezoneId: 'UTC',
  })
  const page = await context.newPage()
  await page.goto(`/?room=${uniqueRoom()}`)
  await expect(page.getByTestId('status')).toHaveAttribute('title', 'online')
  return page
}

/**
 * Assert the menu is closed.
 * @param {import('@playwright/test').Page} page page
 */
async function expectClosed(page) {
  await expect(page.getByTestId('settings-menu')).toBeHidden()
  await expect(page.getByTestId('settings'))
    .toHaveAttribute('aria-expanded', 'false')
}

test.describe('desktop popover', () => {
  test('opens below the gear, right-aligned', async ({ browser }) => {
    const page = await open(browser, 1280, 720)
    const gear = page.getByTestId('settings')
    await expect(gear).toHaveAccessibleName('Settings')
    await expectClosed(page)
    const menu = await openSettings(page)
    await expect(gear).toHaveAttribute('aria-expanded', 'true')
    const g = await gear.boundingBox()
    const m = await menu.boundingBox()
    expect(m.y).toBeGreaterThanOrEqual(g.y + g.height)
    expect(Math.abs(m.x + m.width - (g.x + g.width))).toBeLessThan(2)
    await expect(page.getByTestId('settings-close')).toBeHidden()
    await page.context().close()
  })

  test('closes on gear click, outside click and Escape',
    async ({ browser }) => {
      const page = await open(browser, 1280, 720)
      await openSettings(page)
      await page.getByTestId('settings').click()
      await expectClosed(page)

      await openSettings(page)
      await page.mouse.click(300, 400)
      await expectClosed(page)

      await openSettings(page)
      await page.keyboard.press('Escape')
      await expectClosed(page)
      await expect(page.getByTestId('settings')).toBeFocused()
      await page.context().close()
    })

  test('clicks inside the menu keep it open', async ({ browser }) => {
    const page = await open(browser, 1280, 720)
    const menu = await openSettings(page)
    await menu.getByText('Theme').click()
    await expect(menu).toBeVisible()
    await page.context().close()
  })
})

test.describe('phone dialog', () => {
  test('centred over a visible backdrop', async ({ browser }) => {
    const page = await open(browser, 390, 844)
    const menu = await openSettings(page)
    const m = await menu.boundingBox()
    expect(Math.abs(m.x + m.width / 2 - 195)).toBeLessThan(2)
    expect(Math.abs(m.y + m.height / 2 - 422)).toBeLessThan(2)
    await expect(page.getByTestId('settings-backdrop'))
      .toHaveCSS('background-color', 'rgba(0, 0, 0, 0.5)')
    await page.context().close()
  })

  test('closes by close button, backdrop and Escape', async ({ browser }) => {
    const page = await open(browser, 390, 844)
    await openSettings(page)
    await page.getByTestId('settings-close').click()
    await expectClosed(page)

    await openSettings(page)
    await page.mouse.click(5, 5)
    await expectClosed(page)

    await openSettings(page)
    await page.keyboard.press('Escape')
    await expectClosed(page)
    await page.context().close()
  })
})

test('theme toggles from inside the menu', async ({ browser }) => {
  const page = await open(browser, 1280, 720)
  const html = page.locator('html')
  const before = await html.getAttribute('data-bs-theme')
  const other = before === 'dark' ? 'light' : 'dark'
  const menu = await openSettings(page)
  await menu.getByTestId('theme').click()
  await expect(html).toHaveAttribute('data-bs-theme', other)
  await expect(page.getByTestId('theme'))
    .toHaveAccessibleName(`Switch to ${before} theme`)
  await page.context().close()
})

test('shows the build id at the bottom of the menu', async ({ browser }) => {
  const page = await open(browser, 1280, 720)
  const menu = await openSettings(page)
  const line = menu.getByTestId('build-id')
  await expect(line).toHaveText(/^Build ([0-9a-f]{16}|dev)$/)
  await expect(line).toHaveClass(/text-muted/)
  const l = await line.boundingBox()
  const m = await menu.boundingBox()
  expect(l.y + l.height).toBeGreaterThan(m.y + m.height - 24)
  await page.context().close()
})
