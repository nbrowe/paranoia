/*
 * Playwright global setup: waits until the stack under test answers.
 * Scope: polls the server /healthz and the web client origin.
 * Limitations: fails the run after 60 s; does not start anything.
 */
import { SERVER_URL, BASE_URL, waitFor } from './stack.js'

/**
 * Block until both the server and the web client respond with 2xx.
 * @returns {Promise<void>} resolves when the stack is reachable
 */
export default async function globalSetup() {
  await waitFor(`${SERVER_URL}/healthz`)
  await waitFor(`${BASE_URL}/healthz`)  // proxied through the web service
}
