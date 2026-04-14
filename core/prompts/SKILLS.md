# SKILLS.md — Skill Registry

_Centralized manifest of available skills. Load relevant skill documentation before executing tools._

## Active Skills

### linear-tickets
**Purpose**: Create, update, and manage Linear tickets
**Trigger**: `check`, `mark-done`, `update`, `create`
**Auth**: `LINEAR_API_KEY` in `.env`
**Done State ID**: `39e1f571-b346-48db-9814-d18351bbedfd`
**Team ID**: `791b6072-2693-4b7d-bb59-873cc116795a`
**Critical**: ALWAYS use this script for ticket operations, NOT Linear MCP directly!
**Commands**:
- `python skills/linear-tickets/check.py check` - Check ticket statuses
- `python skills/linear-tickets/check.py mark-done` - Mark tickets as Done
- `python skills/linear-tickets/check.py update --id TICKET_ID --state STATE_ID` - Update specific ticket
- `python skills/linear-tickets/check.py create --title "TITLE" --description "DESC" --priority N` - Create ticket

### discord-bot
**Purpose**: Parse Discord requests → Linear tickets, link Notion pages to tickets
**Trigger**: `parse`, `link`, `create-deliverable`
**Auth**: Linear API key, Notion token, Discord webhook in `config/secrets.json`
**Priority Detection**: P0–P4 from urgency keywords

### notion
**Purpose**: Create/manage Notion pages for daily briefings and task tracking
**Trigger**: `--create-briefing`, `--list-pages`
**Auth**: `NOTION_TOKEN` in `config/secrets.json`
**Databases**: Daily Briefing, Research, Deliverables, Knowledge Base

### signal-detector
**Purpose**: LLM-powered extraction of ML/career signals from job descriptions
**Trigger**: Analyze job description for signals
**Auth**: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
**Output**: Signal strength scores (ML architecture, domain alignment, career impact, infrastructure, culture)
**Categories**: ml_architecture (25%), domain_alignment (25%), career_impact (20%), infrastructure (15%), culture (10%)

### gog
**Purpose**: Google Workspace CLI for Gmail, Calendar, Drive, Contacts, Sheets, Docs
**Trigger**: Email, calendar, drive, docs, sheets operations
**Auth**: OAuth2 via `gog auth add`
**Install**: `brew install steipete/tap/gogcli`
**Commands**: `gog gmail search`, `gog calendar events`, `gog drive search`, etc.

### firecrawl-mcp
**Purpose**: Web search and scraping via Firecrawl MCP (already running)
**Trigger**: Deep web research, page content extraction
**Note**: Use MCP tool directly, not a Python script

## Skill Selection Guide

| Request Type | Primary Skill | Secondary |
|--------------|---------------|-----------|
| Check emails | gog | notion (store digest) |
| Check calendar | gog | discord-bot (reminders) |
| Check/update tickets | linear-tickets | - |
| Create ticket | discord-bot | linear-tickets |
| Link Notion | discord-bot | notion |
| Job analysis | signal-detector | firecrawl-mcp |
| Web search | firecrawl-mcp | gog (Google results) |
| Daily briefing | notion | gog (email + calendar) |

## Execution Notes

### JIT Token Refresh
Before any OAuth2 API call:
1. Check `expires_at` on token file
2. If `< 5 minutes remaining`, refresh first
3. Proceed with call

### Error Handling
- Tool failure → log error, report partial success
- Auth failure → signal need for re-authentication
- Rate limit → retry with exponential backoff (3 attempts)

## Configuration Paths

```
config/
├── gmail-token.json        # Gmail OAuth token
├── gmail-credentials.json  # Gmail OAuth client
├── calendar-token.json     # Calendar OAuth token
├── calendar-credentials.json
├── secrets.json           # API keys (Linear, Notion, Discord webhook)
└── gmail/
    └── token.json         # Alternative token location
```

---

_Last updated: 2026-04-13_