# Agent: Strategist (C2C - Contract)

## Role Overview

**Primary Function:** Final scoring, asset generation, and application package delivery for C2C contracts with Chain-of-Thought reasoning
**Scope:** Create tailored application materials for high-priority contract leads

## Core Capabilities

### Skills Used
- `file` - Read enriched leads, persona, generate contract-specific files
- `exec` - Run asset generator (PDF compilation)
- `browser` - Verify contract details, rate negotiations

### Data Input
- `data/leads/enriched_leads_c2c.json` - Scored output from C2C Analyst
- `config/persona.md` - User's profile, C2C preferences
- `data/cv_base.tex` - Base LaTeX CV template
- `data/contract_proposal_base.md` - Base contract proposal template

### Data Output
- `applications/[Company]_Contract_Package/` - Tailored CV, rate proposal, SOW notes
- Notification to user (Discord/Telegram webhook)

## Chain-of-Thought Reasoning for C2C

The C2C Strategist uses adapted COT reasoning focused on contract specifics:

### Step 1: Evaluate Rate Viability
```
Thought: Let me assess if this rate is worth pursuing.

Rate: $120/hour
Minimum: $100/hour
Analysis: MEETS THRESHOLD - $20 above minimum provides buffer

Considerations:
- Geographic differential? (SF/Seattle rates higher)
- Project complexity? (ML platform builds warrant premium)
- Timeline pressure? (Urgent needs = rate leverage)
```

### Step 2: Project Scope Assessment
```
Thought: What type of project is this and does it align with skills?

Project Type: ML Platform Modernization
Core Skills Required:
- Feature store building (Feast) - MATCH
- Model serving infrastructure - MATCH
- Real-time pipelines - MATCH

Alignment: HIGH - Direct skill match
```

### Step 3: Engagement Risk Analysis
```
Thought: What are the risks of this contract?

Risk 1: Scope creep
Mitigation: Define clear deliverables in SOW

Risk 2: Payment delays
Mitigation: Verify company payment history, prefer established cos

Risk 3: Manager misalignment
Mitigation: Request intro call before accepting

Risk Assessment: MEDIUM - Manageable with clear communication
```

### Step 4: Rate Negotiation Strategy
```
Thought: How should I position my rate?

Current Rate: $120/hour
Target Rate: $130-140/hour

Negotiation Points:
1. Twitter-scale experience (unique qualification)
2. Full ML platform lifecycle (reduces onboarding time)
3. Can start immediately (time-to-value)

Strategy: Lead with $140, settle at $130 minimum
```

## Decision Workflow

### Phase 1: Final Review
1. Read all enriched C2C leads from Analyst
2. Verify contract details still valid
3. Check for rate changes or project updates
4. Confirm engagement type and duration

### Phase 2: Application Triage

**Tier 1: Score 85+ (Immediate Action)**
- Generate full contract package
- Priority notification

**Tier 2: Score 70-84 (Queue)**
- Generate package if capacity allows

**Tier 3: Score <70 (Archive)**

### Phase 3: Contract Asset Generation

For each Tier 1/2 contract, generate:

#### A. Tailored CV (cv_company_contract.md)
Same as FTE but emphasize:
- Contract/consulting experience
- Rapid onboarding ability
- Self-management skills
- Immediate productivity

#### B. Rate Proposal (rate_proposal.md)
```
# Rate Proposal: [Company] - [Role]

## Proposed Terms

**Engagement Type**: C2C / Independent Contractor
**Duration**: [X] months
**Rate**: $[RATE]/hour USD

## Rate Rationale

My standard rate for ML platform work is $[RATE]/hour based on:

1. **Experience Level**: Staff-level ML engineering with hyperscale background
   - Twitter: 1PB/hour data pipelines
   - Full ML platform lifecycle: Feast, Weaviate, model serving

2. **Immediate Value**: Can ramp to productivity in < 2 weeks
   - No visa sponsorship required
   - Can start immediately
   - Self-managed, minimal oversight needed

3. **Specialized Skills**: Two-stage ranking systems are rare
   - Few engineers have managed Twitter-scale systems
   - RecSys expertise directly applicable

## Included in Rate
- Full scope of ML platform work
- Participation in team meetings
- Async communication during engagement
- Documentation and knowledge transfer

## Not Included (Extra)
- Onsite meetings (billed hourly + travel)
- Extended hours beyond scope
- Overtime rates: 1.5x

## Payment Terms
- Net 30 from invoice submission
- Bi-weekly or monthly invoicing
- Accept wire transfer or ACH
```

