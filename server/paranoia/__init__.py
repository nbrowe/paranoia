"""Paranoia chat server package.

Purpose: real-time chat where senders can omit users from reading a
message (omitted users get a server-side masked copy).
Scope: implements docs/protocol.md v1; see app.py for the entrypoint.
Limitations: single process, in-memory state only.
"""
