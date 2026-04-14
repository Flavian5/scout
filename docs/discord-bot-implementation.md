# Discord Bot Implementation Guide

## Overview

This document provides a full implementation reference for the standalone Discord bot described in [discord-bot-architecture.md](./discord-bot-architecture.md).

## Project Structure

```
discord-gateway/              # Standalone bot repo
├── package.json
├── src/
│   ├── index.ts            # Main entry point
│   ├── gateway.ts          # Discord WebSocket handler
│   ├── http.ts             # Express HTTP server
│   ├── types.ts            # TypeScript interfaces
│   └── config.ts           # Environment configuration
├── tsconfig.json
├── Dockerfile
└── README.md
```

## Core Implementation

### package.json

```json
{
  "name": "discord-gateway",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "discord.js": "^14.14.0",
    "express": "^4.18.2",
    "ws": "^8.14.2",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "@types/express": "^4.17.21",
    "@types/node": "^20.10.0",
    "@types/ws": "^8.5.10",
    "tsx": "^4.6.0",
    "typescript": "^5.3.2"
  }
}
```

### src/types.ts

```typescript
import { z } from 'zod';

// Inbound: Bot → OpenClaw
export const DiscordMessageSchema = z.object({
  type: z.literal("discord_message"),
  data: z.object({
    channelId: z.string(),
    messageId: z.string(),
    author: z.object({
      id: z.string(),
      username: z.string(),
      discriminator: z.string().optional(),
    }),
    content: z.string(),
    timestamp: z.number(),
    guildId: z.string().optional(),
    isDirectMessage: z.boolean(),
  })
});

export type DiscordMessage = z.infer<typeof DiscordMessageSchema>;

// Outbound: OpenClaw → Bot
export const SendMessageSchema = z.object({
  type: z.literal("send_message"),
  data: z.object({
    channelId: z.string(),
    content: z.string(),
    replyTo: z.string().optional(),
  })
});

export type SendMessage = z.infer<typeof SendMessageSchema>;

// Bot status update
export const BotStatusSchema = z.object({
  type: z.literal("bot_status"),
  data: z.object({
    status: z.enum(["online", "offline", "reconnecting"]),
    shard: z.number().optional(),
    error: z.string().optional(),
  })
});

export type BotStatus = z.infer<typeof BotStatusSchema>;
```

### src/config.ts

```typescript
import 'dotenv/config';
import { z } from 'zod';

const ConfigSchema = z.object({
  discordToken: z.string().min(1, "DISCORD_TOKEN required"),
  openclawWebhookUrl: z.string().url().optional(),
  openclawHttpUrl: z.string().url().optional(),
  port: z.number().default(3456),
  logLevel: z.enum(["debug", "info", "warn", "error"]).default("info"),
  listenChannels: z.array(z.string()).default([]),  // Empty = all channels
  ignoreBots: z.boolean().default(true),
});

export const config = ConfigSchema.parse(process.env);

export type Config = z.infer<typeof ConfigSchema>;
```

### src/gateway.ts (Discord WebSocket Handler)

```typescript
import { Client, GatewayIntentBits, Partials } from 'discord.js';
import { config } from './config.js';

export interface GatewayEvents {
  onMessage: (message: {
    channelId: string;
    messageId: string;
    author: { id: string; username: string; discriminator?: string };
    content: string;
    timestamp: number;
    guildId?: string;
    isDirectMessage: boolean;
  }) => void;
  onStatusChange: (status: 'online' | 'offline' | 'reconnecting', error?: string) => void;
}

export function createGateway(events: GatewayEvents) {
  const client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.DirectMessages,
      GatewayIntentBits.MessageContent,
    ],
    partials: [Partials.Channel],
  });

  client.on('ready', () => {
    console.log(`[Gateway] Logged in as ${client.user?.tag}`);
    events.onStatusChange('online');
  });

  client.on('messageCreate', (msg) => {
    // Ignore bots unless configured otherwise
    if (config.ignoreBots && msg.author.bot) return;
    
    // Filter by configured channels
    if (config.listenChannels.length > 0 && 
        !config.listenChannels.includes(msg.channelId)) {
      return;
    }

    events.onMessage({
      channelId: msg.channelId,
      messageId: msg.id,
      author: {
        id: msg.author.id,
        username: msg.author.username,
        discriminator: msg.author.discriminator,
      },
      content: msg.content,
      timestamp: msg.createdTimestamp,
      guildId: msg.guildId,
      isDirectMessage: msg.channel.type === 1, // DM = 1
    });
  });

  client.on('disconnect', (event) => {
    console.error('[Gateway] Disconnected', event.code, event.reason);
    events.onStatusChange('offline', event.reason);
  });

  client.on('reconnecting', () => {
    console.log('[Gateway] Reconnecting...');
    events.onStatusChange('reconnecting');
  });

  return {
    login: () => client.login(config.discordToken),
    sendMessage: async (channelId: string, content: string, replyTo?: string) => {
      const channel = await client.channels.fetch(channelId);
      if (!channel || !channel.isTextBased()) {
        throw new Error(`Channel ${channelId} not found or not text-based`);
      }
      
      const options: any = {};
      if (replyTo) {
        options.reply = { messageReference: replyTo };
      }
      
      return channel.send({ content, ...options });
    },
    disconnect: () => client.destroy(),
  };
}
```

