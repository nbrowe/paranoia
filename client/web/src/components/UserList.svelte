<!--
  Sidebar listing users in the room. Each other user has a checkbox that
  toggles them in the sticky omit list. Limitations: stateless; the omit
  list lives in the parent.
-->
<script>
  let { users, nick, omit, ontoggle } = $props()
</script>

<aside
  class="border-start overflow-auto p-2" data-testid="user-list"
  style="width: 12rem">
  <div class="small text-muted mb-1">Users ({users.length}) - tick to omit</div>
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
