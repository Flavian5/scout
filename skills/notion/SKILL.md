---
name: notion
description: Create and manage Notion pages for daily briefings and task tracking. Integrates with Discord for notifications and uses Linear for ticket management.
---

# Notion Integration Skill

Create and manage Notion pages programmatically via Notion API.

## Prerequisites

1. Notion API integration token
2. Parent page ID where databases will be created

## Quick Start

```bash
python skills/notion/notion.py --help
python skills/notion/notion.py --create-briefing    # Create daily briefing
python skills/notion/notion.py --list-pages         # List existing pages
```

## Authentication

Set `NOTION_TOKEN` in `config/secrets.json`:

```json
{
  "notion": {
    "token": "secret_xxx..."
  }
}
```

## Databases

### Daily Briefing Database

Created under the parent page with these properties:

| Property | Type | Description |
|---------|------|-------------|
| Date | Date | Briefing date |
| Email Summary | Text | Emails reviewed |
| Calendar Summary | Text | Events of the day |
| Tasks Completed | Text | Done items |
| Next Day Priorities | Text | Upcoming work |

## Usage

```python
from notion_client import NotionClient

client = NotionClient()
client.create_daily_briefing(
    date="2026-04-13",
    email_summary="3 urgent, 5 important",
    calendar_summary="2 meetings",
    tasks_completed="Finished P1 calendar tickets",
    next_day_priorities="Notion integration, priority execution"
)
```

## Dependencies

```bash
pip install requests