#!/usr/bin/env python3
"""
Mark Epic 3 (Email) tickets as Done
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
    # Epic 3 (Email) tickets to mark as Done
    email_tickets = [
        ("52be9b37-ea09-4efb-b93f-3f907417d0b0", "SEM-16"),
        ("d085841b-be8a-48bd-8e3c-aa87ca13b855", "SEM-17"),
        ("557736c2-7926-4bb5-8aea-e95bdd800903", "SEM-18"),
        ("328cebff-8824-4cd2-b3c9-978e57b50bf4", "SEM-19"),
        ("fc2239a5-01a0-44af-8e50-2632860c51de", "SEM-20"),
    ]
    
    print("=== Marking Epic 3 (Email) tickets as Done ===")
    success_count = 0
    for tid, identifier in email_tickets:
        print(f"  {identifier}...", end=" ", flush=True)
        if update_issue(tid, state_id=DONE_STATE_ID):
            print("✓ Done")
            success_count += 1
        else:
            print("✗ Failed")
    
    print(f"\nMarked {success_count}/{len(email_tickets)} tickets as Done")

if __name__ == "__main__":
    main()