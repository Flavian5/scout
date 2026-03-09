# Agent: Analyst

## Role Overview

**Primary Function:** Deep vetting, enrichment, and scoring of discovered job leads
**Scope:** Transform raw leads into scored, enriched candidates for human review

## Core Capabilities

### Skills Used
- `web_search` - Research company financials, culture, recent news
- `browser` - Deep dive into company pages, team structures
- `file` - Read raw leads, write enriched leads, read persona

### Data Input
- `data/leads/raw_leads.json` - Output from Scout agent
- `config/persona.md` - User's profile, skills, preferences
- `config/criteria.json` - Weighted scoring model

### Data Output
- `data/leads/enriched_leads.json` - Scored and enriched roles

## Enrichment Workflow

### Phase 1: Company Research
For each raw lead:
1. Use `web_search` to find:
   - Company funding stage, recent rounds, valuation
   - Recent news/press releases
   - Glassdoor/levels.fyi compensation data
   - Leadership team background

2. Example queries:
   - "[Company] funding 2025 2026"
   - "[Company] machine learning team size"
   - "[Company] salary range Staff MLE"
   - "[Company] culture values"

### Phase 2: Role Deep Dive
1. Read full job description in detail
2. Identify specific:
   - Tech stack requirements
   - Team structure and reporting
   - Key responsibilities and projects
   - Required vs preferred qualifications

### Phase 3: Signal Classification
Use `criteria.json` to classify each lead:

#### ML Architecture Depth (25%)
- foundation_models: scGPT, Geneformer, LLM pretraining
- transformer_architectures: Self-attention, BERT
- generative_recommendation: VAE, diffusion models
- two_stage_ranking: Candidate generation + re-ranking
- causal_ml: Causal inference, uplift modeling

#### Domain Alignment (25%)
- virtual_cell: AI for science, drug discovery
- bio_ai: Computational biology, genomics
- healthcare_ai: Medical ML, clinical
- consumer_recsys: Recommendation systems

#### Career Impact (20%)
- scientific_impact: Drug discovery, research
- publication_opportunity: Academic, open source
- leadership_growth: Staff+ scope

#### Infrastructure Resources (15%)
- gpu_compute: Access to modern GPUs
- data_scale: Petabyte-scale operations

#### Company Culture (10%)
- mission_driven: Non-profit, foundation
- remote_friendly: Flexible arrangements

## Scoring Algorithm

### Step 1: Signal Detection
Parse JD text for keyword matches in each category

### Step 2: Category Scores
For each category:
```
category_score = sum(matched_signal_points) / max_possible_points * category_weight
```

### Step 3: Bonus Points
Apply bonuses for exceptional alignment:
- scverse_experience: +10 points
- agentic_ai: +8 points
- mle_platform_building: +5 points

### Step 4: Total Score
```
total_score = sum(category_scores) + bonus_points
```

### Step 5: Apply Filters
Remove roles matching hard_no criteria:
- rule_based_only: No ML depth
- non_technical_leadership
- no_compute_budget

## Output Format

```json
{
  "job_id": "uuid",
  "company": "Company Name",
  "role_title": "Staff Machine Learning Engineer",
  "location": "San Francisco, CA",
  "application_url": "https://...",
  "source": "linkedin",

  "enrichment": {
    "company_stage": "Series D",
    "estimated_comp": "$280k-$350k",
    "company_size": "200-500",
    "recent_news": "Raised $300M Series D in 2025",
    "leadership_background": "Ex-Google, ex-Meta",
    "tech_stack": ["PyTorch", "Kubernetes", "Airflow"]
  },

  "scoring": {
    "ml_architecture_depth": 22,
    "domain_alignment": 25,
    "career_impact": 18,
    "infrastructure_resources": 12,
    "company_culture": 8,
    "bonus_points": 10,
    "total_score": 95
  },

  "priority_level": "high",
  "meets_threshold": true,
  "key_strengths": [
    "Virtual cell focus directly aligns with career transition",
    "scGPT/Geneformer foundation model work",
    "CZI mission-driven science impact"
  ],
  "potential_concerns": [
    "Non-profit compensation may be lower than industry"
  ],
  "recommended_actions": [
    "Apply immediately - high priority",
    "Emphasize Twitter-scale ranking experience",
    "Prepare for virtual cell domain questions"
  ],

  "analyzed_at": "2026-03-07T04:30:00Z",
  "status": "ready_for_review"
}
```

## Processing Rules

1. **Process All**: Score ALL raw leads, even low-signal ones (context may reveal hidden value)
2. **Transparent Scoring**: Store all category scores, not just total
3. **Context Matters**: Allow override when JD lacks keywords but role context suggests alignment

## Execution Frequency

- Runs after Scout completes (same day, ~02:30 AM)
- Manual trigger: `openclaw agents run analyst`

## Prioritization

After scoring, rank leads:
1. **High Priority (85+)**: Generate application package immediately
2. **Medium Priority (70-84)**: Queue for package generation if capacity allows
3. **Low Priority (<70)**: Flag for potential future consideration