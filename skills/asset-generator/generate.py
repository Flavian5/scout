#!/usr/bin/env python3
"""
Asset Generator - Generate tailored CVs and cover letters for job applications

Uses LLM to:
1. Tailor CV to specific role/company
2. Generate cover letter
3. Create company-specific talking points

Usage:
    python generate.py --company "Genentech" --role "Staff ML Engineer" --output applications/genentech/
    python generate.py --input data/leads/enriched_leads.json --top 3
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import openai
except ImportError:
    openai = None

# Base path
BASE_PATH = Path(__file__).parent.parent.parent

def load_config():
    """Load configuration files"""
    config = {}
    
    # Secrets
    secrets_path = BASE_PATH / 'config' / 'secrets.json'
    if secrets_path.exists():
        with open(secrets_path) as f:
            config['secrets'] = json.load(f)
    
    # Persona
    persona_path = BASE_PATH / 'config' / 'persona.md'
    if persona_path.exists():
        with open(persona_path) as f:
            config['persona'] = f.read()
    
    # CV template
    cv_path = BASE_PATH / 'data' / 'cv_fte.md'
    if cv_path.exists():
        with open(cv_path) as f:
            config['cv_template'] = f.read()
    
    # Cover letter template
    cl_path = BASE_PATH / 'data' / 'cover_letter_base.md'
    if cl_path.exists():
        with open(cl_path) as f:
            config['cover_letter_template'] = f.read()
    
    # Sourcing config
    sourcing_path = BASE_PATH / 'config' / 'sourcing.json'
    if sourcing_path.exists():
        with open(sourcing_path) as f:
            config['sourcing'] = json.load(f)
    
    return config

# Model selection: Minimax M2.7 for all tasks (migrated from OpenRouter)
DEFAULT_ANALYTICAL_MODEL = "minimax/minimax-m2.7"
DEFAULT_CREATIVE_MODEL = "minimax/minimax-m2.7"

def get_llm_client(config):
    """Get LLM client"""
    if not openai:
        print("Error: openai package not installed", file=sys.stderr)
        return None
    
    secrets = config.get('secrets', {})
    llm_config = secrets.get('llm_api', {})
    
    api_key = llm_config.get('api_key') or os.environ.get('OPENAI_API_KEY')
    provider = llm_config.get('provider', 'minimax.io')
    base_url = llm_config.get('base_url', 'https://api.minimax.io/v1')
    
    if not api_key:
        print("Warning: No LLM API key found", file=sys.stderr)
        return None
    
    # Configure for minimax.io or other OpenAI-compatible providers
    return openai.OpenAI(
        api_key=api_key,
        base_url=base_url
    )

def get_company_info(company_name, sourcing):
    """Get company info from sourcing config"""
    for category in ['traditional_tech', 'bio_ai', 'consulting']:
        for company in sourcing.get('target_companies', {}).get(category, []):
            if company.get('name', '').lower() == company_name.lower():
                return company
    return None

def generate_tailored_cv(client, config, job_data, company_info):
    """Generate tailored CV for a specific job"""
    
    persona = config.get('persona', '')
    cv_template = config.get('cv_template', '')
    jd_text = job_data.get('job_description_raw', '') or job_data.get('raw_jd_text', '')
    company = job_data.get('company', '')
    role = job_data.get('role_title', '')
    
    prompt = f"""You are an expert resume writer. Tailor the following CV for a specific job application.

TARGET COMPANY: {company}
TARGET ROLE: {role}

Company Focus Areas: {', '.join(company_info.get('focus_areas', [])) if company_info else 'N/A'}

Job Description (key parts):
{jd_text[:3000]}

Original CV:
{cv_template}

Instructions:
1. Keep the same structure and format as the original CV
2. Reorder and emphasize experience that matches the job requirements
3. Add any relevant keywords from the JD that are missing
4. Keep all factual information accurate (dates, company names, etc.)
5. If the company is in Bio-AI/healthcare, emphasize relevant experience
6. If the company is in RecSys, emphasize recommendation systems experience

Return ONLY the tailored CV in markdown format. Do not add explanations."""

    try:
        response = client.chat.completions.create(
            model=DEFAULT_ANALYTICAL_MODEL,  # Kimi K2.5 for analytical CV tailoring
            messages=[
                {"role": "system", "content": "You are an expert resume writer. Return only valid markdown CV."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"CV generation error: {e}", file=sys.stderr)
        return cv_template  # Fallback to original

def generate_cover_letter(client, config, job_data, company_info):
    """Generate tailored cover letter"""
    
    persona = config.get('persona', '')
    cl_template = config.get('cover_letter_template', '')
    jd_text = job_data.get('job_description_raw', '') or job_data.get('raw_jd_text', '')
    company = job_data.get('company', '')
    role = job_data.get('role_title', '')
    
    # Extract key requirements from JD
    key_requirements = []
    if jd_text:
        lines = jd_text.split('\n')
        for line in lines[:20]:  # First 20 lines usually have key requirements
            if any(k in line.lower() for k in ['required', 'minimum', 'experience with', 'strong']):
                key_requirements.append(line.strip())
    
    prompt = f"""You are an expert cover letter writer. Write a tailored cover letter.

TARGET COMPANY: {company}
TARGET ROLE: {role}

Company Focus Areas: {', '.join(company_info.get('focus_areas', [])) if company_info else 'N/A'}

Key Job Requirements:
{chr(10).join(key_requirements[:5])}

Persona (your background):
{persona[:2000]}

Template:
{cl_template}

