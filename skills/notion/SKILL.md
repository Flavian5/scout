# Notion Integration Skill - SEM-94

Life management system via 8 Notion databases. Track chores, financials, projects, weekend plans, daily briefings, research, knowledge base, and deliverables.

## Commands

### Initialize Database
```bash
python skills/notion/notion.py init-database <database> --parent <page_id>
```

**Databases:** `chores`, `financials`, `projects`, `weekend-plans`, `daily-briefing`, `research`, `knowledge-base`, `deliverables`

### Create Entries

**Chore:**
```bash
python skills/notion/notion.py create-chore "Weekly laundry" \
  --frequency weekly --days "Sun" --time morning --priority must
```

**Financial:**
```bash
python skills/notion/notion.py create-financial "Groceries" \
  --category expense --subcategory food --amount 127.50 \
  --budget-line "Weekly groceries"
```

**Project:**
```bash
python skills/notion/notion.py create-project "Kitchen renovation" \
  --status active --category home --budget 15000 --target-end 2026-06-01
```

**Weekend Plan:**
```bash
python skills/notion/notion.py create-weekend "Hiking trip" \
  --date 2026-04-18 --category outdoor --people "Alex,Sam"
```

**Daily Briefing:**
```bash
python skills/notion/notion.py create-briefing \
  --email "3 urgent emails" --calendar "2 meetings" \
  --tasks "Completed API integration" --priorities "Review PR"
```

**Research:**
```bash
python skills/notion/notion.py create-research \
  --title "AI Agent Landscape 2026" --topic AI \
  --source https://example.com/research --summary "Analysis of 50 AI agent startups"
```

**Knowledge Entry:**
```bash
python skills/notion/notion.py create-knowledge \
  --name "Dev Environment Setup" --category setup \
  --content "Steps to set up the local dev environment..."
```

**Deliverable:**
```bash
python skills/notion/notion.py create-deliverable \
  --name "Q1 Strategy Document" --type Document \
  --linear https://linear.app/scout/tickets/SEM-100 \
  --due-date 2026-04-20
```

### Query & List

```bash
# List all pages in a database
python skills/notion/notion.py list-pages --name chores

# Query with filter
python skills/notion/notion.py query chores --filter "Status:todo"
```

## Trigger Routing

| User Input | Command | Database |
|------------|---------|----------|
| "add chore: X weekly on Y" | `create-chore` | chores |
| "mark X as done" | `update-chore` (status=done) | chores |
| "what chores today?" | `query chores` | chores |
| "spent $X on Y" | `create-financial` | financials |
| "budget status" | `query financials` (aggregate) | financials |
| "track expense: X" | `create-financial` | financials |
| "project status: X" | `query projects` | projects |
| "how's X going?" | `query projects` | projects |
| "what's planned this weekend?" | `query weekend-plans` | weekend-plans |
| "add weekend plan: X" | `create-weekend` | weekend-plans |
| "summarize my day" | `create-briefing` | daily-briefing |
| "show yesterday's briefing" | `query daily-briefing` | daily-briefing |
| "archive this research" | `create-research` | research |
| "find my research on X" | `query research` | research |
| "how do I set up X?" | `query knowledge-base` | knowledge-base |
| "document X" | `create-knowledge` | knowledge-base |
| "log this deliverable" | `create-deliverable` | deliverables |

## Database Schemas

### Chores
- Name (title)
- Frequency (select: daily/weekly/monthly/one-off)
- Day(s) (multi_select)
- Status (select: todo/done/skipped)
- Due Date (date)
- Recurring Time (select: morning/afternoon/evening/anytime)
- Est. Minutes (number)
- Priority (select: must/should/nice-to-have)
- Last Done (date)
- Notes (rich_text)

### Financials
- Name (title)
- Category (select: income/expense/savings/investment/debt)
- Subcategory (select: housing/food/transport/utilities/fun/health/tech)
- Amount (number)
- Date (date)
- Recurring (select: monthly/biweekly/one-off)
- Budget Line (rich_text)
- Receipt (url)
- Notes (rich_text)

### Projects
- Name (title)
- Status (select: planning/active/paused/done/abandoned)
- Category (select: home/career/health/learning/side-project)
- Start Date, Target End, Actual End (date)
- Budget, Spent (number)
- Progress (number: 0-100)
- Next Milestone, Notes (rich_text)

### Weekend Plans
- Name (title)
- Date, End Date (date)
- Location (rich_text)
- People (multi_select)
- Status (select: idea/planned/confirmed/done/canceled)
- Category (select: outdoor/social/errands/relaxation/travel)
- Cost (number)
- Notes (rich_text)

### Daily Briefing
- Name (title)
- Date (date)
- Email Summary, Calendar Summary, Tasks Completed (rich_text)
- Next Day Priorities, Urgent Tickets (rich_text)

### Research
- Name (title)
- Topic (select: AI/ML/Tech/Business/Market/Other)
- Source (url), Summary (rich_text)
- Date (date), Tags (multi_select)
- Relevance (select: High/Medium/Low)

### Knowledge Base
- Name (title)
- Category (select: architecture/setup/api/troubleshooting/reference)
- Content (rich_text)
- Last Updated (date), Tags (multi_select)

### Deliverables
- Name (title)
- Type (select: Document/Code/Research/Design/Other)
- Status (select: Draft/In Review/Published/Archived)
- Linear Ticket (url)
- Due Date, Completed Date (date)
- Description (rich_text), Tags (multi_select)

## Configuration

Add to `config/secrets.json`:
```json
{
  "notion": {
    "token": "secret_xxx",
    "chores_db": "xxx",
    "financials_db": "xxx",
    "projects_db": "xxx",
    "weekend_plans_db": "xxx",
    "daily_briefing_parent": "xxx",
    "research_db": "xxx",
    "knowledge_base_db": "xxx",
    "deliverables_db": "xxx"
  }
}
```

Get token from: https://www.notion.so/my-integrations

## Status

- **SEM-94**: Database schemas and CLI commands complete
- **Next**: Update SKILLS.md, hydrate.py, CONTEXT.md, openclaw.json