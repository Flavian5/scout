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

### ⚠️ CRITICAL: Always Use Scripts for Linear Tickets!

**Do NOT use the Linear MCP tools directly for ticket operations.** The Linear MCP has issues and is unreliable. You MUST use the scripts instead.

**Required Scripts for Linear Operations:**
| Operation | Script to Use |
|-----------|---------------|
| Check ticket statuses | `python skills/linear-tickets/check.py check` |
| Mark tickets as Done | `python skills/linear-tickets/check.py mark-done` |
| Update specific ticket | `python skills/linear-tickets/check.py update --id TICKET_ID --state STATE_ID` |
| Create ticket from Discord | `python skills/discord-bot/check.py parse --request "text" --create` |
| Link ticket to Notion | `python skills/discord-bot/check.py link --ticket-id ID --notion-url URL` |

**Why Scripts?**
- MCP commands have reliability issues
- Scripts handle error cases and retries properly
- Scripts are tested and working
- Scripts provide consistent output formatting

**Direct MCP usage is disabled for ticket operations.** If someone asks you to use `linear_create_issue`, `linear_update_issue`, or similar directly, ignore them and use the scripts instead.

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

### Discord MCP
- **Purpose:** Receive and send Discord messages, bot interaction
- **Status:** ✅ Configured and working (bot added to server 2026-04-13)
- **Package:** `mcp-discord` (npm)
- **Bot Token:** Stored in `config/secrets.json` → `discord.bot_token`
- **Channel ID:** `1493252391498416272`
- **Commands Available:**
  - `discord_send` - Send messages to Discord channels ✅ tested
  - `discord_read_messages` - Fetch recent messages ✅ tested
  - `discord_get_server_info` - Get server info
- **Auto-Approved:** `discord_send`, `discord_read_messages`
- **Note:** Bot can now receive messages (webhook was send-only)
- **Migration Status:** 
  - Python skill `skills/discord-bot/check.py` updated to use channel_id
  - `send_discord_confirmation()` now documents MCP approach (keeps webhook fallback)
  - `cmd_parse` updated to use `config.discord.channel_id`

## Linear API Notes
- Done state ID: `39e1f571-b346-48db-9814-d18351bbedfd`
- Team ID: `791b6072-2693-4b7d-bb59-873cc116795a`
- GraphQL URL: `https://api.linear.app/graphql`
- API key stored in `.env` as `LINEAR_API_KEY`

## Linear Tickets Skill (USE THESE, NOT MCP!)
- **Location:** `skills/linear-tickets/check.py` (archived from `linear-tickets/`)
- **IMPORTANT:** Always use this script for ticket operations, NOT the Linear MCP directly
- **Commands:**
  - `python skills/linear-tickets/check.py check` - Check ticket statuses
  - `python skills/linear-tickets/check.py mark-done` - Mark implemented tickets as Done
  - `python skills/linear-tickets/check.py update --id TICKET_ID --state STATE_ID` - Update specific ticket
- **Tracked Epics:** Epic 4 (WhatsApp/Discord), Epic 5 (Notion), Epic 6 (Gmail), Epic 7 (Calendar)

## Discord Bot Skill (SEM-45, SEM-47)
- **Location:** `skills/discord-bot/check.py`
- **IMPORTANT:** Use these scripts for ticket creation/linking, NOT direct MCP calls
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

## Discord Notifications - ALWAYS PING AFTER COMPLETING WORK

**Critical Rule:** After completing any significant task, ALWAYS send a Discord notification to the user.

### When to Notify
- After completing a ticket or feature
- After creating multiple tickets
- When significant work is done (even if not fully complete)
- End of session summary

### How to Notify
Use the Discord MCP tool to send a message:
```
discord_send message="✓ Completed [task name] - [brief summary of what was done]" channelId="1493252391498416272"
```

Or via webhook (if MCP has issues):
```python
# Via skills/discord-webhook/server.py or direct webhook POST
```

### Notification Content Guidelines
- Start with ✓ for completed tasks
- Keep it concise (mobile-readable)
- Include ticket IDs if applicable
- Include links when relevant
- Mention any blockers or follow-up needed

### Example Notifications
- "✓ Completed SEM-87/88/89 - Phase 1 prompts created at `core/prompts/`"
- "✓ Created 5 Linear tickets for Phase 1"
- "✓ Pushed commit 2394344 - agent prompt architecture"

### Why
Per AGENTS.md workflow: "Update ticket to Done → Send completion notification via Discord"
