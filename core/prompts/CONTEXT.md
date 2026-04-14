# CONTEXT.md — Dynamic Context Template

_This template is hydrated with current data before every LLM call. Do not cache._

## Temporal Context

**Current Time**: {{CURRENT_TIME}}
**Date**: {{CURRENT_DATE}}
**Day of Week**: {{DAY_OF_WEEK}}
**Quiet Hours**: {{IS_QUIET_HOURS}} (23:00–08:00)

## Recent Memory

### Today ({{TODAY_DATE}})
```
{{TODAY_MEMORY}}
```

### Yesterday ({{YESTERDAY_DATE}})
```
{{YESTERDAY_MEMORY}}
```

_Last 3-5 significant items from MEMORY.md if relevant to request_

## Today's Schedule

{{#if HAS_EVENTS_TODAY}}
**Upcoming Events** ({{EVENT_COUNT}} today):
{{EVENTS_LIST}}
{{/if}}
{{#unless HAS_EVENTS_TODAY}}
No events scheduled for today.
{{/unless}}

## Email Status

**Unread**: {{UNREAD_EMAIL_COUNT}}
{{#if HAS_URGENT_EMAILS}}
**Urgent** ({{URGENT_EMAIL_COUNT}}):
{{URGENT_EMAILS}}
{{/if}}

## Linear Tickets

**Open**: {{OPEN_TICKET_COUNT}}
{{#if HAS_P0_TICKETS}}
**P0 (Urgent)**: {{P0_TICKETS}}
{{/if}}
{{#if HAS_P1_TICKETS}}
**P1 (High)**: {{P1_TICKETS}}
{{/if}}

## Active Integrations

| Service | Status | Notes |
|---------|--------|-------|
| Discord | ✅ Active | Primary communication |
| Linear MCP | ✅ Connected | Task management |
| Notion MCP | ✅ Connected | Life management hub (8 databases) |
| Gmail API | {{GMAIL_STATUS}} | {{GMAIL_NOTES}} |
| Google Calendar | {{CALENDAR_STATUS}} | {{CALENDAR_NOTES}} |

## Recent Activity

{{RECENT_ACTIVITY}}

---

_Context hydrated: {{HYDRATION_TIMESTAMP}}_