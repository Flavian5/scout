---
name: email-alerts
description: Monitor Gmail for urgent emails and send Discord notifications.
metadata:
  {
    "openclaw": {
      "emoji": "📧",
      "requires": { "bins": ["gog"] },
    },
  }
---

# email-alerts

Monitor Gmail for urgent emails (VIP senders, starred, labeled) and send Discord notifications.

## Setup

- Requires `gog` authenticated with Gmail
- Discord webhook URL in `config/secrets.json` under `discord_webhook`
- Optional: VIP senders list in config

## Usage

```bash
python -m skills.email-alerts.check
```

## Urgent Email Detection

1. Check unread emails from last 5 minutes
2. Check for:
   - Starred emails
   - Important label
   - VIP sender matches (configurable list)
   - Subject keywords (configurable)
3. Send Discord embed for each urgent email

## Discord Notification Format

```
📧 Urgent Email
From: sender@example.com
Subject: Email Subject
Preview: First 200 chars of body...
Time: 10:30 AM
```

## Configuration

Add to `config/secrets.json`:
```json
{
  "email_alerts": {
    "vip_senders": ["boss@company.com", "client@important.com"],
    "keywords": ["urgent", "asap", "emergency", "important"],
    "check_interval_minutes": 5
  }
}