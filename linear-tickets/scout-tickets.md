# Scout Project - Linear Tickets

All tickets prefixed with `scout-` to avoid overlap with other Linear projects.

---

## Epic 1: LLM Infrastructure Migration

**Goal:** Switch all LLM calls from OpenRouter (minimax-m2.5) to direct minimax.io (minimax-m2.7)

### SCOUT-INFRA-001
**Title:** Update openclaw.json model config to minimax m2.7
**Description:** Update `openclaw.json` agents.defaults.model.primary to `minimax/minimax-m2.7` with `minimax.io` base URL. Remove OpenRouter dependency.
**Priority:** P0
**Labels:** infrastructure, llm

### SCOUT-INFRA-002
**Title:** Update signal-detector to use minimax.io client
**Description:** Modify `skills/signal-detector/detect.py` to use `https://api.minimax.io/v1` base URL instead of OpenRouter. Update client initialization.
**Priority:** P0
**Labels:** infrastructure, llm

### SCOUT-INFRA-003
**Title:** Verify minimax.io API key works
**Description:** Test that API key format works with minimax.io endpoint. Confirm successful test call returns valid response.
**Priority:** P0
**Labels:** infrastructure, llm

### SCOUT-INFRA-004
**Title:** Audit skills for OpenRouter references
**Description:** Search all skill files for hardcoded `openrouter.ai` references. Update any remaining references to use minimax.io.
**Priority:** P1
**Labels:** infrastructure, cleanup

### SCOUT-INFRA-005
**Title:** Test signal-detector end-to-end with new model
**Description:** Run a complete job description analysis to verify the new model returns valid JSON signals.
**Priority:** P1
**Labels:** infrastructure, testing

---

## Epic 2: Deprecate Job Application Pipeline

**Goal:** Disable Scout → Analyst → Strategist pipeline while preserving configs for reference

### SCOUT-DEPRECATE-001
**Title:** Disable scout agent
**Description:** Set `scout.enabled: false` in openclaw.json. Agent will no longer run on schedule.
**Priority:** P0
**Labels:** deprecate, job-search

### SCOUT-DEPRECATE-002
**Title:** Disable analyst agent
**Description:** Set `analyst.enabled: false` in openclaw.json. Agent will no longer run on schedule.
**Priority:** P0
**Labels:** deprecate, job-search

### SCOUT-DEPRECATE-003
**Title:** Disable strategist agent
**Description:** Set `strategist.enabled: false` in openclaw.json. Agent will no longer run on schedule.
**Priority:** P0
**Labels:** deprecate, job-search

### SCOUT-DEPRECATE-004
**Title:** Archive old agent configs
**Description:** Add `archived: true` flag to scout, analyst, strategist configs. Preserve for reference but mark as deprecated.
**Priority:** P2
**Labels:** deprecate, cleanup

### SCOUT-DEPRECATE-005
**Title:** Update heartbeat to skip old pipeline
**Description:** Remove references to scout/analyst/strategist from heartbeat workflow. Heartbeat should no longer check job pipeline status.
**Priority:** P1
**Labels:** deprecate, heartbeat

---

## Epic 3: Email Monitoring

**Goal:** Check email during heartbeats and summarize urgent messages

### SCOUT-EMAIL-001
**Title:** Create email-check skill directory
**Description:** Create `skills/email-check/` skill directory with SKILL.md following existing skill patterns.
**Priority:** P1
**Labels:** email, skill

### SCOUT-EMAIL-002
**Title:** Implement Gmail API OAuth2
**Description:** Implement OAuth2 authentication for Gmail API. Handle token exchange and refresh.
**Priority:** P1
**Labels:** email, integration

### SCOUT-EMAIL-003
**Title:** Implement inbox fetch
**Description:** Fetch unread emails from last 24h. Return structured list with sender, subject, snippet.
**Priority:** P1
**Labels:** email, integration

### SCOUT-EMAIL-004
**Title:** Implement urgency classification
**Description:** Use LLM to classify emails as urgent/important/routine based on content and sender.
**Priority:** P2
**Labels:** email, llm

### SCOUT-EMAIL-005
**Title:** Integrate email-check into heartbeat
**Description:** Add email check to heartbeat rotation. Include email summary in heartbeat output.
**Priority:** P1
**Labels:** email, heartbeat

### SCOUT-EMAIL-006
**Title:** Send urgent email alerts via WhatsApp
**Description:** When urgent email detected, send WhatsApp notification to user.
**Priority:** P2
**Labels:** email, whatsapp

### SCOUT-EMAIL-007
**Title:** Create Notion Email Digest database
**Description:** Create Notion database template with fields: date, subject, urgency, summary. Use MCP to create.
**Priority:** P2
**Labels:** email, notion

### SCOUT-EMAIL-008
**Title:** Push daily email digest to Notion
**Description:** At end of day, push email summary to Notion Email Digest database.
**Priority:** P2
**Labels:** email, notion

---

## Epic 4: Google Calendar Integration

**Goal:** Monitor calendar events and alert before meetings

