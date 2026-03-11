#!/usr/bin/env python3
"""
Company Research Skill - Uses Tavily for company research

Researches companies to gather information about:
- Company focus areas and mission
- Tech stack and infrastructure
- Funding stage and financial health
- Culture and work environment
- Conversation starters for interviews

Usage:
    python research.py --company "Genentech" --output data/companies/genentech.json
    python research.py --input data/leads/enriched_leads.json --max 5
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Base path for project
BASE_PATH = Path(__file__).parent.parent.parent

def load_secrets():
    """Load secrets from config"""
    secrets_path = BASE_PATH / 'config' / 'secrets.json'
    if secrets_path.exists():
        with open(secrets_path) as f:
            return json.load(f)
    return {}

def get_tavily_api_key():
    """Get Tavily API key from secrets"""
    secrets = load_secrets()
    web_search = secrets.get('web_search', {})
    return web_search.get('api_key') or os.environ.get('TAVILY_API_KEY')

def load_sourcing_config():
    """Load sourcing config for pre-known company info"""
    sourcing_path = BASE_PATH / 'config' / 'sourcing.json'
    if sourcing_path.exists():
        with open(sourcing_path) as f:
            return json.load(f)
    return {}

def search_tavily(query, max_results=5):
    """Search using Tavily"""
    api_key = get_tavily_api_key()
    if not api_key:
        print("Warning: No Tavily API key found", file=sys.stderr)
        return None
    
    # Use the existing tavily search script
    script_path = BASE_PATH / 'skills' / 'openclaw-tavily-search' / 'scripts' / 'tavily_search.py'
    
    if not script_path.exists():
        print(f"Warning: Tavily script not found at {script_path}", file=sys.stderr)
        return None
    
    try:
        result = subprocess.run(
            ['python3', str(script_path), '--query', query, '--max-results', str(max_results), '--include-answer'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            print(f"Tavily error: {result.stderr}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Search error: {e}", file=sys.stderr)
        return None

def get_known_company_info(company_name):
    """Get pre-known company info from sourcing config"""
    sourcing = load_sourcing_config()
    
    # Search in traditional_tech
    for company in sourcing.get('target_companies', {}).get('traditional_tech', []):
        if company.get('name', '').lower() == company_name.lower():
            return company
    
    # Search in bio_ai
    for company in sourcing.get('target_companies', {}).get('bio_ai', []):
        if company.get('name', '').lower() == company_name.lower():
            return company
    
    # Search in consulting
    for company in sourcing.get('target_companies', {}).get('consulting', []):
        if company.get('name', '').lower() == company_name.lower():
            return company
    
    return None

def research_company(company_name):
    """Research a company using Tavily"""
    print(f"Researching {company_name}...")
    
    # First, get known info from config
    known_info = get_known_company_info(company_name)
    
    # Run searches
    queries = [
        f"{company_name} company overview mission focus areas 2024 2025",
        f"{company_name} machine learning AI tech stack infrastructure",
        f"{company_name} funding stage Series valuation 2024 2025",
        f"{company_name} culture remote work life balance",
    ]
    
    search_results = {}
    for query in queries:
        print(f"  Searching: {query[:50]}...")
        result = search_tavily(query)
        if result:
            search_results[query] = result
    
    # Parse results into structured format
    research = {
        'company': company_name,
        'researched_at': datetime.now().isoformat(),
        'known_info': known_info,
        'search_results': search_results,
        'summary': {},
        'talking_points': [],
        'tech_stack': [],
        'focus_areas': [],
        'culture_signals': [],
        'conversation_starters': []
    }
    
    # Extract summary from first search result (overview)
    if search_results:
        first_key = list(search_results.keys())[0]
        first_result = search_results[first_key]
        if first_result.get('answer'):
            research['summary']['overview'] = first_result['answer']
    
    # Parse specific info from search results
    for key, result in search_results.items():
        if 'tech stack' in key.lower():
            # Extract tech mentions from results
            for r in result.get('results', []):
                content = r.get('content', '').lower()
                if 'python' in content or 'pytorch' in content or 'tensorflow' in content:
                    if 'Python/PyTorch' not in research['tech_stack']:
                        research['tech_stack'].append('Python/PyTorch')
                if 'kubernetes' in content or 'k8s' in content:
                    if 'Kubernetes' not in research['tech_stack']:
                        research['tech_stack'].append('Kubernetes')
                if 'aws' in content or 'gcp' in content or 'azure' in content:
                    if 'Cloud' not in research['tech_stack']:
                        research['tech_stack'].append('Cloud')
        
        if 'funding' in key.lower():
            if result.get('answer'):
                research['summary']['funding'] = result['answer']
    
    # Add known focus areas if available
    if known_info:
        research['focus_areas'] = known_info.get('focus_areas', [])
    
    # Generate talking points
    if known_info:
        for area in research['focus_areas']:
            research['talking_points'].append(f"Interested in your {area} work")
    
    if research.get('tech_stack'):
        research['talking_points'].append(f"Excited about your ML infrastructure using {', '.join(research['tech_stack'][:2])}")
    
    # Generate conversation starters
    research['conversation_starters'] = [
        f"What ML/AI initiatives is {company_name} most excited about right now?",
        f"What's the team's approach to balancing research and production ML?",
        f"How does {company_name} think about compute infrastructure and GPU access?",
    ]
    
    return research

def process_leads(input_path, output_dir, max_companies=10):
    """Process leads and research companies"""
    
    # Load leads
    with open(input_path) as f:
        leads = json.load(f)
    
    # Get unique companies
    companies = []
    seen = set()
    for lead in leads:
        company = lead.get('company')
        if company and company not in seen:
            seen.add(company)
            companies.append(company)
            if len(companies) >= max_companies:
                break
    
    print(f"Researching {len(companies)} companies...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_research = []
    for i, company in enumerate(companies):
        print(f"\n[{i+1}/{len(companies)}] {company}")
        
        # Check if already researched
        company_file = output_path / f"{company.lower().replace(' ', '_')}.json"
        if company_file.exists():
            print(f"  Loading existing research...")
            with open(company_file) as f:
                research = json.load(f)
        else:
            research = research_company(company)
            # Save
            with open(company_file, 'w') as f:
                json.dump(research, f, indent=2)
            print(f"  Saved to {company_file}")
        
        all_research.append(research)
    
    # Save combined
    combined_file = output_path / 'combined.json'
    with open(combined_file, 'w') as f:
        json.dump(all_research, f, indent=2)
    
    print(f"\nSaved combined research to: {combined_file}")
    return all_research

def main():
    parser = argparse.ArgumentParser(description='Research companies using Tavily')
    parser.add_argument('--company', help='Company name to research')
    parser.add_argument('--output', '-o', help='Output JSON file')
    parser.add_argument('--input', '-i', help='Input leads JSON file to extract companies from')
    parser.add_argument('--max', type=int, default=10, help='Max companies to research from leads')
    
    args = parser.parse_args()
    
    # Single company mode
    if args.company:
        research = research_company(args.company)
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(research, f, indent=2)
            print(f"Saved to {output_path}")
        else:
            print(json.dumps(research, indent=2))
        return
    
    # Batch mode from leads
    if args.input:
        output_dir = args.output or 'data/companies'
        process_leads(args.input, output_dir, args.max)
        return
    
    parser.print_help()

if __name__ == '__main__':
    main()