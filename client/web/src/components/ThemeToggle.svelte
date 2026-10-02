<!--
  Theme toggle button for the header. Shows the scheme it will switch to;
  clicking flips data-bs-theme on <html> and saves the explicit choice in
  localStorage when available (index.html applies the initial scheme
  before first paint). Limitations: one instance expected per page.
-->
<script>
  import {
    initialTheme, otherTheme, saveChoice,
  } from '../lib/theme.js'

  const getStorage = () => localStorage
  const icons = { light: '☀', dark: '☾' }
  let theme = $state(initialTheme(getStorage))
  let target = $derived(otherTheme(theme))

  $effect(() => {
    document.documentElement.setAttribute('data-bs-theme', theme)
  })

  /** Flip the scheme and remember it. */
  function flip() {
    theme = target
    saveChoice(getStorage, theme)
  }
</script>

<button
  type="button" class="btn btn-sm btn-outline-secondary text-nowrap"
  aria-label="Switch to {target} theme" title="Switch to {target} theme"
  data-testid="theme" onclick={flip}>
  <span aria-hidden="true">{icons[target]}</span> {target}
</button>
