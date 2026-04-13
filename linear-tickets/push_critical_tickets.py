#!/usr/bin/env python3
"""Push expanded descriptions to critical tickets."""

import requests
import os
import time

API_KEY = os.environ.get("LINEAR_API_KEY", "")
if not API_KEY:
    print("Error: LINEAR_API_KEY not set")
    exit(1)

ENDPOINT = "https://api.linear.app/graphql"
HEADERS = {"Authorization": API_KEY, "Content-Type": "application/json"}

# Ticket descriptions - using simple strings
DESCS = [
    ("SEM-8", "d5db349c-4d7c-4519-8d23-da7418c7fe50", """## User Story
As the integration system, I need to verify the minimax.io API credentials are valid so that LLM calls succeed without authentication errors.

## Test Command
```bash
curl -s -X POST "https://api.minimax.io/v1/chat/completions" \\
  -H "Authorization: Bearer $MINIMAX_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"minimax/m2.7","messages":[{"role":"user","content":"say hello"}],"max_tokens":10}'
```

## Expected Response
```json
{"id":"cmpl-xxxxx","choices":[{"message":{"content":"Hello"}}]}
```

## Error Codes
- 401 Unauthorized → Invalid API key
- 403 Forbidden → Key doesn't have access
- 429 Too Many Requests → Rate limited

## Acceptance Criteria
- [ ] Run simple completion test
- [ ] Verify response contains valid JSON
- [ ] Document key format and rate limits"""),

    ("SEM-9", "cbea9ee6-302e-4425-8597-c09f867c4c13", """## User Story
As the code auditor, I need to find all OpenRouter references across the codebase so that we can migrate everything to minimax.io.

## Search Command
```bash
grep -rn "openrouter" --include="*.py" --include="*.json" .
```

## Files to Check
| File | What to Look For |
|------|-----------------|
| skills/signal-detector/detect.py | base_url |
| skills/asset-generator/generate.py | LLM client |
| openclaw.json | model.primary |

## Replacement Map
| Old | New |
|-----|-----|
| https://openrouter.ai/api/v1 | https://api.minimax.io/v1 |
| openrouter/minimax/ | minimax/ |

## Acceptance Criteria
- [ ] Run grep for openrouter
- [ ] Update each file found
- [ ] Test each changed file works"""),

    ("SEM-12", "7fb1978a-6a4e-4a6f-90b7-a4e1c539bb6f", """## User Story
As the system owner, I want to disable the Analyst agent so that job scoring doesn't run on schedule anymore.

## Target State (openclaw.json)
```json
"analyst": {
  "enabled": false,
  "archived": true,
  "reason": "Deprecated - Personal Assistant focus",
  "schedule": null
}
```

## Acceptance Criteria
- [ ] analyst.enabled is false
- [ ] agent does NOT run on cron
- [ ] JSON validates"""),

    ("SEM-13", "0c7de259-54d2-4813-af4f-b4f73cbd3538", """## User Story
As the system owner, I want to disable the Strategist agent so that application package generation doesn't run on schedule anymore.

## Target State (openclaw.json)
```json
"strategist": {
  "enabled": false,
  "archived": true,
  "reason": "Deprecated - Personal Assistant focus",
  "schedule": null
}
```

## Acceptance Criteria
- [ ] strategist.enabled is false
- [ ] agent does NOT run on cron"""),

    ("SEM-14", "63cb008a-3ae4-47d8-b7a7-de6873f3ab0b", """## User Story
As the system archivist, I want to preserve the old agent configurations for reference while marking them as deprecated.

## Implementation
```bash
mkdir -p agents/archived
mv agents/scout.md agents/archived/
mv agents/analyst.md agents/archived/
mv agents/strategist.md agents/archived/
```

Create agents/archived/README.md explaining deprecation.

## Acceptance Criteria
- [ ] agents/archived/ directory created
- [ ] All three agent files moved
- [ ] README.md explains deprecation"""),

    ("SEM-15", "f40e9ed5-46e7-420e-b0b1-f646e694ebb8", """## User Story
As the heartbeat system, I need to remove references to the old job pipeline.

## Target Heartbeat Flow
1. Check Linear for P0/P1 tickets
2. Check Notion for recent activity
3. Check Email for urgent messages
4. Check Calendar for upcoming events

## Implementation
1. Open HEARTBEAT.md
2. Remove scout/analyst/strategist references
3. Add new integration checks

## Acceptance Criteria
- [ ] No references to old pipeline
- [ ] New checks for Linear, Notion, Email, Calendar
- [ ] Heartbeat runs without errors"""),

    ("SEM-17", "d085841b-be8a-48bd-8e3c-aa87ca13b855", """## User Story
As the authentication system, I need Gmail API OAuth2 so that the email skill can securely access inbox data.

## Setup Steps
1. Google Cloud Console → Enable Gmail API
2. Create OAuth2 credentials (Desktop app)
3. Download client_id and client_secret

## Required Scopes
- https://www.googleapis.com/auth/gmail.readonly
- https://www.googleapis.com/auth/gmail.modify

## Code Example
```python
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
```

## Acceptance Criteria
- [ ] OAuth2 flow implemented
- [ ] Can list messages
- [ ] Token refresh works"""),

    ("SEM-26", "8e8f6bb1-54fa-44ab-9202-82aeb1e0423b", """## User Story
As the authentication system, I need Google Calendar API OAuth2 so that the calendar skill can securely access calendar data.

## Setup Steps
1. Google Cloud Console → Enable Google Calendar API
2. Create OAuth2 credentials (can share with Gmail)
3. Implement token flow

## Required Scopes
- https://www.googleapis.com/auth/calendar.readonly
- https://www.googleapis.com/auth/calendar.events

## Code Example
```python
from google_auth_oauthlib.flow import InstalledAppFlow
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)
from googleapiclient.discovery import build
service = build('calendar', 'v3', credentials=creds)
```

## Acceptance Criteria
- [ ] OAuth2 flow implemented
- [ ] Can list calendars
- [ ] Token refresh works"""),

    ("SEM-35", "afa4dc02-0c3d-4d3b-a681-6a788a0b20b7", """## User Story
As the WhatsApp system, I need to connect to WhatsApp Web so that I can send and receive messages.

## Setup
```bash
cd /Users/haomeng/dev/scout
npm install whatsapp-web.js puppeteer
```

## Basic Connection
```javascript
const { Client, LocalAuth } = require('whatsapp-web.js');
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: '.openclaw/whatsapp-session' }),
    puppeteer: { headless: true, args: ['--no-sandbox'] }
});
client.on('qr', (qr) => console.log('Scan:', qr));
client.on('ready', () => console.log('WhatsApp connected!'));
client.initialize();
```

## Directory Structure
skills/whatsapp-bridge/
├── bridge.js
├── package.json
└── .session/ (gitignored)

## Acceptance Criteria
- [ ] WhatsApp session established
- [ ] QR scan only once
- [ ] Session persists
- [ ] Can send/receive"""),

    ("SEM-43", "6827ff63-39e8-43f2-a2b3-e81384bb7b0d", """## User Story
As the automation system, I need to create Linear tickets programmatically via MCP.

## MCP Setup
```bash
npx -y @touchlab/linear-mcp-integration
```

## Available MCP Tools
- linear_create_issue - Create single issue
- linear_create_issues - Create multiple
- linear_search_issues - Search
- linear_update_issue - Update properties

## GraphQL Alternative
```python
import requests
def create_ticket(title, description, priority=2):
    query = 'mutation { issueCreate(input: {title: "$title", description: "$desc", priority: $priority, teamId: "791b6072-2693-4b7d-bb59-873cc116795a", projectId: "8ccf1d0d-dc13-4b61-9aa2-d8278113e83f"}) { issue { id } } }'
    return requests.post("https://api.linear.app/graphql", headers={"Authorization": os.environ["LINEAR_API_KEY"]}, json={"query": query})
```

## Acceptance Criteria
- [ ] MCP server configured
- [ ] Can create tickets
- [ ] Returns ticket ID"""),
]

def update_ticket(ticket_id, description):
    query = "mutation UpdateIssue($id: String!, $description: String!) { issueUpdate(id: $id, input: { description: $description }) { success } }"
    response = requests.post(ENDPOINT, headers=HEADERS, json={"query": query, "variables": {"id": ticket_id, "description": description}})
    result = response.json()
    return result.get("data", {}).get("issueUpdate", {}).get("success", False)

def main():
    print("Pushing critical ticket descriptions to Linear...")
    print("=" * 60)
    success = failed = 0
    for identifier, ticket_id, description in DESCS:
        print(f"Updating {identifier}...", end=" ", flush=True)
        if update_ticket(ticket_id, description):
            print("OK")
            success += 1
        else:
            print("FAIL")
            failed += 1
        time.sleep(0.3)
    print("=" * 60)
    print(f"Done! {success} updated, {failed} failed")

if __name__ == "__main__":
    main()