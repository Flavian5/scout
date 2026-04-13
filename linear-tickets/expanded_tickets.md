# Scout Personal Assistant - Expanded Ticket Specs

All 57 tickets with user stories, technical specs, and acceptance criteria.

---

## Epic 1: LLM Infrastructure Migration

### SCOUT-INFRA-001: Update openclaw.json model config

**User Story:** As the system administrator, I want the global LLM config updated to minimax m2.7 via minimax.io so that all agents use the new model without OpenRouter dependency.

**Technical Specs:**
- File: `openclaw.json`
- Change: `agents.defaults.model.primary` from `openrouter/minimax/minimax-m2.5` to `minimax/minimax-m2.7`
- Add new field: `agents.defaults.model.base_url` = `https://api.minimax.io/v1`
- Remove any OpenRouter references from model config

**Current State (lines 13-15):**
```json
"model": {
  "primary": "openrouter/minimax/minimax-m2.5"
},
```

**Target State:**
```json
"model": {
  "primary": "minimax/minimax-m2.7",
  "provider": "minimax",
  "base_url": "https://api.minimax.io/v1"
},
```

**Acceptance Criteria:**
- [ ] `openclaw.json` shows `minimax/minimax-m2.7` as primary model
- [ ] `base_url` field points to `https://api.minimax.io/v1`
- [ ] `provider` field set to `minimax`
- [ ] No `openrouter` references in model config section
- [ ] JSON validates (no syntax errors)

**Dependencies:** None

---

### SCOUT-INFRA-002: Update signal-detector to use minimax.io client

**User Story:** As the signal detection system, I need to use the minimax.io API directly so that job description analysis works with the new LLM provider.

**Technical Specs:**
- File: `skills/signal-detector/detect.py`
- Function: `get_llm_client()` (lines 47-71)
- Change base_url from `https://openrouter.ai/api/v1` to `https://api.minimax.io/v1`
- Update default models:
  - `DEFAULT_ANALYTICAL_MODEL` from `moonshotai/kimi-k2.5` to `minimax/minimax-m2.7`
  - `DEFAULT_FAST_MODEL` from `minimax/minimax-m2.5` to `minimax/minimax-m2.7`

**Current State (lines 64-68):**
```python
if provider == 'openrouter':
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
```

**Target State:**
```python
if provider == 'minimax' or True:  # Default to minimax
    client = openai.OpenAI(
        api_key=api_key,
        base_url="https://api.minimax.io/v1"
    )
```

**Acceptance Criteria:**
- [ ] `base_url` points to `https://api.minimax.io/v1`
- [ ] `DEFAULT_ANALYTICAL_MODEL` uses `minimax/minimax-m2.7`
- [ ] `DEFAULT_FAST_MODEL` uses `minimax/minimax-m2.7`
- [ ] Remove OpenRouter conditional (default to minimax)
- [ ] Test: `python skills/signal-detector/detect.py --help` works

**Dependencies:** SCOUT-INFRA-001

---

### SCOUT-INFRA-003: Verify minimax.io API key works

**User Story:** As the integration system, I need to verify the minimax.io API credentials are valid so that LLM calls succeed without authentication errors.

**Technical Specs:**
- Test endpoint: `POST https://api.minimax.io/v1/chat/completions`
- Required headers: `Authorization: Bearer <api_key>`
- Test payload: Simple completion request with 1 token

**Verification Steps:**
1. Get API key from `config/secrets.json` → `llm_api.api_key`
2. Run test curl:
```bash
curl -s -X POST "https://api.minimax.io/v1/chat/completions" \
  -H "Authorization: Bearer <key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"minimax/m2.7","messages":[{"role":"user","content":"Hi"}],"max_tokens":5}'
```

**Expected Response:**
```json
{
  "id": "...",
  "choices": [{"message": {"content": "..."}}]
}
```

**Acceptance Criteria:**
- [ ] API key format matches (should start with `minimax_` or similar)
- [ ] Test API call returns valid JSON response
- [ ] No "invalid API key" or "authentication failed" errors
- [ ] Document any rate limits or quota info

