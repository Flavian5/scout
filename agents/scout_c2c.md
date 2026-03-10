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
- **Minimum**: $125/hour USD
- **Preferred**: $150-250/hour USD
- **Project-based**: $25,000+ minimum

### Target Platforms (Priority Order)
1. **Braintrust** - Worker-owned, high rates, C2C-friendly (vetting takes ~2 weeks)
2. **A-Team** - Elite talent network, C2C available
3. **Wellfound** - Startup contracts
4. **LinkedIn** - Good for contract/C2C filter
5. **Toptal/Gun.io** - Premium (requires membership)
6. **Dice** - Fallback only (lower rates)

## Discovery Workflow (New Priority Order)

### Phase 1: Boutique AI Agency Job Boards (Daily)
1. Check Vector Institute partners program job board
2. Check A-List AI/ML staffing opportunities
3. Check Aylien NLP/AI specialist roles
4. Apply directly with tailored pitch

### Phase 2: Vetted Networks (Apply Now - 2 week vetting)
1. **Braintrust**: Submit application immediately (vetting takes ~2 weeks)
   - Application: https://braintrust.com/apply
   - Highlight: Twitter-scale experience, project-based delivery
2. **A-Team**: Submit application
   - Application: https://ateam.io/join
   - Focus: Elite talent, C2C-friendly

### Phase 3: Y Combinator Portal (Daily)
1. Navigate to https://www.workatastartup.com/
2. Search for contract/consulting roles
3. Filter by: ML Engineer, ML Platform, Recommendation
4. Extract: rate, equity, company stage, contract type

### Phase 4: CTO Cold Outreach (20 companies/week)
1. Identify AI-first startups needing ML platform help
2. Research CTO/technical leadership
3. Send personalized outreach (see templates)
4. Track in `data/cto_outreach.json`

### Phase 5: Wellfound Contract Search
1. Navigate to Wellfound contract jobs
2. Search for ML/RecSys keywords
3. Extract: rate, equity, company info

### Phase 6: LinkedIn Contract Search
1. Use authenticated browser session
2. Search with contract filters:
   - Keywords: "ML Engineer", "ML Platform", "RecSys"
   - Filter: "Contract" or "Corp-to-Corp"
3. Extract job details

### Phase 7: Toptal/Gun.io Networks
1. Check if profile matches their requirements
2. Search for relevant opportunities
3. Note: These require application, not direct apply

### Phase 8: Web Search for Contract Opportunities
Additional queries:
- "machine learning engineer contract corp-to-corp 2026"
- "ML platform consultant rate 150+ hourly 2026"
- "senior ML engineer independent contractor 2026"
- "machine learning contract role San Francisco Seattle 2026"

### Phase 9: Dice Search (Fallback Only)
1. Use `browser` to navigate Dice
2. Search for:
   - "Machine Learning Engineer contract"
   - "ML Platform Engineer C2C"
   - "Recommendation Systems contract"
3. Filter by:
   - Location: San Francisco, Seattle, Remote
   - Contract type: C2C, Corp-to-Corp, 1099
   - Posted: Last 2 days
4. Extract: Rate, duration, company, project details

## C2C-Specific Signal Detection

### Contract Type Signals:
- "contract", "C2C", "corp-to-corp", "1099", "independent contractor"
- "6 month", "12 month", "long-term contract", "project-based"

### Rate Signals:
- "$125", "$150", "$175", "$200", "$250", "hourly", "rate"
- Filter OUT roles below $125/hour

### Project Type Signals:
- **Roadmapping**: Strategic planning, architecture design
- **Agentic Projects**: Building AI agents, autonomous systems (common for C2C)
- **GenRec Projects**: Generative recommendation implementation
- **ML Platform**: Feature stores, model serving infrastructure
- **Data Pipelines**: Common C2C work, not a differentiator
- **Prototyping**: Rapid prototyping, POCs (very common for C2C contracts)

### Company Signals:
- Large tech: Amazon, Meta, Google, Netflix, Uber, Airbnb
- AI-first startups: CZI, Recursion, Insitro, Arc Institute
- Y Combinator startups
- Consulting: Accenture, Deloitte, Cognizant

## Output Format

```json
{
  "job_id": "uuid",
  "source": "braintrust|ateam|wellfound|linkedin|toptal|gunio|dice|web_search|yc_portal|cto_outreach",
  "company": "Company Name",
  "role_title": "ML Platform Engineer - Contract",
  "location": "Remote",
  "application_url": "https://...",
  "job_description_raw": "Full JD text...",
  "contract_details": {
    "rate_type": "hourly|project",
    "rate_min": 125,
    "rate_max": 250,
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

1. **Rate Filter First**: Immediately filter out roles below $125/hour
2. **Duration Minimum**: Prefer 6+ month engagements
3. **No Duplicates**: Dedupe by (company + role_title + url)
4. **Capture Project Type**: Identify roadmapping, agentic, genrec, platform projects
5. **Recent Focus**: Prioritize roles posted within 2 days
6. **Braintrust/A-Team Priority**: Apply to vetted networks first (long vetting time)

## Contract Type Priority

| Priority | Type | Notes |
|----------|------|-------|
| 1 | Project-based ($25k+) | Best for scoped work |
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