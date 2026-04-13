#!/usr/bin/env python3
"""Push expanded ticket descriptions to Linear."""

import requests
import json
import time

import os
API_KEY = os.environ.get("LINEAR_API_KEY", "")
if not API_KEY:
    print("Error: LINEAR_API_KEY environment variable not set")
    exit(1)
ENDPOINT = "https://api.linear.app/graphql"

HEADERS = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

# Ticket ID mapping (identifier -> id)
TICKET_IDS = {
    "SEM-6": "40c83e8c-e7d6-4af5-a31b-907893b80212",
    "SEM-7": "760fc9c5-f394-4533-9012-2852e763693c",
    "SEM-8": "d5db349c-4d7c-4519-8d23-da7418c7fe50",
    "SEM-9": "cbea9ee6-302e-4425-8597-c09f867c4c13",
    "SEM-10": "0550773a-9161-49e6-8966-48e0b5a2e957",
    "SEM-11": "e3e83dec-9cb2-45d1-9d33-2ff7570c0402",
    "SEM-12": "7fb1978a-6a4e-4a6f-90b7-a4e1c539bb6f",
    "SEM-13": "0c7de259-54d2-4813-af4f-b4f73cbd3538",
    "SEM-14": "63cb008a-3ae4-47d8-b7a7-de6873f3ab0b",
    "SEM-15": "f40e9ed5-46e7-420e-b0b1-f646e694ebb8",
    "SEM-16": "52be9b37-ea09-4efb-b93f-3f907417d0b0",
    "SEM-17": "d085841b-be8a-48bd-8e3c-aa87ca13b855",
    "SEM-18": "557736c2-7926-4bb5-8aea-e95bdd800903",
    "SEM-19": "328cebff-8824-4cd2-b3c9-978e57b50bf4",
    "SEM-20": "fc2239a5-01a0-44af-8e50-2632860c51de",
    "SEM-21": "30fa6ab2-1031-490e-b4a9-3ce70443c0a3",
    "SEM-22": "f9c606c1-f4ff-4003-95d0-74a92eba730f",
    "SEM-23": "4654f502-ad4f-416b-91a4-6bbc9517d941",
    "SEM-24": "ab119ab3-550e-4fbb-985f-874a17dc4a6a",
    "SEM-25": "9cb0771e-5b9c-4f07-95b0-bb227965f068",
    "SEM-26": "13883c6f-2d1e-492a-941c-ae37b571e08f",
    "SEM-27": "8e8f6bb1-54fa-44ab-9202-82aeb1e0423b",
    "SEM-28": "c1e735ef-bfaa-4a15-9b05-fbd0b2b860d9",
    "SEM-29": "5ad6c4a0-342f-421c-8c19-1b150f94426e",
    "SEM-30": "e5e31346-bc28-411a-9ffb-c3fe83b89442",
    "SEM-31": "fb4743d1-4c9f-4d8c-bfaa-6d3c6f657e25",
    "SEM-32": "7070c1e3-19e4-4efd-8841-fd00b3fd9dea",
    "SEM-33": "14b1f257-7842-46d9-a16b-db4af7713d82",
    "SEM-34": "7ae14729-5c1f-4de2-99b9-b1719aab3af3",
    "SEM-35": "6b0f3616-4e66-4883-8b77-89c68d64d168",
    "SEM-36": "2721c55e-869a-44b6-90d2-61288fa30659",
    "SEM-37": "5e10321b-2bfc-4e4f-89af-0b49b21d733a",
    "SEM-38": "db06d4a3-7344-4ca7-be66-5cc754777b43",
    "SEM-39": "b7af9d0d-cc08-4f9d-bbff-d8a296bfe73a",
    "SEM-40": "1e105d4a-c55f-4fe7-9e57-025e7017c7ef",
    "SEM-41": "012e5e3d-f86f-4968-987f-9c827c0aaaf6",
    "SEM-42": "489f6418-dcf4-498d-8732-3b8a0a0a3959",
    "SEM-43": "6827ff63-39e8-43f2-a2b3-e81384bb7b0d",
    "SEM-44": "8a537fe9-f11b-4ee2-86a0-076c081fbd87",
    "SEM-45": "f3009239-e16f-4e5f-9292-2fea47df1301",
    "SEM-46": "53e8ca0d-31b8-4354-9c68-a41246d1e8ed",
    "SEM-47": "afa4dc02-0c3d-4d3b-a681-6a788a0b20b7",
    "SEM-48": "ce0fed8a-508f-48f0-b67d-d5370d560175",
    "SEM-49": "f5b037ae-017f-4da5-884c-bcea83771773",
    "SEM-50": "9cc7236f-eceb-42dc-aa9d-80d4c883ccbb",
    "SEM-51": "12172040-8f58-48ba-82f3-76a158ba8f96",
    "SEM-52": "2c351fb3-0bbb-4ff7-87ca-96a0771bfff3",
    "SEM-53": "fa83ede4-af2b-4587-89a3-af054475d31d",
    "SEM-54": "4ade8865-0e1e-4955-9e36-b0ac396334f3",
    "SEM-55": "a5c4d6be-1616-4005-b137-f3b9b0e0cbc4",
    "SEM-56": "4dd0d499-7384-41d2-abf4-c1bebd1e2bc7",
    "SEM-57": "9cde5ee0-3a01-46f9-83f5-5e9138331303",
    "SEM-58": "309ac514-af33-4ef2-aa47-04d7e0e9dcbe",
    "SEM-59": "0fd5fd3d-1288-4deb-92aa-89ad41d3e9f3",
}

