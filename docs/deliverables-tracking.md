# Deliverables Tracking

## Overview

The Deliverables database tracks work outputs and links them to Linear tickets for end-to-end traceability.

## Database Schema

**Database ID:** `34226d8a-7d26-81c0-9f8b-c8711f3ee4e6`

| Field | Type | Description |
|-------|------|-------------|
| Name | title | Deliverable title |
| Type | select | Document, Code, Research, Design, Other |
| Status | select | Draft, In Review, Published, Archived |
| Linear Ticket | url | Link to Linear ticket |
| Due Date | date | Deadline |
| Completed Date | date | When work was finished |
| Description | rich_text | Detailed description |
| Tags | multi_select | Searchable tags |

## Linking Pattern

When completing a Linear ticket that produces a deliverable:

1. Create page in Deliverables database
2. Link `Linear Ticket` field to ticket URL (e.g., `https://linear.app/scout-personal/issue/SEM-97`)
3. Set appropriate `Type` and `Status`
4. Add descriptive `Tags` for searchability

## Usage Examples

### Mark Deliverable Complete

```python
# After completing Linear ticket
notion_page = create_page(
    parent_id="34226d8a-7d26-81c0-9f8b-c8711f3ee4e6",
    properties={
        "Name": {"title": [{"text": {"content": "Deliverables Tracking Docs"}}]},
        "Type": {"select": {"name": "Document"}},
        "Status": {"select": {"name": "Published"}},
        "Linear Ticket": {"url": "https://linear.app/scout-personal/issue/SEM-97"},
        "Completed Date": {"date": {"start": "2026-04-14"}},
        "Tags": {"multi_select": [{"name": "documentation"}]}
    }
)
```

### Query Deliverables by Ticket

Use `linear_ticket:"SEM-97"` filter to find all deliverables linked to a specific ticket.

## Integration with Heartbeat

The heartbeat can check for overdue deliverables by querying the Deliverables database for items where:
- `Due Date` < today
- `Status` not in [Published, Archived]

## Related

- [Research Archive Workflow](./research-archive-workflow.md) - Archiving old deliverables
- [Daily Briefing](./daily-briefing-template.md) - How deliverables appear in briefings