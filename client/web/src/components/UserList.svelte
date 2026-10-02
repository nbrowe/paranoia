<!--
  Sidebar listing users in the room. Each other user is a toggle button
  (aria-pressed) that adds/removes them from the sticky omit list; your
  own nick is a plain chip and cannot be omitted. Buttons sit in a
  three-column grid of equal cells (each at most a third of the list, so
  rows line up and wrap); long nicks truncate (full nick in the title).
  Responsive: below md the list is collapsed behind a "Users (N)" toggle
  and expands inline with a bounded height; from md up it is a side
  column. Either way the grid scrolls vertically when the buttons
  overflow it.
  Limitations: stateless apart from the toggle; the omit list lives in
  the parent.
-->
<script>
  let { users, nick, omit, ontoggle } = $props()
  let open = $state(false)
</script>

<aside
  class="users col-md-3 d-md-flex flex-column overflow-md-hidden p-2"
  data-testid="user-list">
  <button
    type="button" class="btn btn-sm btn-outline-secondary d-md-none w-100"
    aria-expanded={open} aria-controls="user-list-body"
    data-testid="user-toggle" onclick={() => { open = !open }}>
    Users ({users.length}) {open ? '▴' : '▾'}
  </button>
  <div class="small text-muted mb-1 d-none d-md-block">
    Users ({users.length}) - click to omit
  </div>
  <div
    id="user-list-body"
    class="grid {open ? 'd-grid' : 'd-none'} d-md-grid gap-1
      mt-2 mt-md-0">
    {#each users as u (u)}
      {#if u === nick}
        <span
          class="user border rounded bg-body-tertiary fw-bold small px-2
            py-1 text-center" title={u}>{u} (you)</span>
      {:else}
        <button
          type="button" title={u} aria-pressed={omit.includes(u)}
          class="user btn btn-sm {omit.includes(u)
            ? 'btn-danger text-decoration-line-through'
            : 'btn-outline-secondary'}"
          onclick={() => ontoggle(u)}>
          <span aria-hidden="true">{omit.includes(u) ? '⊘ ' : ''}</span>{u}
        </button>
      {/if}
    {/each}
  </div>
</aside>

<style>
  .users {
    border-top: var(--bs-border-width) solid var(--bs-border-color);
  }
  /* Phones: bounded box that scrolls; md+: fills the side column. */
  .grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
    max-height: 40vh;
    overflow-y: auto;
    align-content: flex-start;
  }
  .user {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  /* Readable idle buttons in both themes (secondary text is too faint). */
  .user.btn-outline-secondary {
    --bs-btn-color: var(--bs-body-color);
    --bs-btn-border-color: var(--bs-border-color);
  }
  @media (min-width: 768px) {
    .users {
      border-top: 0;
      border-left: var(--bs-border-width) solid var(--bs-border-color);
    }
    .grid {
      flex: 1 1 auto;
      min-height: 0;
      max-height: none;
    }
    .overflow-md-hidden {
      overflow: hidden;
    }
  }
</style>
