# Discord Bot Architecture

## Overview

**Current Implementation Status: ✅ OPERATIONAL**

Discord → Gateway (WebSocket) → Receiver (HTTP) → Scout (HTTP) → Receiver → Gateway → Discord

The Scout Discord bot is running and processing messages. Components:
- **discord-gateway** (port 3456) - Node.js WebSocket client
- **receiver.py** (port 3000) - Python thin bridge
- **scout-discord-webhook** (port 3001) - Python message processor

Commands: `create ticket for <task>`, `search for <topic>`, `calendar`

## Problem Statement

The current `mcp-discord` setup provides **request-response tools**, not real-time event streaming:

| MCP Tool | What It Does | Limitation |
|----------|--------------|------------|
| `discord_read_messages` | Fetch messages on demand | Only works when called |
| `discord_send` | Send messages on demand | Only works when called |

**The gap:** Discord's real-time messaging requires:
1. Persistent WebSocket connection to Discord Gateway
2. Event listener that runs continuously  
3. Background process independent of MCP call cycles

## Architecture

```
┌─────────────────────┐      HTTP/Webhook      ┌──────────────────┐
│   Discord Bot      │ ◄────────────────────► │  OpenClaw/Scout  │
│   (standalone)     │                        │  (main repo)     │
│                    │                        │                  │
│ • Gateway conn     │  POST /discord/in     │ • Business logic │
│ • Message recv     │  POST /discord/out    │ • LLM parsing    │
│ • Message send     │                        │ • Linear/Notion  │
└─────────────────────┘                        └──────────────────┘
         │                                              │
         ▼                                              ▼
   Discord Gateway                              Other services
   (WebSocket)                                  (Linear, Notion, etc.)
```

## Component Responsibilities

### Discord Bot (Standalone)

**Responsibilities:**
- Authenticate and maintain WebSocket connection to Discord Gateway
- Receive message events → forward to OpenClaw
- Expose HTTP endpoint to receive messages from OpenClaw → send to Discord
- Handle reconnection, heartbeats, rate limits

**Does NOT do:**
- Any business logic
- Ticket parsing or creation
- LLM calls
- Database operations

### OpenClaw (Main Repo)

**Responsibilities:**
- Receive Discord messages via webhook
- Parse and process messages (signal detection, intent classification)
- Execute actions using existing skills (Linear, Notion, etc.)
- Send response messages back to bot via HTTP

## Communication Protocol

### Bot → OpenClaw (Inbound)

```http
POST /discord/in HTTP/1.1
Content-Type: application/json

{
  "type": "discord_message",
  "data": {
    "channelId": "123456789",
    "messageId": "987654321",
    "author": {
      "id": "user123",
      "username": "Flavian",
      " discriminator": "0001"
    },
    "content": "create a ticket for updating my resume",
    "timestamp": 1713034500000,
    "guildId": "5544332211",
    "isDirectMessage": false
  }
}
```

### OpenClaw → Bot (Outbound)

```http
POST /discord/send HTTP/1.1
Content-Type: application/json

{
  "type": "send_message",
  "data": {
    "channelId": "123456789",
    "content": "📋 Created ticket **SEM-99**\nhttps://linear.app/scout/issue/SEM-99",
    "replyTo": "987654321"  // optional message ID to reply to
  }
}
```

### Bot Status (OpenClaw → Bot)

```http
POST /discord/status HTTP/1.1
Content-Type: application/json

{
  "type": "bot_status",
  "data": {
    "status": "online|offline",
    "shard": 0
  }
}
```

## Implementation Notes

### WebSocket vs HTTP

Discord requires WebSocket for receiving events. The bot must:
1. Connect via WebSocket to `wss://gateway.discord.gg`
2. Handle Hello, Heartbeat, and Dispatch events
3. Maintain connection with periodic heartbeats

The bot exposes HTTP for OpenClaw to call back.

### Configuration

Bot environment variables:
```
DISCORD_TOKEN=          # Bot token from Discord Developer Portal
OPENCLAW_WEBHOOK_URL=   # Where to send incoming messages
OPENCLAW_HTTP_URL=      # Where bot receives commands to send
PORT=3456               # HTTP server port
LOG_LEVEL=info          # Logging level
```

### Channels & Filtering

Bot should:
- Listen to specific channels (configurable list)
- Optionally filter by keywords or patterns
- Ignore messages from bots (except webhook bots)
- Support DMs for direct interactions

### Error Handling

- Discord Gateway disconnects → bot should auto-reconnect with backoff
- OpenClaw unreachable → queue messages, retry with TTL
- Rate limits → respect Discord's rate limit headers

## Security Considerations

1. **Token storage** - Bot token should be in environment variables, not in code
2. **Webhook authentication** - Consider HMAC signature verification for bot ↔ OpenClaw
3. **Channel permissions** - Bot should only read from allowed channels
4. **Rate limiting** - Never exceed Discord's 120 msgs/sec per channel

## Deployment Options

| Option | Pros | Cons |
|--------|------|------|
| systemd service | Survives reboots, auto-restart | Requires shell access |
| Docker container | Portable, isolated | More complexity |
| tmux/screen | Simple | Manual recovery |
| Fly.io/Railway | Managed, scaling | Vendor lock-in |

Recommended: **systemd service** or **Docker** with health checks.