# Email Check Skill

Gmail inbox monitoring with urgency classification and notifications.

## Setup

### 1. Enable Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Search for "Gmail API" and enable it
4. Go to **APIs & Services > Credentials**
5. Click **Create Credentials > OAuth client ID**
6. Application type: **Desktop app**
7. Download the JSON file
8. Save it as `config/gmail-credentials.json`

### 2. Install Dependencies

```bash
pip install google-auth google-auth-oauthlib google-api-python-client requests
```

### 3. Authenticate

```bash
python skills/email-check/check.py --auth
```

This will open a browser for Google sign-in. Token saved to `config/gmail-token.json`.

### 4. Test Fetch

```bash
python skills/email-check/check.py --fetch
```

## Usage

```bash
# Fetch unread emails from last 24h
python skills/email-check/check.py --fetch

# Fetch and classify urgency
python skills/email-check/check.py --fetch --classify

# Send urgent alerts via WhatsApp
python skills/email-check/check.py --fetch --classify --urgent-alert

# Push digest to Notion
python skills/email-check/check.py --fetch --classify --push-notion
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `--hours` | 24 | Hours to look back |
| `--max` | 50 | Maximum emails to fetch |

## Files

```
skills/email-check/
├── SKILL.md       # Skill documentation
├── check.py       # Main script
├── _meta.json     # Skill metadata
└── README.md      # This file
```

## Output

Results saved to `data/email_fetch.json`:

```json
{
  "emails": [
    {
      "id": "msg123",
      "sender": "boss@company.com",
      "subject": "Urgent: Project deadline",
      "snippet": "We need the report by EOD...",
      "timestamp": "2026-04-12T14:30:00Z",
      "urgency": "urgent"
    }
  ],
  "summary": {
    "urgent": 1,
    "important": 2,
    "routine": 5
  }
}