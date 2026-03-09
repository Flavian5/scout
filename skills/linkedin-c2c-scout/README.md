# Skill: linkedin-scout

## Description
Custom Playwright-based LinkedIn job scraper that uses authenticated session cookies to bypass anti-bot measures. Extracts job postings using LLM vision capabilities to parse the dynamic DOM.

## Capabilities
- `browser` - Navigate LinkedIn with authenticated session
- Extract job details: title, company, location, salary, description
- Handle pagination and filtering
- Session cookie refresh detection

## Configuration

### Required Environment Variables
```bash
LINKEDIN_LI_AT="your_li_at_cookie"
LINKEDIN_JSESSIONID="your_jsessionid_cookie"
```

### Storage Location
Cookies stored in: `~/.openclaw/skills/linkedin-scout/cookies.json`

## Usage

### From OpenClaw
```
Use linkedin-scout to find Staff ML Engineer roles in San Francisco
```

### Direct Command
```bash
cd skills/linkedin-scout
node scrape.js --keywords "Staff Machine Learning Engineer" --location "San Francisco Bay Area"
```

## Output Format

```json
{
  "source": "linkedin",
  "job_id": "linkedin_uuid",
  "company": "CZI",
  "role_title": "Staff Machine Learning Engineer",
  "location": "San Francisco, CA",
  "application_url": "https://linkedin.com/jobs/view/...",
  "job_description_raw": "Full JD text...",
  "salary_range": "$250k - $350k",
  "posted_date": "2026-03-06",
  "easy_apply": false,
  "detected_signals": ["virtual_cell", "foundation_models"],
  "scraped_at": "2026-03-07T04:05:00Z"
}
```

## Error Handling

| Error | Handling |
|-------|----------|
| Cookie expired | Send notification to update credentials |
| Rate limited | Wait 60s, retry with reduced frequency |
| No results | Return empty array, log search params |

## Dependencies
- playwright
- dotenv
- uuid