<!--
  Scrolling timeline of messages and notices. Auto-scrolls to the newest
  entry unless the user has scrolled up. Masked messages are muted italic;
  own messages show who was omitted. Limitations: renders the whole
  (capped) timeline; no virtualization.
-->
<script>
  import { tick } from 'svelte'

  let { items, nick } = $props()
  let el
  let stick = true

  /**
   * Format a unix-seconds timestamp as HH:MM.
   * @param {number} ts server time
   * @returns {string} local time
   */
  function clock(ts) {
    return new Date(ts * 1000).toLocaleTimeString([], {
      hour: '2-digit', minute: '2-digit',
    })
  }

  /** Remember whether the user is pinned to the bottom. */
  function onscroll() {
    stick = el.scrollHeight - el.scrollTop - el.clientHeight < 40
  }

  $effect(() => {
    const last = items.at(-1)
    if (last?.sender === nick) stick = true  // always follow own messages
    if (stick) tick().then(() => { el.scrollTop = el.scrollHeight })
  })
</script>

<div
  class="flex-grow-1 overflow-auto p-2" data-testid="timeline"
  bind:this={el} {onscroll}>
  {#each items as it (it.key)}
    {#if it.kind === 'notice'}
      <div data-testid="notice" class="small fst-italic {it.level === 'error'
        ? 'text-danger' : 'text-muted'}">* {it.text}</div>
    {:else}
      <div
        data-testid="message"
        class={it.masked ? 'text-muted fst-italic' : ''}>
        <span class="text-muted small">{clock(it.ts)}</span>
        <strong
          data-testid="sender"
          class={it.sender === nick ? 'text-primary' : ''}>
          {it.sender}</strong>
        <span class="text-break" data-testid="text">{it.text}</span>
        {#if it.omitted?.length}
          <span class="badge text-bg-secondary" data-testid="omitted">
            hidden from {it.omitted.join(', ')}</span>
        {/if}
      </div>
    {/if}
  {/each}
</div>
