# Discord Bot Skill - SEM-45, SEM-47

Parse Discord requests into Linear tickets and link Notion deliverables to tickets.

## Commands

### Parse Discord Request (SEM-45)
```bash
python skills/discord-bot/check.py parse --request "create a ticket for updating my resume"
```

Parses natural language requests into Linear tickets with:
- Title (actionable, max 60 chars)
- Description (user story)
- Priority (P0-P4 based on urgency keywords)
- Labels (category labels)

### Link Notion Page to Ticket (SEM-47)
```bash
python skills/discord-bot/check.py link --ticket-id TICKET_ID --notion-url "https://notion.so/..."
```

Adds Notion page link to Linear ticket description.

### Create Notion Deliverable
```bash
python skills/discord-bot/check.py create-deliverable \
  --title "Project Research" \
  --database DATABASE_ID \
  --ticket-id TICKET_ID \
  --ticket-identifier SEM-45
```

Creates a Notion page in the specified database and links it to a Linear ticket.

## Configuration

Requires in `config/secrets.json`:
- `LINEAR_API_KEY` - Linear API key
- `llm_api` - MiniMax LLM config for parsing
- `discord_webhook` - Webhook for confirmations
- `notion.token` - Notion integration token

## Ticket Creation Flow

1. User sends request in Discord (e.g., "create a ticket for updating my resume")
2. Scout parses request using LLM → extracts title, description, priority, labels
3. Scout creates Linear ticket via GraphQL API
4. Scout sends confirmation to Discord webhook with ticket URL

## Notion Linking Flow

1. When creating Notion deliverable, specify `--ticket-id` and `--ticket-identifier`
2. Notion page is created with Linear ticket reference
3. Linear ticket description is updated with Notion page link
4. Bidirectional traceability established