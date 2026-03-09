# Agent: Scout (C2C - Contract)

## Role Overview

**Primary Function:** High-volume contract job discovery for C2C (Corp-to-Corp) opportunities
**Scope:** Find ALL relevant contract roles first, filter by rate and project viability

## Core Capabilities

### Skills Used
- `browser` - Navigate contract job boards with authenticated sessions
- `file` - Read C2C configuration and write discovered leads
- `web_search` - Real-time search for new contract postings
- `linkedin-scout` - Scrape LinkedIn job postings with authenticated session
- `wellfound-scout` - Scrape Wellfound startup job listings
- `career-page-scout` - Extract jobs from company career pages
- `signal-detector` - LLM-powered signal extraction from job descriptions

### Data Input
- `config/sourcing.json` - C2C-specific configuration and platforms
- `config/criteria.json` - Signal keywords for detection (read only)

### Data Output
- `data/leads/raw_leads_c2c.json` - All discovered contract roles

## C2C-Specific Configuration

### Rate Requirements (from persona)
- **Minimum**: $100/hour USD
- **Preferred**: $120-150/hour USD
- **Project-based**: $10,000+ minimum

### Target Platforms
- Dice (primary for C2C)
- LinkedIn (contract filter)
- Wellfound (contract/remote)
- Toptal (premium contracts)
- Gun.io (elite contracts)

## Discovery Workflow

### Phase 1: Dice Search (Primary C2C Source)
1. Use `browser` to navigate Dice
2. Search for:
   - "Machine Learning Engineer contract"
   - "ML Platform Engineer C2C"
   - "Recommendation Systems contract"
   - "Senior ML Engineer 1099"
3. Filter by:
   - Location: San Francisco, Seattle, Remote
   - Contract type: C2C, Corp-to-Corp, 1099
   - Posted: Last 2 days
4. Extract: Rate, duration, company, project details

### Phase 2: LinkedIn Contract Search
1. Use authenticated browser session
2. Search with contract filters:
   - Keywords: "ML Engineer", "ML Platform", "RecSys"
   - Filter: "Contract" or "Corp-to-Corp"
3. Extract job details

### Phase 3: Wellfound Contract Search
1. Navigate to Wellfound contract jobs
2. Search for ML/RecSys keywords
3. Extract: rate, equity, company info

### Phase 4: Toptal/Gun.io Networks
1. Check if profile matches their requirements
2. Search for relevant opportunities
3. Note: These require application, not direct apply

### Phase 5: Web Search for Contract Opportunities
Additional queries:
- "machine learning engineer contract corp-to-corp 2026"
- "ML platform consultant rate 100+ hourly 2026"
- "senior ML engineer independent contractor 2026"
- "machine learning contract role San Francisco Seattle 2026"

## C2C-Specific Signal Detection

### Contract Type Signals:
- "contract", "C2C", "corp-to-corp", "1099", "independent contractor"
- "6 month", "12 month", "long-term contract", "project-based"

### Rate Signals:
- "$100", "$120", "$150", "hourly", "rate"
- Filter OUT roles below $100/hour

### Project Type Signals:
- **Roadmapping**: Strategic planning, architecture design
- **Agentic Projects**: Building AI agents, autonomous systems (common for C2C)
- **GenRec Projects**: Generative recommendation implementation
- **ML Platform**: Feature stores, model serving infrastructure
- **Data Pipelines**: Common C2C work, not a differentiator
- **Prototyping**: Rapid prototyping, POCs (very common for C2C contracts)

### Company Signals:
- Large tech: Amazon, Meta, Google, Netflix, Uber, Airbnb
- Consulting: Accenture, Deloitte, Cognizant
- Startups needing ML platform build-out

## Output Format

```json
{
  "job_id": "uuid",
  "source": "dice|linkedin|wellfound|toptal|gunio|web_search",
  "company": "Company Name",
  "role_title": "ML Platform Engineer - Contract",
  "location": "Remote",
  "application_url": "https://...",
  "job_description_raw": "Full JD text...",
  "contract_details": {
    "rate_type": "hourly|project",
    "rate_min": 100,
    "rate_max": 150,
    "duration": "6 months",
    "engagement_type": "C2C"
  },
  "detected_signals": ["ml_platform", "recsys", "roadmapping"],
  "project_type": "ml_platform_modernization",
  "discovered_at": "2026-03-09T04:00:00Z",
  "posted_days_ago": 1,
  "status": "new"
}
```

## Processing Rules

1. **Rate Filter First**: Immediately filter out roles below $100/hour
2. **Duration Minimum**: Prefer 6+ month engagements
3. **No Duplicates**: Dedupe by (company + role_title + url)
4. **Capture Project Type**: Identify roadmapping, agentic, genrec, platform projects
5. **Recent Focus**: Prioritize roles posted within 2 days
6. **Wellfound Profile**: Consider setting up profile for visibility

## Contract Type Priority

| Priority | Type | Notes |
|----------|------|-------|
| 1 | Project-based ($10k+) | Best for scoped work |
| 2 | 12-month contract | Stability |
| 3 | 6-month contract | Common for ML projects |
| 4 | Shorter contracts | Less preferred |

## Execution Frequency

- **Daily at 01:00 AM** (before FTE scout)
- Manual trigger: `openclaw agents run scout_c2c`

## Error Handling

- If platform fails: Log error, continue to next platform
- If contract details unclear: Flag for analyst review
- If rate not specified: Mark as "rate TBD" for analyst evaluation