Instructions:
1. Fill in all {{}} placeholders with specific information
2. Make it specific to {company} - mention their focus areas
3. Highlight 2-3 specific achievements that match the job
4. Keep it to 3-4 paragraphs, 400 words max
5. Be confident but not arrogant
6. End with a clear call to action

Return ONLY the cover letter in markdown format."""

    try:
        response = client.chat.completions.create(
            model=DEFAULT_CREATIVE_MODEL,  # Minimax M2.5 for creative cover letter writing
            messages=[
                {"role": "system", "content": "You are an expert cover letter writer. Return only valid markdown."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Cover letter generation error: {e}", file=sys.stderr)
        return cl_template

def generate_assets_for_job(client, config, job_data, output_dir):
    """Generate all assets for a single job"""
    
    company = job_data.get('company', 'unknown')
    role = job_data.get('role_title', 'unknown')
    job_id = job_data.get('job_id', 'unknown')
    
    # Get company info
    sourcing = config.get('sourcing', {})
    company_info = get_company_info(company, sourcing)
    
    # Create output directory
    company_dir = Path(output_dir) / company.replace(' ', '_')
    company_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"  Generating assets for {role} at {company}...")
    
    # Generate tailored CV
    cv = generate_tailored_cv(client, config, job_data, company_info)
    cv_file = company_dir / 'cv.md'
    with open(cv_file, 'w') as f:
        f.write(cv)
    print(f"    CV: {cv_file}")
    
    # Generate cover letter
    cl = generate_cover_letter(client, config, job_data, company_info)
    cl_file = company_dir / 'cover_letter.md'
    with open(cl_file, 'w') as f:
        f.write(cl)
    print(f"    Cover Letter: {cl_file}")
    
    # Generate company notes
    notes = f"""# {company} - Application Notes

## Role
{role}

## Application URL
{job_data.get('application_url', 'N/A')}

## Score
Total: {job_data.get('total_score', 'N/A')}/100
Priority: {job_data.get('priority_level', 'N/A')}

## Detected Signals
{', '.join(job_data.get('detected_signals', []))}

## Company Focus Areas
{', '.join(company_info.get('focus_areas', [])) if company_info else 'N/A'}

## Talking Points for Interview
- Why {company}? (Their focus on {company_info.get('focus_areas', ['AI/ML'])[0] if company_info else 'technology'})
- My relevant experience: Twitter-scale ML, GenRec, ML infrastructure
- What I can contribute: Building production ML systems at scale

## Key Requirements from JD
{job_data.get('job_description_raw', 'N/A')[:1000]}

---
Generated: {datetime.now().isoformat()}
"""
    
    notes_file = company_dir / 'notes.md'
    with open(notes_file, 'w') as f:
        f.write(notes)
    print(f"    Notes: {notes_file}")
    
    # Save metadata
    metadata = {
        'company': company,
        'role': role,
        'job_id': job_id,
        'generated_at': datetime.now().isoformat(),
        'files': {
            'cv': str(cv_file),
            'cover_letter': str(cl_file),
            'notes': str(notes_file)
        }
    }
    
    meta_file = company_dir / 'metadata.json'
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return metadata

def process_leads(input_path, output_dir, top_n=3):
    """Process leads and generate assets for top jobs"""
    
    config = load_config()
    client = get_llm_client(config)
    
    if not client:
        print("Error: No LLM client available", file=sys.stderr)
        return
    
    # Load leads
    with open(input_path) as f:
        leads = json.load(f)
    
    # Filter to high-priority leads
    high_priority = [l for l in leads if l.get('priority_level') == 'High']
    high_priority.sort(key=lambda x: x.get('total_score', 0), reverse=True)
    
    # Take top N
    top_leads = high_priority[:top_n]
    
    if not top_leads:
        print("No high-priority leads found. Try with more leads or lower threshold.")
        return
    
    print(f"Generating assets for top {len(top_leads)} jobs...")
    
    results = []
    for i, lead in enumerate(top_leads):
        print(f"\n[{i+1}/{len(top_leads)}] {lead.get('role_title')} at {lead.get('company')}")
        result = generate_assets_for_job(client, config, lead, output_dir)
        results.append(result)
    
    # Save summary
    summary = {
        'generated_at': datetime.now().isoformat(),
        'total_applications': len(results),
        'applications': results
    }
    
    summary_file = Path(output_dir) / 'summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Generated {len(results)} application packages")
    print(f"  Summary: {summary_file}")

def main():
    parser = argparse.ArgumentParser(description='Generate application assets')
    parser.add_argument('--company', help='Company name')
    parser.add_argument('--role', help='Role title')
    parser.add_argument('--jd', help='Job description')
    parser.add_argument('--output', '-o', help='Output directory')
    parser.add_argument('--input', '-i', help='Input leads JSON file')
    parser.add_argument('--top', type=int, default=3, help='Number of top jobs to generate for')
    
    args = parser.parse_args()
    
    config = load_config()
    client = get_llm_client(config)
    
    if not client:
        print("Error: No LLM client available. Check config/secrets.json")
        sys.exit(1)
    
    # Single job mode
    if args.company and args.role:
        job_data = {
            'company': args.company,
            'role_title': args.role,
            'job_description_raw': args.jd or '',
            'job_id': 'manual'
        }
        
        output_dir = args.output or f'applications/{args.company.replace(" ", "_")}'
        sourcing = config.get('sourcing', {})
        company_info = get_company_info(args.company, sourcing)
        
        generate_assets_for_job(client, config, job_data, output_dir)
        return
    
    # Batch mode from leads
    if args.input:
        output_dir = args.output or 'applications'
        process_leads(args.input, output_dir, args.top)
        return
    
    parser.print_help()

if __name__ == '__main__':
    main()