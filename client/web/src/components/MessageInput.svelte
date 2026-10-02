<!--
  Message input bar with the active omit list shown above it. Submitting
  calls onsend(text); the field clears only if the frame was sent.
  The field takes focus when it becomes enabled, unless the user already
  focused something else. Limitations: length (500) is enforced by the
  server, not here.
-->
<script>
  let { omit, disabled, onsend, onclear, onremove } = $props()
  let text = $state('')
  let input

  $effect(() => {
    const idle = [null, document.body].includes(document.activeElement)
    if (!disabled && idle) input.focus()
  })

  /**
   * Send the current text and refocus the field.
   * @param {SubmitEvent} e form submit event
   */
  function submit(e) {
    e.preventDefault()
    if (onsend(text)) text = ''
    input.focus()
  }
</script>

<form class="border-top p-2" onsubmit={submit}>
  <div class="small mb-1" data-testid="omit-bar">
    {#if omit.length}
      <span class="text-danger">Omitting:</span>
      {#each omit as n (n)}
        <button
          type="button" class="btn btn-sm btn-outline-danger py-0"
          title="Stop omitting {n}" onclick={() => onremove(n)}>{n} &times;
        </button>
      {/each}
      <button type="button" class="btn btn-sm btn-link py-0" onclick={onclear}>
        clear</button>
    {:else}
      <span class="text-muted">Omitting nobody</span>
    {/if}
  </div>
  <div class="d-flex gap-2">
    <input
      class="form-control rounded-pill px-3" placeholder="Message"
      maxlength="500" autocomplete="off" bind:this={input} bind:value={text} {disabled} />
    <button class="btn btn-primary rounded-pill px-4" {disabled}>Send</button>
  </div>
</form>
