import { Client, GatewayIntentBits, Partials } from 'discord.js';
import { config } from './config.js';
import type { GatewayMessage } from './types.js';

export interface GatewayEvents {
  onMessage: (message: GatewayMessage) => void;
  onStatusChange: (status: 'online' | 'offline' | 'reconnecting', error?: string) => void;
}

export function createGateway(events: GatewayEvents) {
  // Track processed message IDs to prevent loops
  const processedMessages = new Set<string>();
  // Track recent messages to detect bot echoes (throttle per content+author)
  const recentMessages = new Map<string, number>(); // content+author -> timestamp
  
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
    
    // Deduplicate: skip if we've already processed this message
    if (processedMessages.has(msg.id)) {
      return;
    }
    
    // Throttle: skip if same author sent similar content within 3 seconds (bot echo detection)
    const echoKey = `${msg.author.id}:${msg.content.substring(0, 50)}`;
    const now = Date.now();
    const lastSeen = recentMessages.get(echoKey);
    if (lastSeen && now - lastSeen < 3000) {
      return;
    }
    recentMessages.set(echoKey, now);
    
    // Cleanup old entries periodically
    if (processedMessages.size > 1000) {
      processedMessages.clear();
    }
    
    processedMessages.add(msg.id);
    
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
      guildId: msg.guildId ?? undefined,
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
      if (!channel || !channel.isTextBased() || !('send' in channel)) {
        throw new Error(`Channel ${channelId} not found or not text-based`);
      }
      
      const options: { reply?: { messageReference: string } } = {};
      if (replyTo) {
        options.reply = { messageReference: replyTo };
      }
      
      return (channel as any).send({ content, ...options });
    },
    disconnect: () => client.destroy(),
  };
}