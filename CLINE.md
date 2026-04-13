# Cline Best Practices

## Script Execution

**Critical Rule:** When running scripts, always write to a file first (e.g. `skills/*/check.py`), then execute via `python3 skills/*/check.py`. Never embed multi-line Python scripts inline in `execute_command — escaped quotes and special characters cause failures.

### Why
- Inline scripts require escaping of quotes, newlines, and special characters
- Escape sequences often get mangled in shell parsing
- Debugging inline script failures is difficult
- File-based scripts are easier to review, edit, and debug

### How
```bash
# Write script to file first
write_to_file path=skills/skill-name/check.py content=... 

# Execute via python3
execute_command command=python3 skills/skill-name/check.py requires_approval=false
```

### Common Patterns
- Python scripts: Use `python3 script.py`
- Shell scripts: Use `./script.sh` with shebang
- Node scripts: Use `node script.js`

## MCP Servers

### Linear MCP
- **Purpose:** Task management - create, update, search tickets
- **Status:** ✅ Configured and working
- **Commands:** `linear_get_teams`, `linear_create_issue`, `linear_search_issues`, `linear_update_issue`, etc.
- **API key:** Stored in `.env` as `LINEAR_API_KEY`
- **Team ID:** `791b6072-2693-4b7d-bb59-873cc116795a`

### Notion MCP  
- **Purpose:** Documentation and databases - create pages, databases, search content
- **Status:** ✅ Configured and working
- **Commands:** `API-create-a-data-source`, `API-create-a-page`, `API-post-search`, `API-get-block-children`, etc.
- **Workspace:** "Hao's Notion" (connected via bot "Internal")
- **Parent Page:** https://www.notion.so/Teamspace-Home-4ac26d8a7d26828a91d4819c98cdf6ed
- **Databases Created:**
  - Research Database: `34126d8a-7d26-816a-8703-fc6430482336`
  - Email Digest Database: `34126d8a-7d26-8139-9559-ce7242240cc6`

### Google Calendar MCP
- **Purpose:** Calendar event creation and reminders
- **Status:** Requires OAuth with `calendar.events` scope for write access

## Linear API Notes
- Done state ID: `39e1f571-b346-48db-9814-d18351bbedfd`
- Team ID: `791b6072-2693-4b7d-bb59-873cc116795a`
- GraphQL URL: `https://api.linear.app/graphql`
- API key stored in `.env` as `LINEAR_API_KEY`

## Linear Tickets Skill
- **Location:** `skills/linear-tickets/check.py` (archived from `linear-tickets/`)
- **Commands:**
  - `python skills/linear-tickets/check.py check` - Check ticket statuses
  - `python skills/linear-tickets/check.py mark-done` - Mark implemented tickets as Done
  - `python skills/linear-tickets/check.py update --id TICKET_ID --state STATE_ID` - Update specific ticket
- **Tracked Epics:** Epic 4 (WhatsApp/Discord), Epic 5 (Notion), Epic 6 (Gmail), Epic 7 (Calendar)

## Discord Bot Skill (SEM-45, SEM-47)
- **Location:** `skills/discord-bot/check.py`
- **Commands:**
  - `python skills/discord-bot/check.py parse --request "text" --create` - Parse Discord request and create ticket
  - `python skills/discord-bot/check.py link --ticket-id ID --notion-url URL` - Link Notion page to ticket
  - `python skills/discord-bot/check.py create-deliverable --title "X" --database ID --ticket-id TID` - Create Notion deliverable
- **Features:**
  - Natural language ticket creation from Discord requests
  - LLM-powered parsing for title, description, priority, labels
  - Bidirectional Notion ↔ Linear linking
  - Discord webhook confirmations

## Notion Integration
- Database schemas defined in `skills/notion/research_db.py`
- Research Database schema: Name, Topic (select), Source (url), Summary, Date, Tags (multi_select)
- Email Digest schema: Name, Date, Urgency (select), Summary, From (email)
- Daily briefing via `skills/notion/notion.py` → `create_daily_briefing()`
- Direct API creation used for database setup (MCP had version constraints)

## Calendar Integration
- Natural language event creation: `skills/calendar-check/check.py create --request "meeting at 3pm tomorrow"`
- Parse → Create → Confirm via Discord flow implemented
- Requires re-auth for write scope if currently read-only