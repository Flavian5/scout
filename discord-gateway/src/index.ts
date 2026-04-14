import { config } from './config.js';
import { createGateway } from './gateway.js';
import { createHttpServer } from './http.js';

async function main() {
  console.log('[Main] Starting Discord Gateway...');
  console.log(`[Main] OpenClaw webhook: ${config.openclawWebhookUrl || 'not configured'}`);
  console.log(`[Main] Listen channels: ${config.listenChannels.length > 0 ? config.listenChannels.join(', ') : 'all'}`);

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
            return;
          }
          
          // Parse response and send back to Discord
          const responseData = await response.json();
          const responseContent = responseData.content;
          const replyToMessageId = responseData.reply_to_message_id;
          
          if (responseContent) {
            console.log(`[Gateway] Sending response to ${msg.channelId}: ${responseContent.substring(0, 50)}...`);
            await gateway.sendMessage(msg.channelId, responseContent, replyToMessageId);
            console.log('[Gateway] Response sent successfully');
          }
        } catch (error: any) {
          console.error('[Gateway] Failed to forward to OpenClaw:', error.message);
        }
      } else {
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