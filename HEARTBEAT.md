# Heartbeat Checklist

Quick checks to run periodically. Keep this small!

## Periodic Checks (2-4x daily)

- [ ] Check for urgent emails
- [ ] Check calendar for upcoming events (next 24h)
- [ ] Any new Linear notifications?

## Scout Status (Last: 2026-04-12)

### ✅ Phase 1: Infrastructure Migration (Complete)
- Updated `openclaw.json` to v3.0.0 (Scout Personal Assistant)
- Model: `minimax/minimax-m2.7` via minimax.io (migrated from OpenRouter)
- Heartbeat: Now every 30min
- Disabled agents: scout, analyst, strategist (deprecated)
- Updated signal-detector to use minimax.io client

### ✅ Phase 2: Documentation & Cleanup (Complete)
- AGENTS.md: Added Linear + Notion checks to Every Session
- AGENTS.md: Added Task Management section (Linear-first workflow)
- AGENTS.md: Added Integrations section (6 services)
- AGENTS.md: Added Communication Style section
- TOOLS.md: Updated with integration configs

### 🚧 Phase 3: Core Skills Setup (In Progress)
- WhatsApp MCP: Connected (whatsapp-web.js)
- Linear MCP: Connected (via environment)
- Notion MCP: Connected (via environment)
- Gmail: Needs OAuth2 setup
- Google Calendar: Needs OAuth2 setup

### Remaining Setup (Manual - requires user interaction)
- Gmail OAuth2: Create credentials at console.cloud.google.com
- Google Calendar OAuth2: Create credentials at console.cloud.google.com
- WhatsApp: Session ready, needs periodic QR scan if expires