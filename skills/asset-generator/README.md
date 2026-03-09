# Skill: asset-generator

## Description
LLM-powered generation of job application assets (CV, cover letters, company-specific notes, follow-up emails). Uses user's persona and company research to create personalized, high-conversion application materials.

## Capabilities
- `file` - Read/write CV templates and generated assets
- `exec` - Run Python/JS generation scripts
- `browser` - Research company for personalization
- Personalized CV generation
- Cover letter drafting
- Company-specific talking points
- Follow-up email templates
- Interview preparation notes

## Configuration

### Required Environment Variables
```bash
OPENAI_API_KEY="sk-..."
# or
ANTHROPIC_API_KEY="sk-ant-..."
```

### Template Location
Templates stored in: `~/.openclaw/skills/asset-generator/templates/`

### User Persona
Reads from: `config/persona.md`

### Company Research
Reads from: `config/sourcing.json` and `config/criteria.json`

## Usage

### From OpenClaw
```
Use asset-generator to create application materials for CZI Staff ML Engineer role
```

### Direct Command
```bash
cd skills/asset-generator
python generate.py --company "CZI" --role "Staff ML Engineer" --output-dir "./applications/czi"
```

## Input Format
```json
{
  "company": "CZI",
  "role_title": "Staff Machine Learning Engineer",
  "job_url": "https://chanzuckerberg.com/careers/...",
  "persona": "config/persona.md",
  "target_companies": "config/sourcing.json",
  "scoring_criteria": "config/criteria.json",
  "assets_needed": ["cv", "cover_letter", "notes"]
}
```

## Output Format

### Generated CV (Markdown + PDF)
```markdown
# John Doe
Staff Machine Learning Engineer

## Summary
Staff ML Engineer with 8+ years building production ML systems...
Specialized in RecSys, LLMs, and ML infrastructure.

## Experience
### Twitter (2020-Present)
Staff ML Engineer, Recommendation Systems
- Built multi-T request/sec recommendation serving system
- Led migration to transformer-based ranking models
- 40% improvement in engagement metrics

### Capital One (2017-2020)
Senior ML Engineer
- Built real-time fraud detection system
- Led team of 5 ML engineers
```

### Cover Letter
```
Dear Hiring Manager,

I'm excited to apply for the Staff Machine Learning Engineer 
position at CZI. With my background in building production ML 
systems at Twitter and Capital One, and my passion for using 
AI to accelerate science...

My experience aligns directly with your team's work on:
- Foundation models for biological research
- Virtual cell technology and digital twins
- Large-scale ML infrastructure

[Personalized paragraph based on company research]
```

### Company Notes
```json
{
  "company": "CZI",
  "focus_areas": ["education", "health", "biology"],
  "tech_stack": ["python", "pytorch", "kubernetes"],
  "culture_signals": ["mission-driven", "open source", "remote-friendly"],
  "conversation_starters": [
    "CZI's mission to cure, prevent, or manage all diseases",
    "Their open source AI/ML tools (PyTorch, PyTorch)",
    "The ExCITE program for scientific breakthroughs"
  ],
  "tie_ins": [
    "Virtual cell work aligns with my interest in computational biology",
    "Foundation model experience directly applicable to biological models",
    "ML infrastructure work at scale matches their needs"
  ]
}
```

## Template Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `{{name}}` | Full name | persona.md |
| `{{title}}` | Current title | persona.md |
| `{{company}}` | Target company | input |
| `{{role}}` | Target role | input |
| `{{summary}}` | Professional summary | persona.md + LLM |
| `{{experience}}` | Work history | persona.md |
| `{{skills}}` | Technical skills | persona.md |
| `{{achievements}}` | Key accomplishments | persona.md |
| `{{tie_ins}}` | Company-specific connections | sourcing.json + LLM |

## Error Handling

| Error | Handling |
|-------|----------|
| LLM failure | Retry 3x, fallback to template-only |
| Missing persona | Prompt user for required fields |
| Template missing | Use default template |
| Company not in config | Use generic template with company research |

## Dependencies
- openai or anthropic
- python3.10+
- pypandoc (for PDF generation)
- jinja2 (for templating)
- weasyprint (for PDF rendering)

## Workflow Integration

1. **Scout** finds job → outputs to `jobs/discovered/`
2. **Analyst** scores job → outputs to `jobs/scored/`
3. **Strategist** (this skill) generates assets → outputs to `applications/{company}/`
   - `cv.md`, `cv.pdf`
   - `cover_letter.md`, `cover_letter.pdf`
   - `company_notes.md`
   - `followup_email.md`

## Quality Guidelines

- Customize every word to the specific role/company
- Emphasize transferable skills from Twitter, Capital One, MedSender
- Highlight Bio-AI/virtual cell interest and GenRec/MLOps background
- Keep CV to 2 pages maximum
- Cover letter to 300-400 words
- Use active voice and quantifiable metrics