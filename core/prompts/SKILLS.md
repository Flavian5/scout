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
**Purpose**: Life management via 8 Notion databases (chores, financials, projects, weekend-plans, daily-briefing, research, knowledge-base, deliverables)
**Trigger**: `chore`, `financial`, `project`, `weekend`, `briefing`, `research`, `knowledge`, `deliverable`
**Auth**: `NOTION_TOKEN` in `config/secrets.json`
**Commands**:
- `python skills/notion/notion.py init-database <db> --parent <page_id>` - Initialize any database
- `python skills/notion/notion.py create-chore --name "X" --frequency weekly --days "Sun"`
- `python skills/notion/notion.py create-financial --name "X" --category expense --subcategory food --amount 50`
- `python skills/notion/notion.py create-project --name "X" --status active --category home`
- `python skills/notion/notion.py create-weekend --name "X" --date 2026-04-18 --category outdoor`
- `python skills/notion/notion.py create-briefing --email "summary" --calendar "summary"`
- `python skills/notion/notion.py create-research --title "X" --topic AI --source <url>`
- `python skills/notion/notion.py create-knowledge --name "X" --category setup --content "..."`
- `python skills/notion/notion.py create-deliverable --name "X" --type Document --linear <url>`
- `python skills/notion/notion.py list-pages --name <db>` - List entries in database
- `python skills/notion/notion.py query <db> --filter "Status:todo"` - Query with filter

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

### email-check
**Purpose**: Interactive email search for LLM chat - returns formatted email summaries
**Trigger**: "check my emails", "any new messages from X", "show my inbox"
**Auth**: OAuth2 via `gog auth add` (uses gog under the hood)
**Function**: `check(query="in:inbox is:unread", max_results=10, description="...")`
**Example queries**:
- `"in:inbox is:unread newer_than:1d"` - unread from today
- `"from:boss@company.com newer_than:7d"` - from specific sender
- `"subject:meeting is:unread"` - meeting invites
- `"is:starred has:attachment newer_than:30d"` - starred with attachments
**Output**: Formatted text summary the LLM can present to user

### calendar-check
**Purpose**: Interactive calendar lookup for LLM chat - returns formatted event summaries
**Trigger**: "check my calendar", "what's on today", "any meetings this week"
**Auth**: OAuth2 via `gog auth add` (uses gog under the hood)
**Function**: `check(calendar_id="primary", days_ahead=7, description="...")`
**Output**: Formatted text summary of upcoming events

### firecrawl-mcp
**Purpose**: Web search and scraping via Firecrawl MCP (already running)
**Trigger**: Deep web research, page content extraction
**Note**: Use MCP tool directly, not a Python script

## Skill Selection Guide

| Request Type | Primary Skill | Secondary |
|--------------|---------------|-----------|
| Check emails (chat) | email-check | gog |
| Check calendar (chat) | calendar-check | gog |
| Check/update tickets | linear-tickets | - |
| Create ticket | discord-bot | linear-tickets |
| Add/update chore | notion | - |
| Log expense | notion | - |
| Project status | notion | - |
| Weekend plans | notion | - |
| Daily briefing | notion | gog (email + calendar) |
| Research entry | notion | firecrawl-mcp |
| Knowledge query | notion | - |
| Deliverable logging | notion | linear-tickets |
| Link Notion | discord-bot | notion |
| Job analysis | signal-detector | firecrawl-mcp |
| Web search | firecrawl-mcp | gog (Google results) |

## Trigger Routing (Notion)

| User Input | Command | Database |
|------------|---------|----------|
| "add chore: X weekly on Y" | `create-chore` | chores |
| "mark X as done" | update (status=done) | chores |
| "what chores today?" | `list-pages --name chores` | chores |
| "spent $X on Y" | `create-financial` | financials |
| "budget status" | `query financials` | financials |
| "project status: X" | `query projects` | projects |
| "how's X going?" | `query projects` | projects |
| "what's planned this weekend?" | `query weekend-plans` | weekend-plans |
| "add weekend plan: X" | `create-weekend` | weekend-plans |
| "summarize my day" | `create-briefing` | daily-briefing |
| "show yesterday's briefing" | `query daily-briefing` | daily-briefing |
| "archive this research" | `create-research` | research |
| "how do I set up X?" | `query knowledge-base` | knowledge-base |
| "log this deliverable" | `create-deliverable` | deliverables |

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

_Last updated: 2026-04-14_