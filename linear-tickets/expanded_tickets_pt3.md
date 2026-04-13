# Expanded Ticket Specs - Part 3 (Epics 5-8)
# Completes SCOUT-WA-005 through SCOUT-DOCS-006

---

## Epic 5: WhatsApp Communication (continued)

### SCOUT-WA-005: Implement session persistence

**User Story:** As the reliability system, I need WhatsApp sessions to persist across restarts so that the bot stays connected without manual re-authentication.

**Technical Specs:**
- Library: `whatsapp-web.js` with `LocalAuth`
- Storage: `~/.openclaw/whatsapp-session/` directory
- Persistence: Session data (tokens, keys) survives process restart

**Code Pattern:**
```python
import json
import os
import subprocess

SESSION_DIR = os.path.expanduser("~/.openclaw/whatsapp-session")

def is_session_valid():
    """Check if stored session is still valid"""
    session_file = os.path.join(SESSION_DIR, "session.json")
    return os.path.exists(session_file)

def get_or_create_session():
    """Get existing session or create new one"""
    if is_session_valid():
        return load_session()
    else:
        return create_new_session()
```

**Acceptance Criteria:**
- [ ] Session persists in `~/.openclaw/whatsapp-session/`
- [ ] Restarting process doesn't require new QR scan
- [ ] Invalid/expired sessions handled gracefully
- [ ] Manual re-auth triggered only when needed

**Dependencies:** SCOUT-WA-002

---

### SCOUT-WA-006: Format messages for WhatsApp

**User Story:** As the message formatter, I need to convert agent output into WhatsApp-friendly format so that users receive readable, well-formatted messages.

**Technical Specs:**
- Rule 1: No markdown tables (use bullet lists instead)
- Rule 2: No headers with # (use **bold** instead)
- Rule 3: Short lines (WhatsApp is ~50 char width)
- Rule 4: Emojis encouraged for visual hierarchy
- Rule 5: Max message length ~4000 chars (split if needed)

**Formatting Function:**
```python
def format_for_whatsapp(text):
    # Replace tables with bullet lists
    lines = text.split('\n')
    formatted = []
    
    for line in lines:
        # Remove markdown headers
        if line.startswith('# '):
            line = '**' + line[2:] + '**'
        # Convert table rows to bullets (skip separator lines)
        elif '|' in line and not line.strip().startswith('|---'):
            # Extract text between pipes
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if cells:
                formatted.append('• ' + ' | '.join(cells))
        else:
            formatted.append(line)
    
    return '\n'.join(formatted)
```

**Acceptance Criteria:**
- [ ] No markdown tables in output
- [ ] Headers converted to bold
- [ ] Bullet lists used for structured data
- [ ] Long messages split appropriately
- [ ] Emojis preserved when present

**Dependencies:** SCOUT-WA-001

---

### SCOUT-WA-007: Send daily morning briefing

**User Story:** As the daily briefing system, I need to send a morning WhatsApp summary so that users start their day informed.

