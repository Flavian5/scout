#!/usr/bin/env python3
"""
Update WhatsApp tickets in Linear with MCP approach and clone/setup whatsapp-mcp-server
"""
import os
import requests
import subprocess
import json

LINEAR_API_KEY = os.environ.get('LINEAR_API_KEY')
if not LINEAR_API_KEY:
    with open('.env') as f:
        for line in f:
            if line.startswith('LINEAR_API_KEY='):
                LINEAR_API_KEY = line.split('=', 1)[1].strip()
                break

HEADERS = {'Authorization': LINEAR_API_KEY, 'Content-Type': 'application/json'}
GRAPHQL_URL = 'https://api.linear.app/graphql'
DONE_STATE_ID = "39e1f571-b346-48db-9814-d18351bbedfd"

def run_query(query, variables=None):
    resp = requests.post(GRAPHQL_URL, headers=HEADERS, json={'query': query, 'variables': variables})
    return resp.json()

def get_issue_identifier(issue_id):
    data = run_query("query GetIssue($id: String!) { issue(id: $id) { identifier } }", {"id": issue_id})
    return data.get('data', {}).get('issue', {}).get('identifier', issue_id)

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
    return data.get('data', {}).get('issueUpdate', {}).get('success', False)

# WhatsApp ticket descriptions using MCP approach
WHATSAPP_TICKETS = {
    "SEM-33": {
        "id": None,  # Will be filled from query
        "title": "[scout-WHATSAPP-001] Create whatsapp-mcp skill directory",
        "description": """## User Story

As the Scout system, I need a whatsapp-mcp skill directory so that WhatsApp integration is properly organized.

## Implementation

Use the whatsapp-mcp-server approach with Baileys library:

```bash
git clone https://github.com/ydmw74/whatsapp-mcp-server.git
cd whatsapp-mcp-server
npm install && npm run build
```

Add to `cline_mcp_settings.json`:
```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "node",
      "args": ["/absolute/path/to/whatsapp-mcp-server/dist/index.js"]
    }
  }
}
```

## Acceptance Criteria

- [ ] whatsapp-mcp-server cloned
- [ ] Dependencies installed
- [ ] MCP server configured
- [ ] Initial QR code scan completed"""
    },
    "SEM-34": {
        "id": None,
        "title": "[scout-WHATSAPP-002] Implement WhatsApp Web connection via MCP",
        "description": """## User Story

As the WhatsApp integration, I need to connect to WhatsApp Web via MCP server so that I can send and receive messages.

## Implementation

The whatsapp-mcp-server provides tools:
- `wa_connect` - Connect to WhatsApp
- `wa_disconnect` - Disconnect from WhatsApp  
- `wa_getQR` - Get QR code for initial auth

First run: `node dist/index.js` to scan QR code

## Acceptance Criteria

- [ ] WhatsApp MCP server connects successfully
- [ ] QR code scanned and authenticated
- [ ] Connection persists across restarts"""
    },
    "SEM-35": {
        "id": None,
        "title": "[scout-WHATSAPP-003] Implement incoming message handler",
        "description": """## User Story

As the WhatsApp integration, I need to receive incoming messages via MCP so that I can process user commands.

## Implementation

Use whatsapp-mcp-server tools:
- `wa_listen` - Listen for incoming messages
- Process messages and route to appropriate handlers

## Acceptance Criteria

- [ ] Can receive WhatsApp messages
- [ ] Messages routed correctly
- [ ] Commands parsed properly"""
    },
    "SEM-36": {
        "id": None,
        "title": "[scout-WHATSAPP-004] Implement outgoing message sender",
        "description": """## User Story

As the WhatsApp integration, I need to send messages via MCP so that I can notify users.

## Implementation

Use whatsapp-mcp-server tools:
- `wa_send` - Send message to phone number or group

## Acceptance Criteria

- [ ] Can send text messages
- [ ] Can send to individuals and groups
- [ ] Rate limiting handled"""
    },
    "SEM-37": {
        "id": None,
        "title": "[scout-WHATSAPP-005] Implement session persistence",
        "description": """## User Story

As the WhatsApp integration, I need session persistence so that authentication survives restarts.

## Implementation

The whatsapp-mcp-server handles session persistence automatically using Baileys library's session management.

## Acceptance Criteria

- [ ] Session stored between restarts
- [ ] No need to re-scan QR code on restart
- [ ] Session refresh works correctly"""
    },
    "SEM-38": {
        "id": None,
        "title": "[scout-WHATSAPP-006] Format messages for WhatsApp",
        "description": """## User Story

As the WhatsApp integration, I need to format messages properly so that they display well on mobile.

## Implementation

- Plain text for simple messages
- Use WhatsApp formatting: `*bold*`, `_italic_`, `~strikethrough~`
- Keep messages concise for mobile
- Use bullet lists instead of long paragraphs

## Acceptance Criteria

- [ ] Messages formatted for mobile
- [ ] Bold/italic used appropriately
- [ ] Links preview correctly"""
    },
    "SEM-39": {
        "id": None,
        "title": "[scout-WHATSAPP-007] Send daily morning briefing",
        "description": """## User Story

As the Scout system, I need to send daily briefings via WhatsApp so that the user starts their day informed.

## Implementation

Use heartbeat to send morning briefing:
- Time: 8:00 AM daily
- Content: Calendar, emails, priorities
- Use whatsapp-mcp `wa_send` tool

## Acceptance Criteria

- [ ] Morning briefing sent daily
- [ ] Includes calendar summary
- [ ] Includes email summary
- [ ] Shows top priorities"""
    },
    "SEM-40": {
        "id": None,
        "title": "[scout-WHATSAPP-008] Send task completion notifications",
        "description": """## User Story

As the Scout system, I need to send task notifications via WhatsApp so that the user is kept informed.

## Implementation

Send WhatsApp notifications for:
- Long-running task completion
- Important alerts
- Meeting reminders (15 min before)
- End of day summary

Use whatsapp-mcp `wa_send` tool.

## Acceptance Criteria

- [ ] Task completions notified
- [ ] Meeting reminders sent
- [ ] End of day summary delivered"""
    }
}