**Dependencies:** SCOUT-INFRA-001, SCOUT-INFRA-002

---

### SCOUT-INFRA-004: Audit skills for OpenRouter references

**User Story:** As the code auditor, I need to find all OpenRouter references across the codebase so that we can migrate everything to minimax.io.

**Technical Specs:**
- Search pattern: `openrouter.ai`
- Tools: `grep -r` or IDE search
- Files to check: All skill directories, config files, documentation

**Search Command:**
```bash
grep -r "openrouter" --include="*.py" --include="*.json" --include="*.md" .
```

**Files to Check:**
- `skills/signal-detector/detect.py` - Already updating (SCOUT-INFRA-002)
- `skills/asset-generator/generate.py` - Check for LLM calls
- `skills/company-research/research.py` - Check for LLM calls
- `skills/ddg-web-search/` - Check for any API references
- `openclaw.json` - Model configs
- `config/secrets.json` - Provider settings
- Documentation files

**Acceptance Criteria:**
- [ ] Run grep search for `openrouter`
- [ ] Update all found references to `minimax` or `minimax.io`
- [ ] Update any `openrouter.ai` URLs to `api.minimax.io/v1`
- [ ] Update any OpenRouter model names to equivalent minimax models
- [ ] Commit changes with message: "Migrate from OpenRouter to minimax.io"

**Dependencies:** SCOUT-INFRA-001, SCOUT-INFRA-002

---

### SCOUT-INFRA-005: Test signal-detector end-to-end

**User Story:** As the quality assurance system, I need to verify the signal detector works end-to-end with the new model so that job analysis continues without interruption.

**Technical Specs:**
- Test file: `skills/signal-detector/detect.py`
- Test data: Sample job description from `data/leads/raw_leads.json` (or create mock)

**Test Command:**
```bash
cd /Users/haomeng/dev/scout
python skills/signal-detector/detect.py \
  --company "TestCompany" \
  --role "Senior ML Engineer" \
  --jd "We are looking for a senior ML engineer with experience in PyTorch, recommendation systems, and large-scale machine learning. The ideal candidate has worked on production ML systems at scale."
```

**Expected Output:**
```json
{
  "detected_signals": {
    "ml_architecture": {"production_ml": true},
    "domain_alignment": {"recsys": true},
    "career_impact": {"leadership_growth": true}
  },
  "signal_strength": {...},
  "recommendation": "...",
  "method": "llm"
}
```

**Acceptance Criteria:**
- [ ] Script runs without errors
- [ ] Returns valid JSON (no parsing errors)
- [ ] `detected_signals` contains expected keys
- [ ] `method` field is `llm` (not `keyword`)
- [ ] Response time < 10 seconds

**Dependencies:** SCOUT-INFRA-002, SCOUT-INFRA-003

---

## Epic 2: Deprecate Job Application Pipeline

### SCOUT-DEPRECATE-001: Disable scout agent

**User Story:** As the system owner, I want to disable the Scout agent so that job discovery doesn't run on schedule anymore.

**Technical Specs:**
- File: `openclaw.json`
- Section: `agents.scout` (lines 21-31)
- Change: `enabled: true` → `enabled: false`
- Add: `archived: true` for future reference

**Current State:**
```json
"scout": {
  "enabled": true,
  "schedule": "0 2 * * *",
  ...
}
```

**Target State:**
```json
"scout": {
  "enabled": false,
  "archived": true,
  "reason": "Deprecated - moving to Personal Assistant focus",
  "schedule": null,
  ...
}
```

**Acceptance Criteria:**
- [ ] `scout.enabled` is `false`
- [ ] `scout.archived` is `true`
- [ ] Scout agent does NOT run on cron schedule
- [ ] Manual run (`openclaw agents run scout`) fails gracefully

**Dependencies:** None

---

### SCOUT-DEPRECATE-002: Disable analyst agent

**User Story:** As the system owner, I want to disable the Analyst agent so that job scoring doesn't run on schedule anymore.

