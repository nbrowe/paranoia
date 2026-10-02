/*
 * Vite and Vitest configuration for the Paranoia web client.
 * Scope: Svelte plugin, build output in dist/, one-shot test runs.
 * Limitations: tests run in the plain Node environment (core logic only).
 */
import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig({
  plugins: [svelte()],
  test: { include: ['src/**/*.test.js'] },
})
