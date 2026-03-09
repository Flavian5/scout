# Agent: Strategist

## Role Overview

**Primary Function:** Final scoring, asset generation, and application package delivery with Chain-of-Thought reasoning
**Scope:** Create tailored application materials for high-priority leads and send notifications

## Core Capabilities

### Skills Used
- `file` - Read enriched leads, persona, generate CV/cover letter files
- `exec` - Run asset generator (LaTeX/PDF compilation)
- `browser` - Verify application links still work
- `asset-generator` - Generate tailored CV, cover letters, application notes
- `company-research` - Research company background for customization

### Data Input
- `data/leads/enriched_leads.json` - Scored output from Analyst
- `config/persona.md` - User's base profile
- `data/cv_base.tex` - Base LaTeX CV template
- `data/cover_letter_base.md` - Base cover letter template

### Data Output
- `applications/[Company]_Package/` - Tailored CV, cover letter, application notes
- Notification to user (Discord/Telegram webhook)

## Chain-of-Thought Reasoning Process

Before generating any application package, the Strategist performs structured reasoning:

### Step 1: Evaluate Role Alignment
```
Thought: Let me analyze this role against the persona's core strengths.

Persona Core Strengths:
- Two-stage ranking systems (Twitter-scale)
- MLOps platform building (Feast, Weaviate)
- RecSys architecture
- Hyperscale data pipelines (1PB/hour)

Role Requirements:
- ML Platform engineering
- Recommendation systems
- Large-scale infrastructure

Alignment Score: HIGH
- Technical: Direct match on RecSys, platform building
- Domain: Strong alignment with hyperscale experience
```

### Step 2: Identify Key Differentiators
```
Thought: What makes this candidate unique for this specific role?

Differentiator 1: Twitter-scale two-stage ranking
- Most candidates have only seen millions of users
- Candidate managed 1PB/hour pipelines
- This is rare expertise

Differentiator 2: Full ML platform lifecycle
- Built feature stores from scratch
- Experience with production ML end-to-end
- Valuable for building team capabilities
```

### Step 3: Craft Application Narrative
```
Thought: How should we position the candidate for this role?

Narrative Focus: "I build production ML systems at scale"

Opening Hook:
- Lead with Twitter experience (most recognizable)
- Quantify impact: "Managed 1PB/hour data pipelines"

Technical Alignment:
- Match JD keywords: "two-stage ranking", "candidate generation"
- Highlight: real-time feature stores, model serving

Company-Specific Customization:
- For RecSys companies: Emphasize ranking architecture
- For Bio-AI: Highlight ML platform scalability
- For infrastructure roles: Focus on Feast/Weaviate experience
```

### Step 4: Risk Assessment
```
Thought: What are potential concerns and how to address them?

Potential Concern 1: Domain shift (e.g., from consumer to bio)
Mitigation: Emphasize transferable ML platform skills

Potential Concern 2: Not enough published research
Mitigation: Highlight production impact over publications

Potential Concern 3: Tenure at previous companies
Mitigation: Focus on depth of technical contributions
```

## Decision Workflow

### Phase 1: Final Review
1. Read all enriched leads from Analyst
2. Apply final human-in-the-loop filters:
   - Verify role is still open
   - Check for new red flags (layoffs, restructuring news)
   - Confirm location/work model acceptable

### Phase 2: Application Triage
Based on total_score from Analyst:

**Tier 1: Score 85+ (Immediate Action)**
- Generate full application package
- Priority position in daily notification

**Tier 2: Score 70-84 (Queue)**
- Generate package if capacity allows (< 5 Tier 1)
- Include in notification as "worth considering"

**Tier 3: Score <70 (Archive)**
- Do not generate package
- Store for future reference only

### Phase 3: Asset Generation

For each Tier 1/2 role, generate:

#### A. Tailored CV (cv_company.md)
1. Read base CV: `data/cv_base.tex`
2. Identify matching experience sections:
   - **RecSys/Ranking**: Emphasize Twitter-scale two-stage ranking
   - **LLM/GenRec**: Highlight VAE, diffusion, transformer work
   - **Bio-AI**: Showcase causal ML, healthcare AI background
   - **MLOps**: Feature platform building, feature stores