**Technical Specs:**
- Trigger: Configurable time (default: 8:00 AM)
- Source: Calendar (today's meetings), Email (urgent count), Linear (open tasks)

**Briefing Format:**
```
☀️ Good Morning!

📅 Today: X meetings
   • Meeting 1 @ 9am
   • Meeting 2 @ 2pm

📧 Urgent emails: X
   (Check email skill for details)

📋 Open tasks: X
   (Check Linear for priorities)

Have a great day! 🚀
```

**Implementation:**
```python
def send_morning_briefing():
    # 1. Fetch today's events
    events = fetch_upcoming_events(hours=24)
    
    # 2. Count urgent emails
    emails = fetch_unread_emails(hours=24)
    urgent_count = sum(1 for e in emails if e['urgency'] == 'urgent')
    
    # 3. Get open Linear tickets
    tickets = fetch_linear_tickets(status='open')
    
    # 4. Format and send
    message = format_morning_briefing(events, urgent_count, tickets)
    send_whatsapp(user_number, message)
```

**Acceptance Criteria:**
- [ ] Sends at configured time daily
- [ ] Includes today's calendar events
- [ ] Shows urgent email count
- [ ] Shows open task count
- [ ] Respects quiet hours (no messages before 7am or after 11pm)

**Dependencies:** SCOUT-WA-004, SCOUT-CAL-005, SCOUT-EMAIL-005

---

### SCOUT-WA-008: Send task completion notifications

**User Story:** As the notification system, I need to send WhatsApp alerts when Linear tickets are completed so that users stay informed of progress.

**Technical Specs:**
- Trigger: Linear ticket moved to "Done" status
- Action: Send completion message via WhatsApp
- Include: Ticket title, time to complete, next action

**Message Format:**
```
✅ Task Complete

📋 {ticket_title}

Completed at: {timestamp}

{Next action or "You're all caught up!"}
```

**Implementation:**
```python
def on_ticket_completed(ticket):
    message = f"""✅ Task Complete

📋 {ticket['title']}

Completed at: {datetime.now().strftime('%I:%M %p')}

You're all caught up! 🎉"""
    
    send_whatsapp(user_number, message)
```

**Acceptance Criteria:**
- [ ] Notification sent when ticket moves to Done
- [ ] Message includes ticket title
- [ ] Includes completion timestamp
- [ ] Includes next action if applicable
- [ ] Deduplicated (no double notifications)

**Dependencies:** SCOUT-WA-004, SCOUT-LINEAR-003

---

## Epic 6: Linear Integration

### SCOUT-LINEAR-001: Update AGENTS.md with Linear-first workflow

**User Story:** As the workflow designer, I need to document the Linear-first approach so that all tasks follow the same process.

**Technical Specs:**
- File: `AGENTS.md`
- Add: New section "Task Management" documenting Linear-first workflow

**New AGENTS.md Section:**
```markdown
## Task Management

All tasks follow this workflow:

1. **Create** → Create Linear ticket first
2. **Execute** → Work from ticket description
3. **Update** → Mark status: Todo → In Progress → Done
4. **Notify** → Send completion via WhatsApp

### Creating Tickets
When a task is requested (via WhatsApp or direct):
1. Parse request into title + description
2. Create Linear ticket via MCP
3. Confirm creation to user
4. Execute work
5. Update ticket status
6. Send completion notification
```

**Acceptance Criteria:**
- [ ] AGENTS.md updated with Task Management section
- [ ] Linear-first workflow clearly documented
- [ ] All team members understand the process
- [ ] References to old job pipeline removed

**Dependencies:** None

---

### SCOUT-LINEAR-002: Implement ticket creation via MCP

**User Story:** As the automation system, I need to create Linear tickets programmatically via MCP so that tasks can be logged automatically.

**Technical Specs:**
- Use: `@linearhq/linear-mcp-integration` or direct GraphQL
- Endpoint: `mutation issueCreate`
- Input: title, description, priority, teamId

**GraphQL Mutation:**
```graphql
mutation CreateIssue($input: IssueCreateInput!) {
  issueCreate(input: $input) {
    success
    issue {
      id
      identifier
      title
    }
  }
}

Variables:
{
  "input": {
    "title": "Task title",
    "description": "Task description with user story + tech specs",
    "priority": 1,
    "teamId": "team-id-here",
    "projectId": "project-id-here"
  }
}
```

**Acceptance Criteria:**
- [ ] Can create tickets via MCP tool
- [ ] Ticket includes title, description, priority
- [ ] Returns ticket ID and identifier
- [ ] Handles creation failures gracefully
- [ ] Team ID and Project ID configurable

**Dependencies:** SCOUT-LINEAR-001

---

### SCOUT-LINEAR-003: Implement ticket status updates

**User Story:** As the workflow system, I need to update ticket status as work progresses so that the team has visibility into task state.

**Technical Specs:**
- States: `backlog` → `triage` → `todo` → `in_progress` → `in_review` → `done`
- Use: `issueUpdate` mutation
- Trigger: Automatic on work start and completion

**Status Update Function:**
```python
def update_ticket_status(ticket_id, new_state):
    mutation = """
    mutation UpdateIssue($id: String!, $state: String!) {
      issueUpdate(id: $id, input: { state: $state }) {
        success
        issue { id identifier state }
      }
    }
    """
    variables = {"id": ticket_id, "state": new_state}
    return execute_graphql(mutation, variables)
```

**Acceptance Criteria:**
- [ ] Can transition ticket to any valid state
- [ ] Status updates reflect in Linear UI
- [ ] Automatic transitions:
  - Todo → In Progress on work start
  - In Progress → Done on completion
- [ ] Handles state transition errors

**Dependencies:** SCOUT-LINEAR-002

---

### SCOUT-LINEAR-004: Implement priority-based execution

**User Story:** As the task scheduler, I need to execute tickets by priority so that urgent work gets done first.

**Technical Specs:**
- Priority order: P0 (urgent) → P1 (high) → P2 (medium) → P3 (low) → P4 (no priority)
- Selection: Pick highest priority open ticket
- Config: Max tasks per day configurable

**Heartbeat Logic:**
```python
def pick_next_task():
    # Fetch open tickets sorted by priority
    query = """
    query OpenTickets {
      issues(filter: { state: { name: { in: ["Todo", "In Progress"] } } }) {
        nodes {
          id identifier title priority
        }
      }
    }
    """
    tickets = execute_graphql(query)['data']['issues']['nodes']
    
    # Sort by priority (0 = highest)
    tickets.sort(key=lambda t: t['priority'])
    
    return tickets[0] if tickets else None
```

**Acceptance Criteria:**
- [ ] Fetches all open tickets
- [ ] Sorts by priority (P0 first)
- [ ] Returns highest priority ticket
- [ ] Respects daily task limit
- [ ] Skips blocked tickets

**Dependencies:** SCOUT-LINEAR-002

---

### SCOUT-LINEAR-005: Parse WhatsApp requests to tickets

**User Story:** As the intake system, I need to convert WhatsApp messages into Linear tickets so that user requests are properly tracked.

**Technical Specs:**
- Input: Natural language request from WhatsApp
- Output: Structured ticket title + description
- Method: LLM-based parsing with fallback to regex

**Parser Function:**
```python
def parse_whatsapp_to_ticket(message):
    prompt = f"""Convert this user request into a Linear ticket:

Request: {message}

Respond ONLY with JSON:
{{
  "title": "Short, clear ticket title (max 60 chars)",
  "description": "Detailed description including context, requirements, acceptance criteria",
  "priority": 0-4 (0=urgent, 4=none)
}}

Examples:
- "Schedule meeting with Alex tomorrow" → title: "Schedule meeting with Alex", priority: 2
- "URGENT: Fix login bug" → title: "Fix login bug", priority: 0
"""

    response = llm_client.chat.completions.create(
        model="minimax/m2.7",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return json.loads(response.choices[0].message.content)
```

**Acceptance Criteria:**
- [ ] Parses natural language into structured data
- [ ] Extracts title (max 60 chars)
- [ ] Extracts priority from urgency keywords
- [ ] Generates detailed description
- [ ] Handles parsing failures gracefully

**Dependencies:** SCOUT-WA-003, SCOUT-LINEAR-002

---

### SCOUT-LINEAR-006: Auto-assign priority based on keywords

**User Story:** As the priority system, I need to auto-assign priority based on keywords so that urgent requests get immediate attention.

**Technical Specs:**
- Keywords: `urgent`/`asap`/`now` → P0
- Keywords: `important`/`soon`/`today` → P1
- Keywords: `this week`/`when you can` → P2
- Default: P3 (normal priority)

**Keyword Priority Mapper:**
```python
PRIORITY_KEYWORDS = {
    0: ['urgent', 'asap', 'immediately', 'now', 'critical', 'emergency'],
    1: ['important', 'soon', 'today', 'eod', 'priority'],
    2: ['this week', 'when you can', 'eventually'],
    3: ['low priority', 'nice to have', 'someday']
}

def extract_priority(text):
    text_lower = text.lower()
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return priority
    return 3  # Default
```

**Acceptance Criteria:**
- [ ] Detects urgent keywords → P0
- [ ] Detects important keywords → P1
- [ ] Default to P3 when no keywords
- [ ] Case insensitive matching
- [ ] Logs priority assignment reason

**Dependencies:** SCOUT-LINEAR-005

---

### SCOUT-LINEAR-007: Link Notion deliverables to tickets

**User Story:** As the documentation system, I need to link Notion pages to Linear tickets so that work products are easily accessible.

**Technical Specs:**
- When: Creating Notion page as part of ticket work
- Action: Add Notion page URL to Linear ticket metadata
- Method: `issueUpdate` with `displayIconUrl` or custom field

**Link Implementation:**
```python
def link_notion_to_ticket(ticket_id, notion_page_url):
    mutation = """
    mutation LinkNotion($id: String!, $url: String!) {
      issueUpdate(id: $id, input: {
        description: "📎 Notion: {url}"
      }) {
        success
      }
    }
    """
    # Append to description or update custom field
    variables = {"id": ticket_id, "url": notion_page_url}
    return execute_graphql(mutation, variables)
```

**Acceptance Criteria:**
- [ ] Notion URL added to ticket description
- [ ] URL is clickable in Linear UI
- [ ] Works with any Notion page type
- [ ] Handles missing ticket gracefully
- [ ] Preserves existing description

**Dependencies:** SCOUT-LINEAR-003, SCOUT-NOTION-004

---

## Epic 7: Notion Integration

### SCOUT-NOTION-001: Define Notion workspace structure

**User Story:** As the architect, I need to define the Notion workspace structure so that all team members know where to find and create content.

**Technical Specs:**
- Root: "Scout Assistant" workspace/database
- Databases:
  1. Daily Briefing
  2. Research
  3. Deliverables
  4. Knowledge Base

**Workspace Structure:**
```
Scout Assistant (Workspace)
├── Daily Briefing (Database)
│   ├── Properties: date, email_summary, calendar_summary, tasks
│   └── Entries: One per day
├── Research (Database)
│   ├── Properties: topic, source, summary, date, tags
│   └── Entries: One per research task
├── Deliverables (Database)
│   ├── Properties: title, type, project, link, status, date
│   └── Entries: One per deliverable
└── Knowledge Base (Database)
    ├── Properties: title, category, content, tags, date
    └── Entries: Reference materials
```

**Acceptance Criteria:**
- [ ] Workspace structure documented
- [ ] Database purposes defined
- [ ] Property schemas planned
- [ ] Access permissions set
- [ ] Team knows the structure

**Dependencies:** None

---

### SCOUT-NOTION-002: Create Daily Briefing database

**User Story:** As the briefing system, I need a Daily Briefing database so that daily summaries are organized and searchable.

**Technical Specs:**
- Use: Notion API to create database
- Parent: Root page or specified parent page
- Schema: See below

**Database Schema:**
```json
{
  "name": "Daily Briefing",
  "properties": {
    "Date": {
      "type": "date",
      "date": {}
    },
    "Email Summary": {
      "type": "rich_text",
      "rich_text": {}
    },
    "Urgent Count": {
      "type": "number",
      "number": {"format": "number"}
    },
    "Calendar Summary": {
      "type": "rich_text",
      "rich_text": {}
    },
    "Meeting Count": {
      "type": "number",
      "number": {"format": "number"}
    },
    "Tasks Completed": {
      "type": "rich_text",
      "rich_text": {}
    },
    "Task Count": {
      "type": "number", 
      "number": {"format": "number"}
    },
    "Notes": {
      "type": "rich_text",
      "rich_text": {}
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Database created via Notion API
- [ ] All properties present with correct types
- [ ] Database accessible in workspace
- [ ] Parent page correctly set
- [ ] Can add entries programmatically

**Dependencies:** SCOUT-NOTION-001

---

### SCOUT-NOTION-003: Create Research database

**User Story:** As the research system, I need a Research database so that research tasks are organized and referenceable.

**Technical Specs:**
- Use: Notion API to create database
- Parent: Root page or specified parent page

**Database Schema:**
```json
{
  "name": "Research",
  "properties": {
    "Topic": {
      "type": "title",
      "title": {}
    },
    "Source": {
      "type": "rich_text",
      "rich_text": {}
    },
    "Summary": {
      "type": "rich_text",
      "rich_text": {}
    },
    "Date": {
      "type": "date",
      "date": {}
    },
    "Tags": {
      "type": "multi_select",
      "multi_select": {
        "options": ["tech", "business", "market", "competitor", "other"]
      }
    },
    "Link": {
      "type": "url",
      "url": {}
    },
    "Status": {
      "type": "select",
      "select": {
        "options": [
          {"name": "In Progress", "color": "yellow"},
          {"name": "Complete", "color": "green"},
          {"name": "On Hold", "color": "gray"}
        ]
      }
    }
  }
}
```

**Acceptance Criteria:**
- [ ] Database created via Notion API
- [ ] All properties present with correct types
- [ ] Multi-select tags working
- [ ] Status select options configured
- [ ] Can add entries programmatically

**Dependencies:** SCOUT-NOTION-001

---

### SCOUT-NOTION-004: Implement Notion page creation via MCP

**User Story:** As the automation system, I need to create Notion pages programmatically via MCP so that work outputs are captured automatically.

**Technical Specs:**
- Use: Notion MCP `API-post-page` tool
- Content: Block structure (paragraphs, lists, headings)
- Parent: Database ID or page ID

**Page Creation Function:**
```python
def create_notion_page(parent_id, title, blocks):
    """
    parent_id: Database ID or Page ID
    title: Page title
    blocks: List of content blocks
    """
    payload = {
        "parent": {"database_id": parent_id},
        "properties": {
            "title": {
                "title": [{"text": {"content": title}}]
            }
        },
        "children": blocks
    }
    
    return notion_client.pages.create(**payload)
```

**Block Types:**
```python
# Paragraph
{"paragraph": {"rich_text": [{"text": {"content": "Text"}}]}, "type": "paragraph"}

# Heading
{"heading_2": {"rich_text": [{"text": {"content": "Heading"}}]}, "type": "heading_2"}

# Bulleted list
{"bulleted_list_item": {"rich_text": [{"text": {"content": "Item"}}]}, "type": "bulleted_list_item"}

# Divider
{"type": "divider", "divider": {}}
```

**Acceptance Criteria:**
- [ ] Can create page in database
- [ ] Page title set correctly
- [ ] Content blocks rendered
- [ ] Parent correctly set
- [ ] Returns page ID

**Dependencies:** SCOUT-NOTION-002, SCOUT-NOTION-003

---

### SCOUT-NOTION-005: Push daily briefing to Notion

**User Story:** As the archival system, I need to push daily briefings to Notion so that users have a historical record of daily activity.

**Technical Specs:**
- Trigger: End of day (configurable, e.g., 6pm)
- Source: Today's email digest, calendar, completed tasks
- Target: Daily Briefing database

**Implementation:**
```python
def push_daily_briefing():
    # 1. Gather today's data
    date = datetime.now().strftime('%Y-%m-%d')
    
    emails = fetch_today_emails()
    urgent_count = sum(1 for e in emails if e['urgency'] == 'urgent')
    email_summary = format_email_summary(emails)
    
    events = fetch_today_events()
    meeting_count = len(events)
    calendar_summary = format_calendar_summary(events)
    
    tasks = fetch_completed_tasks_today()
    task_count = len(tasks)
    tasks_summary = format_task_summary(tasks)
    
    # 2. Create Notion page
    page_title = f"Daily Briefing - {date}"
    blocks = [
        {"heading_1": {"rich_text": [{"text": {"content": "Daily Briefing"}}]}, "type": "heading_1"},
        {"heading_2": {"rich_text": [{"text": {"content": "Email Summary"}}]}, "type": "heading_2"},
        {"paragraph": {"rich_text": [{"text": {"content": email_summary}}]}, "type": "paragraph"},
        {"divider": {}, "type": "divider"},
        {"heading_2": {"rich_text": [{"text": {"content": "Calendar Summary"}}]}, "type": "heading_2"},
        {"paragraph": {"rich_text": [{"text": {"content": calendar_summary}}]}, "type": "paragraph"},
        {"divider": {}, "type": "divider"},
        {"heading_2": {"rich_text": [{"text": {"content": "Tasks Completed"}}]}, "type": "heading_2"},
        {"paragraph": {"rich_text": [{"text": {"content": tasks_summary}}]}, "type": "paragraph"},
    ]
    
    create_notion_page(Daily_Briefing_DB_ID, page_title, blocks)
```

**Acceptance Criteria:**
- [ ] Runs at configured end-of-day time
- [ ] Creates page in Daily Briefing database
- [ ] Includes email summary with counts
- [ ] Includes calendar summary with meeting list
- [ ] Includes completed tasks
- [ ] Page searchable by date

**Dependencies:** SCOUT-NOTION-002, SCOUT-NOTION-004, SCOUT-EMAIL-008, SCOUT-CAL-005

---

### SCOUT-NOTION-006: Push research results to Notion

**User Story:** As the research system, I need to push research results to Notion so that findings are preserved and shared.

**Technical Specs:**
- Trigger: Research task completion
- Source: Task output (summary, source, tags)
- Target: Research database

**Implementation:**
```python
def push_research_results(topic, source, summary, tags=None, link=None):
    blocks = [
        {"heading_1": {"rich_text": [{"text": {"content": topic}}]}, "type": "heading_1"},
        {"heading_2": {"rich_text": [{"text": {"content": "Summary"}}]}, "type": "heading_2"},
        {"paragraph": {"rich_text": [{"text": {"content": summary}}]}, "type": "paragraph"},
    ]
    
    if source:
        blocks.append(
            {"heading_2": {"rich_text": [{"text": {"content": "Source"}}]}, "type": "heading_2"},
            {"paragraph": {"rich_text": [{"text": {"content": source}}]}, "type": "paragraph"},
        )
    
    if link:
        blocks.append(
            {"heading_2": {"rich_text": [{"text": {"content": "Link"}}]}, "type": "heading_2"},
            {"paragraph": {"rich_text": [{"text": {"content": link}}]}, "type": "paragraph"},
        )
    
    page = create_notion_page(Research_DB_ID, topic, blocks)
    
    # Update status if tracking
    update_research_status(page['id'], 'Complete')
    
    return page
```

**Acceptance Criteria:**
- [ ] Creates page in Research database
- [ ] Includes topic, summary, source, link
- [ ] Tags applied correctly
- [ ] Status set to Complete
- [ ] Linked to originating Linear ticket

**Dependencies:** SCOUT-NOTION-003, SCOUT-NOTION-004, SCOUT-LINEAR-007

---

## Epic 8: AGENTS.md Rewrite

### SCOUT-DOCS-001: Rewrite Every Session section

**User Story:** As the identity system, I need to update the Every Session section so that the new workflow loads correctly.

**Technical Specs:**
- File: `AGENTS.md`
- Section: "Every Session"
- Changes: Add Linear and Notion context loading

**Current Section:**
```markdown
## Every Session

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION**: Also read `MEMORY.md`
```

**Updated Section:**
```markdown
## Every Session

Before doing anything else:

1. Read `SOUL.md` — this is who you are
2. Read `USER.md` — this is who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) for recent context
4. **If in MAIN SESSION**: Also read `MEMORY.md`
5. Check Linear for open tickets — look for P0 and P1 priorities
6. Check Notion for recent Daily Briefings — understand recent activity
```

**Acceptance Criteria:**
- [ ] Section updated with Linear check step
- [ ] Section updated with Notion check step
- [ ] Steps in logical order
- [ ] Clear why each step matters
- [ ] Links to relevant docs

**Dependencies:** None

---

### SCOUT-DOCS-002: Add Task Management section

**User Story:** As the workflow system, I need a Task Management section so that the Linear-first workflow is documented.

**Technical Specs:**
- File: `AGENTS.md`
- Add: New section after "Task Management" exists or after Memory section
- Content: Linear-first workflow documentation

**New Section:**
```markdown
## Task Management

