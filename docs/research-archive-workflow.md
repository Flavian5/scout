# Research Archive Workflow - SEM-96

## Overview

This document specifies the workflow for archiving research findings to Notion so that knowledge is preserved and searchable.

## Trigger Conditions

### Manual Trigger
- User requests "archive this research about X"
- Web search results need to be saved for later
- After completing a research task in Linear

### Automatic Trigger
- When any web search is performed and results are deemed useful
- When Linear ticket with "Research" label is completed

## Page Structure

Each research entry in Notion has:

### Required Fields
- **Name**: Title/summary of research topic
- **Topic**: Category (AI, ML, Tech, Business, Market, Other)
- **Source**: URL where research was found
- **Summary**: Key findings and takeaways
- **Date**: When research was captured
- **Tags**: Multi-select for quick filtering

### Optional Fields
- **Relevance**: High/Medium/Low rating
- **Linked Tickets**: Linear ticket IDs related to this research

## Push Mechanism

### Via Notion MCP
```python
# Use notion.py create_page() with research_schema()
from skills.notion.schemas import research_schema

page_data = {
    'title': research_title,
    'topic': topic_category,
    'source': source_url,
    'summary': key_findings,
    'tags': ['relevant', 'tags']
}
```

### Via Direct API
```bash
POST https://api.notion.com/v1/pages
Authorization: Bearer {notion_token}
Notion-Version: 2022-06-28

{
  "parent": {"database_id": "34126d8a-7d26-816a-8703-fc6430482336"},
  "properties": {...},
  "children": [...]
}
```

## Retention & Update Policy

1. **Retention**: Research entries are kept indefinitely
2. **Updates**: Can update summary/tags but source is immutable
3. **Review**: Quarterly review to mark stale entries as Archived
4. **Cleanup**: Entries older than 2 years with no tags get auto-archived

## Data Flow

```
User Request → LLM decides to archive → Extract topic/source/summary
                                    → Call notion.create_page()
                                    → Log to agent-trace.jsonl
                                    → Confirm to user via Discord
```

## Integration Points

- **Linear**: Links to Research-labeled tickets
- **Discord**: Confirmation when research archived
- **Heartbeat**: Can trigger archive of last search results

## Example Usage

```
User: "archive this research about AI agents"
Bot:  Creating Notion page...
Bot:  [Research] AI Agents saved to Notion
      https://notion.so/workspace/research-ai-agents
```

## File Locations

- Schema: `skills/notion/schemas.py` (research_schema)
- API: `skills/notion/notion.py` (create_page)
- Database ID: `34126d8a-7d26-816a-8703-fc6430482336`