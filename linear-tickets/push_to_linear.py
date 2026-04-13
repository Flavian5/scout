#!/usr/bin/env python3
"""
Push Scout tickets to Linear via API
"""

import json
import subprocess
import time
import os

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY", "")
if not LINEAR_API_KEY:
    print("Error: LINEAR_API_KEY environment variable not set")
    exit(1)
LINEAR_ENDPOINT = "https://api.linear.app/graphql"
PROJECT_ID = "8ccf1d0d-dc13-4b61-9aa2-d8278113e83f"
TEAM_ID = "791b6072-2693-4b7d-bb59-873cc116795a"

# Tickets to create - formatted for Linear GraphQL mutation
TICKETS = [
    # Epic 1: LLM Migration (5 tickets)
    {"title": "[scout-INFRA-001] Update openclaw.json model config to minimax m2.7", "priority": 2, "description": "Update `openclaw.json` agents.defaults.model.primary to `minimax/minimax-m2.7` with `minimax.io` base URL. Remove OpenRouter dependency.", "labels": ["infrastructure", "llm"]},
    {"title": "[scout-INFRA-002] Update signal-detector to use minimax.io client", "priority": 2, "description": "Modify `skills/signal-detector/detect.py` to use `https://api.minimax.io/v1` base URL instead of OpenRouter. Update client initialization.", "labels": ["infrastructure", "llm"]},
    {"title": "[scout-INFRA-003] Verify minimax.io API key works", "priority": 2, "description": "Test that API key format works with minimax.io endpoint. Confirm successful test call returns valid response.", "labels": ["infrastructure", "llm"]},
    {"title": "[scout-INFRA-004] Audit skills for OpenRouter references", "priority": 1, "description": "Search all skill files for hardcoded `openrouter.ai` references. Update any remaining references to use minimax.io.", "labels": ["infrastructure", "cleanup"]},
    {"title": "[scout-INFRA-005] Test signal-detector end-to-end with new model", "priority": 1, "description": "Run a complete job description analysis to verify the new model returns valid JSON signals.", "labels": ["infrastructure", "testing"]},
    
    # Epic 2: Deprecate Pipeline (5 tickets)
    {"title": "[scout-DEPRECATE-001] Disable scout agent", "priority": 2, "description": "Set `scout.enabled: false` in openclaw.json. Agent will no longer run on schedule.", "labels": ["deprecate", "job-search"]},
    {"title": "[scout-DEPRECATE-002] Disable analyst agent", "priority": 2, "description": "Set `analyst.enabled: false` in openclaw.json. Agent will no longer run on schedule.", "labels": ["deprecate", "job-search"]},
    {"title": "[scout-DEPRECATE-003] Disable strategist agent", "priority": 2, "description": "Set `strategist.enabled: false` in openclaw.json. Agent will no longer run on schedule.", "labels": ["deprecate", "job-search"]},
    {"title": "[scout-DEPRECATE-004] Archive old agent configs", "priority": 0, "description": "Add `archived: true` flag to scout, analyst, strategist configs. Preserve for reference but mark as deprecated.", "labels": ["deprecate", "cleanup"]},
    {"title": "[scout-DEPRECATE-005] Update heartbeat to skip old pipeline", "priority": 1, "description": "Remove references to scout/analyst/strategist from heartbeat workflow. Heartbeat should no longer check job pipeline status.", "labels": ["deprecate", "heartbeat"]},
    
    # Epic 3: Email (8 tickets)
    {"title": "[scout-EMAIL-001] Create email-check skill directory", "priority": 1, "description": "Create `skills/email-check/` skill directory with SKILL.md following existing skill patterns.", "labels": ["email", "skill"]},
    {"title": "[scout-EMAIL-002] Implement Gmail API OAuth2", "priority": 1, "description": "Implement OAuth2 authentication for Gmail API. Handle token exchange and refresh.", "labels": ["email", "integration"]},
    {"title": "[scout-EMAIL-003] Implement inbox fetch", "priority": 1, "description": "Fetch unread emails from last 24h. Return structured list with sender, subject, snippet.", "labels": ["email", "integration"]},
    {"title": "[scout-EMAIL-004] Implement urgency classification", "priority": 0, "description": "Use LLM to classify emails as urgent/important/routine based on content and sender.", "labels": ["email", "llm"]},
    {"title": "[scout-EMAIL-005] Integrate email-check into heartbeat", "priority": 1, "description": "Add email check to heartbeat rotation. Include email summary in heartbeat output.", "labels": ["email", "heartbeat"]},
    {"title": "[scout-EMAIL-006] Send urgent email alerts via WhatsApp", "priority": 0, "description": "When urgent email detected, send WhatsApp notification to user.", "labels": ["email", "whatsapp"]},
    {"title": "[scout-EMAIL-007] Create Notion Email Digest database", "priority": 0, "description": "Create Notion database template with fields: date, subject, urgency, summary. Use MCP to create.", "labels": ["email", "notion"]},
    {"title": "[scout-EMAIL-008] Push daily email digest to Notion", "priority": 0, "description": "At end of day, push email summary to Notion Email Digest database.", "labels": ["email", "notion"]},
    
    # Epic 4: Calendar (9 tickets)
    {"title": "[scout-CAL-001] Create calendar-check skill directory", "priority": 1, "description": "Create `skills/calendar-check/` skill directory with SKILL.md following existing skill patterns.", "labels": ["calendar", "skill"]},
    {"title": "[scout-CAL-002] Implement Google Calendar API OAuth2", "priority": 1, "description": "Implement OAuth2 authentication for Google Calendar API. Handle token exchange and refresh.", "labels": ["calendar", "integration"]},
    {"title": "[scout-CAL-003] Fetch upcoming events", "priority": 1, "description": "Fetch events for next 24-48h. Return structured list with title, time, location, attendees.", "labels": ["calendar", "integration"]},
    {"title": "[scout-CAL-004] Send 15-minute meeting reminder", "priority": 1, "description": "Send WhatsApp reminder before each meeting. Alert 15 minutes before start time.", "labels": ["calendar", "whatsapp"]},
    {"title": "[scout-CAL-005] Integrate calendar-check into heartbeat", "priority": 1, "description": "Add calendar check to heartbeat rotation. Include upcoming events in heartbeat output.", "labels": ["calendar", "heartbeat"]},
    {"title": "[scout-CAL-006] Handle multiple calendars", "priority": 0, "description": "Support primary and work calendars. Include events from all configured calendars.", "labels": ["calendar", "enhancement"]},
    {"title": "[scout-CAL-007] Parse natural language event requests", "priority": 0, "description": "From WhatsApp message like 'Meeting with Alex tomorrow at 3pm', extract structured event details.", "labels": ["calendar", "whatsapp", "nlp"]},
    {"title": "[scout-CAL-008] Create Google Calendar event", "priority": 0, "description": "Use Google Calendar API to create event from parsed request. Include title, time, attendees.", "labels": ["calendar", "integration"]},
    {"title": "[scout-CAL-009] Confirm event creation via WhatsApp", "priority": 0, "description": "After successful event creation, send confirmation message to user via WhatsApp.", "labels": ["calendar", "whatsapp"]},
    
    # Epic 5: WhatsApp (8 tickets)
    {"title": "[scout-WA-001] Create whatsapp-bridge skill directory", "priority": 1, "description": "Create `skills/whatsapp-bridge/` skill directory with SKILL.md following existing patterns.", "labels": ["whatsapp", "skill"]},
    {"title": "[scout-WA-002] Implement WhatsApp Web connection", "priority": 2, "description": "Use whatsapp-web.js or similar to maintain WhatsApp session. Handle authentication.", "labels": ["whatsapp", "integration"]},
    {"title": "[scout-WA-003] Implement incoming message handler", "priority": 2, "description": "Parse incoming WhatsApp messages and route to assistant logic for processing.", "labels": ["whatsapp", "integration"]},
    {"title": "[scout-WA-004] Implement outgoing message sender", "priority": 2, "description": "Agent can send text messages via WhatsApp. Queue messages if rate limited.", "labels": ["whatsapp", "integration"]},
    {"title": "[scout-WA-005] Implement session persistence", "priority": 1, "description": "WhatsApp connection survives process restart. Handle reconnection gracefully.", "labels": ["whatsapp", "reliability"]},
    {"title": "[scout-WA-006] Format messages for WhatsApp", "priority": 1, "description": "Remove markdown tables, use bullet lists instead. No headers - use **bold** for emphasis.", "labels": ["whatsapp", "formatting"]},
    {"title": "[scout-WA-007] Send daily morning briefing", "priority": 0, "description": "At configured time, send daily summary via WhatsApp with calendar + email overview.", "labels": ["whatsapp", "proactive"]},
    {"title": "[scout-WA-008] Send task completion notifications", "priority": 0, "description": "When Linear ticket updated to Done, send WhatsApp notification to user.", "labels": ["whatsapp", "linear"]},
    
    # Epic 6: Linear (10 tickets)
    {"title": "[scout-LINEAR-001] Update AGENTS.md with Linear-first workflow", "priority": 1, "description": "Add section documenting that all tasks must create Linear ticket first, then execute from Linear.", "labels": ["linear", "docs"]},
    {"title": "[scout-LINEAR-002] Implement ticket creation via MCP", "priority": 1, "description": "Use Linear MCP to create tickets programmatically from agent workflow.", "labels": ["linear", "integration"]},
    {"title": "[scout-LINEAR-003] Implement ticket status updates", "priority": 1, "description": "As work progresses, update ticket status: Todo → In Progress → Done.", "labels": ["linear", "integration"]},
    {"title": "[scout-LINEAR-004] Implement priority-based execution", "priority": 1, "description": "Heartbeat picks highest priority open ticket (P0 first, then P1, etc.) to execute.", "labels": ["linear", "heartbeat"]},
    {"title": "[scout-LINEAR-005] Parse WhatsApp requests to tickets", "priority": 0, "description": "When user sends request via WhatsApp, parse into ticket title and description automatically.", "labels": ["linear", "whatsapp"]},
    {"title": "[scout-LINEAR-006] Auto-assign priority based on keywords", "priority": 0, "description": "Parse request for 'urgent', 'today', 'asap' etc. and assign appropriate priority.", "labels": ["linear", "nlp"]},
    {"title": "[scout-LINEAR-007] Link Notion deliverables to tickets", "priority": 0, "description": "When work produces Notion page, add link to Linear ticket metadata.", "labels": ["linear", "notion"]},
    
    # Epic 7: Notion (6 tickets)
    {"title": "[scout-NOTION-001] Define Notion workspace structure", "priority": 1, "description": "Define databases and pages: Daily Briefing, Research, Deliverables, Knowledge Base.", "labels": ["notion", "project-setup"]},
    {"title": "[scout-NOTION-002] Create Daily Briefing database", "priority": 1, "description": "Create Notion database with fields: date, email_summary, calendar_summary, tasks_completed.", "labels": ["notion", "database"]},
    {"title": "[scout-NOTION-003] Create Research database", "priority": 0, "description": "Create Notion database with fields: topic, source, summary, date, tags.", "labels": ["notion", "database"]},
    {"title": "[scout-NOTION-004] Implement Notion page creation via MCP", "priority": 1, "description": "Use Notion MCP to create pages programmatically from agent workflow.", "labels": ["notion", "integration"]},
    {"title": "[scout-NOTION-005] Push daily briefing to Notion", "priority": 0, "description": "At end of day, push summary with email digest, calendar summary, completed tasks.", "labels": ["notion", "heartbeat"]},
    {"title": "[scout-NOTION-006] Push research results to Notion", "priority": 0, "description": "When research task completes, output results to Research database.", "labels": ["notion", "research"]},
    
    # Epic 8: AGENTS.md Rewrite (6 tickets)
    {"title": "[scout-DOCS-001] Rewrite Every Session section", "priority": 1, "description": "Update load sequence: SOUL.md, USER.md, memory files, plus Linear/Notion context.", "labels": ["docs", "agents"]},
    {"title": "[scout-DOCS-002] Add Task Management section", "priority": 2, "description": "Document Linear-first workflow: All tasks → Linear ticket → Execute → Update status → Notify.", "labels": ["docs", "agents"]},
    {"title": "[scout-DOCS-003] Add Integrations section", "priority": 1, "description": "Document each integration: Email, Calendar, WhatsApp, Linear, Notion. Include setup notes.", "labels": ["docs", "agents"]},
    {"title": "[scout-DOCS-004] Update Heartbeats section", "priority": 1, "description": "Rotate through: Email, Calendar, Linear, WhatsApp. No more job pipeline references.", "labels": ["docs", "heartbeat"]},
    {"title": "[scout-DOCS-005] Add Communication Style section", "priority": 0, "description": "Document WhatsApp formatting rules and proactive update guidelines.", "labels": ["docs", "whatsapp"]},
    {"title": "[scout-DOCS-006] Archive job search references", "priority": 0, "description": "Mark scout/analyst/strategist as deprecated. Remove from active workflow diagrams.", "labels": ["docs", "cleanup"]},
]