All tasks follow the Linear-first workflow:

### The Process
1. **Create Ticket** → Any task request becomes a Linear ticket first
2. **Execute** → Work from ticket description (has user story + tech specs)
3. **Update Status** → Todo → In Progress → Done
4. **Notify** → Send completion via WhatsApp

### Creating Tickets
When you receive a task request:
1. Parse request into title + description
2. Create ticket via Linear MCP with:
   - Title: Clear, actionable (max 60 chars)
   - Description: User story + technical specs + acceptance criteria
   - Priority: Based on urgency keywords
   - Team: Semops
3. Confirm creation to user via WhatsApp
4. Execute the work
5. Update ticket to In Progress
6. Complete work
7. Update ticket to Done
8. Send completion notification

### Priority Guidelines
- **P0 (Urgent)**: Needs done now, blocking other work
- **P1 (High)**: Important, do soon
- **P2 (Medium)**: Normal priority
- **P3 (Low)**: Can wait, nice to have
- **P4 (None)**: Backlog filler

### Execution Order
Heartbeat picks tasks in priority order:
1. P0 tickets first
2. Then P1, P2, P3 in order
3. Respect daily limits
4. Skip blocked tickets
```

**Acceptance Criteria:**
- [ ] Section added to AGENTS.md
- [ ] Process clearly documented (Create → Execute → Update → Notify)
- [ ] Ticket creation steps detailed
- [ ] Priority guidelines included
- [ ] Examples provided

**Dependencies:** SCOUT-LINEAR-001, SCOUT-LINEAR-002

---

### SCOUT-DOCS-003: Add Integrations section

**User Story:** As the documentation system, I need an Integrations section so that all external services are documented.

**Technical Specs:**
- File: `AGENTS.md`
- Add: New section documenting each integration

**New Section:**
```markdown
## Integrations

