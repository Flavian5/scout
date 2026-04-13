# Heartbeat Checklist

Quick checks to run periodically. Keep this small!

## Periodic Checks (2-4x daily)

Priority order: P0 → P1 → P2 → P3

- [ ] Check for urgent emails (`python skills/email-check/check.py --fetch --classify`)
- [ ] Check calendar for upcoming events (`python skills/calendar-check/check.py --fetch --remind`)
- [ ] Any new Linear notifications?

**Note:** Heartbeat no longer checks job pipeline (scout/analyst/strategist deprecated and archived).

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

### ✅ Phase 3: Core Skills Setup (Complete - 2026-04-12)
- WhatsApp MCP: Connected (whatsapp-web.js)
- Linear MCP: Connected (via environment)
- Notion MCP: Connected (via environment)
- Gmail: Needs OAuth2 setup
- Google Calendar: Needs OAuth2 setup

### ✅ Phase 4: Email Monitoring (Complete - 2026-04-12)
- Created `skills/email-check/` with full implementation:
  - `check.py` - Gmail OAuth2 + fetch + urgency classification
  - `SKILL.md` - Skill documentation
  - `_meta.json` - Skill metadata
  - `README.md` - Setup instructions
- Email fetch: Uses Gmail API with OAuth2
- Urgency classification: Uses MiniMax-M2.7 LLM
- Placeholder stubs for WhatsApp alerts + Notion push (blocked on those skills)

### Phase 5: Feature Implementation (Pending)
- Review remaining Linear tickets for next priorities
- Gmail OAuth2 setup (manual - user interaction required)
- Google Calendar OAuth2 setup (manual - user interaction required)

**Last pushed:** 2026-04-12, commit ca5ab86 (Phase 3: Core Skills setup + TOOLS.md updates)