# Linear Tickets Skill

Check and update Linear ticket statuses via GraphQL API.

## Commands

### Check Ticket Statuses
```bash
python skills/linear-tickets/check.py check
```
Lists all tracked tickets grouped by epic with their current state.

### Mark Tickets as Done
```bash
python skills/linear-tickets/check.py mark-done
```
Marks pre-defined implemented tickets as Done in Linear.

### Update Specific Ticket
```bash
python skills/linear-tickets/check.py update --id TICKET_ID --state STATE_ID
```

## Configuration

Requires `LINEAR_API_KEY` in `.env` file or environment variable.

## Tracked Tickets

- **Epic 4 - WhatsApp/Discord**: SEM-33 through SEM-40 (8 tickets)
- **Epic 5 - Notion**: SEM-27, SEM-28, SEM-29, SEM-30, SEM-47 (5 tickets)
- **Epic 6 - Gmail**: SEM-49, SEM-50, SEM-51, SEM-52, SEM-53 (5 tickets)
- **Epic 7 - Calendar**: SEM-54, SEM-55, SEM-56 (3 tickets)

## Ticket Definitions

| Ticket ID | Identifier | Description |
|-----------|------------|-------------|
| 14b1f257-7842-46d9-a16b-db4af7713d82 | SEM-33 | WhatsApp message notifications |
| 7ae14729-5c1f-4de2-99b9-b1719aab3af3 | SEM-34 | WhatsApp message formatting |
| 6b0f3616-4e66-4883-8b77-89c68d64d168 | SEM-35 | WhatsApp response handling |
| 2721c55e-869a-44b6-90d2-61288fa30659 | SEM-36 | WhatsApp error handling |
| 5e10321b-2bfc-4e4f-89af-0b49b21d733a | SEM-37 | WhatsApp session management |
| db06d4a3-7344-4ca7-be66-5cc754777b43 | SEM-38 | WhatsApp connection monitoring |
| b7af9d0d-cc08-4f9d-bbff-d8a296bfe73a | SEM-39 | WhatsApp message queuing |
| 1e105d4a-c55f-4fe7-9e57-025e7017c7ef | SEM-40 | WhatsApp integration tests |
| 8e8f6bb1-54fa-44ab-9202-82aeb1e0423b | SEM-27 | Calendar reminder notifications |
| afa4dc02-0c3d-4d3b-a681-6a788a0b20b7 | SEM-47 | Link Notion deliverables to tickets |
| f5b037ae-017f-4da5-884c-bcea83771773 | SEM-49 | Create Daily Briefing database |
| 6d4e8f22-91c3-4e8b-9a5f-7c3d2e1b8a4f | SEM-50 | Create Research database |
| e9f4c7b2-3d5a-4e8c-9b6f-1a4e8d7c3b5a | SEM-52 | Email urgency classification |
| 2d5f8e3c-7a4b-4c9d-8e5f-1a3c7b5d9e4f | SEM-53 | Email to Notion push |