### Minimax LLM
- **Purpose**: Primary language model for all AI tasks
- **Provider**: minimax.io
- **Model**: minimax-m2.7
- **Endpoint**: `https://api.minimax.io/v1`
- **Config**: `openclaw.json` → `agents.defaults.model`
- **Skills**: Used by signal-detector, email classification, calendar parsing

### Linear (Task Management)
- **Purpose**: All tasks tracked in Linear
- **Access**: Via Linear MCP or GraphQL API
- **Project**: Scout Personal Assistant
- **Team**: Semops
- **Config**: API key in push script
- **Workflow**: Linear-first (see Task Management section)

### Notion (Documentation)
- **Purpose**: Daily briefings, research, deliverables database
- **Access**: Via Notion MCP
- **Databases**: Daily Briefing, Research, Deliverables, Knowledge Base
- **Config**: API key in environment
- **Sync**: End-of-day push for briefings

### Gmail (Email)
- **Purpose**: Monitor inbox for urgent emails
- **Access**: Gmail API v1 via OAuth2
- **Config**: `config/secrets.json` → `gmail`
- **Scope**: Read-only (labels, metadata)
- **Sync**: Hourly check via heartbeat

### Google Calendar
- **Purpose**: Track meetings and send reminders
- **Access**: Google Calendar API v3 via OAuth2
- **Config**: `config/secrets.json` → `google_calendar`
- **Scope**: Read/write events
- **Sync**: 15-min reminder before meetings

