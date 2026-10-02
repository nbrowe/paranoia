<!--
  Root component: owns the chat state, wires the WebSocket connection to
  the reducer in lib/state.js, and lays out header (logo mark, title,
  room, status, theme), timeline, user list and input. Scope: layout and
  wiring only. Limitations: single room per page load (taken from
  ?room=).
-->
<script>
  import { untrack } from 'svelte'
  import { connect } from './lib/connection.js'
  import { wsUrl, buildSay } from './lib/protocol.js'
  import {
    initialState, applyFrame, setStatus, toggleOmit, clearOmit,
  } from './lib/state.js'
  import MessageList from './components/MessageList.svelte'
  import UserList from './components/UserList.svelte'
  import MessageInput from './components/MessageInput.svelte'
  import ThemeSelect from './components/ThemeSelect.svelte'

  // Raw state: the reducer returns fresh objects, no deep proxying needed.
  let s = $state.raw(initialState())
  let conn

  $effect(() => {
    // connect() calls onStatus synchronously; keep that out of the effect
    conn = untrack(() => connect({
      url: wsUrl(location, import.meta.env.VITE_WS_URL),
      onFrame: (frame) => { s = applyFrame(s, frame) },
      onStatus: (status) => { s = setStatus(s, status) },
    }))
    return () => conn.close()
  })

  const badge = {
    open: 'text-bg-success',
    connecting: 'text-bg-warning',
    disconnected: 'text-bg-danger',
  }
  const label = {
    open: 'online',
    connecting: 'connecting',
    disconnected: 'offline',
  }

  /**
   * Send the text with the current omit list.
   * @param {string} text raw input
   * @returns {boolean} true if the frame went out
   */
  function send(text) {
    const frame = buildSay(text, s.omit)
    return frame !== null && conn.send(frame)
  }
</script>

<div class="d-flex flex-column vh-100">
  <header class="d-flex flex-wrap align-items-center gap-2 p-2 border-bottom">
    <img src="/logo.svg" alt="" width="26" height="26">
    <strong>Paranoia</strong>
    {#if s.room}
      <span class="text-muted text-truncate room">#{s.room}</span>
    {/if}
    <span class="ms-auto d-flex align-items-center gap-2 mw-100 who">
      <span class="text-truncate">
        <span class="d-none d-sm-inline">you are</span>
        <strong data-testid="nick">{s.nick ?? '—'}</strong></span>
      <span class="badge {badge[s.status]}" data-testid="status">
        {label[s.status]}</span>
      <ThemeSelect />
    </span>
  </header>

  <div
    class="panes d-flex flex-column flex-md-row flex-grow-1">
    <MessageList items={s.items} nick={s.nick} />
    <UserList
      users={s.users} nick={s.nick} omit={s.omit}
      ontoggle={(n) => { s = toggleOmit(s, n) }} />
  </div>

  <MessageInput
    omit={s.omit} disabled={s.status !== 'open'} onsend={send}
    onclear={() => { s = clearOmit(s) }}
    onremove={(n) => { s = toggleOmit(s, n) }} />
</div>

<style>
  /* Phones: the header wraps to a second line; long names truncate. */
  .room {
    flex: 1 1 4rem;
    min-width: 0;
  }
  .who {
    min-width: 0;
  }
  /* Phones: the pane scrolls so the timeline keeps a usable minimum
     height beside the (height-bounded) user list. */
  .panes {
    overflow: auto;
  }
  .panes :global([data-testid="timeline"]) {
    min-height: 50vh;
  }
  @media (min-width: 768px) {
    .panes {
      overflow: hidden;
    }
    .panes :global([data-testid="timeline"]) {
      min-height: 0;
    }
  }
</style>
