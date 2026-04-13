# SKILLS.md — Skill Registry

_Centralized manifest of available skills. Load relevant skill documentation before executing tools._

## Active Skills

### email-check
**Purpose**: Check Gmail inbox for unread messages, classify urgency
**Trigger**: `--fetch`, `--classify`, `--urgent-alert`
**Auth**: OAuth2 at `config/gmail-token.json`
**Scope**: `gmail.modify` (required for drafts)
**Output**: Array of emails with sender, subject, snippet, timestamp, urgency classification
**Priority Labels**: urgent | important | routine

### calendar-check
**Purpose**: Check Google Calendar for upcoming events, send 15-min reminders
**Trigger**: `--fetch`, `--remind`, `--digest`
**Auth**: OAuth2 at `config/calendar-token.json`
**Output**: Array of events with title, start, end, location, attendees, minutes_until
**Reminder Window**: 15 minutes before event

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

### ddg-web-search
**Purpose**: Web search via DuckDuckGo Lite
**Trigger**: Search for current information
**Auth**: None required

### openclaw-tavily-search
**Purpose**: Enhanced web search via Tavily AI
**Trigger**: Deep research search
**Auth**: `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`

## Skill Selection Guide

| Request Type | Primary Skill | Secondary |
|--------------|---------------|-----------|
| Check emails | email-check | notion (store digest) |
| Check calendar | calendar-check | discord-bot (reminders) |
| Create ticket | discord-bot | - |
| Link Notion | discord-bot | notion |
| Job analysis | signal-detector | ddg-web-search |
| Web search | ddg-web-search | openclaw-tavily-search |
| Daily briefing | notion | email-check, calendar-check |

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