### SCOUT-CAL-001
**Title:** Create calendar-check skill directory
**Description:** Create `skills/calendar-check/` skill directory with SKILL.md following existing skill patterns.
**Priority:** P1
**Labels:** calendar, skill

### SCOUT-CAL-002
**Title:** Implement Google Calendar API OAuth2
**Description:** Implement OAuth2 authentication for Google Calendar API. Handle token exchange and refresh.
**Priority:** P1
**Labels:** calendar, integration

### SCOUT-CAL-003
**Title:** Fetch upcoming events
**Description:** Fetch events for next 24-48h. Return structured list with title, time, location, attendees.
**Priority:** P1
**Labels:** calendar, integration

### SCOUT-CAL-004
**Title:** Send 15-minute meeting reminder
**Description:** Send WhatsApp reminder before each meeting. Alert 15 minutes before start time.
**Priority:** P1
**Labels:** calendar, whatsapp

### SCOUT-CAL-005
**Title:** Integrate calendar-check into heartbeat
**Description:** Add calendar check to heartbeat rotation. Include upcoming events in heartbeat output.
**Priority:** P1
**Labels:** calendar, heartbeat

### SCOUT-CAL-006
**Title:** Handle multiple calendars
**Description:** Support primary and work calendars. Include events from all configured calendars.
**Priority:** P2
**Labels:** calendar, enhancement

### SCOUT-CAL-007
**Title:** Parse natural language event requests
**Description:** From WhatsApp message like "Meeting with Alex tomorrow at 3pm", extract structured event details.
**Priority:** P2
**Labels:** calendar, whatsapp, nlp

### SCOUT-CAL-008
**Title:** Create Google Calendar event
**Description:** Use Google Calendar API to create event from parsed request. Include title, time, attendees.
**Priority:** P2
**Labels:** calendar, integration

### SCOUT-CAL-009
**Title:** Confirm event creation via WhatsApp
**Description:** After successful event creation, send confirmation message to user via WhatsApp.
**Priority:** P2
**Labels:** calendar, whatsapp

---

## Epic 5: WhatsApp Communication

**Goal:** Use WhatsApp as primary communication channel

### SCOUT-WA-001
**Title:** Create whatsapp-bridge skill directory
**Description:** Create `skills/whatsapp-bridge/` skill directory with SKILL.md following existing patterns.
**Priority:** P1
**Labels:** whatsapp, skill

### SCOUT-WA-002
**Title:** Implement WhatsApp Web connection
**Description:** Use whatsapp-web.js or similar to maintain WhatsApp session. Handle authentication.
**Priority:** P0
**Labels:** whatsapp, integration

### SCOUT-WA-003
**Title:** Implement incoming message handler
**Description:** Parse incoming WhatsApp messages and route to assistant logic for processing.
**Priority:** P0
**Labels:** whatsapp, integration

### SCOUT-WA-004
**Title:** Implement outgoing message sender
**Description:** Agent can send text messages via WhatsApp. Queue messages if rate limited.
**Priority:** P0
**Labels:** whatsapp, integration

### SCOUT-WA-005
**Title:** Implement session persistence
**Description:** WhatsApp connection survives process restart. Handle reconnection gracefully.
**Priority:** P1
**Labels:** whatsapp, reliability

### SCOUT-WA-006
**Title:** Format messages for WhatsApp
**Description:** Remove markdown tables, use bullet lists instead. No headers - use **bold** for emphasis.
**Priority:** P1
**Labels:** whatsapp, formatting

### SCOUT-WA-007
**Title:** Send daily morning briefing
**Description:** At configured time, send daily summary via WhatsApp with calendar + email overview.
**Priority:** P2
**Labels:** whatsapp, proactive

### SCOUT-WA-008
**Title:** Send task completion notifications
**Description:** When Linear ticket updated to Done, send WhatsApp notification to user.
**Priority:** P2
**Labels:** whatsapp, linear

---

## Epic 6: Linear Task Management

**Goal:** Track all actionable tasks in Linear with prioritization

### SCOUT-LINEAR-001
**Title:** Create Personal Assistant project in Linear
**Description:** Create new Linear project named "Personal Assistant" with correct team assignment. Prefix all tickets with `scout-`.
**Priority:** P0
**Labels:** linear, project-setup

### SCOUT-LINEAR-002
**Title:** Define Linear labels
**Description:** Create labels: email, calendar, research, admin, urgent. These categorize tickets by domain.
**Priority:** P0
**Labels:** linear, project-setup

### SCOUT-LINEAR-003
**Title:** Define priority levels
**Description:** Document priority criteria: P0 (urgent, immediate), P1 (today), P2 (this week), P3 (backlog).
**Priority:** P0
**Labels:** linear, project-setup

### SCOUT-LINEAR-004
**Title:** Update AGENTS.md with Linear-first workflow
**Description:** Add section documenting that all tasks must create Linear ticket first, then execute from Linear.
**Priority:** P1
**Labels:** linear, docs

### SCOUT-LINEAR-005
**Title:** Implement ticket creation via MCP
**Description:** Use Linear MCP to create tickets programmatically from agent workflow.
**Priority:** P1
**Labels:** linear, integration

