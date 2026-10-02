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
| `say` | `text: string`, `omit: string[]` (opt.)  | send a message to the room |

- `text` is stripped of leading/trailing whitespace; must be 1-500
  characters after stripping, else `error` (`bad_text`).
- `omit` lists nicknames that must not be able to read the message.
  Own nickname and duplicates are ignored. Nicknames not currently present
  are accepted (they apply to the stored message, so a user who later
  joins under an omitted nickname sees it masked in history).
- The "sticky omit list" is client UX only; the server keeps no per-user
  omit state. Clients send the current list with every `say`.

## Server -> client

| type      | fields                                                         |
|-----------|----------------------------------------------------------------|
| `welcome` | `nick`, `room`, `users: string[]`, `history: Message[]`        |
| `join`    | `nick`                                                         |
| `leave`   | `nick`                                                         |
| `message` | a `Message` (below)                                            |
| `error`   | `code: string`, `message: string`                              |

`welcome` is always the first frame. `users` includes the recipient.

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

`bad_json`, `bad_text`, `unknown_type`, `room_full`.
Errors other than `room_full` do not close the connection.

## Client UX conventions (non-normative)

- Omit commands in text clients: `/omit alice bob` sets the sticky list,
  `/omit` alone clears it, and the active list is shown in the input
  prompt/status line. Masked messages should be visibly distinguishable.
