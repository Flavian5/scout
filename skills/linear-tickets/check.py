#!/usr/bin/env python3
"""
Linear Tickets Skill
Check and update Linear ticket statuses via GraphQL API
"""
import os
import requests
import json
import argparse
from datetime import datetime

# Configuration
CONFIG_PATH = ".env"
GRAPHQL_URL = "https://api.linear.app/graphql"
DONE_STATE_ID = "39e1f571-b346-48db-9814-d18351bbedfd"
TEAM_ID = "791b6072-2693-4b7d-bb59-873cc116795a"


def load_api_key():
    """Load Linear API key from environment or .env file"""
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        try:
            with open(CONFIG_PATH) as f:
                for line in f:
                    if line.startswith("LINEAR_API_KEY="):
                        api_key = line.split("=", 1)[1].strip()
                        break
        except:
            pass
    return api_key


def get_headers():
    """Get HTTP headers for Linear API"""
    api_key = load_api_key()
    if not api_key:
        print("ERROR: LINEAR_API_KEY not found")
        return None
    return {
        "Authorization": api_key,
        "Content-Type": "application/json"
    }


def run_query(query, variables=None):
    """Execute a GraphQL query"""
    headers = get_headers()
    if not headers:
        return None
    
    response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
    result = response.json()
    if "errors" in result:
        print(f"  GraphQL Error: {result['errors']}")
        return None
    return result.get("data")


def get_state_id(state_name):
    """Get state ID by name"""
    query = """
    query GetStates($teamId: String!) {
        team(id: $teamId) {
            states { nodes { id name type } }
        }
    }
    """
    data = run_query(query, {"teamId": TEAM_ID})
    if not data:
        return None
    for state in data["team"]["states"]["nodes"]:
        if state["name"].lower() == state_name.lower():
            return state["id"]
    return None


def update_issue(issue_id, state_id=None, title=None, description=None):
    """Update a Linear issue"""
    vars_dict = {"id": issue_id}
    
    if state_id:
        vars_dict["stateId"] = state_id
    if title:
        vars_dict["title"] = title
    if description:
        vars_dict["description"] = description
    
    mutation = """
    mutation Update($id: String!, $stateId: String, $title: String, $description: String) {
        issueUpdate(id: $id, input: {stateId: $stateId, title: $title, description: $description}) {
            success
        }
    }
    """
    
    data = run_query(mutation, vars_dict)
    return data and data.get("issueUpdate", {}).get("success")


def get_issue_status(issue_id):
    """Get issue status and details"""
    query = """
    query GetIssue($id: String!) {
        issue(id: $id) {
            identifier
            title
            state { name }
            priority
        }
    }
    """
    data = run_query(query, {"id": issue_id})
    if data and "issue" in data:
        return data["issue"]
    return None


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


# =============================================================================
# Ticket Definitions
# =============================================================================

# Tickets to mark as Done (already implemented)
TICKETS_TO_MARK_DONE = [
    # Discord bot - notifications (SEM-21, SEM-22, SEM-23)
    "14b1f257-7842-46d9-a16b-db4af7713d82",  # SEM-33
    "7ae14729-5c1f-4de2-99b9-b1719aab3af3",  # SEM-34
    "6b0f3616-4e66-4883-8b77-89c68d64d168",  # SEM-35
    "2721c55e-869a-44b6-90d2-61288fa30659",  # SEM-36
    "5e10321b-2bfc-4e4f-89af-0b49b21d733a",  # SEM-37
    "db06d4a3-7344-4ca7-be66-5cc754777b43",  # SEM-38
    "b7af9d0d-cc08-4f9d-bbff-d8a296bfe73a",  # SEM-39
    "1e105d4a-c55f-4fe7-9e57-025e7017c7ef",  # SEM-40
    # Notion integration (SEM-27, SEM-47, SEM-49)
    "8e8f6bb1-54fa-44ab-9202-82aeb1e0423b",  # SEM-27
    "afa4dc02-0c3d-4d3b-a681-6a788a0b20b7",  # SEM-47
    "f5b037ae-017f-4da5-884c-bcea83771773",  # SEM-49
    # Gmail/Email (SEM-50, SEM-52, SEM-53)
    "6d4e8f22-91c3-4e8b-9a5f-7c3d2e1b8a4f",  # SEM-50
    "e9f4c7b2-3d5a-4e8c-9b6f-1a4e8d7c3b5a",  # SEM-52
    "2d5f8e3c-7a4b-4c9d-8e5f-1a3c7b5d9e4f",  # SEM-53
]

