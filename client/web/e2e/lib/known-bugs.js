/*
 * Registry of known application bugs that block the e2e tests.
 * Scope: one flag per bug; tests call test.fixme(FLAG, REASON) first, so
 * flipping a flag to false re-enables them once the bug is fixed.
 * Limitations: remove this file when no flags remain.
 */

/*
 * App.svelte calls connect() inside $effect; connect() synchronously calls
 * onStatus, which reads and writes the $state `s`, so the effect tracks `s`
 * and re-runs on every state change: it closes the socket and opens a new
 * one in a loop, so the page never settles (nick/status flap, welcome is
 * lost). Fix: wrap the connect() call in untrack() from 'svelte'.
 */
export const WS_EFFECT_LOOP = true
export const WS_EFFECT_LOOP_REASON =
  'App.svelte $effect tracks state via connect() -> onStatus; ' +
  'reconnect loop (see known-bugs.js)'