### WhatsApp
- **Purpose**: Proactive notifications and user communication
- **Access**: whatsapp-web.js (local session)
- **Config**: `~/.openclaw/whatsapp-session/`
- **Setup**: Initial QR code scan required
- **Messages**: Daily briefing, task notifications, reminders
```

**Acceptance Criteria:**
- [ ] Section added to AGENTS.md
- [ ] All 6 integrations documented
- [ ] Purpose, access method, config location for each
- [ ] Setup requirements clear
- [ ] Links to relevant skills/docs

**Dependencies:** SCOUT-EMAIL-002, SCOUT-CAL-002, SCOUT-WA-002, SCOUT-LINEAR-002, SCOUT-NOTION-001

---

### SCOUT-DOCS-004: Update Heartbeats section

**User Story:** As the heartbeat system, I need to update the Heartbeats section so that the new integrations are checked properly.

**Technical Specs:**
- File: `AGENTS.md`
- Section: "Heartbeats"
- Changes: Replace old pipeline checks with new integration checks

**Current Heartbeat Items:**
```markdown
### Heartbeat vs Cron: When to Use Each

**Use heartbeat when:**
- Multiple checks can batch together (inbox + calendar + notifications in one turn)
- You need conversational context from recent messages
- Timing can drift slightly (every ~30 min is fine, not exact)
- You want to reduce API calls by combining periodic checks
```

**Updated Section:**
```markdown
## Heartbeats

