---
name: calendar-check
description: Check Google Calendar for upcoming events. Returns events from the next 24 hours with title, time, location, and attendees. Integrates with Discord for meeting reminders and Notion for calendar digest storage.
---

# Calendar Check Skill

Check Google Calendar for upcoming events using Google Calendar API with OAuth2 authentication.

## Prerequisites

1. Google Calendar API enabled in Google Cloud Console
2. OAuth2 credentials (desktop app type)
3. Token file stored at `config/calendar-token.json`

## Quick Start

```bash
python skills/calendar-check/check.py --help
python skills/calendar-check/check.py --fetch          # Fetch upcoming events
python skills/calendar-check/check.py --remind        # Send 15-minute reminders via Discord
python skills/calendar-check/check.py --digest        # Send daily digest to Discord
```

## Authentication

First run will initiate OAuth2 flow:

```bash
python skills/calendar-check/check.py --auth
```

Opens browser for Google sign-in. Token saved to `config/calendar-token.json`.

## Event Fetch

Returns upcoming events from the next 24 hours:

```json
{
  "events": [
    {
      "id": "event123",
      "title": "Team Standup",
      "start": "2026-04-13T09:00:00Z",
      "end": "2026-04-13T09:30:00Z",
      "location": "https://meet.google.com/abc-defg-hij",
      "attendees": ["alice@example.com", "bob@example.com"],
      "minutes_until": 45
    }
  ],
  "count": 1
}
```

## Meeting Reminders

Checks for events starting in ~15 minutes and sends Discord notifications:

- Checks every 15 minutes via heartbeat
- Includes event title, time, location/link
- Avoids duplicate reminders

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `calendar_token_path` | `config/calendar-token.json` | OAuth token file |
| `credentials_path` | `config/calendar-credentials.json` | OAuth client config |
| `lookback_minutes` | 0 | How far back to fetch (0 = future only) |
| `max_results` | 50 | Maximum events to return |
| `reminder_window` | 15 | Minutes before event to send reminder |

## Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client requests