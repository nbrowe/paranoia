/*
 * Vite and Vitest configuration for the Paranoia web client.
 * Scope: Svelte plugin, dev proxy of /ws and /healthz to the server
 * (VITE_PROXY_TARGET, default http://localhost:8000; note that inside the
 * npmw container "localhost" is the container, see README), one-shot
 * test runs. The dev and preview servers always listen on port 5000
 * inside the container; hosts map to it (npmw, e2e/compose.yaml).
 * Limitations: tests run in plain Node (core logic only).
 */
import { defineConfig, loadEnv } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.VITE_PROXY_TARGET || 'http://localhost:8000'
  return {
    plugins: [svelte()],
    server: {
      host: true,
      port: 5000,
      strictPort: true,
      proxy: {
        '/ws': { target, ws: true },
        '/healthz': { target },
      },
    },
    preview: { host: true, port: 5000, strictPort: true },
    test: { include: ['src/**/*.test.js'] },
  }
})