# Descriptions for key tickets
DESCRIPTIONS = {
    "SEM-6": """## User Story
As the system administrator, I want the global LLM config updated to minimax m2.7 via minimax.io so that all agents use the new model without OpenRouter dependency.

## Technical Specs
- File: openclaw.json
- Change: agents.defaults.model.primary from openrouter/minimax/minimax-m2.5 to minimax/minimax-m2.7
- Add: agents.defaults.model.base_url = https://api.minimax.io/v1
- Add: agents.defaults.model.provider = minimax
- Remove any OpenRouter references from model config

## Target State
```json
"model": {
  "primary": "minimax/minimax-m2.7",
  "provider": "minimax",
  "base_url": "https://api.minimax.io/v1"
}
```

## Acceptance Criteria
- [ ] openclaw.json shows minimax/minimax-m2.7 as primary model
- [ ] base_url field points to https://api.minimax.io/v1
- [ ] provider field set to minimax
- [ ] No openrouter references in model config section
- [ ] JSON validates (no syntax errors)

## Dependencies
None""",

    "SEM-7": """## User Story
As the signal detection system, I need to use the minimax.io API directly so that job description analysis works with the new LLM provider.

## Technical Specs
- File: skills/signal-detector/detect.py
- Function: get_llm_client() (lines 47-71)
- Change base_url from https://openrouter.ai/api/v1 to https://api.minimax.io/v1
- Update DEFAULT_ANALYTICAL_MODEL from moonshotai/kimi-k2.5 to minimax/minimax-m2.7
- Update DEFAULT_FAST_MODEL from minimax/minimax-m2.5 to minimax/minimax-m2.7

## Target State
```python
if provider == 'minimax' or True:  # Default to minimax
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.io/v1"
    )
```

## Acceptance Criteria
- [ ] base_url points to https://api.minimax.io/v1
- [ ] DEFAULT_ANALYTICAL_MODEL uses minimax/minimax-m2.7
- [ ] DEFAULT_FAST_MODEL uses minimax/minimax-m2.7
- [ ] Remove OpenRouter conditional (default to minimax)
- [ ] Test: python skills/signal-detector/detect.py --help works

## Dependencies
SCOUT-INFRA-001""",

    "SEM-11": """## User Story
As the system owner, I want to disable the Scout agent so that job discovery doesn't run on schedule anymore.

## Technical Specs
- File: openclaw.json
- Section: agents.scout
- Change: enabled: true → enabled: false
- Add: archived: true for future reference

## Target State
```json
"scout": {
  "enabled": false,
  "archived": true,
  "reason": "Deprecated - moving to Personal Assistant focus",
  "schedule": null
}
```

## Acceptance Criteria
- [ ] scout.enabled is false
- [ ] scout.archived is true
- [ ] Scout agent does NOT run on cron schedule
- [ ] Manual run (openclaw agents run scout) fails gracefully

## Dependencies
None""",

    "SEM-16": """## User Story
As the skill system, I need a standard skill structure for the email-check skill so that it follows the same pattern as other skills.

## Technical Specs
- Directory: skills/email-check/
- Files to create: SKILL.md, check.py, _meta.json, README.md

## Directory Structure
```
skills/email-check/
├── SKILL.md       # Skill documentation
├── check.py       # Main script (stub initially)
├── _meta.json     # Skill metadata
└── README.md      # Setup instructions
```

## Acceptance Criteria
- [ ] skills/email-check/ directory created
- [ ] SKILL.md follows existing skill pattern
- [ ] check.py exists with basic CLI structure
- [ ] _meta.json contains skill metadata
- [ ] README.md has setup instructions

## Dependencies
None""",

    "SEM-25": """## User Story
As the skill system, I need a standard skill structure for the calendar-check skill.

## Technical Specs
- Directory: skills/calendar-check/
- Files: SKILL.md, check.py, _meta.json, README.md

## Directory Structure
```
skills/calendar-check/
├── SKILL.md       # Skill documentation
├── check.py       # Main script
├── _meta.json     # Metadata
└── README.md      # Setup guide
```

## Acceptance Criteria
- [ ] skills/calendar-check/ directory created
- [ ] SKILL.md follows existing skill pattern
- [ ] check.py exists with basic CLI structure
- [ ] _meta.json contains skill metadata
- [ ] README.md has setup instructions

## Dependencies
None""",

    "SEM-34": """## User Story
As the skill system, I need a standard skill structure for the whatsapp-bridge skill.

## Technical Specs
- Directory: skills/whatsapp-bridge/
- Files: SKILL.md, bridge.py, _meta.json, README.md

## Directory Structure
```
skills/whatsapp-bridge/
├── SKILL.md       # Skill documentation
├── bridge.py     # Main bridge script
├── _meta.json     # Metadata
└── README.md     # Setup guide
```

## Acceptance Criteria
- [ ] skills/whatsapp-bridge/ directory created
- [ ] SKILL.md follows existing skill pattern
- [ ] bridge.py exists with basic structure
- [ ] README.md has setup instructions

## Dependencies
None""",

    "SEM-42": """## User Story
As the workflow designer, I need to document the Linear-first approach so that all tasks follow the same process.

## Technical Specs
- File: AGENTS.md
- Add: New section "Task Management" documenting Linear-first workflow

## The Process
1. **Create** → Create Linear ticket first
2. **Execute** → Work from ticket description
3. **Update** → Mark status: Todo → In Progress → Done
4. **Notify** → Send completion via WhatsApp

## Creating Tickets
When you receive a task request:
1. Parse request into title + description
2. Create ticket via Linear MCP with:
   - Title: Clear, actionable (max 60 chars)
   - Description: User story + technical specs + acceptance criteria
   - Priority: Based on urgency keywords
3. Confirm creation to user via WhatsApp
4. Execute the work
5. Update ticket to In Progress
6. Complete work
7. Update ticket to Done
8. Send completion notification

## Acceptance Criteria
- [ ] AGENTS.md updated with Task Management section
- [ ] Linear-first workflow clearly documented
- [ ] All team members understand the process
- [ ] References to old job pipeline removed

## Dependencies
None""",

    "SEM-49": """## User Story
As the architect, I need to define the Notion workspace structure so that all team members know where to find and create content.

## Technical Specs
- Root: "Scout Assistant" workspace/database
- Databases: Daily Briefing, Research, Deliverables, Knowledge Base

## Workspace Structure
```
Scout Assistant/
├── Daily Briefing/ (date, email_summary, calendar_summary, tasks)
├── Research/ (topic, source, summary, date, tags)
├── Deliverables/ (title, type, project, link, status, date)
└── Knowledge Base/ (title, category, content, tags, date)
```

## Acceptance Criteria
- [ ] Workspace structure documented
- [ ] Database purposes defined
- [ ] Property schemas planned
- [ ] Access permissions set
- [ ] Team knows the structure

## Dependencies
None""",

    "SEM-55": """## User Story
As the identity system, I need to update the Every Session section so that the new workflow loads correctly.

## Technical Specs
- File: AGENTS.md
- Section: "Every Session"
- Changes: Add Linear and Notion context loading

## Updated Steps
1. Read SOUL.md — this is who you are
2. Read USER.md — this is who you're helping
3. Read memory/YYYY-MM-DD.md (today + yesterday)
4. If in MAIN SESSION: Read MEMORY.md
5. **Check Linear for open tickets** — look for P0 and P1 priorities
6. **Check Notion for recent Daily Briefings** — understand recent activity

## Acceptance Criteria
- [ ] Section updated with Linear check step
- [ ] Section updated with Notion check step
- [ ] Steps in logical order
- [ ] Clear why each step matters
- [ ] Links to relevant docs

## Dependencies
None""",
}

