# Skill: wellfound-scout

## Description
Wellfound (formerly AngelList Talent) job scraper for startup roles. Particularly valuable for finding early-stage Bio-AI and AI-first biotech companies that may not post on LinkedIn.

## Capabilities
- `browser` - Navigate Wellfound job listings
- Extract job details: title, company, location, equity, salary, description
- Identify startup stage (seed, Series A, B, etc.)
- Detect funding rounds and investor signals
- Extract team size and engineering culture signals

## Configuration

### Required Environment Variables
```bash
WELLFOUND_AUTH_TOKEN="your_auth_token"
```

### Storage Location
Cache stored in: `~/.openclaw/skills/wellfound-scout/cache.json`

## Usage

### From OpenClaw
```
Use wellfound-scout to find Staff ML Engineer roles at Series A Bio-AI startups
```

### Direct Command
```bash
cd skills/wellfound-scout
node scrape.js --keywords "Machine Learning Engineer" --stage "Series A" --category "Biotech"
```

## Output Format

```json
{
  "source": "wellfound",
  "job_id": "wellfound_uuid",
  "company": "Recursion Pharmaceuticals",
  "role_title": "Staff Machine Learning Engineer",
  "location": "Remote (US)",
  "application_url": "https://wellfound.com/jobs/...",
  "job_description_raw": "Full JD text...",
  "salary_range": "$200k - $280k",
  "equity": "0.1% - 0.25%",
  "startup_stage": "Series C",
  "team_size": "200-500",
  "funding": "$600M+",
  "detected_signals": ["virtual_cell", "digital_twin", "drug_discovery"],
  "scraped_at": "2026-03-07T04:05:00Z"
}
```

## Error Handling

| Error | Handling |
|-------|----------|
| Auth expired | Refresh token, notify user |
| Rate limited | Exponential backoff (30s, 60s, 120s) |
| No results | Return empty with search params logged |

## Dependencies
- playwright
- dotenv
- uuid

## Target Companies
Use with config/sourcing.json Bio-AI companies that are startup-focused:
- Recursion Pharmaceuticals
- Insitro
- Arc Institute
- Second Renaissance
- Other emerging Bio-AI startups