### Check Rotation
Rotate through these checks (don't check everything every heartbeat):

1. **Email** (every 2 hours during work hours)
   - Run: `python skills/email-check/check.py --recent 24`
   - Action: Alert if urgent emails found
   - Alert: Send WhatsApp for urgent items

2. **Calendar** (morning heartbeat)
   - Run: `python skills/calendar-check/check.py --hours 48`
   - Action: Include in morning briefing
   - Alert: 15-min reminder before meetings

3. **Linear** (every heartbeat)
   - Run: Check for P0/P1 open tickets
   - Action: Execute highest priority task
   - Update: Move ticket through workflow

4. **WhatsApp** (respond to messages)
   - Monitor: Incoming messages
   - Action: Parse request, create ticket, confirm

### Quiet Hours
- **No proactive alerts**: 11pm - 7am
- **Urgent exceptions**: P0 tickets always alert
- **Timezone**: America/Toronto (UTC-4)

### Morning Briefing (8am)
Send daily summary via WhatsApp:
- Today's meetings
- Urgent emails
- Open tasks
- Have a great day! ☀️
```

**Acceptance Criteria:**
- [ ] Section updated with new rotation
- [ ] Email, Calendar, Linear, WhatsApp checks defined
- [ ] Quiet hours documented
- [ ] Morning briefing time and format specified
- [ ] No references to old job pipeline

**Dependencies:** SCOUT-EMAIL-005, SCOUT-CAL-005, SCOUT-LINEAR-004, SCOUT-WA-007

---

### SCOUT-DOCS-005: Add Communication Style section

**User Story:** As the communication system, I need to document the WhatsApp communication style so that messages are consistent.

**Technical Specs:**
- File: `AGENTS.md`
- Add: New section with formatting rules

**New Section:**
```markdown
## Communication Style

### WhatsApp Format Rules
When sending messages via WhatsApp:

1. **No Markdown Tables**
   - Bad: `| Name | Value |`
   - Good: Use bullet lists
     - Name: John
     - Value: 123

2. **No Headers with #**
   - Bad: `## Section Title`
   - Good: Use **bold** for emphasis

3. **Use Emojis** (sparingly for hierarchy)
   - 📧 Email notifications
   - 📅 Calendar/meetings
   - 📋 Tasks/tickets
   - ⏰ Reminders
   - ✅ Completed tasks
   - 🚨 Urgent issues

4. **Short Lines**
   - WhatsApp width is ~50 chars
   - Break long lines
   - One idea per line

5. **Bullet Lists**
   - Use • for bullets
   - Indent sub-items with spaces

### Message Examples

**Task Complete:**
```
✅ Task Complete

📋 Fix login bug

Completed at: 2:30 PM

You're all caught up! 🎉
```

**Meeting Reminder:**
```
⏰ Meeting in 15 minutes

📅 Sprint Planning
🕐 3:00 PM
📍 Zoom (link in calendar)
```

**Daily Briefing:**
```
☀️ Good Morning!

📅 Today: 3 meetings
   • Sprint Planning @ 9am
   • 1:1 with Manager @ 11am
   • Team Standup @ 2pm

📧 Urgent emails: 1
   Check email skill for details

📋 Open tasks: 5
   (Check Linear for priorities)

Have a great day! 🚀
```

**Urgent Alert:**
```
🚨 Urgent Email

From: recruiter@company.com
Subject: Interview Tomorrow!

Snippet: Hi! Wanted to follow up about 
your interview scheduled for...

Action: Check email immediately
```
```

**Acceptance Criteria:**
- [ ] Section added to AGENTS.md
- [ ] Table rule clearly stated
- [ ] Header/bold rule clearly stated
- [ ] Emoji usage documented
- [ ] Message examples provided
- [ ] Examples match actual output format

**Dependencies:** SCOUT-WA-006

---

### SCOUT-DOCS-006: Archive job search references

**User Story:** As the archivist, I need to remove job search references so that the agent doesn't accidentally fall back to old behaviors.

**Technical Specs:**
- File: `AGENTS.md`
- Remove/Update: All references to scout, analyst, strategist agents
- Add: Deprecation notices where needed

**Changes Required:**
1. Remove from any active workflow diagrams
2. Add deprecation note in Task Management
3. Remove from Memory section if mentioned
4. Update any other references

**Deprecation Notice Template:**
```markdown
> ⚠️ **Deprecated**: The Scout (job discovery), Analyst (job scoring), 
> and Strategist (application generator) agents have been deprecated.
> See [Archive] for reference. All work now follows Linear-first workflow.
```

**Acceptance Criteria:**
- [ ] No active workflow references to old agents
- [ ] Deprecation notice added where appropriate
- [ ] Archive location noted
- [ ] All team members understand old system deprecated
- [ ] Old agent files moved to agents/archived/

**Dependencies:** SCOUT-DEPRECATE-004