# Scout Agent Setup Guide

This document outlines what's been created and what steps are needed to get the autonomous job search agent running.

---

## What's Been Created

### Configuration Files
| File | Purpose |
|------|---------|
| `.gitignore` | Excludes secrets, cookies, logs, and generated data |
| `config/secrets.json` | **Template** - Fill in your API keys and cookies |
| `openclaw.json` | OpenClaw runtime configuration with agent schedules |

### Data Files
| File | Purpose |
|------|---------|
| `data/cv_base.md` | Base CV template with Jinja2-style placeholders |
| `data/cover_letter_base.md` | Base cover letter template |
| `data/contract_proposal_base.md` | C2C contract proposal template |
| `data/leads/raw_leads.json` | Empty array for Scout FTE output |
| `data/leads/enriched_leads.json` | Empty array for Analyst FTE output |
| `data/leads/raw_leads_c2c.json` | Empty array for Scout C2C output |
| `data/leads/enriched_leads_c2c.json` | Empty array for Analyst C2C output |
| `applications/archive/.gitkeep` | Archive directory placeholder |

---

## What's Missing (Required for Operation)

### 1. Secrets Configuration
Copy and fill in `config/secrets.json`:

```bash
cp config/secrets.json config/secrets.json.bak
# Edit config/secrets.json with your actual values
```

Required secrets:
- **LinkedIn cookies**: Get from browser DevTools → Application → Cookies → linkedin.com
  - `li_at` cookie value
  - `JSESSIONID` cookie value
- **LLM API key**: Anthropic (recommended) or OpenAI
- **Notification webhook**: Discord or Telegram bot

### 2. Skill Implementations
The skill directories currently only have README.md files. The actual scraping/analysis logic needs to be implemented:

| Skill | Status | Priority |
|-------|--------|----------|
| `linkedin-scout/` | README only | **High** |
| `wellfound-scout/` | README only | High |
| `signal-detector/` | README only | High |
| `asset-generator/` | README only | High |
| `company-research/` | Empty | Medium |
| `career-page-scout/` | Empty | Medium |
| `ats-scout/` | Empty | Low |

### 3. OpenClaw Installation
Following the setup guide in `docs/setup.md`:

```bash
# Install OpenClaw CLI
curl -fsSL https://openclaw.ai/install.sh | bash

# Run onboarding
openclaw onboard --install-daemon

# Initialize project
cd /Users/haomeng/dev/scout
openclaw init
```

---

## Quick Start Checklist

- [ ] Fill in `config/secrets.json` with actual API keys and cookies
- [ ] Install OpenClaw CLI
- [ ] Run `openclaw doctor` to verify setup
- [ ] Test LinkedIn scraper with a single query
- [ ] Configure notification webhook (Discord/Telegram)
- [ ] Set up daily heartbeat schedule

---

## Daily Heartbeat Schedule

Based on `openclaw.json`:

| Time | Agent | Task |
|------|-------|------|
| 01:00 AM | Scout C2C | Find contract roles |
| 01:30 AM | Analyst C2C | Score contract roles |
| 02:00 AM | Scout (FTE) | Find full-time roles |
| 02:30 AM | Analyst (FTE) | Score full-time roles |
| 03:00 AM | Strategist | Generate application packages |
| 08:00 AM | Notification | Send Daily Heartbeat to user |

---

## Testing Without Full Credentials

You can test the pipeline with mock data:

1. Create test leads in `data/leads/raw_leads.json`:
```json
[
  {
    "job_id": "test-001",
    "company": "Netflix",
    "role_title": "Staff ML Engineer",
    "location": "Los Gatos, CA",
    "job_description_raw": "Build recommendation systems...",
    "detected_signals": ["recsys", "two_stage_ranking"]
  }
]
```

2. Run Analyst manually:
```bash
openclaw agents run analyst --manual
```

3. Check enriched output in `data/leads/enriched_leads.json`

---

## Next Steps

1. **Immediate**: Fill in `config/secrets.json`
2. **Before running**: Implement at least one skill (linkedin-scout recommended)
3. **Verification**: Run dry test with mock data
4. **Automation**: Set up full OpenClaw daemon

---

## Files Reference

- **Agent definitions**: `agents/*.md`
- **Configuration**: `config/*.json`, `config/*.md`
- **Skills**: `skills/*/README.md`
- **Documentation**: `docs/*.md`