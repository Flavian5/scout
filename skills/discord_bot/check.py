#!/usr/bin/env python3
"""
Discord Bot Skill - SEM-45, SEM-47
Parse Discord requests to tickets and link Notion deliverables
"""
import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Configuration
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "secrets.json")
GRAPHQL_URL = "https://api.linear.app/graphql"
TEAM_ID = "791b6072-2693-4b7d-bb59-873cc116795a"


def load_config():
    """Load configuration from secrets file"""
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def load_api_key():
    """Load Linear API key"""
    config = load_config()
    # Try environment first
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        # Try .env file
        try:
            with open(".env") as f:
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
    """Execute GraphQL query"""
    headers = get_headers()
    if not headers:
        return None
    
    import requests
    response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
    result = response.json()
    if "errors" in result:
        print(f"  GraphQL Error: {result['errors']}")
        return None
    return result.get("data")


def get_llm_config():
    """Get LLM config for parsing"""
    config = load_config()
    llm = config.get("llm_api", {})
    return {
        "api_key": llm.get("api_key", os.environ.get("MINIMAX_API_KEY", "")),
        "endpoint": llm.get("endpoint", "https://api.minimax.io/v1/text/chatcompletion_v2"),
        "model": llm.get("model", "MiniMax-M2.7"),
    }


def call_llm(api_key, endpoint, model, messages, temperature=0.3):
    """Call LLM for parsing"""
    import requests
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "top_p": 0.95,
    }
    
    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    result = response.json()
    choices = result.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


# =============================================================================
# Discord Request Parsing (SEM-45)
# =============================================================================

def parse_discord_request(request_text, llm_config):
    """Parse natural language Discord request into ticket details.
    
    Takes a request like "create a ticket for updating my resume" and converts it to:
    - title: Clear, actionable title
    - description: User story with details
    - priority: P1-P4 based on urgency
    - labels: Relevant labels
    """
    prompt = f"""Parse this Discord request into a Linear ticket.

Request: "{request_text}"

Extract and respond with ONLY valid JSON:
{{
    "title": "Clear actionable title (max 60 chars)",
    "description": "User story with context and requirements",
    "priority": 1-4 (1=urgent, 4=none),
    "labels": ["label1", "label2"]
}}

Priority rules:
- P0 (priority 0): Blocking, needs immediate attention
- P1 (priority 1): Important, do soon
- P2 (priority 2): Normal priority  
- P3 (priority 3): Can wait
- P4 (priority 4): Backlog

Respond ONLY with JSON, no markdown or explanation."""

    messages = [{"role": "user", "content": prompt}]
    result = call_llm(
        api_key=llm_config["api_key"],
        endpoint=llm_config["endpoint"],
        model=llm_config["model"],
        messages=messages,
        temperature=0.1
    )
    
    # Extract JSON from response
    import re
    json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
    
    # Fallback parsing
    return {
        "title": request_text[:60],
        "description": f"Request from Discord: {request_text}",
        "priority": 2,
        "labels": ["discord"]
    }


def create_linear_ticket(title, description, priority=2, labels=None):
    """Create a Linear ticket via GraphQL"""
    query = """
    mutation CreateIssue($input: IssueCreateInput!) {
        issueCreate(input: $input) {
            success
            issue {
                id
                identifier
                title
                url
            }
        }
    }
    """
    
    # Build label names (Linear uses label names, not IDs for creation)
    label_names = labels or []
    
    variables = {
        "input": {
            "teamId": TEAM_ID,
            "title": title,
            "description": description,
            "priority": priority,
        }
    }
    
    # Note: Linear API expects labelIds (UUIDs), not labelNames
    # Labels would need to be looked up first to get their IDs
    # For now, create tickets without labels
    
    data = run_query(query, variables)
    if data and data.get("issueCreate", {}).get("success"):
        issue = data["issueCreate"]["issue"]
        return {
            "success": True,
            "identifier": issue["identifier"],
            "id": issue["id"],
            "url": f"https://linear.app/scout/issue/{issue['identifier']}"
        }
    
    return {"success": False}


