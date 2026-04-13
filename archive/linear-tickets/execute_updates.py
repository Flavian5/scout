#!/usr/bin/env python3
"""
Execute bulk updates on Linear tickets via GraphQL API
"""
import os
import requests
import json

LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY")
if not LINEAR_API_KEY:
    try:
        with open(".env") as f:
            for line in f:
                if line.startswith("LINEAR_API_KEY="):
                    LINEAR_API_KEY = line.split("=", 1)[1].strip()
                    break
    except:
        pass

if not LINEAR_API_KEY:
    print("ERROR: LINEAR_API_KEY not found")
    exit(1)

HEADERS = {
    "Authorization": LINEAR_API_KEY,
    "Content-Type": "application/json"
}

GRAPHQL_URL = "https://api.linear.app/graphql"

def run_query(query, variables=None):
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query, "variables": variables})
    result = response.json()
    if "errors" in result:
        print(f"  GraphQL Error: {result['errors']}")
        return None
    return result.get("data")

def get_state_id(state_name):
    query = """
    query GetStates($teamId: String!) {
        team(id: $teamId) {
            states { nodes { id name type } }
        }
    }
    """
    data = run_query(query, {"teamId": "791b6072-2693-4b7d-bb59-873cc116795a"})
    if not data:
        return None
    for state in data["team"]["states"]["nodes"]:
        if state["name"].lower() == state_name.lower():
            return state["id"]
    return None

def update_issue(issue_id, state_id=None, title=None, description=None):
    # Build the input fields and variables dict
    input_fields = []
    vars_dict = {"id": issue_id}
    
    if state_id:
        input_fields.append("stateId: $stateId")
        vars_dict["stateId"] = state_id
    if title:
        input_fields.append("title: $title")
        vars_dict["title"] = title
    if description:
        input_fields.append("description: $description")
        vars_dict["description"] = description
    
    input_str = ", ".join(input_fields) if input_fields else ""
    
    # Declare all variables in mutation signature
    mutation = """
    mutation Update($id: String!, $stateId: String, $title: String, $description: String) {
        issueUpdate(id: $id, input: {stateId: $stateId, title: $title, description: $description}) {
            success
        }
    }
    """
    
    data = run_query(mutation, vars_dict)
    return data and data.get("issueUpdate", {}).get("success")

def get_issue_identifier(issue_id):
    """Get issue identifier from ID"""
    query = """
    query GetIssue($id: String!) {
        issue(id: $id) { identifier }
    }
    """
    data = run_query(query, {"id": issue_id})
    if data and "issue" in data:
        return data["issue"]["identifier"]
    return issue_id

