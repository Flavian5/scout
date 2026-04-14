// Discord Commands Hook Handler
// Handles Discord command invocations via OpenClaw hook system

import { HookHandler, HookEvent, HookResponse } from '@openclaw/sdk';
import { spawn } from 'child_process';

interface DiscordCommand {
  command: string;
  args: string[];
  userId: string;
  channelId: string;
  guildId?: string;
}

interface CommandResult {
  success: boolean;
  response?: string;
  error?: string;
  messages?: any[];
}

async function dispatchToPython(command: string): Promise<CommandResult> {
  return new Promise((resolve) => {
    const dispatcher = spawn('python3', [
      'scripts/hook_dispatcher.py',
      command
    ], {
      cwd: process.cwd()
    });

    let output = '';
    let errorOutput = '';

    dispatcher.stdout.on('data', (data) => {
      output += data.toString();
    });

    dispatcher.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    dispatcher.on('close', (code) => {
      if (code !== 0 || errorOutput) {
        resolve({
          success: false,
          error: errorOutput || `Process exited with code ${code}`
        });
        return;
      }

      try {
        const result = JSON.parse(output);
        resolve(result);
      } catch (e) {
        resolve({
          success: false,
          error: `Failed to parse result: ${output}`
        });
      }
    });

    dispatcher.on('error', (err) => {
      resolve({
        success: false,
        error: `Failed to spawn dispatcher: ${err.message}`
      });
    });
  });
}

export const handler: HookHandler = async (event: HookEvent): Promise<HookResponse> => {
  try {
    const payload = event.payload as DiscordCommand;
    
    // Validate payload
    if (!payload.command) {
      return {
        success: false,
        error: 'Missing command in payload',
      };
    }

    const command = payload.command.toLowerCase();

    // Special handling for commands that need Python skill integration
    if (['email', 'calendar'].includes(command)) {
      const result = await dispatchToPython(command);
      
      if (!result.success) {
        return {
          success: false,
          error: result.error || 'Command failed',
        };
      }

      // Format response for Discord
      let responseText = '';
      if (result.messages && Array.isArray(result.messages)) {
        responseText = result.messages
          .slice(0, 5)
          .map((m: any) => {
            const from = m.from || m.sender || 'Unknown';
            const subject = m.subject || '(no subject)';
            return `📧 From: ${from}\n   Subject: ${subject}`;
          })
          .join('\n\n');
        
        if (result.messages.length === 0) {
          responseText = 'No urgent emails found.';
        } else {
          responseText = `Found ${result.messages.length} urgent email(s):\n\n${responseText}`;
        }
      } else if (result.response) {
        responseText = result.response;
      }

      return {
        success: true,
        data: { 
          response: responseText || 'Command completed.',
          raw: result
        },
      };
    }

    // Built-in commands
    const builtInCommands: Record<string, () => string> = {
      help: () => 'Available commands: !email, !calendar, !help',
      ping: () => 'Pong! 🏓',
    };

    const builtIn = builtInCommands[command];
    if (builtIn) {
      return {
        success: true,
        data: { response: builtIn() },
      };
    }

    return {
      success: false,
      error: `Unknown command: ${command}`,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
};

export default handler;