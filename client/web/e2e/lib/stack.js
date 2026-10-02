/*
 * Helpers for talking to the stack under test from inside a test run.
 * Scope: health polling and restarting the server container through the
 * Podman REST API on a mounted unix socket (see ./run).
 * Limitations: restart needs E2E_PODMAN_SOCK; there is no CLI in the
 * Playwright image, so the compat API is called directly.
 */
import http from 'node:http'

export const SERVER_URL = process.env.E2E_SERVER_URL || 'http://localhost:18000'
export const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:15173'
const SOCK = process.env.E2E_PODMAN_SOCK || '/run/podman.sock'
const CONTAINER = process.env.E2E_SERVER_CONTAINER || 'paranoia-e2e-server'

/**
 * Poll a URL until it returns a 2xx status.
 * @param {string} url URL to fetch
 * @param {number} [timeoutMs] give up after this long
 * @returns {Promise<void>} resolves once the URL is healthy
 */
export async function waitFor(url, timeoutMs = 60000) {
  const deadline = Date.now() + timeoutMs
  for (;;) {
    try {
      const res = await fetch(url)
      if (res.ok) return
    } catch { /* not up yet */ }
    if (Date.now() > deadline) throw new Error(`timed out waiting for ${url}`)
    await new Promise((r) => setTimeout(r, 500))
  }
}

/**
 * Restart the server container and wait until it is healthy again.
 * @returns {Promise<void>} resolves when /healthz answers
 */
export async function restartServer() {
  await new Promise((resolve, reject) => {
    const req = http.request({
      socketPath: SOCK,
      path: `/v4.0.0/libpod/containers/${CONTAINER}/restart?t=1`,
      method: 'POST',
    }, (res) => {
      res.resume()
      res.on('end', () => (res.statusCode < 300
        ? resolve() : reject(new Error(`restart failed: ${res.statusCode}`))))
    })
    req.on('error', reject)
    req.end()
  })
  await waitFor(`${SERVER_URL}/healthz`)
}
