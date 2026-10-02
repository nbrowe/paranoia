/*
 * Playwright configuration for the Paranoia web client e2e suite.
 * Scope: Chromium only, one worker (tests share one server and the
 * reconnect test restarts it), list + JUnit reporters. URLs come from
 * E2E_BASE_URL (web) and E2E_SERVER_URL (server), set by ./run.
 * Limitations: expects the stack to be up; see ./run and README.md.
 */
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  globalSetup: './lib/global-setup.js',
  workers: 1,
  fullyParallel: false,
  retries: 0,
  timeout: 30000,
  expect: { timeout: 7000 },
  reporter: [
    ['list'],
    ['junit', { outputFile: 'test-results/junit.xml' }],
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:15173',
    trace: 'retain-on-failure',
    ...devices['Desktop Chrome'],
  },
})
