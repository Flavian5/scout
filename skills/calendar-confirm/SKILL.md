---
name: calendar-confirm
description: Send Discord confirmation after creating calendar events via gog.
metadata:
  {
    "openclaw": {
      "emoji": "📅",
      "requires": { "bins": ["gog"] },
    },
  }
---

# calendar-confirm

Send Discord confirmation when calendar events are created.

## Setup

- Requires `gog` authenticated with Google Calendar
- Discord webhook URL in `config/secrets.json` under `discord_webhook`

## Usage

```bash
python -m skills.calendar-confirm.check --event-id <event_id> --action create
python -m skills.calendar-confirm.check --event-id <event_id> --action cancel
```

## Event Confirmation Format

**Event Created:**
```
📅 Event Created
Title: Meeting with John
Time: Tomorrow at 2:00 PM
Location: https://meet.google.com/abc-defg-hij
React with ✏️ to edit or ❌ to cancel
```

**Event Canceled:**
```
📅 Event Canceled
The following event has been removed:
Title: Meeting with John
```

## Integration

This skill is called after `gog calendar create` succeeds. The workflow:

1. User requests event creation via chat
2. Create event via `gog calendar create ...`
3. Call this skill with `--event-id <id> --action create`
4. Discord notification sent with event details and quick actions