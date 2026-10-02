<!--
  Compact theme selector (Light / Dark / Auto) for the header. Sets
  data-bs-theme on <html>; Auto follows the OS colour scheme live. The
  choice is persisted in localStorage when available (index.html applies
  it before first paint). Limitations: one instance expected per page.
-->
<script>
  import {
    THEMES, loadChoice, saveChoice, resolveTheme,
  } from '../lib/theme.js'

  const getStorage = () => localStorage
  const labels = { light: 'Light', dark: 'Dark', auto: 'Auto' }
  let choice = $state(loadChoice(getStorage))

  $effect(() => {
    const mq = matchMedia('(prefers-color-scheme: dark)')
    const apply = () => document.documentElement.setAttribute(
      'data-bs-theme', resolveTheme(choice, mq.matches))
    apply()
    mq.addEventListener('change', apply)
    return () => mq.removeEventListener('change', apply)
  })
</script>

<select
  class="form-select form-select-sm w-auto" aria-label="Theme"
  data-testid="theme" bind:value={choice}
  onchange={() => saveChoice(getStorage, choice)}>
  {#each THEMES as t (t)}
    <option value={t}>{labels[t]}</option>
  {/each}
</select>
