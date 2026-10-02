/*
 * E2E: the Light / Dark / Auto theme selector.
 * Scope: Auto follows the OS colour scheme live, an explicit choice
 * overrides it and survives a reload (localStorage), and the page still
 * works when storage throws. Limitations: checks the data-bs-theme
 * attribute and the body background, not pixel-level styling.
 */
import { test, expect } from '@playwright/test'
import { uniqueRoom } from '../lib/user.js'

/**
 * Open the app in a context with the given OS colour scheme.
 * @param {import('@playwright/test').Browser} browser browser
 * @param {string} colorScheme light | dark
 * @returns {Promise<import('@playwright/test').Page>} loaded page
 */
async function open(browser, colorScheme) {
  const context = await browser.newContext({ colorScheme })
  const page = await context.newPage()
  await page.goto(`/?room=${uniqueRoom()}`)
  await expect(page.getByTestId('status')).toHaveText('online')
  return page
}

test('auto is the default and follows the system live', async ({ browser }) => {
  const page = await open(browser, 'dark')
  const html = page.locator('html')
  await expect(page.getByTestId('theme')).toHaveValue('auto')
  await expect(html).toHaveAttribute('data-bs-theme', 'dark')
  await expect(page.locator('body'))
    .toHaveCSS('background-color', 'rgb(33, 37, 41)')

  await page.emulateMedia({ colorScheme: 'light' })
  await expect(html).toHaveAttribute('data-bs-theme', 'light')
  await expect(page.locator('body'))
    .toHaveCSS('background-color', 'rgb(255, 255, 255)')
  await page.context().close()
})

test('explicit choice overrides the system and survives reload',
  async ({ browser }) => {
    const page = await open(browser, 'light')
    const html = page.locator('html')
    await page.getByTestId('theme').selectOption('dark')
    await expect(html).toHaveAttribute('data-bs-theme', 'dark')

    await page.reload()
    await expect(page.getByTestId('status')).toHaveText('online')
    await expect(page.getByTestId('theme')).toHaveValue('dark')
    await expect(html).toHaveAttribute('data-bs-theme', 'dark')

    // The OS flipping does not matter once a choice is made.
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.emulateMedia({ colorScheme: 'light' })
    await expect(html).toHaveAttribute('data-bs-theme', 'dark')

    await page.getByTestId('theme').selectOption('light')
    await page.emulateMedia({ colorScheme: 'dark' })
    await expect(html).toHaveAttribute('data-bs-theme', 'light')

    await page.getByTestId('theme').selectOption('auto')
    await expect(html).toHaveAttribute('data-bs-theme', 'dark')
    await page.context().close()
  })

test('works without storage', async ({ browser }) => {
  const context = await browser.newContext({ colorScheme: 'dark' })
  await context.addInitScript(() => {
    Object.defineProperty(window, 'localStorage', {
      get() { throw new Error('storage blocked') },
    })
  })
  const page = await context.newPage()
  await page.goto(`/?room=${uniqueRoom()}`)
  await expect(page.getByTestId('status')).toHaveText('online')
  await expect(page.getByTestId('theme')).toHaveValue('auto')
  await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'dark')
  await page.getByTestId('theme').selectOption('light')
  await expect(page.locator('html')).toHaveAttribute('data-bs-theme', 'light')
  await context.close()
})
