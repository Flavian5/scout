# Expanded Ticket Specs - Part 2 (Tickets 6-57)

---

### SCOUT-EMAIL-004: Implement urgency classification (continued)

```python
"urgency": "urgent|important|routine",
"reason": "one sentence explanation"
}}

Rules:
- urgent: Requires immediate action (interview invites, deadlines, crises)
- important: Should respond within 24h (business opportunities, time-sensitive)
- routine: Can wait (newsletters, notifications, low-priority)
```

**Acceptance Criteria:**
- [ ] Uses minimax m2.7 for classification
- [ ] Returns valid JSON
- [ ] Classifies as urgent/important/routine
- [ ] Includes one-sentence reason
- [ ] Falls back to keyword matching if LLM fails

**Dependencies:** SCOUT-EMAIL-003

---

### SCOUT-EMAIL-005: Integrate email-check into heartbeat

**User Story:** As the heartbeat system, I need to check emails automatically so that users get notified of urgent messages.

**Technical Specs:**
- File: `HEARTBEAT.md`
- Add: Email check to heartbeat rotation

**Heartbeat Update:**
```markdown
## Email Check (rotate with other checks)
1. Run: `python skills/email-check/check.py --recent 24`
2. Parse output for urgent emails
3. If urgent count > 0, include in heartbeat summary
4. If critical, send WhatsApp notification
```