def send_discord_confirmation(ticket, channel_id):
    """Send ticket creation confirmation to Discord via MCP
    
    NOTE: This function is deprecated. Use MCP tool 'discord_send' instead:
    
    MCP Tool: discord_send
    Args: {
      "channelId": "<channel_id>",
      "message": f"📋 Created Linear ticket **{ticket['identifier']}**\n{ticket.get('url', '')}"
    }
    
    This implementation kept for backwards compatibility with existing scripts.
    """
    # MCP approach (recommended):
    # Use discord_send MCP tool with message:
    # f"📋 Created Linear ticket **{ticket['identifier']}**\n{ticket.get('url', '')}"
    
    # Legacy webhook approach:
    config = load_config()
    webhook_url = config.get("discord_webhook")
    if not webhook_url:
        print("[MCP] Use discord_send with:", f"📋 Created Linear ticket **{ticket['identifier']}**")
        return True
    
    import requests
    embed = {
        "title": f"✅ Ticket Created: {ticket['identifier']}",
        "description": ticket.get("title", "New Ticket"),
        "url": ticket.get("url", ""),
        "color": 3066993,  # Green
        "footer": {"text": "Scout Bot"}
    }
    
    payload = {
        "content": f"📋 Created Linear ticket **{ticket['identifier']}**",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code in (200, 204)
    except Exception as e:
        print(f"Error sending Discord confirmation: {e}")
        return False


# =============================================================================
# Notion Linking (SEM-47)
# =============================================================================

def link_notion_to_ticket(ticket_id, notion_page_url, notion_page_title):
    """Link a Notion page to a Linear ticket description"""
    query = """
    query GetIssue($id: String!) {
        issue(id: $id) {
            identifier
            title
            description
        }
    }
    """
    
    data = run_query(query, {"id": ticket_id})
    if not data or "issue" not in data:
        return False
    
    issue = data["issue"]
    current_desc = issue.get("description", "")
    
    # Append Notion link to description
    notion_link = f"\n\n---\n📎 Notion Deliverable: [{notion_page_title}]({notion_page_url})"
    new_description = current_desc + notion_link if current_desc else f"📎 Notion Deliverable: [{notion_page_title}]({notion_page_url})"
    
    # Update the ticket
    mutation = """
    mutation Update($id: String!, $description: String) {
        issueUpdate(id: $id, input: {description: $description}) {
            success
        }
    }
    """
    
    update_data = run_query(mutation, {"id": ticket_id, "description": new_description})
    return update_data and update_data.get("issueUpdate", {}).get("success", False)


def create_notion_deliverable(database_id, title, ticket_id, ticket_identifier):
    """Create a Notion page linked to a Linear ticket
    
    Creates a page in the specified database with:
    - Title
    - Link back to Linear ticket
    - Status property if exists
    """
    config = load_config()
    notion_token = config.get("notion", {}).get("token")
    
    if not notion_token:
        print("[SYNTHETIC] Notion not configured - would create:")
        print(f"  Database: {database_id}")
        print(f"  Title: {title}")
        print(f"  Linked to: {ticket_identifier}")
        return {
            "success": True,
            "url": f"https://notion.so/{database_id}",
            "synthetic": True
        }
    
    import requests
    
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    properties = {
        "Name": {"title": [{"text": {"content": title}}]},
    }
    
    # Try to add Linear ticket reference
    if ticket_identifier:
        properties["Linear Ticket"] = {"rich_text": [{"text": {"content": ticket_identifier}}]}
    
    payload = {
        "parent": {"database_id": database_id},
        "properties": properties
    }
    
    response = requests.post("https://api.notion.com/v1/pages", headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return {
            "success": True,
            "id": result.get("id"),
            "url": result.get("url")
        }
    else:
        print(f"Notion API error: {response.text}")
        return {"success": False}


# =============================================================================
# Commands
# =============================================================================

def cmd_parse(args):
    """Parse a Discord request into ticket details"""
    if not args.request:
        print("Error: --request required")
        return 1
    
    llm_config = get_llm_config()
    if not llm_config["api_key"]:
        print("ERROR: LLM API key not configured")
        return 1
    
    print(f"Parsing: \"{args.request}\"")
    parsed = parse_discord_request(args.request, llm_config)
    
    print("\nParsed ticket:")
    print(f"  Title: {parsed.get('title', 'N/A')}")
    print(f"  Priority: P{parsed.get('priority', '?')}")
    print(f"  Labels: {', '.join(parsed.get('labels', []))}")
    print(f"  Description: {parsed.get('description', 'N/A')[:100]}...")
    
    # Optionally create the ticket
    if args.create:
        print("\nCreating ticket...")
        result = create_linear_ticket(
            title=parsed["title"],
            description=parsed["description"],
            priority=parsed.get("priority", 2),
            labels=parsed.get("labels")
        )
        
        if result["success"]:
            print(f"✅ Created: {result['identifier']}")
            print(f"   URL: {result['url']}")
            
            # Send Discord confirmation via MCP
            # MCP Tool: discord_send
            # channel_id from config.discord.channel_id
            # message: f"📋 Created Linear ticket **{result['identifier']}**\n{result['url']}"
            channel_id = load_config().get("discord", {}).get("channel_id")
            if channel_id:
                send_discord_confirmation(result, channel_id)
        else:
            print("❌ Failed to create ticket")
            return 1
    
    return 0


def cmd_link(args):
    """Link Notion page to Linear ticket"""
    if not args.ticket_id or not args.notion_url:
        print("Error: --ticket-id and --notion-url required")
        return 1
    
    # Extract page title from URL or use provided
    page_title = args.title or "Linked Deliverable"
    
    success = link_notion_to_ticket(args.ticket_id, args.notion_url, page_title)
    
    if success:
        print(f"✅ Linked Notion page to ticket")
        return 0
    else:
        print("❌ Failed to link Notion page")
        return 1


def cmd_create_deliverable(args):
    """Create Notion deliverable linked to ticket"""
    if not args.title or not args.database:
        print("Error: --title and --database required")
        return 1
    
    ticket_id = args.ticket_id
    ticket_identifier = args.ticket_identifier or "Unknown"
    
    result = create_notion_deliverable(
        database_id=args.database,
        title=args.title,
        ticket_id=ticket_id,
        ticket_identifier=ticket_identifier
    )
    
    if result["success"]:
        if result.get("synthetic"):
            print(f"[SYNTHETIC] Would create deliverable")
        else:
            print(f"✅ Created Notion page: {result['url']}")
            
            # If ticket_id provided, link them
            if ticket_id:
                link_notion_to_ticket(ticket_id, result['url'], args.title)
                print(f"✅ Linked to Linear ticket")
        return 0
    else:
        print("❌ Failed to create Notion deliverable")
        return 1


def main():
    parser = argparse.ArgumentParser(description="Discord Bot Skill - SEM-45, SEM-47")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Parse command (SEM-45)
    parse_parser = subparsers.add_parser("parse", help="Parse Discord request to ticket")
    parse_parser.add_argument("--request", required=True, help="Natural language request")
    parse_parser.add_argument("--create", action="store_true", help="Actually create the ticket")
    
    # Link command (SEM-47)
    link_parser = subparsers.add_parser("link", help="Link Notion page to ticket")
    link_parser.add_argument("--ticket-id", required=True, help="Linear ticket ID")
    link_parser.add_argument("--notion-url", required=True, help="Notion page URL")
    link_parser.add_argument("--title", help="Notion page title")
    
    # Create deliverable command
    deliverable_parser = subparsers.add_parser("create-deliverable", help="Create Notion deliverable")
    deliverable_parser.add_argument("--title", required=True, help="Deliverable title")
    deliverable_parser.add_argument("--database", required=True, help="Notion database ID")
    deliverable_parser.add_argument("--ticket-id", help="Linear ticket ID to link")
    deliverable_parser.add_argument("--ticket-identifier", help="Linear ticket identifier (e.g., SEM-45)")
    
    args = parser.parse_args()
    
    if args.command == "parse":
        return cmd_parse(args)
    elif args.command == "link":
        return cmd_link(args)
    elif args.command == "create-deliverable":
        return cmd_create_deliverable(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    exit(main())