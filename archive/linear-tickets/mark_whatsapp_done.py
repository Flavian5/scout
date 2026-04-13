#!/usr/bin/env python3
"""
Mark Epic 4 (WhatsApp) tickets as Done - Abandoning WhatsApp in favor of Discord
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

def update_issue(issue_id, state_id=None, title=None, description=None):
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

def get_issue_identifier(issue_id):
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
    # Epic 4 (WhatsApp) tickets to mark as Done - switching to Discord
    whatsapp_tickets = [
        ("14b1f257-7842-46d9-a16b-db4af7713d82", "SEM-33"),
        ("7ae14729-5c1f-4de2-99b9-b1719aab3af3", "SEM-34"),
        ("6b0f3616-4e66-4883-8b77-89c68d64d168", "SEM-35"),
        ("2721c55e-869a-44b6-90d2-61288fa30659", "SEM-36"),
        ("5e10321b-2bfc-4e4f-89af-0b49b21d733a", "SEM-37"),
        ("db06d4a3-7344-4ca7-be66-5cc754777b43", "SEM-38"),
        ("b7af9d0d-cc08-4f9d-bbff-d8a296bfe73a", "SEM-39"),
        ("1e105d4a-c55f-4fe7-9e57-025e7017c7ef", "SEM-40"),
    ]
    
    print("=== Marking Epic 4 (WhatsApp) tickets as Done ===")
    print("Switching to Discord for notifications - easier setup, more reliable")
    print()
    success_count = 0
    for tid, identifier in whatsapp_tickets:
        print(f"  {identifier}...", end=" ", flush=True)
        if update_issue(tid, state_id=DONE_STATE_ID):
            print("✓ Done")
            success_count += 1
        else:
            print("✗ Failed")
    
    print(f"\nMarked {success_count}/{len(whatsapp_tickets)} tickets as Done")

if __name__ == "__main__":
    main()