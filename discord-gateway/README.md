# Discord Gateway

A standalone Discord bot that provides real-time bidirectional messaging with Discord's Gateway API. This bridges the gap where `mcp-discord` only provides request-response tools.

## Features

- **WebSocket Connection**: Persistent connection to Discord Gateway for real-time events
- **Message Forwarding**: Automatically forwards Discord messages to configured webhook
- **HTTP API**: Exposes endpoints to send messages back to Discord
- **Channel Filtering**: Listen to specific channels or all channels
- **Bot Filtering**: Option to ignore messages from other bots

## Quick Start

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Configure environment
cp .env.example .env
# Edit .env with your Discord bot token

# Start the gateway
npm start
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Bot token from Discord Developer Portal |
| `OPENCLAW_WEBHOOK_URL` | No | - | Webhook URL to forward incoming messages |
| `OPENCLAW_HTTP_URL` | No | - | URL for receiving outbound messages |
| `PORT` | No | 3456 | HTTP server port |
| `LOG_LEVEL` | No | info | Logging level |
| `LISTEN_CHANNELS` | No | all | Comma-separated channel IDs |
| `IGNORE_BOTS` | No | true | Ignore messages from other bots |

## API Endpoints

### `GET /health`
Health check endpoint.

### `GET /status`
Returns bot status and available endpoints.

### `POST /send`
Send a message to a Discord channel.

Request body:
```json
{
  "type": "send_message",
  "data": {
    "channelId": "123456789",
    "content": "Hello from the gateway!",
    "replyTo": "987654321"  // optional
  }
}
```

## Message Flow

```
Discord → Gateway (WebSocket) → Your App (Webhook POST)
Your App → Gateway (HTTP POST /send) → Discord
```

## Architecture

```
┌─────────────────────┐      HTTP/Webhook      ┌──────────────────┐
│   Discord Bot       │ ◄────────────────────► │  Your App       │
│   (Gateway)         │                        │                 │
│                     │  POST /send           │  Business logic │
│ • Gateway conn      │  POST /discord/in     │  LLM parsing   │
│ • Message recv     │                        │  etc.          │
│ • Message send     │                        │                 │
└─────────────────────┘                        └─────────────────┘
         │                                              │
         ▼                                              ▼
   Discord Gateway                              Other services
   (WebSocket)                                (Linear, Notion, etc.)
```

## Discord Developer Portal Setup

1. Create a new application at https://discord.com/developers/applications
2. Add a Bot to your application
3. Enable these Privileged Gateway Intents:
   - **Message Content Intent** (required for reading message content)
4. Save your Bot Token (keep it secret!)
5. Generate an invite link with appropriate permissions

## Docker

```bash
# Build
docker build -t discord-gateway .

# Run
docker run -d --env-file .env discord-gateway
```

## Development

```bash
# Run in development mode with hot reload
npm run dev

# Build TypeScript
npm run build
```

## License

MIT