def update_ticket(ticket_id, description):
    """Update a single ticket's description."""
    query = """
    mutation UpdateIssue($id: String!, $description: String!) {
      issueUpdate(id: $id, input: { description: $description }) {
        success
      }
    }
    """
    variables = {"id": ticket_id, "description": description}
    
    response = requests.post(
        ENDPOINT,
        headers=HEADERS,
        json={"query": query, "variables": variables}
    )
    
    result = response.json()
    if result.get("data", {}).get("issueUpdate", {}).get("success"):
        return True
    else:
        print(f"  Error: {result.get('errors', 'Unknown error')}")
        return False

def main():
    print("Pushing expanded descriptions to Linear tickets...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    # Update key tickets
    for identifier, description in DESCRIPTIONS.items():
        ticket_id = TICKET_IDS.get(identifier)
        if not ticket_id:
            print(f"[SKIP] {identifier} - no ID mapping")
            continue
            
        print(f"Updating {identifier}...", end=" ", flush=True)
        
        if update_ticket(ticket_id, description):
            print("✓")
            success_count += 1
        else:
            print("✗")
            fail_count += 1
        
        time.sleep(0.3)  # Rate limiting
    
    print("=" * 60)
    print(f"Done! {success_count} updated, {fail_count} failed")
    print()
    print("Full expanded specs available in:")
    print("  - linear-tickets/expanded_tickets.md (Epics 1-3)")
    print("  - linear-tickets/expanded_tickets_pt2.md (Epic 4-5)")
    print("  - linear-tickets/expanded_tickets_pt3.md (Epic 5-8)")

if __name__ == "__main__":
    main()