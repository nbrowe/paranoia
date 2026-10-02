<!--
  Sidebar listing users in the room. Each other user has a checkbox that
  toggles them in the sticky omit list. Responsive: a short wrapping strip
  under the timeline on narrow screens, a side column from md up.
  Limitations: stateless; the omit list lives in the parent.
-->
<script>
  let { users, nick, omit, ontoggle } = $props()
</script>

<aside
  class="users col-md-3 overflow-auto p-2
    d-flex flex-wrap column-gap-3 d-md-block"
  data-testid="user-list">
  <div class="small text-muted mb-1 w-100">Users ({users.length}) - tick to omit</div>
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
</aside>

<style>
  .users {
    max-height: 25vh;
    border-top: var(--bs-border-width) solid var(--bs-border-color);
  }
  @media (min-width: 768px) {
    .users {
      max-height: none;
      border-top: 0;
      border-left: var(--bs-border-width) solid var(--bs-border-color);
    }
  }
</style>
