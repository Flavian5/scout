---
name: email-check
description: Check Gmail inbox for unread messages from the last 24 hours. Returns sender, subject, snippet, and timestamp. Supports urgency classification to identify important/urgent emails. Integrates with WhatsApp for urgent alerts and Notion for email digest storage.
---

# Email Check Skill

Check Gmail inbox and classify email urgency using Gmail API with OAuth2 authentication.

## Prerequisites

1. Gmail API enabled in Google Cloud Console
2. OAuth2 credentials (desktop app type)
3. Token file stored at `config/gmail-token.json`

## Quick Start

```bash
python skills/email-check/check.py --help
python skills/email-check/check.py --fetch          # Fetch unread emails
python skills/email-check/check.py --classify      # Classify urgency
python skills/email-check/check.py --urgent-alert   # Send urgent alerts via WhatsApp
```

## Authentication

First run will initiate OAuth2 flow:

```bash
python skills/email-check/check.py --auth
```

Opens browser for Google sign-in. Token saved to `config/gmail-token.json`.

## Email Fetch

Returns unread emails from last 24 hours:

```json
{
  "emails": [
    {
      "id": "msg123",
      "sender": "boss@company.com",
      "subject": "Urgent: Project deadline",
      "snippet": "We need the report by EOD...",
      "timestamp": "2026-04-12T14:30:00Z"
    }
  ],
  "count": 1
}
```

## Urgency Classification

Uses MiniMax-M2.7 LLM to classify emails:

- **urgent** — needs immediate attention
- **important** — should respond today
- **routine** — can wait

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `gmail_token_path` | `config/gmail-token.json` | OAuth token file |
| `credentials_path` | `config/gmail-credentials.json` | OAuth client config |
| `lookback_hours` | `24` | How far back to fetch |
| `max_results` | `50` | Maximum emails to return |

## Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client