#### C. SOW Notes (sow_notes.md)
```
# SOW Notes: [Company] - [Role]

## Project Overview
- **Type**: [ML Platform Build / Roadmapping / Agentic Project]
- **Duration**: [6 months]
- **Scope**: [Brief description]

## Chain of Thought Analysis
- Rate: $[X]/hour vs $100 minimum
- Project alignment: [HIGH/MEDIUM/LOW]
- Manager quality: [Assessed rating]
- Risk level: [LOW/MEDIUM/HIGH]

## Key Terms to Negotiate
1. **Rate**: Start at $140, settle at $130
2. **Payment**: Net 30 preferred, Net 15 for established companies
3. **Scope**: Define clear deliverables upfront
4. **IP**: Work product belongs to client, background IP remains mine

## Questions for Initial Call
1. What does success look like at 3 months? 6 months?
2. Who will I be reporting to? How many existing contractors?
3. What's the onboarding process?
4. What's the budget approval timeline?

## Red Flags to Watch
- [ ] Unclear project scope
- [ ] No existing contractor program
- [ ] Manager has no contractor experience
- [ ] Rate below $100/hour (auto-reject)
- [ ] Payment terms > Net 45

## Application Status
- [ ] CV tailored
- [ ] Rate proposal drafted
- [ ] Intro call scheduled
- [ ] SOW drafted
```

### Phase 4: Package Assembly
```
applications/
└── [Company]_Contract_[Date]/
    ├── cv_tailored.pdf
    ├── rate_proposal.md
    ├── rate_proposal.pdf
    ├── sow_notes.md
    └── meta.json
```

### Phase 5: Notification (C2C Daily Heartbeat)

```
💼 C2C Contract Opportunities - March 9, 2026

🟢 HIGH PRIORITY CONTRACTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [Company A] ML Platform Engineer - Contract
   Rate: $130-150/hr | Duration: 6 months
   Score: 95/100
   Reasoning: Rate above threshold, ML platform project aligns with skills
   → [View Package](./applications/CompanyA_Contract_2026-03-09)

2. [Company B] RecSys Consultant - Contract
   Rate: $120/hr | Duration: 3 months
   Score: 88/100
   Reasoning: Strong recsys alignment, established contractor program
   → [View Package](./applications/CompanyB_Contract_2026-03-09)

📊 C2C SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Total C2C leads discovered: 12
- Passed rate filter ($100+): 8
- High priority: 2
- Medium priority: 4

💰 RATE GUIDANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Minimum acceptable: $100/hour
- Target rate: $130-140/hour
- Premium for specialized skills: $150/hour

💬 ACTIONS NEEDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review high priority contracts
2. Schedule intro calls
3. Submit rate proposals at $140 minimum
```

## Processing Rules

1. **Rate-First**: Only generate packages for roles meeting $100/hour minimum
2. **Contract-Specific Assets**: Include rate proposal and SOW notes, not just CV/CL
3. **Negotiation Focus**: C2C is more negotiable than FTE - include strategy
4. **Human-in-the-Loop**: Do NOT auto-submit - generate materials only

## Key Differences from FTE Strategist

| Aspect | FTE | C2C |
|--------|-----|-----|
| Main asset | CV + Cover Letter | CV + Rate Proposal + SOW Notes |
| Compensation | Salary + Equity | Hourly Rate |
| Negotiation | Annual review | Per-contract |
| Timeline | Long-term | 3-12 months |
| Narrative | Career growth | Immediate value |

## Execution Frequency

- Runs after Analyst C2C completes (same day, ~02:00 AM)
- Manual trigger: `openclaw agents run strategist_c2c`

## Error Handling

- Contract expired: Mark as "expired", skip package
- Rate changed: Recalculate and regenerate proposal
- Platform issue: Save to pending, retry next run