# Epic groupings for reference
EPIC_GROUPS = {
    "Epic 4 - WhatsApp/Discord": [
        ("14b1f257-7842-46d9-a16b-db4af7713d82", "SEM-33"),
        ("7ae14729-5c1f-4de2-99b9-b1719aab3af3", "SEM-34"),
        ("6b0f3616-4e66-4883-8b77-89c68d64d168", "SEM-35"),
        ("2721c55e-869a-44b6-90d2-61288fa30659", "SEM-36"),
        ("5e10321b-2bfc-4e4f-89af-0b49b21d733a", "SEM-37"),
        ("db06d4a3-7344-4ca7-be66-5cc754777b43", "SEM-38"),
        ("b7af9d0d-cc08-4f9d-bbff-d8a296bfe73a", "SEM-39"),
        ("1e105d4a-c55f-4fe7-9e57-025e7017c7ef", "SEM-40"),
    ],
    "Epic 5 - Notion": [
        ("8e8f6bb1-54fa-44ab-9202-82aeb1e0423b", "SEM-27"),
        ("e2c00b05-31d5-4d29-9c69-4c9e1e3b6f49", "SEM-28"),
        ("7a3f5c11-82e4-4b91-a8f5-6d2e4a8c3f62", "SEM-29"),
        ("4f9e2d33-81c6-4e3a-b7d5-8e3f2a1c9e4b", "SEM-30"),
        ("afa4dc02-0c3d-4d3b-a681-6a788a0b20b7", "SEM-47"),
    ],
    "Epic 6 - Gmail": [
        ("f5b037ae-017f-4da5-884c-bcea83771773", "SEM-49"),
        ("6d4e8f22-91c3-4e8b-9a5f-7c3d2e1b8a4f", "SEM-50"),
        ("c3a7f5e1-8d4c-4b9a-8f3e-2d5c7b1a4e9f", "SEM-51"),
        ("e9f4c7b2-3d5a-4e8c-9b6f-1a4e8d7c3b5a", "SEM-52"),
        ("2d5f8e3c-7a4b-4c9d-8e5f-1a3c7b5d9e4f", "SEM-53"),
    ],
    "Epic 7 - Calendar": [
        ("4ade8865-0e1e-4955-9e36-b0ac396334f3", "SEM-54"),
        ("a5c4d6be-1616-4005-b137-f3b9b0e0cbc4", "SEM-55"),
        ("4dd0d499-7384-41d2-abf4-c1bebd1e2bc7", "SEM-56"),
    ],
}


# =============================================================================
# Commands
# =============================================================================

def cmd_check(args):
    """Check ticket statuses"""
    print("=== Checking Ticket Statuses ===\n")
    
    for epic, ticket_list in EPIC_GROUPS.items():
        print(f"{epic}:")
        done_count = 0
        for tid, identifier in ticket_list:
            status = get_issue_status(tid)
            if status:
                state = status["state"]["name"]
                marker = "✓" if state == "Done" else " "
                print(f"  [{marker}] {identifier}: {state}")
                if state == "Done":
                    done_count += 1
            else:
                print(f"  [?] {identifier}: Not found")
        print(f"  ({done_count}/{len(ticket_list)} done)\n")
    
    print("=== Check Complete ===")
    return 0


def cmd_mark_done(args):
    """Mark tickets as Done"""
    done_state_id = get_state_id("Done")
    if not done_state_id:
        print("ERROR: Could not get Done state ID")
        return 1
    
    print(f"Done state ID: {done_state_id}")
    
    if args.tickets:
        # Mark specific tickets
        tickets = args.tickets
        print(f"\n=== Marking {len(tickets)} ticket(s) as Done ===")
    else:
        # Mark all pre-defined tickets
        tickets = TICKETS_TO_MARK_DONE
        print(f"\n=== Marking {len(tickets)} ticket(s) as Done ===")
    
    success_count = 0
    for tid in tickets:
        identifier = get_issue_identifier(tid)
        print(f"  {identifier}...", end=" ", flush=True)
        if update_issue(tid, state_id=done_state_id):
            print("✓ Done")
            success_count += 1
        else:
            print("✗ Failed")
    
    print(f"\nMarked {success_count}/{len(tickets)} tickets as Done")
    return 0


def cmd_update(args):
    """Update specific ticket fields"""
    if not args.ticket_id:
        print("ERROR: --id required")
        return 1
    
    tid = args.ticket_id
    
    # Get current identifier
    identifier = get_issue_identifier(tid)
    print(f"Updating {identifier}...")
    
    success = update_issue(
        tid,
        state_id=args.state,
        title=args.title,
        description=args.description
    )
    
    if success:
        print("✓ Updated successfully")
        return 0
    else:
        print("✗ Update failed")
        return 1


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Linear Tickets Skill")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Check command
    check_parser = subparsers.add_parser("check", help="Check ticket statuses")
    
    # Mark done command
    done_parser = subparsers.add_parser("mark-done", help="Mark tickets as Done")
    done_parser.add_argument("--tickets", nargs="+", help="Specific ticket IDs to mark done")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update a ticket")
    update_parser.add_argument("--id", dest="ticket_id", required=True, help="Ticket ID")
    update_parser.add_argument("--state", help="New state ID")
    update_parser.add_argument("--title", help="New title")
    update_parser.add_argument("--description", help="New description")
    
    args = parser.parse_args()
    
    if args.command == "check":
        return cmd_check(args)
    elif args.command == "mark-done":
        return cmd_mark_done(args)
    elif args.command == "update":
        return cmd_update(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    exit(main())