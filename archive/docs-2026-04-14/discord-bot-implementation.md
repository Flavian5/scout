# Discord Bot Implementation Guide

> **⚠️ DEPRECATED** - This document describes the old standalone Discord bot implementation that has been removed. The system now uses **OpenClaw native Discord integration**.

## Status: REMOVED

The standalone Discord gateway described in this document has been **removed** from the system. The services were:

- `discord-gateway/` (port 3456) - Node.js WebSocket client
- `receiver.py` (port 3000) - Python thin bridge
- `scout-discord-webhook/` (port 3001) - Python message processor

## Current Implementation

OpenClaw now natively handles Discord integration via its hooks system:

- **Hook Handler**: `hooks/discord-commands/handler.ts`
- **Dispatcher**: `scripts/hook_dispatcher.py`
- **Skills**: `skills/email_alerts/`, `skills/gog/`, `skills/calendar_confirm/`

## If You Need to Rebuild

This document is kept for reference only. If you need to rebuild the standalone gateway in the future:

1. The code examples in this document show the old architecture
2. That architecture required 3 separate services communicating via HTTP
3. The current approach uses OpenClaw's built-in hook system instead

## See Also

- [Discord Bot Architecture](./discord-bot-architecture.md) - Current setup