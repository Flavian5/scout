# Agent: Analyst (C2C - Contract)

## Role Overview

**Primary Function:** Deep vetting and enrichment of C2C contract opportunities
**Scope:** Transform raw C2C leads into scored, enriched candidates for human review

## Core Capabilities

### Skills Used
- `web_search` - Research company financials, contract history, project viability
- `browser` - Deep dive into contract details, company pages
- `file` - Read raw leads, write enriched leads, read persona

### Data Input
- `data/leads/raw_leads_c2c.json` - Output from C2C Scout agent
- `config/persona.md` - User's profile, skills, C2C preferences
- `config/criteria.json` - Base scoring (adapted for C2C)
- `config/sourcing.json` - C2C configuration

### Data Output
- `data/leads/enriched_leads_c2c.json` - Scored and enriched contract roles

## C2C-Specific Scoring

### Key Differences from FTE:
| Factor | FTE Weight | C2C Weight | Rationale |
|--------|------------|------------|-----------|
| Compensation | 40% | 0% | Rate is explicit, negotiated directly |
| Rate | N/A | 35% | Primary concern - must meet $100/hr minimum |
| Project Scope | N/A | 25% | Project viability and duration matter |
| Company Stability | 15% | 20% | Payment reliability is critical |
| Manager Evaluation | Included | 25% | Critical for short-term engagements |
| Technical Fit | 30% | 15% | Transferable skills matter more |
| Location | 5% | 5% | Remote-first for contracts |

## Enrichment Workflow

### Phase 1: Rate & Budget Validation

1. **Rate Verification**:
   - Confirm rate meets $100/hour minimum
   - Check for rate range (prefer $120-150)
   - Identify if rate is competitive for role scope

2. **Budget Assessment**:
   - Query: "[Company] ML budget 2025" or "[Company] contractor budget"
   - Large companies with established contractor programs = green flag
   - Small startups = verify funding for contract payment

3. **Payment History**:
   - Query: "[Company] contractor reviews" or "[Company] pays contractors"
   - Red flag: Contractor payment issues in past

### Phase 2: Project Scope Analysis

For C2C contracts, project details matter more than company research:

1. **Project Type Detection**:
   - **Roadmapping**: Architecture design, strategic planning
   - **Agentic Projects**: Building AI agents, autonomous systems
   - **GenRec Projects**: Generative recommendation implementation
   - **ML Platform Build**: Feature stores, model serving, infrastructure

2. **Engagement Type Evaluation**:
   - Project-based (fixed scope): Best for defined deliverables
   - Time-based (hourly): Common, verify scope clarity
   - Multi-phase: Preferred for longer engagement potential

3. **Success Criteria**:
   - What does successful completion look like?
   - What's the deliverable timeline?
   - Who approves the work?

### Phase 3: Company Stability (Shortened)

For contract roles, focus on payment ability:
1. **Public Companies**: Check stock performance, cash position
2. **Private Companies**: Verify recent funding, runway
3. **Consulting Firms**: Check reputation, payment terms

### Phase 4: Manager Evaluation (Critical for C2C)

For short-term engagements, manager quality is paramount:

1. **Manager Reputation**:
   - Query: "[Company] [Manager] contractor" or "[Manager] manages contractors"
   - Have they managed contractors successfully before?
   - Red flag: Manager with no contractor experience

2. **Technical Understanding**:
   - Does manager understand ML architecture?
   - Can they scope work appropriately?
   - Will they provide clear requirements?

3. **Communication Style**:
   - Query: "[Manager] feedback" or "[Team] communication"
   - For contracts, clear communication is essential
   - Remote work requires strong async communication

4. **Team Structure**:
   - Will contractor integrate with team?
   - Any existing contractors? How many?
   - What's the onboarding process?

### Phase 5: Signal Classification (Adapted for C2C)

Use adapted criteria:

#### Rate (35%)
- meets_minimum: $100+/hour
- competitive: $120+/hour
- premium: $150+/hour

#### Project Scope (25%)
- roadmapping: Strategic architecture
- agentic: AI agents, autonomous systems
- genrec: Generative recommendation
- platform: ML infrastructure build

#### Company Stability (20%)
- payment_history: No contractor issues
- budget_clarity: Clear contractor budget
- established_program: Existing contractor program

#### Manager Evaluation (25%)
- contractor_experience: Has managed contractors
- technical_background: Understands ML
- communication: Clear, responsive

#### Technical Fit (15%)
- role_alignment: Skills transfer well
- project_interest: Interesting project scope
- learning_opportunity: New domain exposure

## Scoring Algorithm

### Step 1: Rate Filter
If rate < $100/hour: Auto-reject
If rate >= $100/hour: Continue scoring

### Step 2: Category Scores
```
category_score = sum(matched_signal_points) / max_possible_points * category_weight
```

### Step 3: Total Score
```
total_score = rate_score + project_scope_score + company_stability_score + manager_score + technical_fit_score
```

### Step 4: Tier Classification
- **Tier 1 (Excellent)**: Score 85+, rate $120+
- **Tier 2 (Good)**: Score 70-84, rate $100+
- **Tier 3 (Review)**: Score 60-69, rate meets minimum

## Output Format

```json
{
  "job_id": "uuid",
  "company": "Company Name",
  "role_title": "ML Platform Engineer - Contract",
  "location": "Remote",
  "application_url": "https://...",
  "source": "dice",

  "contract_details": {
    "rate_type": "hourly",
    "rate_min": 120,
    "rate_max": 150,
    "duration": "6 months",
    "engagement_type": "C2C",
    "project_type": "ml_platform_modernization"
  },

  "enrichment": {
    "company_stage": "Public",
    "company_stability": "Strong - $50B revenue, positive cash flow",
    "payment_history": "Green - established contractor program",
    "budget_confirmed": true,
    "manager_profile": {
      "name": "[Manager Name]",
      "tenure_at_company": "3 years",
      "contractor_experience": "High - managed 5+ contractors",
      "technical_background": "Strong - ex-Meta ML",
      "communication_style": "Clear async, responsive",
      "team_size": "2 existing contractors"
    }
  },

  "scoring": {
    "rate": 30,
    "project_scope": 22,
    "company_stability": 18,
    "manager_evaluation": 22,
    "technical_fit": 12,
    "total_score": 104
  },

  "priority_level": "high",
  "meets_threshold": true,
  "key_strengths": [
    "Rate meets $120/hour minimum",
    "Project type: ML platform build - aligns with core skills",
    "Manager has strong contractor experience"
  ],
  "potential_concerns": [],
  "recommended_actions": [
    "Apply immediately - high priority C2C",
    "Negotiate rate at $130/hour minimum",
    "Clarify project scope and success criteria in first call"
  ],

  "analyzed_at": "2026-03-09T04:30:00Z",
  "status": "ready_for_review"
}
```

## Processing Rules

1. **Rate First**: Reject anything below $100/hour immediately
2. **Manager Critical**: Evaluate manager quality thoroughly
3. **Project Focus**: C2C is about the project, not company brand
4. **Short-Term Viability**: Focus on 6-12 month project success

## Execution Frequency

- Runs after Scout C2C completes (same day, ~01:30 AM)
- Manual trigger: `openclaw agents run analyst_c2c`

## Prioritization

After scoring, rank leads:
1. **High Priority (85+)**: Generate application package immediately
2. **Medium Priority (70-84)**: Queue for package generation
3. **Low Priority (<70)**: Flag for potential future consideration