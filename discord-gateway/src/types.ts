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

// Message interface for internal use
export interface GatewayMessage {
  channelId: string;
  messageId: string;
  author: { id: string; username: string; discriminator?: string };
  content: string;
  timestamp: number;
  guildId?: string;
  isDirectMessage: boolean;
}