def main():
    done_state_id = get_state_id("Done")
    print(f"Done state ID: {done_state_id}")
    
    # All tickets to mark as Done
    done_tickets = [
        # Epic 1: LLM Migration (5)
        "e3e83dec-9cb2-45d1-9d33-2ff7570c0402",  # SEM-11
        "7fb1978a-6a4e-4a6f-90b7-a4e1c539bb6f",  # SEM-12
        "0c7de259-54d2-4813-af4f-b4f73cbd3538",  # SEM-13
        "63cb008a-3ae4-47d8-b7a7-de6873f3ab0b",  # SEM-14
        "f40e9ed5-46e7-420e-b0b1-f646e694ebb8",  # SEM-15
        "760fc9c5-f394-4533-9012-2852e763693c",  # SEM-7
        "40c83e8c-e7d6-4af5-a31b-907893b80212",  # SEM-6
        "d5db349c-4d7c-4519-8d23-da7418c7fe50",  # SEM-8
        "cbea9ee6-302e-4425-8597-c09f867c4c13",  # SEM-9
        "0550773a-9161-49e6-8966-48e0b5a2e957",  # SEM-10
        # Epic 8: AGENTS.md (9)
        "012e5e3d-f86f-4968-987f-9c827c0aaaf6",  # SEM-41
        "489f6418-dcf4-498d-8732-3b8a0a0a3959",  # SEM-42
        "6827ff63-39e8-43f2-a2b3-e81384bb7b0d",  # SEM-43
        "4ade8865-0e1e-4955-9e36-b0ac396334f3",  # SEM-54
        "a5c4d6be-1616-4005-b137-f3b9b0e0cbc4",  # SEM-55
        "4dd0d499-7384-41d2-abf4-c1bebd1e2bc7",  # SEM-56
        "9cde5ee0-3a01-46f9-83f5-5e9138331303",  # SEM-57
        "309ac514-af33-4ef2-aa47-04d7e0e9dcbe",  # SEM-58
        "0fd5fd3d-1288-4deb-92aa-89ad41d3e9f3",  # SEM-59
    ]
    
    print("\n=== Marking 19 tickets as Done ===")
    success_count = 0
    for tid in done_tickets:
        identifier = get_issue_identifier(tid)
        print(f"  {identifier}...", end=" ", flush=True)
        if update_issue(tid, state_id=done_state_id):
            print("✓ Done")
            success_count += 1
        else:
            print("✗ Failed")
    
    print(f"\nMarked {success_count}/{len(done_tickets)} tickets as Done")
    
    # Fix mislabeled descriptions
    fixes = {
        "8e8f6bb1-54fa-44ab-9202-82aeb1e0423b": {  # SEM-27
            "title": "[scout-CAL-004] Send 15-minute meeting reminder",
            "description": "## User Story\n\nAs the calendar system, I need to send reminders 15 minutes before meetings so users don't miss their events.\n\n## Implementation\n\n1. Fetch upcoming events via Google Calendar API\n2. Calculate time until each event\n3. Send WhatsApp notification for events starting in ~15 minutes\n\n## Acceptance Criteria\n\n- [ ] Check events every 15 minutes\n- [ ] Send reminder 15 min before meeting\n- [ ] Include event title, time, location/link\n- [ ] Don't send duplicate reminders"
        },
        "afa4dc02-0c3d-4d3b-a681-6a788a0b20b7": {  # SEM-47
            "title": "[scout-LINEAR-007] Link Notion deliverables to tickets",
            "description": "## User Story\n\nAs the automation system, I need to link Notion deliverables to Linear tickets so that work is traceable across systems.\n\n## Implementation\n\n1. When creating Notion page for a task, add Linear ticket ID\n2. When updating Linear ticket, sync status to Notion\n3. Include Notion page link in Linear ticket description\n\n## Acceptance Criteria\n\n- [ ] Notion pages include Linear ticket reference\n- [ ] Linear tickets show Notion page link\n- [ ] Status changes sync bidirectionally"
        },
        "f5b037ae-017f-4da5-884c-bcea83771773": {  # SEM-49
            "title": "[scout-NOTION-002] Create Daily Briefing database",
            "description": "## User Story\n\nAs the Notion integration, I need a Daily Briefing database so that end-of-day summaries are organized.\n\n## Database Schema\n\n* Name: Daily Briefing\n* Properties:\n  - Date (date)\n  - Email Summary (text)\n  - Calendar Summary (text)\n  - Tasks Completed (text)\n  - Next Day Priorities (text)\n\n## Implementation\n\nUse Notion MCP to create the database programmatically.\n\n## Acceptance Criteria\n\n- [ ] Daily Briefing database created in Notion\n- [ ] Schema matches above properties\n- [ ] Can be queried by date range"
        },
    }
    
    print("\n=== Fixing 3 mislabeled descriptions ===")
    fix_count = 0
    for tid, data in fixes.items():
        identifier = get_issue_identifier(tid)
        print(f"  {identifier}...", end=" ", flush=True)
        if update_issue(tid, title=data["title"], description=data["description"]):
            print("✓ Fixed")
            fix_count += 1
        else:
            print("✗ Failed")
    
    print(f"\nFixed {fix_count}/{len(fixes)} descriptions")
    print("\n=== Update complete ===")

if __name__ == "__main__":
    main()