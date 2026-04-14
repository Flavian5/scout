# Testing Phases 3 & 4

## Phase 3: Manual Discord Testing (User - You)

These are real-world scenarios to test by interacting with the bot on Discord:

| # | Use Case | Steps | Expected Result |
|---|----------|-------|----------------|
| 1 | Email Check | Send "check my emails" in Discord | Bot responds with email summary (urgent/important counts) |
| 2 | Calendar Check | Send "what's on my calendar today" | Bot responds with today's events |
| 3 | Create Ticket | Send "create a ticket for fixing the login bug" | Linear ticket created, confirmation sent to Discord |
| 4 | Daily Briefing | Trigger heartbeat | Discord receives daily briefing with email + calendar + tickets |
| 5 | Calendar Reminder | Wait for event within 15 min | Discord receives reminder embed with Meet link |
| 6 | Web Search | Send "search for React 19 release notes" | Bot responds with search results |
| 7 | Ticket Status | Send "what tickets are in progress" | Bot responds with filtered Linear tickets |
| 8 | Notion Research | Send "save this to research: [URL]" | Notion page created in Research DB |
| 9 | Error Handling | Send invalid command | Bot responds gracefully, no crash |
| 10 | Quiet Hours | Send message during 23:00-08:00 | Bot responds but doesn't send proactive notifications |

## Phase 4: Smoke Tests (Quick Health Checks)

Run these after any deployment or major change:

```bash
# 1. Bridge server health
curl http://localhost:8080/health

# 2. Discord gateway health
curl http://localhost:3456/health

# 3. Discord webhook health
curl http://localhost:3001/health

# 4. gog CLI
gog gmail search 'newer_than:1d is:unread' --max 1
gog calendar events primary --from today --to tomorrow

# 5. All unit tests
pytest tests/ -v

# 6. Context hydrator
python core/prompts/hydrate.py --request "check my emails"
```

## Implementation Order (Reference)

1. Bridge server tests — Highest value, covers transport layer
2. Discord bot tests — Core user-facing functionality
3. Hydrator tests — Critical for prompt assembly
4. Signal detector tests — Simple, high coverage potential
5. Tool registry tests — Validates skill discovery
6. Live integration tests — Run only when APIs configured
7. Manual Discord testing — Real-world validation