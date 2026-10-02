<!--
  Message input bar with the active omit list shown above it. Submitting
  calls onsend(text); the field clears only if the frame was sent.
  Limitations: length (500) is enforced by the server, not here.
-->
<script>
  let { omit, disabled, onsend, onclear, onremove } = $props()
  let text = $state('')
  let input

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
  <div class="small mb-1">
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
  <div class="input-group">
    <input
      class="form-control" placeholder="Message" maxlength="500"
      autocomplete="off" bind:this={input} bind:value={text} {disabled} />
    <button class="btn btn-primary" {disabled}>Send</button>
  </div>
</form>
