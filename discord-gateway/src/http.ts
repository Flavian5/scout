import express from 'express';
import http from 'http';
import { SendMessageSchema } from './types.js';

export interface HttpEvents {
  onSendMessage: (channelId: string, content: string, replyTo?: string) => Promise<void>;
}

export function createHttpServer(events: HttpEvents) {
  const app = express();
  app.use(express.json());

  let server: http.Server | null = null;

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
    start: (port: number) => {
      server = app.listen(port, () => {
        console.log(`[HTTP] Server listening on port ${port}`);
      });
    },
    stop: () => {
      if (server) {
        server.close();
      }
    },
  };
}
