/*
 * E2E with a scripted WebSocket (page.routeWebSocket, no real server):
 * the topic header, /me, /topic, /kick frames, and kick handling.
 * Scope: client behaviour for the commands protocol additions that the
 * server under test may not implement yet. Limitations: the "server" is
 * a stub that only answers what each test scripts.
 */
import { test, expect } from '@playwright/test'

const LONG_TOPIC = 'a very long topic '.repeat(12).trim()

/**
 * Open the app against a stub server.
 * @param {import('@playwright/test').Browser} browser browser
 * @param {object} opts
 * @param {number} [opts.width] viewport width
 * @param {string} [opts.topic] topic in the welcome frame
 * @returns {Promise<{page: object, sent: object[], conns: {n: number},
 *   push: (frame: object) => void}>} page, frames the client sent, the
 *   connection counter, and a function to push a frame to the client
 */
async function open(browser, { width = 1280, topic = '' } = {}) {
  const context = await browser.newContext({
    viewport: { width, height: 800 },
  })
  const page = await context.newPage()
  const sent = []
  const conns = { n: 0 }
  let socket = null
  await page.routeWebSocket(/\/ws/, (ws) => {
    conns.n += 1
    socket = ws
    ws.onMessage((m) => sent.push(JSON.parse(m)))
    ws.send(JSON.stringify({
      type: 'welcome', nick: 'pikachu', room: 'stub', topic, op: 'mew',
      users: ['pikachu', 'gengar', 'mew'], history: [],
    }))
  })
  await page.goto('/?room=stub')
  await expect(page.getByTestId('status')).toHaveAttribute('title', 'online')
  const push = (f) => socket.send(JSON.stringify(f))
  return { page, sent, conns, push }
}

for (const width of [320, 390, 1280]) {
  test(`long topic is truncated and fits at ${width}px`, async ({ browser }) => {
    const { page } = await open(browser, { width, topic: LONG_TOPIC })
    const topic = page.getByTestId('topic')
    await expect(topic).toContainText('a very long topic')
    const m = await page.evaluate(() => {
      const el = document.documentElement
      const t = document.querySelector('[data-testid=topic]')
      return {
        overflow: el.scrollWidth - el.clientWidth,
        clipped: t.scrollWidth > t.clientWidth,
        right: t.getBoundingClientRect().right,
      }
    })
    expect(m.overflow).toBe(0)
    expect(m.clipped).toBe(true)
    expect(m.right).toBeLessThanOrEqual(width)
    await page.context().close()
  })
}

test('/me, /topic and /kick send the right frames', async ({ browser }) => {
  const { page, sent } = await open(browser)
  const input = page.getByPlaceholder('Message')
  for (const line of ['/me waves', '/topic hello all', '/kick gengar rude']) {
    await input.fill(line)
    await input.press('Enter')
  }
  await expect.poll(() => sent.length).toBe(3)
  expect(sent).toEqual([
    { type: 'say', text: 'waves', omit: [], action: true },
    { type: 'topic', text: 'hello all' },
    { type: 'kick', nick: 'gengar', reason: 'rude' },
  ])
  await page.context().close()
})

test('/topic - sends an empty topic frame', async ({ browser }) => {
  const { page, sent } = await open(browser, { topic: 'cake' })
  await page.getByPlaceholder('Message').fill('/topic -')
  await page.getByPlaceholder('Message').press('Enter')
  await expect.poll(() => sent.length).toBe(1)
  expect(sent).toEqual([{ type: 'topic', text: '' }])
  await page.context().close()
})

test('/topic alone shows the topic locally', async ({ browser }) => {
  const { page, sent } = await open(browser, { topic: 'cake' })
  await page.getByPlaceholder('Message').fill('/topic')
  await page.getByPlaceholder('Message').press('Enter')
  await expect(page.getByTestId('notice').filter({ hasText: 'Topic: cake' }))
    .toHaveCount(1)
  expect(sent).toEqual([])
  await page.context().close()
})

test('topic, action and kick frames render', async ({ browser }) => {
  const { page, push } = await open(browser)
  push({ type: 'topic', nick: 'mew', text: 'new plan' })
  await expect(page.getByTestId('topic')).toContainText('new plan')
  await expect(page.getByTestId('notice')
    .filter({ hasText: 'mew set the topic to: new plan' })).toHaveCount(1)

  push({
    type: 'message', id: 1, ts: 1, sender: 'gengar', text: 'dances',
    masked: false, action: true,
  })
  await expect(page.getByTestId('message')).toContainText('* gengar dances')

  push({ type: 'kick', nick: 'gengar', by: 'mew', reason: 'rude' })
  await expect(page.getByTestId('notice')
    .filter({ hasText: 'gengar was kicked by mew: rude' })).toHaveCount(1)
  await expect(page.getByRole('button', { name: 'gengar' })).toHaveCount(0)
  await page.context().close()
})

test('being kicked shows the reason and stops reconnecting',
  async ({ browser }) => {
    const { page, conns, push } = await open(browser)
    push({ type: 'kick', nick: 'pikachu', by: 'mew', reason: 'spamming' })
    await expect(page.getByTestId('notice')
      .filter({ hasText: 'You were kicked by mew: spamming' })).toHaveCount(1)
    await expect(page.getByTestId('status'))
      .toHaveAttribute('title', 'offline')
    await expect(page.getByPlaceholder('Message')).toBeDisabled()
    await page.waitForTimeout(2000)  // longer than the first backoff
    expect(conns.n).toBe(1)
    await page.context().close()
  })