**Acceptance Criteria:**
- [ ] Heartbeat calls email-check skill
- [ ] Urgent emails appear in heartbeat output
- [ ] WhatsApp notification sent for critical emails
- [ ] Follows rotation pattern (don't check every heartbeat)

**Dependencies:** SCOUT-EMAIL-001, SCOUT-EMAIL-002, SCOUT-EMAIL-003, SCOUT-EMAIL-004

---

### SCOUT-EMAIL-006: Send urgent email alerts via WhatsApp

**User Story:** As the notification system, I need to send WhatsApp alerts for urgent emails so that users never miss critical messages.

**Technical Specs:**
- Trigger: Email classified as "urgent"
- Action: Send WhatsApp message via WhatsApp bridge
- Format: Brief summary + action link

**Message Format:**
```
📧 Urgent Email

From: {sender}
Subject: {subject}

Snippet: {first 100 chars}...

Action: Reply to email / Open in Gmail
```

**Acceptance Criteria:**
- [ ] Urgent emails trigger WhatsApp message
- [ ] Message includes sender, subject, snippet
- [ ] Includes action button (open email)
- [ ] Rate limited (max 1 urgent alert per email)
- [ ] Deduplicated (no double alerts)

**Dependencies:** SCOUT-EMAIL-004, Epic 5 (WhatsApp)

---

### SCOUT-EMAIL-007: Create Notion Email Digest database

**User Story:** As the documentation system, I need a Notion database for email digests so that important emails are preserved for later reference.

**Technical Specs:**
- Use Notion MCP to create database
- Database name: "Email Digest"

**Schema:**
```json
{
  "name": "Email Digest",
  "properties": {
    "Date": {"type": "date"},
    "From": {"type": "rich_text"},
    "Subject": {"type": "rich_text"},
    "Urgency": {"type": "select", "options": ["urgent", "important", "routine"]},
    "Summary": {"type": "rich_text"},
    "Action Required": {"type": "checkbox"},
    "Link": {"type": "url"}
  }
}
```

**Acceptance Criteria:**
- [ ] Notion database created via MCP
- [ ] All fields present with correct types
- [ ] Database accessible in Notion workspace
- [ ] Schema matches requirements

**Dependencies:** Epic 7 (Notion)

---

### SCOUT-EMAIL-008: Push daily email digest to Notion

**User Story:** As the archival system, I need to push daily email summaries to Notion so that users have a searchable history of their communications.

**Technical Specs:**
- Trigger: End of day (configurable)
- Action: Create Notion page with daily digest
- Content: All emails from the day, grouped by urgency

**Notion Page Structure:**
```
Daily Email Digest - {date}

## Urgent Emails (X)
- [Email 1]
- [Email 2]

## Important Emails (X)
- [Email 1]
- [Email 2]

## Routine Emails (X)
- [Email 1]
- [Email 2]

## Summary
- Total emails: X
- Urgent: X
- Important: X
- Routine: X
```

**Acceptance Criteria:**
- [ ] Daily digest page created in Notion
- [ ] All emails included with correct grouping
- [ ] Summary statistics included
- [ ] Page searchable by date

**Dependencies:** SCOUT-EMAIL-007

---

## Epic 4: Google Calendar Integration

### SCOUT-CAL-001: Create calendar-check skill directory

**User Story:** As the skill system, I need a standard skill structure for the calendar-check skill.

**Technical Specs:**
- Directory: `skills/calendar-check/`
- Files: `SKILL.md`, `check.py`, `_meta.json`, `README.md`

**Directory Structure:**
```
skills/calendar-check/
├── SKILL.md       # Skill documentation
├── check.py       # Main script
├── _meta.json      # Metadata
└── README.md      # Setup guide
```

**Acceptance Criteria:**
- [ ] `skills/calendar-check/` directory created
- [ ] `SKILL.md` follows existing skill pattern
- [ ] `check.py` exists with basic CLI structure
- [ ] `_meta.json` contains skill metadata
- [ ] `README.md` has setup instructions

**Dependencies:** None

---

### SCOUT-CAL-002: Implement Google Calendar API OAuth2

**User Story:** As the authentication system, I need Google Calendar API OAuth2 so that the calendar skill can securely access calendar data.

**Technical Specs:**
- API: Google Calendar API v3
- Auth: OAuth2 with refresh tokens
- Scope: `https://www.googleapis.com/auth/calendar.readonly`

**Setup Steps:**
1. Enable Google Calendar API in Google Cloud Console
2. Use existing OAuth2 credentials (can share with Gmail)
3. Store in `config/secrets.json`:
```json
{
  "google_calendar": {
    "client_id": "...",
    "client_secret": "...",
    "refresh_token": "..."
  }
}
```

**Acceptance Criteria:**
- [ ] OAuth2 flow implemented
- [ ] Can list calendars without manual re-auth
- [ ] Token refresh works automatically
- [ ] Handles expired tokens gracefully

**Dependencies:** SCOUT-CAL-001

---

### SCOUT-CAL-003: Fetch upcoming events

**User Story:** As the calendar monitor, I need to fetch upcoming events so that I can alert users before meetings.

**Technical Specs:**
- Endpoint: `GET /calendars/primary/events`
- Time range: Now to +48 hours
- Fields: `id, summary, start, end, attendees, location`

**Code Pattern:**
```python
def fetch_upcoming_events(service, hours=48):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    later = (datetime.datetime.utcnow() + 
            datetime.timedelta(hours=hours)).isoformat() + 'Z'
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=later,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    return events_result.get('items', [])
```

**Acceptance Criteria:**
- [ ] Fetches events for next 24-48h
- [ ] Returns: id, summary, start, end, location, attendees
- [ ] Handles empty calendar gracefully
- [ ] Filters out declined events

**Dependencies:** SCOUT-CAL-002

---

### SCOUT-CAL-004: Send 15-minute meeting reminder

**User Story:** As the reminder system, I need to send WhatsApp reminders 15 minutes before meetings so that users are never late.

**Technical Specs:**
- Trigger: Event start time - 15 minutes
- Check: Run every 5 minutes during active hours
- Action: Send WhatsApp message

**Message Format:**
```
⏰ Meeting in 15 minutes

📅 {event_title}
🕐 {start_time}
📍 {location or "No location"}

Click to join: {meeting_link}
```

**Acceptance Criteria:**
- [ ] Reminder sent 15 min before each meeting
- [ ] Message includes title, time, location
- [ ] Includes meeting link if available
- [ ] Deduplicated (no double reminders)
- [ ] Respects quiet hours (no late-night alerts)

**Dependencies:** SCOUT-CAL-003, Epic 5 (WhatsApp)

---

### SCOUT-CAL-005: Integrate calendar-check into heartbeat

**User Story:** As the heartbeat system, I need to check calendar automatically so that users get a daily overview of upcoming events.

**Technical Specs:**
- File: `HEARTBEAT.md`
- Add: Calendar check to heartbeat rotation

**Heartbeat Update:**
```markdown
## Calendar Check (morning heartbeat)
1. Run: `python skills/calendar-check/check.py --hours 48`
2. Parse output for today's events
3. Include in heartbeat summary:
   - Today's meetings (count + titles)
   - Tomorrow's meetings (count + titles)
   - Any all-day events
```

**Acceptance Criteria:**
- [ ] Heartbeat calls calendar-check skill
- [ ] Today's events appear in heartbeat output
- [ ] Tomorrow's events also shown
- [ ] Follows rotation pattern

**Dependencies:** SCOUT-CAL-001, SCOUT-CAL-002, SCOUT-CAL-003

---

### SCOUT-CAL-006: Handle multiple calendars

**User Story:** As the calendar system, I need to support multiple calendars so that users don't miss events from work or personal calendars.

**Technical Specs:**
- Supported: Primary, Work, Personal
- Config: `config/secrets.json` with calendar IDs
- Merge: Combine events from all calendars, deduplicate

**Config Structure:**
```json
{
  "calendars": {
    "primary": "primary",
    "work": "work@example.com",
    "personal": "personal@gmail.com"
  }
}
```

**Acceptance Criteria:**
- [ ] Config supports multiple calendar IDs
- [ ] Events from all calendars fetched
- [ ] Duplicates removed (same event, different calendars)
- [ ] User can enable/disable specific calendars

**Dependencies:** SCOUT-CAL-003

---

### SCOUT-CAL-007: Parse natural language event requests

**User Story:** As the calendar assistant, I need to understand natural language event requests so that users can create events by typing naturally.

**Technical Specs:**
- Input: "Meeting with Alex tomorrow at 3pm"
- Output: Structured event data
- Library: LLM (minimax m2.7) or regex patterns

**LLM Approach:**
```python
def parse_event_request(text, client):
    prompt = f"""Parse this calendar request into structured JSON:

Request: {text}

Respond ONLY with JSON:
{{
  "title": "Event title",
  "date": "YYYY-MM-DD",
  "start_time": "HH:MM",
  "end_time": "HH:MM or null",
  "location": "location or null",
  "attendees": ["email1", "email2"] or []
}}
```

**Acceptance Criteria:**
- [ ] Understands "tomorrow at 3pm"
- [ ] Understands "next Monday at 2pm"
- [ ] Extracts title, time, location, attendees
- [ ] Handles ambiguous requests (asks for clarification)

**Dependencies:** SCOUT-CAL-001

---

### SCOUT-CAL-008: Create Google Calendar event

**User Story:** As the calendar assistant, I need to create calendar events from parsed requests so that users can add events via chat.

**Technical Specs:**
- Endpoint: `POST /calendars/primary/events`
- Input: Structured event data from parser

**Code Pattern:**
```python
def create_event(service, event_data):
    event = {
        'summary': event_data['title'],
        'start': {
            'dateTime': f"{event_data['date']}T{event_data['start_time']}:00",
            'timeZone': 'America/Los_Angeles'
        },
        'end': {
            'dateTime': f"{event_data['date']}T{event_data['end_time']}:00",
            'timeZone': 'America/Los_Angeles'
        }
    }
    
    if event_data.get('location'):
        event['location'] = event_data['location']
    
    if event_data.get('attendees'):
        event['attendees'] = [{'email': a} for a in event_data['attendees']]
    
    return service.events().insert(
        calendarId='primary',
        body=event
    ).execute()
```

**Acceptance Criteria:**
- [ ] Creates event with correct title
- [ ] Sets correct start/end times
- [ ] Adds location if provided
- [ ] Adds attendees if provided
- [ ] Returns event ID

**Dependencies:** SCOUT-CAL-007

---

### SCOUT-CAL-009: Confirm event creation via WhatsApp

**User Story:** As the notification system, I need to confirm event creation via WhatsApp so that users know the event was added successfully.

**Technical Specs:**
- Trigger: Successful event creation
- Action: Send WhatsApp confirmation

**Message Format:**
```
✅ Event Created

📅 {event_title}
🕐 {date} at {start_time}
📍 {location or "No location"}

View in Google Calendar: {link}
```

**Acceptance Criteria:**
- [ ] Confirmation sent after successful creation
- [ ] Message includes all event details
- [ ] Includes Google Calendar link
- [ ] Handles creation failure gracefully (error message)

**Dependencies:** SCOUT-CAL-008, Epic 5 (WhatsApp)

---

## Epic 5: WhatsApp Communication

### SCOUT-WA-001: Create whatsapp-bridge skill directory

**User Story:** As the skill system, I need a standard skill structure for the whatsapp-bridge skill.

**Technical Specs:**
- Directory: `skills/whatsapp-bridge/`
- Files: `SKILL.md`, `bridge.py`, `_meta.json`, `README.md`

**Directory Structure:**
```
skills/whatsapp-bridge/
├── SKILL.md       # Skill documentation
├── bridge.py     # Main bridge script
├── _meta.json     # Metadata
└── README.md     # Setup guide
```

**Acceptance Criteria:**
- [ ] `skills/whatsapp-bridge/` directory created
- [ ] `SKILL.md` follows existing skill pattern
- [ ] `bridge.py` exists with basic structure
- [ ] `README.md` has setup instructions

**Dependencies:** None

---

### SCOUT-WA-002: Implement WhatsApp Web connection

**User Story:** As the WhatsApp system, I need to connect to WhatsApp Web so that I can send and receive messages.

**Technical Specs:**
- Library: `whatsapp-web.js` (Node.js)
- Auth: QR code scan (initial), session persistence
- Session storage: Local file system

**Setup Steps:**
1. Install: `npm install whatsapp-web.js`
2. Create `bridge.py` that spawns Node process
3. Initial auth requires QR code scan
4. Session saved to `~/.openclaw/whatsapp-session.json`

**Code Pattern (bridge.py):**
```javascript
const { Client, LocalAuth } = require('whatsapp-web.js');

const client = new Client({
    authStrategy: new LocalAuth({
        dataPath: '~/.openclaw/whatsapp-session'
    })
});

client.on('qr', (qr) => {
    // Generate QR code for user to scan
});

client.on('ready', () => {
    console.log('WhatsApp connected');
});

client.initialize();
```

**Acceptance Criteria:**
- [ ] WhatsApp Web session established
- [ ] QR code generated for initial auth
- [ ] Session persists across restarts
- [ ] Reconnects automatically on disconnect

**Dependencies:** SCOUT-WA-001

---

### SCOUT-WA-003: Implement incoming message handler

**User Story:** As the message handler, I need to process incoming WhatsApp messages so that I can respond to user requests.

**Technical Specs:**
- Event: `message_create`
- Action: Parse message, route to agent
- Format: JSON with message details

**Message Format:**
```json
{
  "from": "+1234567890",
  "body": "User's message",
  "timestamp": "2026-04-12T12:00:00Z",
  "type": "chat"
}
```

**Handler Pattern:**
```python
def handle_message(message_json):
    from_number = message_json['from']
    body = message_json['body']
    
    # Create Linear ticket
    create_ticket(
        title=f"WhatsApp: {body[:50]}...",
        description=body,
        from_number=from_number
    )
```

**Acceptance Criteria:**
- [ ] Incoming messages logged
- [ ] Messages parsed into structured format
- [ ] Routing to appropriate handler
- [ ] Acknowledge receipt (quick reply)

**Dependencies:** SCOUT-WA-002

---

### SCOUT-WA-004: Implement outgoing message sender

**User Story:** As the notification system, I need to send WhatsApp messages so that users receive proactive updates.

**Technical Specs:**
- Method: `client.sendMessage(number, message)`
- Rate limiting: Max 1 message per 5 seconds per conversation
- Queue: Messages queued if rate limited

**Code Pattern:**
```python
def send_whatsapp(number, message, bridge_port=9090):
    # Send to local bridge service
    response = requests.post(
        f"http://localhost:{bridge_port}/send",
        json={"to": number, "message": message}
    )
    return response.json()
```

**Message Formatting:**
- No markdown tables
- Use bullet points (- or *)
- No headers (use **bold** instead)
- Emojis allowed and encouraged

**Acceptance Criteria:**
- [ ] Can send to any phone number
- [ ] Rate limiting respects WhatsApp limits
- [ ] Queue handles burst messages
- [ ] Returns delivery status

**Dependencies:** SCOUT-WA-002

---

### SCOUT-WA-005: Implement session persistence

**User Story:** As the reliability system,