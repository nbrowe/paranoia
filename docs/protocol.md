# Paranoia wire protocol (v1)

This document is the contract between the server and every client (TUI,
desktop, web). If code and this document disagree, fix one of them.

## Transport

- WebSocket at `ws://<host>:<port>/ws`; optional query `?room=<name>`
  (default `lobby`). Rooms are created on first join.
- Every frame is a UTF-8 JSON text frame: an object with a `"type"` key.
- `GET /healthz` returns `200 {"status": "ok"}` for container health checks.
- Unknown `type` values from the client produce an `error` frame; clients
  must ignore unknown `type` values from the server (forward compatibility).

## Identity

There are no accounts. On connect the server assigns the connection a
random nickname drawn from the first 821 Pokemon (the lowercase PokeAPI
slug, e.g. `bulbasaur`, `mr-mime`, `nidoran-f`), skipping nicknames already
in use in that room. The nickname lasts for the life of the connection.
If every nickname is taken the server sends `error` (`room_full`) and
closes the socket.

## Client -> server

| type  | fields                                   | notes                      |
|-------|------------------------------------------|----------------------------|
| `say` | `text: string`, `omit: string[]` (opt.), `action: bool` (opt.) | send a message to the room |
| `topic` | `text: string`                         | set the room topic         |
| `kick` | `nick: string`, `reason: string` (opt.) | remove a user (ops only)  |

- `text` is stripped of leading/trailing whitespace; must be 1-500
  characters after stripping, else `error` (`bad_text`).
- `omit` lists nicknames that must not be able to read the message.
  Own nickname and duplicates are ignored. Nicknames not currently present
  are accepted (they apply to the stored message, so a user who later
  joins under an omitted nickname sees it masked in history).
- `action: true` marks an IRC-style `/me` message: clients render it as
  `* nick text` instead of `<nick> text`. Omission and masking work the
  same as for normal messages.
- `topic`: any user may set it (IRC without `+t`). `text` is stripped and
  may be empty (clears the topic); max 200 characters, else `error`
  (`bad_text`). The server broadcasts a `topic` frame to everyone,
  including the setter.
- `kick`: only the room operator may kick. The operator is the user who
  has been connected longest; when they leave it passes to the next
  oldest. `nick` must be present and not the operator's own nickname.
  `reason` is stripped, max 200 characters, default empty. Everyone,
  including the target, receives a `kick` frame, then the server closes
  the target's socket. A kicked user may reconnect (new nickname). Errors:
  `not_op`, `no_such_nick`, `bad_target` (self).
- The "sticky omit list" is client UX only; the server keeps no per-user
  omit state. Clients send the current list with every `say`.

## Server -> client

| type      | fields                                                         |
|-----------|----------------------------------------------------------------|
| `welcome` | `nick`, `room`, `users: string[]`, `topic: string`, `op: string`, `history: Message[]` |
| `join`    | `nick`                                                         |
| `leave`   | `nick`                                                         |
| `message` | a `Message` (below)                                            |
| `topic`   | `nick` (who set it), `text`                                    |
| `kick`    | `nick` (target), `by`, `reason`                                |
| `op`      | `nick` (new operator; sent when the operator leaves)           |
| `error`   | `code: string`, `message: string`                              |

`welcome` is always the first frame. `users` includes the recipient.
`topic` is `""` when unset; `op` is the current operator's nickname.
A kicked user is not followed by a `leave` frame for that user: `kick`
replaces it. If the kicked user was never the operator, `op` is unchanged.

### Message

```json
{
  "type": "message",
  "id": 42,
  "ts": 1767312000.123,
  "sender": "pikachu",
  "text": "meet at noon",
  "masked": false,
  "omitted": ["gengar"]
}
```

- `id`: integer, monotonically increasing per room.
- `ts`: server time, Unix seconds (float).
- `action`: `true` only for `/me` messages; absent otherwise.
- `masked`: `true` if this recipient was omitted. Then `text` is the
  original with every non-whitespace character replaced by `*`
  (whitespace and length preserved). **The server performs masking; the
  real text is never sent to an omitted recipient.**
- `omitted`: present ONLY in the copy sent to the sender (and in the
  sender's own history copy): the effective list of omitted nicknames,
  sorted. Other recipients never learn who was omitted.
- The sender always sees their own real text, `masked: false`.
- History entries inside `welcome` are `Message` objects without the
  `"type"` key, rendered for the joining recipient by the same rules.
  Up to the last 100 messages are retained per room, in memory only.

### Error codes

`bad_json`, `bad_text`, `unknown_type`, `room_full`, `not_op`,
`no_such_nick`, `bad_target`.
Errors other than `room_full` do not close the connection.

## Client UX conventions (non-normative)

- Slash commands (all clients; the web client uses its single input box):
  `/help` (client-side list), `/omit [nick...]` (sets the sticky list;
  alone clears it), `/me <action>`, `/kick <nick> [reason]`,
  `/topic [text]` (alone shows the current topic from the last
  `welcome`/`topic` frame). A leading `//` sends a literal `/`. Unknown
  commands are reported locally, not sent. The active omit list is shown
  in the input prompt/status line. Masked messages should be visibly
  distinguishable. A `kick` frame naming your own nickname means you were
  removed: show the reason and stop reconnecting.
