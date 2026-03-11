# Skill: linkedin-scout

## Description
LinkedIn Recommended Jobs Scraper - Uses authenticated session cookies to scrape job listings from LinkedIn's recommended feed. Clicks each job card and extracts full job descriptions from the right panel.

## Capabilities
- `browser` - Navigate LinkedIn with authenticated session
- Extract job details: title, company, location, salary, description
- Click-based JD extraction from job details panel
- Signal detection in job descriptions

## Configuration

### Required Environment Variables
```bash
LINKEDIN_LI_AT="your_li_at_cookie"
LINKEDIN_JSESSIONID="your_jsessionid_cookie"
```

### Storage Location
Cookies stored in: `config/secrets.json`

```json
{
  "linkedin": {
    "li_at": "your_li_at_cookie",
    "jsessionid": "your_jsessionid_cookie"
  }
}
```

## Usage

### Basic Usage
```bash
cd skills/linkedin-scout
node scrape.js --keywords "Machine Learning Engineer"
```

### Options
```bash
# Limit number of jobs to process
node scrape.js --keywords "ML Engineer" --max-jd 10

# Set location
node scrape.js --keywords "ML Engineer" --location "San Francisco Bay Area"

# Save to file
node scrape.js --keywords "ML Engineer" --output data/jobs.json

# Filter by experience level (4 = senior, 5 = director)
node scrape.js --keywords "ML Engineer" --experience 4

# Filter by work type (1 = onsite, 2 = remote, 3 = hybrid)
node scrape.js --keywords "ML Engineer" --work-type 2
```

## Output Format

```json
{
  "source": "linkedin",
  "job_id": "linkedin_1234567890",
  "company": "Pinterest",
  "role_title": "Sr. Staff Machine Learning Engineer, Homefeed",
  "location": "United States (Remote)",
  "application_url": "https://www.linkedin.com/jobs/view/4275256717/",
  "job_description_raw": "About Pinterest... What You'll Do...",
  "salary_range": "$227,871—$469,147 USD",
  "posted_date": null,
  "job_type": "FTE",
  "detected_signals": ["recsys", "foundation_models"],
  "scraped_at": "2026-03-11T14:00:00Z"
}
```

## Detected Signals

The scraper automatically detects the following signals in job descriptions:

- **recsys**: Recommendation systems
- **two_stage_ranking**: Two-stage ranking
- **genrec**: Generative recommendation
- **foundation_models**: LLMs, transformers
- **virtual_cell**: Virtual cell / cellular biology
- **drug_discovery**: Drug discovery
- **bio_ai**: Computational biology
- **ml_platform**: ML platform / infrastructure
- **feature_store**: Feature store
- **ml_pipeline**: ML pipelines
- **voice_agent**: Voice AI agents
- **cx_automation**: Customer experience automation

## Error Handling

| Error | Handling |
|-------|----------|
| Cookie expired | Exit with error to update credentials |
| Rate limited | Exit with error |
| No job cards found | Exit with error - LinkedIn may have blocked |

## Dependencies
- playwright
- uuid