### SCOUT-LINEAR-006
**Title:** Implement ticket status updates
**Description:** As work progresses, update ticket status: Todo → In Progress → Done.
**Priority:** P1
**Labels:** linear, integration

### SCOUT-LINEAR-007
**Title:** Implement priority-based execution
**Description:** Heartbeat picks highest priority open ticket (P0 first, then P1, etc.) to execute.
**Priority:** P1
**Labels:** linear, heartbeat

### SCOUT-LINEAR-008
**Title:** Parse WhatsApp requests to tickets
**Description:** When user sends request via WhatsApp, parse into ticket title and description automatically.
**Priority:** P2
**Labels:** linear, whatsapp

### SCOUT-LINEAR-009
**Title:** Auto-assign priority based on keywords
**Description:** Parse request for "urgent", "today", "asap" etc. and assign appropriate priority.
**Priority:** P2
**Labels:** linear, nlp

### SCOUT-LINEAR-010
**Title:** Link Notion deliverables to tickets
**Description:** When work produces Notion page, add link to Linear ticket metadata.
**Priority:** P2
**Labels:** linear, notion

---

## Epic 7: Notion Documentation

**Goal:** Push deliverables, notes, and documentation to Notion

### SCOUT-NOTION-001
**Title:** Define Notion workspace structure
**Description:** Define databases and pages: Daily Briefing, Research, Deliverables, Knowledge Base.
**Priority:** P1
**Labels:** notion, project-setup

### SCOUT-NOTION-002
**Title:** Create Daily Briefing database
**Description:** Create Notion database with fields: date, email_summary, calendar_summary, tasks_completed.
**Priority:** P1
**Labels:** notion, database

### SCOUT-NOTION-003
**Title:** Create Research database
**Description:** Create Notion database with fields: topic, source, summary, date, tags.
**Priority:** P2
**Labels:** notion, database

### SCOUT-NOTION-004
**Title:** Implement Notion page creation via MCP
**Description:** Use Notion MCP to create pages programmatically from agent workflow.
**Priority:** P1
**Labels:** notion, integration

### SCOUT-NOTION-005
**Title:** Push daily briefing to Notion
**Description:** At end of day, push summary with email digest, calendar summary, completed tasks.
**Priority:** P2
**Labels:** notion, heartbeat

### SCOUT-NOTION-006
**Title:** Push research results to Notion
**Description:** When research task completes, output results to Research database.
**Priority:** P2
**Labels:** notion, research

---

## Epic 8: AGENTS.md Rewrite

**Goal:** Update agent instructions for task-driven, Linear-first workflow

### SCOUT-DOCS-001
**Title:** Rewrite Every Session section
**Description:** Update load sequence: SOUL.md, USER.md, memory files, plus Linear/Notion context.
**Priority:** P1
**Labels:** docs, agents

### SCOUT-DOCS-002
**Title:** Add Task Management section
**Description:** Document Linear-first workflow: All tasks → Linear ticket → Execute → Update status → Notify.
**Priority:** P0
**Labels:** docs, agents

### SCOUT-DOCS-003
**Title:** Add Integrations section
**Description:** Document each integration: Email, Calendar, WhatsApp, Linear, Notion. Include setup notes.
**Priority:** P1
**Labels:** docs, agents

### SCOUT-DOCS-004
**Title:** Update Heartbeats section
**Description:** Rotate through: Email, Calendar, Linear, WhatsApp. No more job pipeline references.
**Priority:** P1
**Labels:** docs, heartbeat

### SCOUT-DOCS-005
**Title:** Add Communication Style section
**Description:** Document WhatsApp formatting rules and proactive update guidelines.
**Priority:** P2
**Labels:** docs, whatsapp

### SCOUT-DOCS-006
**Title:** Archive job search references
**Description:** Mark scout/analyst/strategist as deprecated. Remove from active workflow diagrams.
**Priority:** P2
**Labels:** docs, cleanup

---

## Ticket Summary

| Epic | Tickets | P0 | P1 | P2 |
|------|----------|----|----|-----|
| 1. LLM Migration | 5 | 3 | 2 | 0 |
| 2. Deprecate Pipeline | 5 | 3 | 1 | 1 |
| 3. Email | 8 | 0 | 4 | 4 |
| 4. Calendar | 9 | 0 | 5 | 4 |
| 5. WhatsApp | 8 | 2 | 3 | 3 |
| 6. Linear | 10 | 3 | 4 | 3 |
| 7. Notion | 6 | 0 | 3 | 3 |
| 8. AGENTS.md | 6 | 1 | 3 | 2 |
| **Total** | **57** | **12** | **25** | **20** |

## Suggested Execution Order

**Week 1:** Epic 1 (LLM) + Epic 2 (Deprecate) + Epic 8 (Docs)
**Week 2:** Epic 6 (Linear) + Epic 5 (WhatsApp)  
**Week 3:** Epic 3 (Email) + Epic 4 (Calendar)
**Week 4:** Epic 7 (Notion) + Polish

---

*This file created for Linear import. All tickets prefixed with `scout-` to prevent ID overlap with other projects.*