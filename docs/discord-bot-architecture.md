# Discord Bot Architecture

## Current Implementation Status: ✅ OPERATIONAL (OpenClaw Native)

OpenClaw directly handles Discord events via its built-in hooks system:

```
Discord → OpenClaw (native) → skills → response
```

**Components:**
- OpenClaw core handles Discord webhook events
- `hooks/discord-commands/` processes commands
- Skills (email-alerts, gog, calendar-confirm, etc.) handle actual work

### OpenClaw Configuration

Relevant config in `openclaw.json`:

```json
{
  "skills": {
    "entries": {
      "discord-bot": { "enabled": true },
      "email-alerts": { "enabled": true },
      "gog": { "enabled": true }
    }
  },
  "hooks": {
    "discord-commands": {
      "enabled": true,
      "path": "hooks/discord-commands",
      "events": ["discord.command", "discord.message"]
    }
  }
}
```

## Troubleshooting

### If "check my emails" doesn't work:
1. Verify OpenClaw is running and processing Discord events
2. Check `logs/openclaw.log` for hook invocation errors
3. Verify the `discord-commands` hook is properly configured

### Commands
- `!email` - Check urgent emails via email-alerts skill
- `!calendar` - Check upcoming meetings via calendar-confirm skill
- Natural language like "check my emails" should be handled by OpenClaw's LLM

## References
- [Discord Commands Hook Handler](../hooks/discord-commands/handler.ts)
- [Hook Dispatcher](../scripts/hook_dispatcher.py)
- [Email Alerts Skill](../skills/email_alerts/check.py)
- [Gog Skill](../skills/gog/SKILL.md)