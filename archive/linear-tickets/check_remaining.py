#!/usr/bin/env python3
"""
Check remaining Linear tickets status
"""
import os
import requests

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
DONE_STATE_ID = "39e1f571-b346-48db-9814-d18351bbedfd"

def run_query(query, variables=None):
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query, "variables": variables})
    result = response.json()
    if "errors" in result:
        print(f"  GraphQL Error: {result['errors']}")
        return None
    return result.get("data")

def get_ticket_status(issue_id):
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

def main():
    # All tickets to check (grouped by epic)
    tickets = {
        "Epic 4 - WhatsApp (8)": [
            ("14b1f257-7842-46d9-a16b-db4af7713d82", "SEM-33"),
            ("7ae14729-5c1f-4de2-99b9-b1719aab3af3", "SEM-34"),
            ("6b0f3616-4e66-4883-8b77-89c68d64d168", "SEM-35"),
            ("2721c55e-869a-44b6-90d2-61288fa30659", "SEM-36"),
            ("5e10321b-2bfc-4e4f-89af-0b49b21d733a", "SEM-37"),
            ("db06d4a3-7344-4ca7-be66-5cc754777b43", "SEM-38"),
            ("b7af9d0d-cc08-4f9d-bbff-d8a296bfe73a", "SEM-39"),
            ("1e105d4a-c55f-4fe7-9e57-025e7017c7ef", "SEM-40"),
        ],
        "Epic 5 - Notion (5)": [
            ("8e8f6bb1-54fa-44ab-9202-82aeb1e0423b", "SEM-27"),
            ("e2c00b05-31d5-4d29-9c69-4c9e1e3b6f49", "SEM-28"),
            ("7a3f5c11-82e4-4b91-a8f5-6d2e4a8c3f62", "SEM-29"),
            ("4f9e2d33-81c6-4e3a-b7d5-8e3f2a1c9e4b", "SEM-30"),
            ("afa4dc02-0c3d-4d3b-a681-6a788a0b20b7", "SEM-47"),
        ],
        "Epic 6 - Gmail (5)": [
            ("f5b037ae-017f-4da5-884c-bcea83771773", "SEM-49"),
            ("6d4e8f22-91c3-4e8b-9a5f-7c3d2e1b8a4f", "SEM-50"),
            ("c3a7f5e1-8d4c-4b9a-8f3e-2d5c7b1a4e9f", "SEM-51"),
            ("e9f4c7b2-3d5a-4e8c-9b6f-1a4e8d7c3b5a", "SEM-52"),
            ("2d5f8e3c-7a4b-4c9d-8e5f-1a3c7b5d9e4f", "SEM-53"),
        ],
        "Epic 7 - Calendar (3)": [
            ("4ade8865-0e1e-4955-9e36-b0ac396334f3", "SEM-54"),
            ("a5c4d6be-1616-4005-b137-f3b9b0e0cbc4", "SEM-55"),
            ("4dd0d499-7384-41d2-abf4-c1bebd1e2bc7", "SEM-56"),
        ],
        "Epic 8 - AGENTS.md (9)": [
            ("9cde5ee0-3a01-46f9-83f5-5e9138331303", "SEM-57"),
            ("309ac514-af33-4ef2-aa47-04d7e0e9dcbe", "SEM-58"),
            ("0fd5fd3d-1288-4deb-92aa-89ad41d3e9f3", "SEM-59"),
        ],
        "Epic 9 - Documentation (9)": [
            ("3f8d5c21-a7e4-4c8b-9d5e-2f6a4b8c3d7e", "SEM-60"),
            ("9b4e7f32-c8d5-4e9a-8f4b-3c7a5d2e1f8b", "SEM-61"),
        ],
    }
    
    print("=== Checking Remaining Tickets Status ===\n")
    
    for epic, ticket_list in tickets.items():
        print(f"{epic}:")
        done_count = 0
        for tid, identifier in ticket_list:
            status = get_ticket_status(tid)
            if status:
                state = status["state"]["name"]
                if state == "Done":
                    print(f"  {identifier}: ✓ {state}")
                    done_count += 1
                else:
                    print(f"  {identifier}: {state}")
            else:
                print(f"  {identifier}: Not found")
        print(f"  ({done_count}/{len(ticket_list)} done)\n")
    
    print("=== Summary ===")
    total_tickets = sum(len(t) for t in tickets.values())
    print(f"Total remaining tickets to process: {total_tickets}")

if __name__ == "__main__":
    main()