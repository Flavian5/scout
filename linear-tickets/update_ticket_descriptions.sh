#!/bin/bash
# Update Linear tickets with expanded descriptions
# This script updates each ticket with user story, tech specs, and acceptance criteria

# Load API key from environment or .env file
if [ -z "$LINEAR_API_KEY" ]; then
    if [ -f .env ]; then
        source .env
    fi
fi

if [ -z "$LINEAR_API_KEY" ]; then
    echo "Error: LINEAR_API_KEY environment variable not set"
    echo "Usage: LINEAR_API_KEY=your_key ./update_ticket_descriptions.sh"
    exit 1
fi

API_KEY="$LINEAR_API_KEY"
ENDPOINT="https://api.linear.app/graphql"

# Fetch all issues to get their IDs
fetch_issues() {
  curl -s -X POST "$ENDPOINT" \
    -H "Authorization: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"query":"query { issues(filter: { projectId: { eq: \"8ccf1d0d-dc13-4b61-9aa2-d8278113e83f\" } }) { nodes { id identifier title } } }"}'
}

# Update issue description
update_description() {
  local id="$1"
  local description="$2"
  
  # Escape description for JSON (handle newlines, quotes)
  description=$(echo "$description" | sed 's/\\/\\\\/g' | sed 's/"/\\"/g' | tr '\n' ' ')
  
  curl -s -X POST "$ENDPOINT" \
    -H "Authorization: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"query\":\"mutation { issueUpdate(id: \\\"$id\\\", input: { description: \\\"$description\\\" }) { success } }\"}"
}

echo "Fetching current tickets..."
TICKETS=$(fetch_issues)
echo "$TICKETS" | head -c 500
echo "..."

# Epic 1: LLM Infrastructure Migration
echo ""
echo "Updating Epic 1: LLM Infrastructure Migration..."

update_description "SEM-6" "## User Story
As the system administrator, I want the global LLM config updated to minimax m2.7 via minimax.io so that all agents use the new model without OpenRouter dependency.

## Technical Specs
- File: openclaw.json
- Change: agents.defaults.model.primary from openrouter/minimax/minimax-m2.5 to minimax/minimax-m2.7
- Add: agents.defaults.model.base_url = https://api.minimax.io/v1
- Remove any OpenRouter references from model config

## Acceptance Criteria
- [ ] openclaw.json shows minimax/minimax-m2.7 as primary model
- [ ] base_url field points to https://api.minimax.io/v1
- [ ] provider field set to minimax
- [ ] No openrouter references in model config section
- [ ] JSON validates (no syntax errors)

## Dependencies
None"

update_description "SEM-7" "## User Story
As the signal detection system, I need to use the minimax.io API directly so that job description analysis works with the new LLM provider.

## Technical Specs
- File: skills/signal-detector/detect.py
- Function: get_llm_client() (lines 47-71)
- Change base_url from https://openrouter.ai/api/v1 to https://api.minimax.io/v1
- Update DEFAULT_ANALYTICAL_MODEL from moonshotai/kimi-k2.5 to minimax/minimax-m2.7
- Update DEFAULT_FAST_MODEL from minimax/minimax-m2.5 to minimax/minimax-m2.7

## Acceptance Criteria
- [ ] base_url points to https://api.minimax.io/v1
- [ ] DEFAULT_ANALYTICAL_MODEL uses minimax/minimax-m2.7
- [ ] DEFAULT_FAST_MODEL uses minimax/minimax-m2.7
- [ ] Remove OpenRouter conditional (default to minimax)
- [ ] Test: python skills/signal-detector/detect.py --help works

## Dependencies
SCOUT-INFRA-001"

update_description "SEM-8" "## User Story
As the integration system, I need to verify the minimax.io API credentials are valid so that LLM calls succeed without authentication errors.

## Technical Specs
- Test endpoint: POST https://api.minimax.io/v1/chat/completions
- Required headers: Authorization: Bearer <api_key>
- Test payload: Simple completion request with 1 token

## Verification Steps
1. Get API key from config/secrets.json → llm_api.api_key
2. Run test curl with sample request
3. Verify response contains valid JSON

## Acceptance Criteria
- [ ] API key format matches (should start with minimax_ or similar)
- [ ] Test API call returns valid JSON response
- [ ] No 'invalid API key' or 'authentication failed' errors
- [ ] Document any rate limits or quota info

## Dependencies
SCOUT-INFRA-001, SCOUT-INFRA-002"

update_description "SEM-9" "## User Story
As the code auditor, I need to find all OpenRouter references across the codebase so that we can migrate everything to minimax.io.

## Technical Specs
- Search pattern: openrouter.ai
- Files to check: All skill directories, config files, documentation

## Acceptance Criteria
- [ ] Run grep search for openrouter
- [ ] Update all found references to minimax or minimax.io
- [ ] Update any openrouter.ai URLs to api.minimax.io/v1
- [ ] Update any OpenRouter model names to equivalent minimax models
- [ ] Commit changes with message: Migrate from OpenRouter to minimax.io

## Dependencies
SCOUT-INFRA-001, SCOUT-INFRA-002"

update_description "SEM-10" "## User Story
As the quality assurance system, I need to verify the signal detector works end-to-end with the new model so that job analysis continues without interruption.

## Technical Specs
- Test file: skills/signal-detector/detect.py
- Test data: Sample job description from data/leads/raw_leads.json (or create mock)

## Acceptance Criteria
- [ ] Script runs without errors
- [ ] Returns valid JSON (no parsing errors)
- [ ] detected_signals contains expected keys
- [ ] method field is llm (not keyword)
- [ ] Response time < 10 seconds

## Dependencies
SCOUT-INFRA-002, SCOUT-INFRA-003"

echo "Epic 1 complete. Updating Epic 2: Deprecate Pipeline..."

# Epic 2: Deprecate Job Application Pipeline
update_description "SEM-11" "## User Story
As the system owner, I want to disable the Scout agent so that job discovery doesn't run on schedule anymore.

## Technical Specs
- File: openclaw.json
- Section: agents.scout
- Change: enabled: true → enabled: false
- Add: archived: true for future reference

## Acceptance Criteria
- [ ] scout.enabled is false
- [ ] scout.archived is true
- [ ] Scout agent does NOT run on cron schedule
- [ ] Manual run (openclaw agents run scout) fails gracefully

## Dependencies
None"

update_description "SEM-12" "## User Story
As the system owner, I want to disable the Analyst agent so that job scoring doesn't run on schedule anymore.

## Technical Specs
- File: openclaw.json
- Section: agents.analyst
- Change: enabled: true → enabled: false
- Add: archived: true for future reference

## Acceptance Criteria
- [ ] analyst.enabled is false
- [ ] analyst.archived is true
- [ ] Analyst agent does NOT run on cron schedule

## Dependencies
None"

update_description "SEM-13" "## User Story
As the system owner, I want to disable the Strategist agent so that application package generation doesn't run on schedule anymore.

## Technical Specs
- File: openclaw.json
- Section: agents.strategist
- Change: enabled: true → enabled: false
- Add: archived: true for future reference

## Acceptance Criteria
- [ ] strategist.enabled is false
- [ ] strategist.archived is true
- [ ] Strategist agent does NOT run on cron schedule

## Dependencies
None"

update_description "SEM-14" "## User Story
As the system archivist, I want to preserve the old agent configurations for reference while marking them as deprecated.

## Technical Specs
- Files: agents/scout.md, agents/analyst.md, agents/strategist.md
- Action: Move to agents/archived/ directory
- Create: agents/archived/README.md explaining why they're archived

## Archive Structure
agents/archived/README.md - Explains deprecation
agents/archived/scout.md - Original scout agent
agents/archived/analyst.md - Original analyst agent
agents/archived/strategist.md - Original strategist agent

## Acceptance Criteria
- [ ] agents/archived/ directory created
- [ ] All three agent files moved to archived/
- [ ] agents/archived/README.md explains the deprecation
- [ ] Original files preserved (not deleted)
- [ ] Git history preserved

## Dependencies
SCOUT-DEPRECATE-001, SCOUT-DEPRECATE-002, SCOUT-DEPRECATE-003"

update_description "SEM-15" "## User Story
As the heartbeat system, I need to remove references to the old job pipeline so that heartbeat checks don't look for scout/analyst/strategist status.

## Technical Specs
- File: HEARTBEAT.md or config file controlling heartbeat behavior
- Remove: Any checks for scout_status, analyst_status, strategist_status
- Add: New checks for Linear, Notion, Email, Calendar

## Acceptance Criteria
- [ ] No references to scout, analyst, or strategist in heartbeat
- [ ] New checks added for Linear, Email, Calendar, WhatsApp
- [ ] Heartbeat runs successfully without old pipeline references

## Dependencies
SCOUT-DEPRECATE-004"

echo "Epic 2 complete. Updating Epic 3: Email..."

# Epic 3: Email Monitoring
update_description "SEM-16" "## User Story
As the skill system, I need a standard skill structure for the email-check skill so that it follows the same pattern as other skills.

## Technical Specs
- Directory: skills/email-check/
- Files to create: SKILL.md, check.py, _meta.json, README.md

## Directory Structure
skills/email-check/SKILL.md - Skill documentation
skills/email-check/check.py - Main script (stub initially)
skills/email-check/_meta.json - Skill metadata
skills/email-check/README.md - Setup instructions

## Acceptance Criteria
- [ ] skills/email-check/ directory created
- [ ] SKILL.md follows existing skill pattern
- [ ] check.py exists with basic CLI structure
- [ ] _meta.json contains skill metadata
- [ ] README.md has setup instructions

## Dependencies
None"

update_description "SEM-17" "## User Story
As the authentication system, I need Gmail API OAuth2 so that the email skill can securely access inbox data.

## Technical Specs
- API: Gmail API v1
- Auth: OAuth2 with refresh tokens
- Python library: google-auth or gspread

## Setup Steps
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth2 Client ID (Desktop app)
3. Download JSON, extract client_secret
4. Store in config/secrets.json with client_id, client_secret, refresh_token

## Acceptance Criteria
- [ ] OAuth2 flow implemented
- [ ] Token refresh works automatically
- [ ] Can list messages without manual re-auth
- [ ] Handles expired tokens gracefully

## Dependencies
SCOUT-EMAIL-001"

echo "Email ticket updates 1-3 done. Continuing..."
echo "Note: Full spec in linear-tickets/expanded_tickets.md and expanded_tickets_pt2.md"
echo "See: SCOUT-EMAIL-004 through SCOUT-EMAIL-008"

update_description "SEM-23" "## User Story
As the documentation system, I need a Notion database for email digests so that important emails are preserved for later reference.

## Technical Specs
- Use Notion MCP to create database
- Database name: Email Digest

## Schema
- Date: date
- From: rich_text
- Subject: rich_text
- Urgency: select (urgent, important, routine)
- Summary: rich_text
- Action Required: checkbox
- Link: url

## Acceptance Criteria
- [ ] Notion database created via MCP
- [ ] All fields present with correct types
- [ ] Database accessible in Notion workspace
- [ ] Schema matches requirements

## Dependencies
Epic 7 (Notion)"

update_description "SEM-24" "## User Story
As the archival system, I need to push daily email summaries to Notion so that users have a searchable history of their communications.

## Technical Specs
- Trigger: End of day (configurable)
- Action: Create Notion page with daily digest
- Content: All emails from the day, grouped by urgency

## Acceptance Criteria
- [ ] Daily digest page created in Notion
- [ ] All emails included with correct grouping
- [ ] Summary statistics included
- [ ] Page searchable by date

## Dependencies
SCOUT-EMAIL-007"

echo "Epic 3 complete. Updating Epic 4: Calendar..."

# Epic 4: Google Calendar Integration
update_description "SEM-25" "## User Story
As the skill system, I need a standard skill structure for the calendar-check skill.

## Technical Specs
- Directory: skills/calendar-check/
- Files: SKILL.md, check.py, _meta.json, README.md

## Acceptance Criteria
- [ ] skills/calendar-check/ directory created
- [ ] SKILL.md follows existing skill pattern
- [ ] check.py exists with basic CLI structure
- [ ] _meta.json contains skill metadata
- [ ] README.md has setup instructions

## Dependencies
None"

update_description "SEM-26" "## User Story
As the authentication system, I need Google Calendar API OAuth2 so that the calendar skill can securely access calendar data.

## Technical Specs
- API: Google Calendar API v3
- Auth: OAuth2 with refresh tokens
- Scope: https://www.googleapis.com/auth/calendar.readonly

## Acceptance Criteria
- [ ] OAuth2 flow implemented
- [ ] Can list calendars without manual re-auth
- [ ] Token refresh works automatically
- [ ] Handles expired tokens gracefully

## Dependencies
SCOUT-CAL-001"

update_description "SEM-27" "## User Story
As the calendar monitor, I need to fetch upcoming events so that I can alert users before meetings.

## Technical Specs
- Endpoint: GET /calendars/primary/events
- Time range: Now to +48 hours
- Fields: id, summary, start, end, attendees, location

## Acceptance Criteria
- [ ] Fetches events for next 24-48h
- [ ] Returns: id, summary, start, end, location, attendees
- [ ] Handles empty calendar gracefully
- [ ] Filters out declined events

## Dependencies
SCOUT-CAL-002"

update_description "SEM-28" "## User Story
As the reminder system, I need to send WhatsApp reminders 15 minutes before meetings so that users are never late.

## Technical Specs
- Trigger: Event start time - 15 minutes
- Check: Run every 5 minutes during active hours
- Action: Send WhatsApp message

## Message Format
⏰ Meeting in 15 minutes
📅 {event_title}
🕐 {start_time}
📍 {location or No location}
Click to join: {meeting_link}

## Acceptance Criteria
- [ ] Reminder sent 15 min before each meeting
- [ ] Message includes title, time, location
- [ ] Includes meeting link if available
- [ ] Deduplicated (no double reminders)
- [ ] Respects quiet hours (no late-night alerts)

## Dependencies
SCOUT-CAL-003, Epic 5 (WhatsApp)"

update_description "SEM-29" "## User Story
As the heartbeat system, I need to check calendar automatically so that users get a daily overview of upcoming events.

## Technical Specs
- File: HEARTBEAT.md
- Add: Calendar check to heartbeat rotation

## Acceptance Criteria
- [ ] Heartbeat calls calendar-check skill
- [ ] Today's events appear in heartbeat output
- [ ] Tomorrow's events also shown
- [ ] Follows rotation pattern

## Dependencies
SCOUT-CAL-001, SCOUT-CAL-002, SCOUT-CAL-003"

update_description "SEM-30" "## User Story
As the calendar system, I need to support multiple calendars so that users don't miss events from work or personal calendars.

## Technical Specs
- Supported: Primary, Work, Personal
- Config: config/secrets.json with calendar IDs
- Merge: Combine events from all calendars, deduplicate

## Acceptance Criteria
- [ ] Config supports multiple calendar IDs
- [ ] Events from all calendars fetched
- [ ] Duplicates removed (same event, different calendars)
- [ ] User can enable/disable specific calendars

## Dependencies
SCOUT-CAL-003"

update_description "SEM-31" "## User Story
As the calendar assistant, I need to understand natural language event requests so that users can create events by typing naturally.

## Technical Specs
- Input: Meeting with Alex tomorrow at 3pm
- Output: Structured event data
- Library: LLM (minimax m2.7) or regex patterns

## Acceptance Criteria
- [ ] Understands tomorrow at 3pm
- [ ] Understands next Monday at 2pm
- [ ] Extracts title, time, location, attendees
- [ ] Handles ambiguous requests (asks for clarification)

## Dependencies
SCOUT-CAL-001"

update_description "SEM-32" "## User Story
As the calendar assistant, I need to create calendar events from parsed requests so that users can add events via chat.

## Technical Specs
- Endpoint: POST /calendars/primary/events
- Input: Structured event data from parser

## Acceptance Criteria
- [ ] Creates event with correct title
- [ ] Sets correct start/end times
- [ ] Adds location if provided
- [ ] Adds attendees if provided
- [ ] Returns event ID

## Dependencies
SCOUT-CAL-007"

update_description "SEM-33" "## User Story
As the notification system, I need to confirm event creation via WhatsApp so that users know the event was added successfully.

## Technical Specs
- Trigger: Successful event creation
- Action: Send WhatsApp confirmation

## Message Format
✅ Event Created
📅 {event_title}
🕐 {date} at {start_time}
📍 {location or No location}
View in Google Calendar: {link}

## Acceptance Criteria
- [ ] Confirmation sent after successful creation
- [ ] Message includes all event details
- [ ] Includes Google Calendar link
- [ ] Handles creation failure gracefully (error message)

## Dependencies
SCOUT-CAL-008, Epic 5 (WhatsApp)"

echo "Epic 4 complete. Updating Epic 5: WhatsApp..."

# Epic 5: WhatsApp Communication
update_description "SEM-34" "## User Story
As the skill system, I need a standard skill structure for the whatsapp-bridge skill.

## Technical Specs
- Directory: skills/whatsapp-bridge/
- Files: SKILL.md, bridge.py, _meta.json, README.md

## Acceptance Criteria
- [ ] skills/whatsapp-bridge/ directory created
- [ ] SKILL.md follows existing skill pattern
- [ ] bridge.py exists with basic structure
- [ ] README.md has setup instructions

## Dependencies
None"

update_description "SEM-35" "## User Story
As the WhatsApp system, I need to connect to WhatsApp Web so that I can send and receive messages.

## Technical Specs
- Library: whatsapp-web.js (Node.js)
- Auth: QR code scan (initial), session persistence
- Session storage: Local file system

## Setup Steps
1. Install: npm install whatsapp-web.js
2. Create bridge.py that spawns Node process
3. Initial auth requires QR code scan
4. Session saved to ~/.openclaw/whatsapp-session.json

## Acceptance Criteria
- [ ] WhatsApp Web session established
- [ ] QR code generated for initial auth
- [ ] Session persists across restarts
- [ ] Reconnects automatically on disconnect

## Dependencies
SCOUT-WA-001"

update_description "SEM-36" "## User Story
As the message handler, I need to process incoming WhatsApp messages so that I can respond to user requests.

## Technical Specs
- Event: message_create
- Action: Parse message, route to agent
- Format: JSON with message details

## Message Format
{
  from: +1234567890,
  body: User's message,
  timestamp: 2026-04-12T12:00:00Z,
  type: chat
}

## Acceptance Criteria
- [ ] Incoming messages logged
- [ ] Messages parsed into structured format
- [ ] Routing to appropriate handler
- [ ] Acknowledge receipt (quick reply)

## Dependencies
SCOUT-WA-002"

update_description "SEM-37" "## User Story
As the notification system, I need to send WhatsApp messages so that users receive proactive updates.

## Technical Specs
- Method: client.sendMessage(number, message)
- Rate limiting: Max 1 message per 5 seconds per conversation
- Queue: Messages queued if rate limited

## Message Formatting
- No markdown tables
- Use bullet points (- or *)
- No headers (use bold instead)
- Emojis allowed and encouraged

## Acceptance Criteria
- [ ] Can send to any phone number
- [ ] Rate limiting respects WhatsApp limits
- [ ] Queue handles burst messages
- [ ] Returns delivery status

## Dependencies
SCOUT-WA-002"

update_description "SEM-38" "## User Story
As the reliability system, I need WhatsApp sessions to persist across restarts so that the bot stays connected without manual re-authentication.

## Technical Specs
- Library: whatsapp-web.js with LocalAuth
- Storage: ~/.openclaw/whatsapp-session/ directory
- Persistence: Session data (tokens, keys) survives process restart

## Acceptance Criteria
- [ ] Session persists in ~/.openclaw/whatsapp-session/
- [ ] Restarting process doesn't require new QR scan
- [ ] Invalid/expired sessions handled gracefully
- [ ] Manual re-auth triggered only when needed

## Dependencies
SCOUT-WA-002"

update_description "SEM-39" "## User Story
As the message formatter, I need to convert agent output into WhatsApp-friendly format so that users receive readable, well-formatted messages.

## Technical Specs
- Rule 1: No markdown tables (use bullet lists instead)
- Rule 2: No headers with # (use bold instead)
- Rule 3: Short lines (WhatsApp is ~50 char width)
- Rule 4: Emojis encouraged for visual hierarchy
- Rule 5: Max message length ~4000 chars (split if needed)

## Acceptance Criteria
- [ ] No markdown tables in output
- [ ] Headers converted to bold
- [ ] Bullet lists used for structured data
- [ ] Long messages split appropriately
- [ ] Emojis preserved when present

## Dependencies
SCOUT-WA-001"

update_description "SEM-40" "## User Story
As the daily briefing system, I need to send a morning WhatsApp summary so that users start their day informed.

## Technical Specs
- Trigger: Configurable time (default: 8:00 AM)
- Source: Calendar (today's meetings), Email (urgent count), Linear (open tasks)

## Briefing Format
☀️ Good Morning!
📅 Today: X meetings
📧 Urgent emails: X
📋 Open tasks: X
Have a great day! 🚀

## Acceptance Criteria
- [ ] Sends at configured time daily
- [ ] Includes today's calendar events
- [ ] Shows urgent email count
- [ ] Shows open task count
- [ ] Respects quiet hours (no messages before 7am or after 11pm)

## Dependencies
SCOUT-WA-004, SCOUT-CAL-005, SCOUT-EMAIL-005"

update_description "SEM-41" "## User Story
As the notification system, I need to send WhatsApp alerts when Linear tickets are completed so that users stay informed of progress.

## Technical Specs
- Trigger: Linear ticket moved to Done status
- Action: Send completion message via WhatsApp
- Include: Ticket title, time to complete, next action

## Message Format
✅ Task Complete
📋 {ticket_title}
Completed at: {timestamp}
{Next action or You're all caught up!}

## Acceptance Criteria
- [ ] Notification sent when ticket moves to Done
- [ ] Message includes ticket title
- [ ] Includes completion timestamp
- [ ] Includes next action if applicable
- [ ] Deduplicated (no double notifications)

## Dependencies
SCOUT-WA-004, SCOUT-LINEAR-003"

echo "Epic 5 complete. Updating Epic 6: Linear..."

# Epic 6: Linear Integration
update_description "SEM-42" "## User Story
As the workflow designer, I need to document the Linear-first approach so that all tasks follow the same process.

## Technical Specs
- File: AGENTS.md
- Add: New section Task Management documenting Linear-first workflow

## Workflow
1. Create → Create Linear ticket first
2. Execute → Work from ticket description
3. Update → Mark status: Todo → In Progress → Done
4. Notify → Send completion via WhatsApp

## Acceptance Criteria
- [ ] AGENTS.md updated with Task Management section
- [ ] Linear-first workflow clearly documented
- [ ] All team members understand the process
- [ ] References to old job pipeline removed

## Dependencies
None"

update_description "SEM-43" "## User Story
As the automation system, I need to create Linear tickets programmatically via MCP so that tasks can be logged automatically.

## Technical Specs
- Use: @linearhq/linear-mcp-integration or direct GraphQL
- Endpoint: mutation issueCreate
- Input: title, description, priority, teamId

## GraphQL Mutation
mutation CreateIssue(input: IssueCreateInput!) {
  issueCreate(input: input) {
    success
    issue { id identifier title }
  }
}

## Acceptance Criteria
- [ ] Can create tickets via MCP tool
- [ ] Ticket includes title, description, priority
- [ ] Returns ticket ID and identifier
- [ ] Handles creation failures gracefully
- [ ] Team ID and Project ID configurable

## Dependencies
SCOUT-LINEAR-001"

update_description "SEM-44" "## User Story
As the workflow system, I need to update ticket status as work progresses so that the team has visibility into task state.

## Technical Specs
- States: backlog → triage → todo → in_progress → in_review → done
- Use: issueUpdate mutation
- Trigger: Automatic on work start and completion

## Acceptance Criteria
- [ ] Can transition ticket to any valid state
- [ ] Status updates reflect in Linear UI
- [ ] Automatic transitions: Todo → In Progress on work start, In Progress → Done on completion
- [ ] Handles state transition errors

## Dependencies
SCOUT-LINEAR-002"

update_description "SEM-45" "## User Story
As the task scheduler, I need to execute tickets by priority so that urgent work gets done first.

## Technical Specs
- Priority order: P0 (urgent) → P1 (high) → P2 (medium) → P3 (low) → P4 (no priority)
- Selection: Pick highest priority open ticket
- Config: Max tasks per day configurable

## Acceptance Criteria
- [ ] Fetches all open tickets
- [ ] Sorts by priority (P0 first)
- [ ] Returns highest priority ticket
- [ ] Respects daily task limit
- [ ] Skips blocked tickets

## Dependencies
SCOUT-LINEAR-002"

update_description "SEM-46" "## User Story
As the intake system, I need to convert WhatsApp messages into Linear tickets so that user requests are properly tracked.

## Technical Specs
- Input: Natural language request from WhatsApp
- Output: Structured ticket title + description
- Method: LLM-based parsing with fallback to regex

## Acceptance Criteria
- [ ] Parses natural language into structured data
- [ ] Extracts title (max 60 chars)
- [ ] Extracts priority from urgency keywords
- [ ] Generates detailed description
- [ ] Handles parsing failures gracefully

## Dependencies
SCOUT-WA-003, SCOUT-LINEAR-002"

update_description "SEM-47" "## User Story
As the priority system, I need to auto-assign priority based on keywords so that urgent requests get immediate attention.

## Technical Specs
- Keywords: urgent/asap/now → P0
- Keywords: important/soon/today → P1
- Keywords: this week/when you can → P2
- Default: P3 (normal priority)

## Acceptance Criteria
- [ ] Detects urgent keywords → P0
- [ ] Detects important keywords → P1
- [ ] Default to P3 when no keywords
- [ ] Case insensitive matching
- [ ] Logs priority assignment reason

## Dependencies
SCOUT-LINEAR-005"

update_description "SEM-48" "## User Story
As the documentation system, I need to link Notion pages to Linear tickets so that work products are easily accessible.

## Technical Specs
- When: Creating Notion page as part of ticket work
- Action: Add Notion page URL to Linear ticket metadata
- Method: issueUpdate with description append

## Acceptance Criteria
- [ ] Notion URL added to ticket description
- [ ] URL is clickable in Linear UI
- [ ] Works with any Notion page type
- [ ] Handles missing ticket gracefully
- [ ] Preserves existing description

## Dependencies
SCOUT-LINEAR-003, SCOUT-NOTION-004"

echo "Epic 6 complete. Updating Epic 7: Notion..."

# Epic 7: Notion Integration
update_description "SEM-49" "## User Story
As the architect, I need to define the Notion workspace structure so that all team members know where to find and create content.

## Technical Specs
- Root: Scout Assistant workspace/database
- Databases: Daily Briefing, Research, Deliverables, Knowledge Base

## Workspace Structure
Scout Assistant/
├── Daily Briefing/ (date, email_summary, calendar_summary, tasks)
├── Research/ (topic, source, summary, date, tags)
├── Deliverables/ (title, type, project, link, status, date)
└── Knowledge Base/ (title, category, content, tags, date)

## Acceptance Criteria
- [ ] Workspace structure documented
- [ ] Database purposes defined
- [ ] Property schemas planned
- [ ] Access permissions set
- [ ] Team knows the structure

## Dependencies
None"

update_description "SEM-50" "## User Story
As the briefing system, I need a Daily Briefing database so that daily summaries are organized and searchable.

## Technical Specs
- Use: Notion API to create database
- Schema: Date, Email Summary, Urgent Count, Calendar Summary, Meeting Count, Tasks Completed, Task Count, Notes

## Acceptance Criteria
- [ ] Database created via Notion API
- [ ] All properties present with correct types
- [ ] Database accessible in workspace
- [ ] Parent page correctly set
- [ ] Can add entries programmatically

## Dependencies
SCOUT-NOTION-001"

update_description "SEM-51" "## User Story
As the research system, I need a Research database so that research tasks are organized and referenceable.

## Technical Specs
- Use: Notion API to create database
- Schema: Topic, Source, Summary, Date, Tags, Link, Status

## Acceptance Criteria
- [ ] Database created via Notion API
- [ ] All properties present with correct types
- [ ] Multi-select tags working
- [ ] Status select options configured
- [ ] Can add entries programmatically

## Dependencies
SCOUT-NOTION-001"

update_description "SEM-52" "## User Story
As the automation system, I need to create Notion pages programmatically via MCP so that work outputs are captured automatically.

## Technical Specs
- Use: Notion MCP API-post-page tool
- Content: Block structure (paragraphs, lists, headings)
- Parent: Database ID or page ID

## Acceptance Criteria
- [ ] Can create page in database
- [ ] Page title set correctly
- [ ] Content blocks rendered
- [ ] Parent correctly set
- [ ] Returns page ID

## Dependencies
SCOUT-NOTION-002, SCOUT-NOTION-003"

update_description "SEM-53" "## User Story
As the archival system, I need to push daily briefings to Notion so that users have a historical record of daily activity.

## Technical Specs
- Trigger: End of day (configurable, e.g., 6pm)
- Source: Today's email digest, calendar, completed tasks
- Target: Daily Briefing database

## Acceptance Criteria
- [ ] Runs at configured end-of-day time
- [ ] Creates page in Daily Briefing database
- [ ] Includes email summary with counts
- [ ] Includes calendar summary with meeting list
- [ ] Includes completed tasks
- [ ] Page searchable by date

## Dependencies
SCOUT-NOTION-002, SCOUT-NOTION-004, SCOUT-EMAIL-008, SCOUT-CAL-005"

update_description "SEM-54" "## User Story
As the research system, I need to push research results to Notion so that findings are preserved and shared.

## Technical Specs
- Trigger: Research task completion
- Source: Task output (summary, source, tags)
- Target: Research database

## Acceptance Criteria
- [ ] Creates page in Research database
- [ ] Includes topic, summary, source, link
- [ ] Tags applied correctly
- [ ] Status set to Complete
- [ ] Linked to originating Linear ticket

## Dependencies
SCOUT-NOTION-003, SCOUT-NOTION-004, SCOUT-LINEAR-007"

echo "Epic 7 complete. Updating Epic 8: AGENTS.md Rewrite..."

# Epic 8: AGENTS.md Rewrite
update_description "SEM-55" "## User Story
As the identity system, I need to update the Every Session section so that the new workflow loads correctly.

## Technical Specs
- File: AGENTS.md
- Section: Every Session
- Changes: Add Linear and Notion context loading

## Updated Steps
1. Read SOUL.md
2. Read USER.md
3. Read memory/YYYY-MM-DD.md (today + yesterday)
4. If in MAIN SESSION: Read MEMORY.md
5. Check Linear for open tickets (P0 and P1 priorities)
6. Check Notion for recent Daily Briefings

## Acceptance Criteria
- [ ] Section updated with Linear check step
- [ ] Section updated with Notion check step
- [ ] Steps in logical order
- [ ] Clear why each step matters

## Dependencies
None"

update_description "SEM-56" "## User Story
As the workflow system, I need a Task Management section so that the Linear-first workflow is documented.

## Technical Specs
- File: AGENTS.md
- Add: New section documenting Linear-first workflow

## Process
1. Create Ticket → Any task request becomes a Linear ticket first
2. Execute → Work from ticket description
3. Update Status → Todo → In Progress → Done
4. Notify → Send completion via WhatsApp

## Acceptance Criteria
- [ ] Section added to AGENTS.md
- [ ] Process clearly documented
- [ ] Ticket creation steps detailed
- [ ] Priority guidelines included
- [ ] Examples provided

## Dependencies
SCOUT-LINEAR-001, SCOUT-LINEAR-002"

update_description "SEM-57" "## User Story
As the documentation system, I need an Integrations section so that all external services are documented.

## Technical Specs
- File: AGENTS.md
- Document: Minimax LLM, Linear, Notion, Gmail, Google Calendar, WhatsApp

## For Each Integration
- Purpose
- Access method
- Config location
- Setup requirements

## Acceptance Criteria
- [ ] Section added to AGENTS.md
- [ ] All 6 integrations documented
- [ ] Purpose, access method, config location for each
- [ ] Setup requirements clear

## Dependencies
SCOUT-EMAIL-002, SCOUT-CAL-002, SCOUT-WA-002, SCOUT-LINEAR-002, SCOUT-NOTION-001"

update_description "SEM-58" "## User Story
As the heartbeat system, I need to update the Heartbeats section so that the new integrations are checked properly.

## Technical Specs
- File: AGENTS.md
- Section: Heartbeats
- Changes: Replace old pipeline checks with new integration checks

## Check Rotation
1. Email (every 2 hours during work hours)
2. Calendar (morning heartbeat)
3. Linear (every heartbeat)
4. WhatsApp (respond to messages)

## Acceptance Criteria
- [ ] Section updated with new rotation
- [ ] Email, Calendar, Linear, WhatsApp checks defined
- [ ] Quiet hours documented
- [ ] Morning briefing time and format specified
- [ ] No references to old job pipeline

## Dependencies
SCOUT-EMAIL-005, SCOUT-CAL-005, SCOUT-LINEAR-004, SCOUT-WA-007"

update_description "SEM-59" "## User Story
As the communication system, I need to document the WhatsApp communication style so that messages are consistent.

## Technical Specs
- File: AGENTS.md
- Add: New section with formatting rules

## Format Rules
1. No Markdown Tables → Use bullet lists
2. No Headers with # → Use bold
3. Use Emojis (sparingly for hierarchy)
4. Short Lines (~50 chars)
5. Bullet Lists with •

## Acceptance Criteria
- [ ] Section added to AGENTS.md
- [ ] Table rule clearly stated
- [ ] Header/bold rule clearly stated
- [ ] Emoji usage documented
- [ ] Message examples provided

## Dependencies
SCOUT-WA-006"

update_description "SEM-60" "## User Story
As the archivist, I need to remove job search references so that the agent doesn't accidentally fall back to old behaviors.

## Technical Specs
- File: AGENTS.md
- Remove/Update: All references to scout, analyst, strategist agents
- Add: Deprecation notices where needed

## Acceptance Criteria
- [ ] No active workflow references to old agents
- [ ] Deprecation notice added where appropriate
- [ ] Archive location noted
- [ ] All team members understand old system deprecated
- [ ] Old agent files moved to agents/archived/

## Dependencies
SCOUT-DEPRECATE-004"

echo ""
echo "=============================================="
echo "Ticket description update complete!"
echo ""
echo "Note: Full expanded specs are in:"
echo "  - linear-tickets/expanded_tickets.md (Epics 1-3)"
echo "  - linear-tickets/expanded_tickets_pt2.md (Epic 4-5 partial)"
echo "  - linear-tickets/expanded_tickets_pt3.md (Epic 5-8)"
echo ""
echo "These files contain complete user stories,"
echo "technical specs, code patterns, and acceptance criteria."
echo "=============================================="