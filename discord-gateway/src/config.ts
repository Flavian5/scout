import { config as dotenvConfig } from 'dotenv';
dotenvConfig({ path: '.env' });
import { z } from 'zod';

const ConfigSchema = z.object({
  discordToken: z.string().min(1, "DISCORD_TOKEN required"),
  openclawWebhookUrl: z.string().url().optional(),
  openclawHttpUrl: z.string().url().optional(),
  port: z.coerce.number().default(3456),
  logLevel: z.enum(["debug", "info", "warn", "error"]).default("info"),
  listenChannels: z.string().transform(s => s ? s.split(',').map(c => c.trim()) : []).default(""),
  ignoreBots: z.string().transform(s => s !== "false").default("true"),
});

let config: z.infer<typeof ConfigSchema>;

try {
  config = ConfigSchema.parse({
    discordToken: process.env.DISCORD_TOKEN,
    openclawWebhookUrl: process.env.OPENCLAW_WEBHOOK_URL,
    openclawHttpUrl: process.env.OPENCLAW_HTTP_URL,
    port: process.env.PORT,
    logLevel: process.env.LOG_LEVEL,
    listenChannels: process.env.LISTEN_CHANNELS,
    ignoreBots: process.env.IGNORE_BOTS,
  });
} catch (error) {
  console.error("Configuration error:", error);
  process.exit(1);
}

export { config };
export type Config = z.infer<typeof ConfigSchema>;