### src/http.ts (HTTP Server for OpenClaw callbacks)

```typescript
import express from 'express';
import { SendMessageSchema } from './types.js';

export interface HttpEvents {
  onSendMessage: (channelId: string, content: string, replyTo?: string) => Promise<void>;
}

export function createHttpServer(events: HttpEvents) {
  const app = express();
  app.use(express.json());

  // Health check
  app.get('/health', (_, res) => {
    res.json({ status: 'ok', timestamp: Date.now() });
  });

  // Receive messages from OpenClaw to send to Discord
  app.post('/send', async (req, res) => {
    try {
      const payload = SendMessageSchema.parse(req.body);
      
      if (payload.type !== 'send_message') {
        return res.status(400).json({ error: 'Unknown message type' });
      }

      await events.onSendMessage(
        payload.data.channelId,
        payload.data.content,
        payload.data.replyTo
      );

      res.json({ ok: true });
    } catch (error: any) {
      console.error('[HTTP] Send error:', error.message);
      res.status(400).json({ error: error.message });
    }
  });

  // Optional: Status endpoint for OpenClaw to check bot health
  app.get('/status', (_, res) => {
    res.json({ 
      status: 'ready',
      endpoints: ['/health', '/send', '/status']
    });
  });

  return {
    start: (port: number) => app.listen(port, () => {
      console.log(`[HTTP] Server listening on port ${port}`);
    }),
    stop: () => app.close(),
  };
}
```

### src/index.ts (Main Entry Point)

```typescript
import { config } from './config.js';
import { createGateway } from './gateway.js';
import { createHttpServer } from './http.js';

async function main() {
  console.log('[Main] Starting Discord Gateway...');
  console.log(`[Main] OpenClaw webhook: ${config.openclawWebhookUrl || 'not configured'}`);
  console.log(`[Main] Listen channels: ${config.listenChannels.length > 0 ? config.listenChannels.join(', ') : 'all'}`);

  // Track pending messages for OpenClaw
  const pendingMessages: Array<{
    channelId: string;
    messageId: string;
    author: { id: string; username: string; discriminator?: string };
    content: string;
    timestamp: number;
    guildId?: string;
    isDirectMessage: boolean;
  }> = [];

  const gateway = createGateway({
    onMessage: async (msg) => {
      console.log(`[Gateway] Message from ${msg.author.username}: ${msg.content.substring(0, 50)}...`);

      // Forward to OpenClaw webhook if configured
      if (config.openclawWebhookUrl) {
        try {
          const response = await fetch(config.openclawWebhookUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: 'discord_message',
              data: msg,
            }),
          });
          
          if (!response.ok) {
            console.warn(`[Gateway] OpenClaw webhook returned ${response.status}`);
          }
        } catch (error: any) {
          console.error('[Gateway] Failed to forward to OpenClaw:', error.message);
          // TODO: Queue message for retry
        }
      } else {
        // No OpenClaw configured - just log
        console.log('[Gateway] No OpenClaw webhook configured, message not forwarded');
      }
    },

    onStatusChange: (status, error) => {
      console.log(`[Gateway] Status: ${status}${error ? ` (${error})` : ''}`);
    },
  });

  const http = createHttpServer({
    onSendMessage: async (channelId, content, replyTo) => {
      console.log(`[HTTP] Sending to ${channelId}: ${content.substring(0, 50)}...`);
      await gateway.sendMessage(channelId, content, replyTo);
    },
  });

  // Start services
  http.start(config.port);
  await gateway.login();

  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('[Main] Shutting down...');
    gateway.disconnect();
    http.stop();
    process.exit(0);
  });
}

main().catch((error) => {
  console.error('[Main] Fatal error:', error);
  process.exit(1);
});
```