**Technical Specs:**
- File: `openclaw.json`
- Section: `agents.analyst` (lines 33-43)
- Change: `enabled: true` → `enabled: false`
- Add: `archived: true` for future reference

**Target State:**
```json
"analyst": {
  "enabled": false,
  "archived": true,
  "reason": "Deprecated - moving to Personal Assistant focus"
}
```

**Acceptance Criteria:**
- [ ] `analyst.enabled` is `false`
- [ ] `analyst.archived` is `true`
- [ ] Analyst agent does NOT run on cron schedule

**Dependencies:** None

---

### SCOUT-DEPRECATE-003: Disable strategist agent

**User Story:** As the system owner, I want to disable the Strategist agent so that application package generation doesn't run on schedule anymore.

**Technical Specs:**
- File: `openclaw.json`
- Section: `agents.strategist` (lines 45-55)
- Change: `enabled: true` → `enabled: false`
- Add: `archived: true` for future reference

**Target State:**
```json
"strategist": {
  "enabled": false,
  "archived": true,
  "reason": "Deprecated - moving to Personal Assistant focus"
}
```

**Acceptance Criteria:**
- [ ] `strategist.enabled` is `false`
- [ ] `strategist.archived` is `true`
- [ ] Strategist agent does NOT run on cron schedule

**Dependencies:** None

---

### SCOUT-DEPRECATE-004: Archive old agent configs

**User Story:** As the system archivist, I want to preserve the old agent configurations for reference while marking them as deprecated.

**Technical Specs:**
- Files: `agents/scout.md`, `agents/analyst.md`, `agents/strategist.md`
- Action: Move to `agents/archived/` directory
- Create `agents/archived/README.md` explaining why they're archived

**Archive Structure:**
```
agents/
├── archived/
│   ├── README.md        # Explains deprecation
│   ├── scout.md         # Original scout agent
│   ├── analyst.md       # Original analyst agent
│   └── strategist.md    # Original strategist agent
├── ...                  # Active agents go here
```

**Acceptance Criteria:**
- [ ] `agents/archived/` directory created
- [ ] All three agent files moved to `archived/`
- [ ] `agents/archived/README.md` explains the deprecation
- [ ] Original files preserved (not deleted)
- [ ] Git history preserved

**Dependencies:** SCOUT-DEPRECATE-001, SCOUT-DEPRECATE-002, SCOUT-DEPRECATE-003

---

### SCOUT-DEPRECATE-005: Update heartbeat to skip old pipeline

**User Story:** As the heartbeat system, I need to remove references to the old job pipeline so that heartbeat checks don't look for scout/analyst/strategist status.

**Technical Specs:**
- File: `HEARTBEAT.md` or config file controlling heartbeat behavior
- Remove: Any checks for `scout_status`, `analyst_status`, `strategist_status`
- Add: New checks for Linear, Notion, Email, Calendar

**Current Heartbeat (if any):**
```markdown
## Checks
- [ ] Scout agent status
- [ ] Analyst agent status  
- [ ] Strategist agent status
```

**Target Heartbeat:**
```markdown
## Checks
- [ ] Check Linear for open tickets
- [ ] Check email for urgent messages
- [ ] Check calendar for upcoming events
- [ ] Check WhatsApp for pending messages
```

**Acceptance Criteria:**
- [ ] No references to `scout`, `analyst`, or `strategist` in heartbeat
- [ ] New checks added for Linear, Email, Calendar, WhatsApp
- [ ] Heartbeat runs successfully without old pipeline references

**Dependencies:** SCOUT-DEPRECATE-004

---

## Epic 3: Email Monitoring

### SCOUT-EMAIL-001: Create email-check skill directory

**User Story:** As the skill system, I need a standard skill structure for the email-check skill so that it follows the same pattern as other skills.

**Technical Specs:**
- Directory: `skills/email-check/`
- Files to create:
  - `SKILL.md` - Skill documentation
  - `check.py` - Main script (stub initially)
  - `_meta.json` - Skill metadata
  - `README.md` - Setup instructions

