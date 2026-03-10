# Skill: cto-search

## Description
Find CTOs, VP Engineering, and technical decision makers at companies with C2C budget for ML platform consulting. Uses LinkedIn and web search to discover and verify targets.

## Capabilities
- `linkedin-scout` - Find technical leadership profiles
- `web_search` - Search for company funding, ML initiatives, technical leadership
- `company-research` - Verify company stage and budget signals
- `browser` - Navigate company pages to find leadership info

## Target Criteria

### Company Requirements (C2C Budget)
- **Stage**: Series C+ or 100+ employees
- **Funding**: $50M+ raised
- **Indicators**: Active ML hiring, established contractor programs

### Industries
- AI-first companies
- Bio-AI / Virtual Cell (CZI, Recursion, Insitro, etc.)
- Voice AI / Agentic systems
- RecSys-heavy platforms (TikTok, Netflix, Spotify)
- Large tech (for contract roles)

### Roles
- CTO
- VP Engineering
- Head of ML/AI
- Chief AI Officer
- VP Data Science

## Usage

### From OpenClaw
```
Use cto-search to find CTOs at Series C+ AI companies
Use cto-search to find VP Engineering at Bio-AI companies
```

### Direct Command
```bash
cd skills/cto-search
node search.js --company "Recursion Pharmaceuticals"
node search.js --industry "bio-ai"
```

## Output Format

```json
{
  "target_id": "uuid",
  "company": "Company Name",
  "company_stage": "Series C",
  "company_industry": "Bio-AI",
  "funding_total": "$150M",
  "contact": {
    "name": "John Doe",
    "title": "CTO",
    "linkedin_url": "https://linkedin.com/in/...",
    "found_via": "linkedin_search"
  },
  "budget_signals": {
    "ml_job_postings": true,
    "funding_amount": "$150M",
    "ml_team_size": "10-20"
  },
  "qualification_score": 85,
  "discovered_at": "2026-03-09T04:00:00Z"
}
```

## Search Strategies

### 1. LinkedIn Profile Search
- Query: "site:linkedin.com/in [Company] CTO"
- Query: "site:linkedin.com/in [Company] VP Engineering"
- Query: "[Company] Head of ML LinkedIn"

### 2. Company Leadership Pages
- Visit company "About" or "Team" page
- Search for technical leadership

### 3. Funding/News Search
- "[Company] Series C funding"
- "[Company] ML platform announcement"
- "[Company] AI initiative 2025"

## Configuration

### Required Secrets
None - uses public search and LinkedIn scraper

### Optional
- LinkedIn cookies for enhanced search (see linkedin-scout)

## Dependencies
- playwright (via linkedin-scout)
- web search (built-in)