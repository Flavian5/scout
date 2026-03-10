# C2C Job Scrapers - Setup Guide

This directory contains scrapers for C2C (Contract-to-Contract) and freelance job opportunities. All scrapers use a **shared library** (`shared.js`) for common functionality.

## Architecture

```
skills/c2c-scrapers/
├── shared.js          # Shared utilities (signal detection, normalization, filtering)
├── README.md          # This file
├── dice-scout/        # Dice.com scraper
├── cybercoders-scout/ # CyberCoders scraper
├── linkedin-c2c-scout/# LinkedIn C2C/Contract scraper
└── wellfound-scout/   # Wellfound scraper
```

## Shared Library Features

The `shared.js` module provides:

- **Signal Detection**: Identifies project-based vs staff augmentation opportunities
- **Rate Extraction**: Parses hourly and project rates from job postings
- **Job Normalization**: Standardizes job data across all sources
- **Filtering**: Filters jobs based on C2C criteria

### Signal Categories

**Project-Based Signals (GOOD - Filter FOR):**
- `project_sow` - Statement of Work
- `project_fixed_price` - Fixed-price/fixed fee
- `project_deliverable` - Deliverable-based
- `project_based` - Project-based engagement
- `consulting` - Consulting (not staffing)
- `implementation` - Implementation (not augmentation)
- `c2c` - Corp-to-Corp

**Staff Augmentation Signals (BAD - Filter OUT):**
- `staff_augmentation` - Staff augmentation
- `staffing` - Staffing agency
- `w2_employee` - W2/employee
- `through_agency` - Through agency/staffing

---

## Available Scrapers

| Scraper | Platform | Auth Required? | Priority |
|---------|----------|----------------|----------|
| `dice-scout` | Dice.com | Recommended | 1 |
| `linkedin-c2c-scout` | LinkedIn | Optional | 2 |
| `cybercoders-scout` | CyberCoders | Recommended | 3 |
| `wellfound-scout` | Wellfound | Optional | 4 |

---

## User Actions Required by Platform

### 1. Dice.com (PRIMARY C2C SOURCE)
**Priority: 1 | Action: Create account (recommended)**

1. Go to https://www.dice.com and create a free account
2. Search for your target jobs to establish a session
3. Get your session cookie:
   - Open browser DevTools (F12) → Application → Cookies → dice.com
   - Copy the `JSESSIONID` value
4. Add to `config/secrets.json`:
```json
"dice": {
  "session": "YOUR_JSESSIONID_HERE"
}
```

---

### 2. LinkedIn (C2C Jobs)
**Priority: 2 | Action: Optional - Get cookies**

1. Log into LinkedIn in your browser
2. Get cookies:
   - DevTools → Application → Cookies → linkedin.com
   - Copy `li_at` and `JSESSIONID` values
3. Add to `config/secrets.json`:
```json
"linkedin": {
  "li_at": "YOUR_LI_AT",
  "jsessionid": "YOUR_JSESSIONID"
}
```

**Note:** The scraper works without auth using public search.

---

### 3. CyberCoders
**Priority: 3 | Action: Create account (recommended)**

1. Go to https://www.cybercoders.com and create free account
2. Get session cookie from DevTools
3. Add to `config/secrets.json`:
```json
"cybercoders": {
  "session": "YOUR_SESSION_COOKIE"
}
```

---

### 4. Wellfound (Startup Contracts)
**Priority: 4 | Action: Optional - Refresh cookies if blocked**

Your `config/secrets.json` may already have Wellfound credentials:
```json
"wellfound": {
  "auth_token": "...",
  "cf_clearance": "...",
  "datadome": "...",
  "ajs_user_id": "..."
}
```

**Note:** The `cf_clearance` token may be expired. If blocked, log in and refresh cookies.

---

## Usage

### Install dependencies:

```bash
# For each scraper
cd skills/dice-scout && npm install
cd skills/cybercoders-scout && npm install
cd skills/linkedin-c2c-scout && npm install
cd skills/wellfound-scout && npm install
```

### Run a scraper:

```bash
# Basic usage
cd skills/dice-scout
node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco, CA"

# Filter for project-based only
node scrape.js --keywords "ML Platform" --project-based

# With output file
node scrape.js --keywords "ML Engineer" --output ../data/leads/dice_ml.json
```

### Common flags:
- `--keywords` / `-k`: Search keywords (required)
- `--location` / `-l`: Location (default varies by scraper)
- `--project-based`: Filter for project-based opportunities only
- `--limit` / `-L`: Max results (default: 50)
- `--output` / `-o`: Output file path
- `--remote-only` / `-r`: Remote jobs only

---

## Filtering

All scrapers now support `--project-based` flag which filters jobs using the shared library:

- Shows only jobs with project-based signals (SOW, fixed-price, consulting)
- Excludes jobs with staff augmentation signals (staffing, W2, through agency)

You can also use `filterJobs()` in your own code:

```javascript
const { filterJobs } = require('./c2c-scrapers/shared');

const filtered = filterJobs(jobs, {
  minRate: 100,              // Minimum hourly rate
  requireProjectBased: true, // Only project-based
  excludeStaffAugmentation: true
});
```

---

## Rate Requirements (from persona)

- **Project-Based**: $20K-200K per project
- **Hourly**: $100-150/hour USD minimum

The scrapers capture all jobs, but the analyst agent filters based on these requirements.

---

## Troubleshooting

### "Access Denied" / Cloudflare blocks
- Refresh cookies (they expire frequently)
- Try running scraper again later
- Use authenticated session

### No results found
- Check keywords are correct
- Try different location (e.g., "Remote" instead of specific city)
- Verify the job board is accessible from your network

### Rate limiting
- Add delays between requests (scrapers already have this)
- Use authenticated sessions
- Wait and retry later