**Directory Structure:**
```
skills/email-check/
├── SKILL.md       # Skill documentation
├── check.py       # Main script
├── _meta.json      # Metadata
└── README.md      # Setup guide
```

**SKILL.md Template:**
```markdown
# Email Check Skill

## Purpose
Monitor Gmail inbox and detect urgent messages.

## Setup
1. Enable Gmail API at console.cloud.google.com
2. Create OAuth2 credentials
3. Store in config/secrets.json

## Usage
python check.py --recent 24

## Output
JSON array of email summaries with urgency classification.
```

**Acceptance Criteria:**
- [ ] `skills/email-check/` directory created
- [ ] `SKILL.md` follows existing skill pattern
- [ ] `check.py` exists with basic CLI structure
- [ ] `_meta.json` contains skill metadata
- [ ] `README.md` has setup instructions

**Dependencies:** None

---

### SCOUT-EMAIL-002: Implement Gmail API OAuth2

**User Story:** As the authentication system, I need Gmail API OAuth2 so that the email skill can securely access inbox data.

**Technical Specs:**
- API: Gmail API v1
- Auth: OAuth2 with refresh tokens
- Python library: `google-auth` or `gspread`

**Setup Steps:**
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Create OAuth2 Client ID (Desktop app)
3. Download JSON, extract `client_secret`
4. Store in `config/secrets.json`:
```json
{
  "gmail": {
    "client_id": "...",
    "client_secret": "...",
    "refresh_token": "..."
  }
}
```

**Code Pattern (check.py):**
```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

def get_gmail_client():
    creds = Credentials(
        token=None,
        refresh_token=secrets['gmail']['refresh_token'],
        client_id=secrets['gmail']['client_id'],
        client_secret=secrets['gmail']['client_secret'],
        token_uri="https://oauth2.googleapis.com/token"
    )
    creds.refresh(Request())
    return creds
```

**Acceptance Criteria:**
- [ ] OAuth2 flow implemented
- [ ] Token refresh works automatically
- [ ] Can list messages without manual re-auth
- [ ] Handles expired tokens gracefully

**Dependencies:** SCOUT-EMAIL-001

---

### SCOUT-EMAIL-003: Implement inbox fetch

**User Story:** As the email monitor, I need to fetch recent unread emails so that I can analyze and summarize them.

**Technical Specs:**
- Endpoint: `GET https://gmail.googleapis.com/gmail/v1/users/me/messages`
- Query: `is:unread newer_than:1d`
- Fields: `id, subject, from, snippet, date`

**Code Pattern:**
```python
def fetch_unread_emails(service, hours=24):
    query = f"is:unread newer_than:{hours}h"
    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=50
    ).execute()
    
    messages = results.get('messages', [])
    emails = []
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='metadata',
            metadataHeaders=['From', 'Subject', 'Date']
        ).execute()
        
        headers = msg_data['payload']['headers']
        email = {
            'id': msg['id'],
            'from': get_header(headers, 'From'),
            'subject': get_header(headers, 'Subject'),
            'date': get_header(headers, 'Date'),
            'snippet': msg_data['snippet']
        }
        emails.append(email)
    
    return emails
```

**Acceptance Criteria:**
- [ ] Fetches unread emails from last 24h
- [ ] Returns: id, from, subject, date, snippet
- [ ] Handles empty inbox gracefully
- [ ] Handles rate limits (429) with backoff

**Dependencies:** SCOUT-EMAIL-002

---

### SCOUT-EMAIL-004: Implement urgency classification

**User Story:** As the email analyzer, I need LLM-powered urgency classification so that I can prioritize which emails need immediate attention.

**Technical Specs:**
- Model: minimax m2.7 (via API)
- Prompt: Classify email as urgent/important/routine
- Output: `{urgency: "urgent"|"important"|"routine", reason: "..."}`

**Code Pattern:**
```python
def classify_urgency(email, client):
    prompt = f"""Classify this email's urgency level:

From: {email['from']}
Subject: {email['subject']}
Snippet: {email['snippet']}

Respond ONLY with JSON:
{{"