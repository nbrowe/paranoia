/*
 * E2E: the theme toggle button.
 * Scope: with no saved choice the scheme follows local time (dark
 * 18:00-06:00, via a Playwright clock override, ignoring the OS scheme),
 * clicking flips it and the explicit choice survives a reload and beats
 * the clock, and the page still works when storage throws.
 * Limitations: checks the data-bs-theme attribute and the body
 * background, not pixel-level styling.
 */
import { test, expect } from '@playwright/test'
import { uniqueRoom } from '../lib/user.js'

const DARK_BG = 'rgb(33, 37, 41)'
const LIGHT_BG = 'rgb(255, 255, 255)'

/**
 * Open the app with the browser clock fixed at a local (UTC) time.
 * @param {import('@playwright/test').Browser} browser browser
 * @param {string} localTime ISO local time, e.g. 2026-01-15T23:00:00
 * @param {(context: object) => Promise<void>} [setup] runs before goto
 * @returns {Promise<import('@playwright/test').Page>} loaded page
 */
async function openAt(browser, localTime, setup) {
  const context = await browser.newContext({
    timezoneId: 'UTC', colorScheme: 'light',  // OS scheme must not matter
  })
  const page = await context.newPage()
  await page.clock.setFixedTime(new Date(`${localTime}Z`))
  if (setup) await setup(context)
  await page.goto(`/?room=${uniqueRoom()}`)
  await expect(page.getByTestId('status')).toHaveText('online')
  return page
}

const cases = [
  ['23:00', 'dark', DARK_BG], ['18:00', 'dark', DARK_BG],
  ['05:59', 'dark', DARK_BG], ['06:00', 'light', LIGHT_BG],
  ['12:00', 'light', LIGHT_BG], ['17:59', 'light', LIGHT_BG],
]
for (const [time, scheme, bg] of cases) {
  test(`no saved choice at ${time} is ${scheme}`, async ({ browser }) => {
    const page = await openAt(browser, `2026-01-15T${time}:00`)
    await expect(page.locator('html')).toHaveAttribute('data-bs-theme', scheme)
    await expect(page.locator('body')).toHaveCSS('background-color', bg)
    await page.context().close()
  })
}

test('click flips, persists across reload and beats the clock',
  async ({ browser }) => {
    const page = await openAt(browser, '2026-01-15T12:00:00')
    const html = page.locator('html')
    const btn = page.getByTestId('theme')
    await expect(html).toHaveAttribute('data-bs-theme', 'light')
    await expect(btn).toHaveAccessibleName('Switch to dark theme')

    await btn.click()
    await expect(html).toHaveAttribute('data-bs-theme', 'dark')
    await expect(btn).toHaveAccessibleName('Switch to light theme')

    await page.reload()
    await expect(page.getByTestId('status')).toHaveText('online')
    await expect(html).toHaveAttribute('data-bs-theme', 'dark')

    await page.getByTestId('theme').click()
    await expect(html).toHaveAttribute('data-bs-theme', 'light')
    await page.reload()
    await expect(html).toHaveAttribute('data-bs-theme', 'light')
    await page.context().close()
  })

test('works without storage', async ({ browser }) => {
  const page = await openAt(browser, '2026-01-15T23:00:00', (context) =>
    context.addInitScript(() => {
      Object.defineProperty(window, 'localStorage', {
        get() { throw new Error('storage blocked') },
      })
    }))
  await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'dark')
  await page.getByTestId('theme').click()
  await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'light')
  await page.context().close()
})
