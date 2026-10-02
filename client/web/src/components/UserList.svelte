<!--
  Sidebar listing users in the room. Each other user has a checkbox that
  toggles them in the sticky omit list. Responsive: below md the list is
  collapsed behind a "Users (N)" toggle and expands inline (no nested
  scroll box; the parent scrolls); from md up it is a side column.
  Limitations: stateless apart from the toggle; the omit list lives in
  the parent.
-->
<script>
  let { users, nick, omit, ontoggle } = $props()
  let open = $state(false)
</script>

<aside class="users col-md-3 overflow-md-auto p-2" data-testid="user-list">
  <button
    type="button" class="btn btn-sm btn-outline-secondary d-md-none w-100"
    aria-expanded={open} aria-controls="user-list-body"
    data-testid="user-toggle" onclick={() => { open = !open }}>
    Users ({users.length}) {open ? '▴' : '▾'}
  </button>
  <div class="small text-muted mb-1 d-none d-md-block">
    Users ({users.length}) - tick to omit
  </div>
  <div
    id="user-list-body"
    class="{open ? 'd-block' : 'd-none'} d-md-block mt-2 mt-md-0">
    {#each users as u (u)}
      {#if u === nick}
        <div class="fw-bold">{u} (you)</div>
      {:else}
        <label class="form-check d-block {omit.includes(u)
          ? 'text-danger' : ''}">
          <input
            type="checkbox" class="form-check-input"
            checked={omit.includes(u)} onchange={() => ontoggle(u)} />
          {u}
        </label>
      {/if}
    {/each}
  </div>
</aside>

<style>
  .users {
    border-top: var(--bs-border-width) solid var(--bs-border-color);
  }
  @media (min-width: 768px) {
    .users {
      border-top: 0;
      border-left: var(--bs-border-width) solid var(--bs-border-color);
    }
    .overflow-md-auto {
      overflow: auto;
    }
  }
</style>
