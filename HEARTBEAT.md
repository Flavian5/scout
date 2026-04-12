# Heartbeat Reminders

Last updated: 2026-04-01

## Notes

- 2026-04-01: Scout ran via DuckDuckGo/BuiltInSF (LinkedIn still blocked). Got 20 leads, saved to data/leads/raw_leads.json. Analyst ran - all 20 failed threshold (scores 2.65-19.32, all unknown_tier). Issue: BuiltInSF anonymizes company names, can't match criteria.json tier lists. Need actual company names.
- 2026-03-24: Analyst ran - 20 leads scored, 0 met threshold (all ❌)
- Scout and Analyst agents ran successfully on 2026-03-13, found 24 job leads
- LinkedIn scraper via web search (not Chrome CDP) works fine
- 2026-03-18/19: LinkedIn scraper failing with ERR_TOO_MANY_REDIRECTS - LinkedIn blocking automation
- Current leads: 0 High/Medium priority (all scored leads failed threshold)
- Alternative: Use web search for job leads instead of LinkedIn scraper
- 2026-04-02: LinkedIn scraper still failing (ERR_TOO_MANY_REDIRECTS). Alternative: use web search. Analyst ran - 20 leads scored, all ❌ (threshold not met). Strategist: skipped (0 High priority leads)
- 2026-04-10: Scout failed (LinkedIn blocked). Analyst ran - all ❌. Strategist: skipped (0 High priority). Issue: anonymized company names can't match criteria.json