## Docker Setup

### Dockerfile

```dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better layer caching)
COPY package*.json ./
RUN npm ci --only=production

# Copy compiled code (or source if using tsx)
COPY dist/ ./dist/
# Or if running from source:
# COPY src/ ./src/

# Create non-root user for security
RUN addgroup -g 1001 -S discordbot && \
    adduser -S discordbot -u 1001
USER discordbot

EXPOSE 3456

CMD ["node", "dist/index.js"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  discord-gateway:
    build: .
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - OPENCLAW_WEBHOOK_URL=${OPENCLAW_WEBHOOK_URL}
      - OPENCLAW_HTTP_URL=http://openclaw:3000
      - PORT=3456
      - LOG_LEVEL=info
      - IGNORE_BOTS=true
    ports:
      - "3456:3456"
    volumes:
      - discord-gateway-data:/app/data

volumes:
  discord-gateway-data:
```

## systemd Service

```ini
[Unit]
Description=Discord Gateway Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/your-user/discord-gateway
Environment=DISCORD_TOKEN=your-token-here
Environment=OPENCLAW_WEBHOOK_URL=https://your-domain.com/discord/in
Environment=PORT=3456
ExecStart=/home/your-user/discord-gateway/node_modules/.bin/node dist/index.js
Restart=always
RestartSec=5

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/home/your-user/discord-gateway/data

[Install]
WantedBy=multi-user.target
```

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_TOKEN` | Yes | - | Bot token from Discord Developer Portal |
| `OPENCLAW_WEBHOOK_URL` | No | - | Where bot POSTs incoming messages |
| `OPENCLAW_HTTP_URL` | No | - | Where bot calls to receive outbound messages |
| `PORT` | No | 3456 | HTTP server port |
| `LOG_LEVEL` | No | info | Logging level |
| `LISTEN_CHANNELS` | No | all | Comma-separated channel IDs to listen to |
| `IGNORE_BOTS` | No | true | Ignore messages from other bots |

## Building & Running

```bash
# Clone/fork the repo
git clone https://github.com/yourusername/discord-gateway.git
cd discord-gateway

# Install dependencies
npm install

# Build TypeScript
npm run build

# Run
DISCORD_TOKEN=your-token npm start

# Or with Docker
docker build -t discord-gateway .
docker run -d --env-file .env discord-gateway
```

## Integration with OpenClaw

OpenClaw needs to:

1. **Receive messages** - Add a webhook handler at `POST /discord/in`
   - Validate the payload using `DiscordMessageSchema`
   - Process through signal detector → action routing
   - Optionally queue response for async sending

2. **Send messages** - Call bot's `/send` endpoint
   ```typescript
   await fetch(`${BOT_HTTP_URL}/send`, {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       type: 'send_message',
       data: {
         channelId: '123456789',
         content: '📋 Created ticket **SEM-99**',
         replyTo: '987654321'  // optional
       }
     })
   });
   ```

3. **Handle failures** - Implement retry logic with exponential backoff

## Testing Locally

```bash
# Start the bot
DISCORD_TOKEN=test-token OPENCLAW_WEBHOOK_URL=http://localhost:3000/discord/in npm run dev

# Send a test message to bot via HTTP
curl -X POST http://localhost:3456/send \
  -H "Content-Type: application/json" \
  -d '{
    "type": "send_message",
    "data": {
      "channelId": "test-channel",
      "content": "Hello from the bot!"
    }
  }'

# Check health
curl http://localhost:3456/health
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot won't login | Verify DISCORD_TOKEN is valid and bot has correct intents |
| Messages not arriving | Check bot has "Message Content Intent" in Developer Portal |
| OpenClaw webhook fails | Verify URL is accessible, check firewall/network |
| Rate limited | Implement message queuing, respect Discord rate limits (120/sec) |
| Reconnecting loops | Check Discord status page, implement backoff |