def main():
    print("=== Step 1: Query WhatsApp tickets from Linear ===\n")
    
    # Query all issues to find WhatsApp ones
    all_issues = []
    query = """
    query GetIssues {
      issues(first: 100, filter: {team: {id: {eq: "791b6072-2693-4b7d-bb59-873cc116795a"}}}) {
        nodes { id identifier title }
      }
    }
    """
    data = run_query(query)
    if data.get('data'):
        all_issues = data['data']['issues']['nodes']
    
    # Map identifier to id
    id_map = {issue['identifier']: issue['id'] for issue in all_issues}
    
    # Find matching WhatsApp tickets
    whatsapp_ids = {
        "SEM-33", "SEM-34", "SEM-35", "SEM-36", "SEM-37", 
        "SEM-38", "SEM-39", "SEM-40"
    }
    
    print("Found ticket IDs:")
    for sem in whatsapp_ids:
        if sem in id_map:
            print(f"  {sem}: {id_map[sem]}")
            WHATSAPP_TICKETS[sem]["id"] = id_map[sem]
    
    print("\n=== Step 2: Update WhatsApp tickets ===\n")
    
    for sem, info in WHATSAPP_TICKETS.items():
        if info["id"]:
            identifier = get_issue_identifier(info["id"])
            print(f"  Updating {identifier}...", end=" ", flush=True)
            success = update_issue(
                info["id"], 
                title=info["title"], 
                description=info["description"]
            )
            print("✓" if success else "✗")
    
    print("\n=== Step 3: Clone whatsapp-mcp-server ===\n")
    
    mcp_dir = "/Users/haomeng/dev/whatsapp-mcp-server"
    if not os.path.exists(mcp_dir):
        print(f"  Cloning whatsapp-mcp-server...")
        result = subprocess.run(
            ["git", "clone", "https://github.com/ydmw74/whatsapp-mcp-server.git", mcp_dir],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  ✓ Cloned successfully")
        else:
            print(f"  ✗ Clone failed: {result.stderr}")
    else:
        print(f"  ✓ Already exists at {mcp_dir}")
    
    print("\n=== Step 4: Install and build whatsapp-mcp-server ===\n")
    
    if os.path.exists(mcp_dir):
        result = subprocess.run(
            ["npm", "install"],
            cwd=mcp_dir, capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  ✓ npm install succeeded")
        else:
            print(f"  ✗ npm install failed: {result.stderr}")
        
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=mcp_dir, capture_output=True, text=True
        )
        if result.returncode == 0:
            print("  ✓ npm run build succeeded")
        else:
            print(f"  ✗ npm run build failed: {result.stderr}")
    else:
        print("  ✗ Directory not found, skipping build")
    
    print("\n=== Step 5: Add to MCP settings ===\n")
    
    mcp_settings_path = os.path.expanduser("~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json")
    
    if os.path.exists(mcp_settings_path):
        with open(mcp_settings_path) as f:
            settings = json.load(f)
        
        if "mcpServers" not in settings:
            settings["mcpServers"] = {}
        
        settings["mcpServers"]["whatsapp"] = {
            "command": "node",
            "args": [f"{mcp_dir}/dist/index.js"]
        }
        
        with open(mcp_settings_path, 'w') as f:
            json.dump(settings, f, indent=2)
        
        print(f"  ✓ Added whatsapp to {mcp_settings_path}")
    else:
        print(f"  ✗ MCP settings file not found at {mcp_settings_path}")
    
    print("\n=== Update Complete ===")
    print(f"\nWhatsApp MCP server location: {mcp_dir}")
    print(f"To start: cd {mcp_dir} && node dist/index.js")
    print("(First run will show QR code for WhatsApp authentication)")

if __name__ == "__main__":
    main()