def run_query(query, variables=None):
    """Execute GraphQL query via curl"""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    cmd = [
        "curl", "-s", "-X", "POST", LINEAR_ENDPOINT,
        "-H", f"Authorization: {LINEAR_API_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return json.loads(result.stdout)

def create_issue(title, description, priority, labels=None):
    """Create a single issue in Linear"""
    query = """
    mutation CreateIssue($title: String!, $description: String!, $priority: Int!, $projectId: String!) {
        issueCreate(input: {
            title: $title,
            description: $description,
            priority: $priority,
            projectId: $projectId
        }) {
            issue {
                identifier
                title
            }
        }
    }
    """
    
    variables = {
        "title": title,
        "description": description,
        "priority": priority,
        "projectId": PROJECT_ID
    }
    
    result = run_query(query, variables)
    
    if "errors" in result:
        return {"success": False, "error": result["errors"][0]["message"]}
    
    return {"success": True, "identifier": result["data"]["issueCreate"]["issue"]["identifier"]}

def main():
    print(f"Creating {len(TICKETS)} tickets in Linear...")
    print(f"Project ID: {PROJECT_ID}")
    print("-" * 50)
    
    created = []
    failed = []
    
    for i, ticket in enumerate(TICKETS):
        print(f"[{i+1}/{len(TICKETS)}] Creating: {ticket['title'][:60]}...")
        
        result = create_issue(
            title=ticket["title"],
            description=ticket["description"],
            priority=ticket["priority"],
            labels=ticket.get("labels", [])
        )
        
        if result["success"]:
            created.append(result["identifier"])
            print(f"  ✓ {result['identifier']}")
        else:
            failed.append({"title": ticket["title"], "error": result["error"]})
            print(f"  ✗ {result['error']}")
        
        # Rate limit
        time.sleep(0.2)
    
    print("-" * 50)
    print(f"\nResults: {len(created)} created, {len(failed)} failed")
    
    if failed:
        print("\nFailed tickets:")
        for f in failed:
            print(f"  - {f['title']}: {f['error']}")
