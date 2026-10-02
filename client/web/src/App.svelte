<!--
  Root component: owns the chat state, wires the WebSocket connection to
  the reducer in lib/state.js, and lays out header (logo mark, title,
  room, status dot, settings, topic), timeline, user list and input. Input
  lines (text and slash commands) go through lib/commands.js. A kick of
  our own nick closes the socket for good. Scope: layout and wiring only. Limitations: single room per page load (taken from
  ?room=).
-->
<script>
  import { untrack } from 'svelte'
  import { connect } from './lib/connection.js'
  import { wsUrl } from './lib/protocol.js'
  import { handleInput } from './lib/commands.js'
  import {
    initialState, applyFrame, setStatus, toggleOmit, clearOmit,
  } from './lib/state.js'
  import MessageList from './components/MessageList.svelte'
  import UserList from './components/UserList.svelte'
  import MessageInput from './components/MessageInput.svelte'
  import SettingsMenu from './components/SettingsMenu.svelte'

  // Raw state: the reducer returns fresh objects, no deep proxying needed.
  let s = $state.raw(initialState())
  let conn

  $effect(() => {
    // connect() calls onStatus synchronously; keep that out of the effect
    conn = untrack(() => connect({
      url: wsUrl(location, import.meta.env.VITE_WS_URL),
      onFrame: (frame) => {
        s = applyFrame(s, frame)
        if (s.kicked) conn.close()  // stop the reconnect loop
      },
      onStatus: (status) => { s = setStatus(s, status) },
    }))
    return () => conn.close()
  })

  const dot = {
    open: 'bg-success',
    connecting: 'bg-warning',
    disconnected: 'bg-danger',
  }
  const label = {
    open: 'online',
    connecting: 'connecting',
    disconnected: 'offline',
  }

  /**
   * Run an input line: plain text or a slash command (lib/commands.js).
   * @param {string} text raw input
   * @returns {boolean} true if handled and every frame went out
   */
  function send(text) {
    const r = handleInput(s, text)
    s = r.state
    return r.frames.every((f) => conn.send(f))
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
      <span
        class="status-dot rounded-circle flex-shrink-0 {dot[s.status]}"
        role="img" aria-label={label[s.status]} title={label[s.status]}
        data-testid="status"></span>
      <SettingsMenu />
    </span>
    {#if s.topic}
      <div
        class="w-100 small text-truncate" data-testid="topic"
        title={s.topic}>
        <span class="text-muted">Topic:</span> {s.topic}</div>
    {/if}
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
  .status-dot {
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
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
