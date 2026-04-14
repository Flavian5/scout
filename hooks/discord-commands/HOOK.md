# Discord Commands Hook

## Metadata
- **hook_id**: discord-commands
- **version**: 1.0.0
- **description**: Handle Discord command invocations via webhook
- **author**: scout
- **created**: 2026-04-14

## Event Bindings
- **trigger**: External webhook from Discord gateway
- **events**: 
  - `discord.command`
  - `discord.message`
- **filter**: Command prefix `!` or mention-based commands

## Configuration
```yaml
enabled: true
command_prefix: "!"
mention_required: false
```

## Capabilities
- [ ] Handle `!email` command
- [ ] Handle `!calendar` command  
- [ ] Handle `!help` command
- [ ] Rate limiting (5 req/min per user)