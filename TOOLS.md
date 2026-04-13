# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

---

## Scout Personal Assistant - Integration Config

### Minimax LLM
- **API Key**: Stored in `config/secrets.json` → `llm_api.api_key`
- **Model**: minimax/minimax-m2.7
- **Endpoint**: https://api.minimax.io/v1

### Linear (Task Management)
- **MCP Server**: `@linearhq/linear-mcp-integration`
- **Project**: Scout Personal Assistant
- **Team**: Semops
- **Config**: API key in environment variable `LINEAR_API_KEY`

### Notion (Documentation)
- **MCP Server**: `@notionhq/notion-mcp-server`
- **Databases**: Daily Briefing, Research, Deliverables, Knowledge Base
- **Config**: `NOTION_API_KEY` environment variable

### WhatsApp
- **Library**: whatsapp-web.js
- **Session Dir**: `~/.openclaw/whatsapp-session/`
- **Setup**: Requires QR code scan on first run
- **Status**: Session persisted, ready for use

### Gmail (Email)
- **OAuth2**: Requires credentials.json and token.json
- **Config Path**: `config/gmail/`
- **Scopes**: https://www.googleapis.com/auth/gmail.readonly
- **Status**: Not configured - needs OAuth setup

### Google Calendar
- **OAuth2**: Requires credentials.json and token.json
- **Config Path**: `config/calendar/`
- **Scopes**: https://www.googleapis.com/auth/calendar
- **Status**: Not configured - needs OAuth setup

## Setup Requirements

### For Gmail/Google Calendar:
1. Create OAuth2 credentials at https://console.cloud.google.com
2. Download `credentials.json` to `config/gmail/credentials.json`
3. Run initial auth flow to generate `token.json`
4. Refresh tokens before expiry

### For WhatsApp:
1. Session is persisted at `~/.openclaw/whatsapp-session/`
2. If session expires, QR code scan required to re-authenticate

### For Linear/Notion MCP:
- No local config needed - MCP handles authentication via environment