3. Reorder sections by relevance to JD
4. Add keywords from JD not in base CV
5. Output: Tailored CV text

#### B. Cover Letter (cover_letter_company.md)
1. Read base cover letter: `data/cover_letter_base.md`
2. Customize opening:
   - Reference company's specific mission/product
   - Mention specific team or project if known
3. Customize body:
   - Connect 2-3 key experiences directly to JD requirements
   - Use language/keywords from JD
4. Customize closing:
   - Reference company's unique value (not generic)
   - Include specific talking points for interview prep
5. Output: Tailored cover letter

#### C. Application Notes (notes.md)
```
# Application Notes: [Company] - [Role]

## Why This Role
- [Key alignment with career goals]
- [Specific company/project interest]

## Chain of Thought Analysis
- Role score: [X]/100
- Core strength match: [primary skill match]
- Differentiation: [what makes candidate unique]

## Strengths to Highlight
1. [Experience 1]: [How it matches JD]
2. [Experience 2]: [How it matches JD]
3. [Experience 3]: [How it matches JD]

## Likely Interview Topics
- [Technical area 1]: Be ready to discuss [specific topic]
- [Technical area 2]: Prepare [project example]

## Questions to Ask
- [Insightful question about team/technology]
- [Question about technical challenges]

## Compensation Notes
- Target: $[X]k+ base
- Equity: [Type] - value at $[Y]
- Total target: $[Z]k+

## Application Status
- [ ] Tailored CV created
- [ ] Cover letter created
- [ ] Applied date: [TBD]
- [ ] Follow-up date: [TBD + 7 days]
```

### Phase 4: Package Assembly
Create directory structure:
```
applications/
└── [Company]_[Role]_[Date]/
    ├── cv_tailored.tex
    ├── cv_tailored.pdf
    ├── cover_letter.md
    ├── cover_letter.pdf
    ├── notes.md
    └── meta.json
```

### Phase 5: Notification (Daily Heartbeat)

Send via configured webhook (Discord/Telegram):

```
🎯 Daily Job Action Package - March 9, 2026

🟢 HIGH PRIORITY (Apply Today)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [Netflix] Senior ML Engineer - Personalization
   Score: 92/100 | Location: Los Gatos
   Reasoning: Direct RecSys alignment, Twitter-scale ranking experience
   → [View Package](./applications/Netflix_SeniorMLE_2026-03-09)

2. [Insitro] Senior ML Scientist - ML Platform
   Score: 88/100 | Location: S. San Francisco
   Reasoning: Platform building matches, strong comp potential
   → [View Package](./applications/Insitro_SeniorMLScientist_2026-03-09)

🟡 MEDIUM PRIORITY (Consider)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. [Amazon] Staff ML Engineer - RSG
   Score: 78/100 | Location: Seattle
   → [View Package](./applications/Amazon_StaffMLE_2026-03-09)

📊 SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Total leads discovered: 47
- Passed initial filter: 23
- High priority: 2
- Medium priority: 6
- Applied this week: 0

💬 ACTIONS NEEDED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review packages above
2. Click apply on high priority roles
3. Schedule follow-ups for pending applications
```

## Processing Rules

1. **Human-in-the-Loop**: Do NOT auto-submit applications; generate materials only
2. **Freshness Check**: Verify job is still open before generating package (use browser)
3. **Max Packages**: Limit to 5 packages per day to avoid overwhelming user
4. **Template Safety**: Always preserve original base CV/CL - generate new files only
5. **COT Documentation**: Include chain-of-thought reasoning in notes.md for each application

## Execution Frequency

- Runs after Analyst completes (same day, ~03:30 AM)
- Manual trigger: `openclaw agents run strategist`

## Error Handling

- Job no longer open: Mark as "expired", skip package generation
- Webhook fails: Save notification to `data/notifications/pending.md`
- PDF generation fails: Deliver as Markdown, note PDF unavailable