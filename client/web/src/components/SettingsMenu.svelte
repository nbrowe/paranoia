<!--
  Settings menu: a gear button in the header that opens a panel with the
  theme toggle and the build id. From the md breakpoint up the panel is a
  popover dropped below the button, right-aligned; below it, a centred
  dialog over a dimmed backdrop (with a close button). Both close on
  backdrop (outside) click or Escape. Same markup for both; CSS decides
  the presentation. The panel stays mounted (hidden) so the theme toggle
  keeps its state. Limitations: no focus trap; one instance per page.
-->
<script>
  import ThemeToggle from './ThemeToggle.svelte'

  const buildId = import.meta.env.VITE_BUILD_ID || 'dev'
  let open = $state(false)
  let button
  let panel

  /** Open the menu and move focus into it. */
  function show() {
    open = true
    queueMicrotask(() => panel?.focus())
  }

  /** Close the menu and return focus to the gear button. */
  function close() {
    if (!open) return
    open = false
    button?.focus()
  }

  /**
   * Close on Escape.
   * @param {KeyboardEvent} e key event
   */
  function onkeydown(e) {
    if (e.key === 'Escape') close()
  }
</script>

<svelte:window {onkeydown} />

<span class="position-relative">
  <button
    bind:this={button} type="button"
    class="btn btn-sm btn-outline-secondary settings-btn"
    aria-label="Settings" title="Settings" aria-haspopup="dialog"
    aria-expanded={open} data-testid="settings"
    onclick={() => (open ? close() : show())}>
    <span aria-hidden="true">⚙&#xFE0E;</span>
  </button>
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
  <div
    class="backdrop" class:d-none={!open} data-testid="settings-backdrop"
    onclick={close}></div>
  <div
    bind:this={panel} tabindex="-1" role="dialog" aria-label="Settings"
    class="panel card shadow" class:d-none={!open}
    data-testid="settings-menu">
    <div class="card-body p-3">
      <div class="d-flex align-items-center mb-2">
        <strong class="me-auto">Settings</strong>
        <button
          type="button" class="btn-close d-md-none" aria-label="Close"
          data-testid="settings-close" onclick={close}></button>
      </div>
      <div class="d-flex align-items-center justify-content-between">
        <span>Theme</span>
        <ThemeToggle />
      </div>
      <div class="small text-muted mt-3" data-testid="build-id">
        Build {buildId}</div>
    </div>
  </div>
</span>

<style>
  .settings-btn {
    width: 2rem;
    height: 2rem;
    padding: 0;
    line-height: 1;
  }
  /* Phones: centred dialog over a dimmed backdrop. */
  .backdrop {
    position: fixed;
    inset: 0;
    z-index: 1040;
    background: rgba(0, 0, 0, 0.5);
  }
  .panel {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: min(20rem, calc(100vw - 2rem));
    z-index: 1045;
  }
  /* md and up: popover below the button, right-aligned; the backdrop is
     invisible but still catches outside clicks, with the gear above it
     so a second click toggles the menu shut. */
  @media (min-width: 768px) {
    .settings-btn {
      position: relative;
      z-index: 1045;
    }
    .backdrop {
      background: transparent;
    }
    .panel {
      position: absolute;
      top: 100%;
      left: auto;
      right: 0;
      transform: none;
      width: 16rem;
      margin-top: 0.25rem;
    }
  }
</style>
