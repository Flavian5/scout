#!/usr/bin/env python3
"""
Signal Detector - LLM-powered signal extraction from job descriptions

Uses semantic analysis to identify technical signals, domain alignment,
career value indicators beyond simple keyword matching.

Usage:
    python detect.py --input data/leads/raw_leads.json --output data/leads/signals.json
    python detect.py --company "Genentech" --role "Staff ML Engineer" --jd "job description text"
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    import openai
except ImportError:
    openai = None

# Try to load from config
def load_config():
    """Load configuration from config files"""
    config = {}
    
    # Load secrets
    secrets_path = Path(__file__).parent.parent.parent / 'config' / 'secrets.json'
    if secrets_path.exists():
        with open(secrets_path) as f:
            config['secrets'] = json.load(f)
    
    # Load criteria
    criteria_path = Path(__file__).parent.parent.parent / 'config' / 'criteria.json'
    if criteria_path.exists():
        with open(criteria_path) as f:
            config['criteria'] = json.load(f)
    
    return config

def get_llm_client(config):
    """Get LLM client from config"""
    if not openai:
        print("Error: openai package not installed", file=sys.stderr)
        return None
    
    secrets = config.get('secrets', {})
    llm_config = secrets.get('llm_api', {})
    
    api_key = llm_config.get('api_key') or os.environ.get('OPENAI_API_KEY')
    provider = llm_config.get('provider', 'openrouter')
    
    if not api_key:
        print("Warning: No LLM API key found", file=sys.stderr)
        return None
    
    # Configure for OpenRouter
    if provider == 'openrouter':
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        return client
    
    return openai.OpenAI(api_key=api_key)

# Model selection: Kimi K2.5 for analytical work, Minimax M2.5 for fast/simple tasks
DEFAULT_ANALYTICAL_MODEL = "moonshot/kimi-k2.5"
DEFAULT_FAST_MODEL = "minimax/minimax-m2.5"

def detect_signals_with_llm(client, job_data, model=DEFAULT_ANALYTICAL_MODEL):
    """Use LLM to detect signals from job description"""
    
    jd_text = job_data.get('job_description_raw', '') or job_data.get('raw_jd_text', '')
    company = job_data.get('company', '')
    role = job_data.get('role_title', '')
    
    if not jd_text:
        # Fall back to company + role if no JD
        jd_text = f"Role: {role} at {company}"
    
    prompt = f"""You are an expert ML career advisor. Analyze this job description for a Senior/Staff ML Engineer position.

Company: {company}
Role: {role}

Job Description:
{jd_text[:5000]}

Analyze and identify the following signals. Return a JSON object with your analysis:

{{
    "detected_signals": {{
        "ml_architecture": {{
            "foundation_models": <true/false>,
            "transformers": <true/false>,
            "generative_recommendation": <true/false>,
            "two_stage_ranking": <true/false>,
            "causal_ml": <true/false>,
            "production_ml": <true/false>
        }},
        "domain_alignment": {{
            "recsys": <true/false>,
            "virtual_cell": <true/false>,
            "bio_ai": <true/false>,
            "voice_agent": <true/false>,
            "healthcare_ai": <true/false>
        }},
        "career_impact": {{
            "scientific_impact": <true/false>,
            "hyperscale": <true/false>,
            "publication_opportunity": <true/false>,
            "leadership_growth": <true/false>,
            "cutting_edge": <true/false>
        }},
        "infrastructure": {{
            "gpu_compute": <true/false>,
            "data_scale": <true/false>,
            "ml_platform": <true/false>
        }}
    }},
    "signal_strength": {{
        "overall": <0.0-1.0>,
        "technical": <0.0-1.0>,
        "domain": <0.0-1.0>,
        "career": <0.0-1.0>
    }},
    "recommendation": "<strong_match/medium_match/weak_match>",
    "reasoning": "<2-3 sentence explanation of why this role matches or not>",
    "key_requirements": ["list of key requirements from JD"],
    "nice_to_have": ["list of nice-to-have skills"]
}}

Focus on:
1. Does this role involve building recommendation systems, ML infrastructure, or AI for science?
2. Is this a research-heavy or production-heavy role?
3. What scale of data/compute is mentioned?
4. Any mention of virtual cells, drug discovery, GenRec, foundation models?
"""

    try:
        # Handle model name for OpenRouter
        if '/' in model:
            model = model  # Already in provider/model format
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert ML career advisor. Analyze job descriptions and return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content
        
        # Extract JSON from response
        # Find JSON block
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        
        if start >= 0 and end > start:
            json_str = result_text[start:end]
            return json.loads(json_str)
        
        return {"error": "Could not parse LLM response", "raw": result_text}
        
    except Exception as e:
        return {"error": str(e)}

def detect_signals_keyword(job_data):
    """Fallback: Detect signals using keyword matching"""
    
    jd_text = (job_data.get('job_description_raw', '') or 
               job_data.get('raw_jd_text', '') or 
               job_data.get('role_title', '') + ' ' + 
               job_data.get('company', '')).lower()
    
    signals = {
        "ml_architecture": {
            "foundation_models": any(k in jd_text for k in ['foundation model', 'llm', 'gpt', 'transformer', 'bert']),
            "transformers": 'transformer' in jd_text,
            "generative_recommendation": any(k in jd_text for k in ['genrec', 'generative rec', 'vae', 'diffusion']),
            "two_stage_ranking": any(k in jd_text for k in ['two-stage', 'two stage', 'candidate generation', 're-ranking']),
            "causal_ml": any(k in jd_text for k in ['causal', 'uplift', 'counterfactual']),
            "production_ml": any(k in jd_text for k in ['feature store', 'mlops', 'model serving'])
        },
        "domain_alignment": {
            "recsys": any(k in jd_text for k in ['recommendation', 'recsys', 'personalization']),
            "virtual_cell": any(k in jd_text for k in ['virtual cell', 'cell', 'biological']),
            "bio_ai": any(k in jd_text for k in ['bio-ai', 'drug discovery', 'computational biology']),
            "voice_agent": any(k in jd_text for k in ['voice agent', 'voice ai', 'conversational']),
            "healthcare_ai": any(k in jd_text for k in ['healthcare', 'medical', 'clinical'])
        },
        "career_impact": {
            "scientific_impact": any(k in jd_text for k in ['drug discovery', 'research', 'scientific']),
            "hyperscale": any(k in jd_text for k in ['petabyte', 'hyperscale', 'billion']),
            "publication_opportunity": any(k in jd_text for k in ['publish', 'conference', 'research']),
            "leadership_growth": any(k in jd_text for k in ['staff', 'senior', 'lead', 'mentor']),
            "cutting_edge": any(k in jd_text for k in ['cutting edge', 'state of the art', 'innovation'])
        },
        "infrastructure": {
            "gpu_compute": any(k in jd_text for k in ['gpu', 'h100', 'a100', 'nvidia']),
            "data_scale": any(k in jd_text for k in ['petabyte', 'large scale', 'massive']),
            "ml_platform": any(k in jd_text for k in ['ml platform', 'ml infrastructure'])
        }
    }
    
    # Calculate scores
    total_signals = sum(1 for cat in signals.values() for v in cat.values() if v)
    max_signals = sum(1 for cat in signals.values() for v in cat.values())
    
    return {
        "detected_signals": signals,
        "signal_strength": {
            "overall": round(total_signals / max_signals, 2),
            "technical": round(sum(1 for v in signals["ml_architecture"].values() if v) / 6, 2),
            "domain": round(sum(1 for v in signals["domain_alignment"].values() if v) / 5, 2),
            "career": round(sum(1 for v in signals["career_impact"].values() if v) / 5, 2)
        },
        "recommendation": "strong_match" if total_signals >= 8 else "medium_match" if total_signals >= 4 else "weak_match",
        "reasoning": f"Found {total_signals} signals via keyword matching",
        "method": "keyword"
    }

def process_leads(input_path, output_path, use_llm=True):
    """Process leads and detect signals"""
    
    config = load_config()
    client = get_llm_client(config) if use_llm else None
    
    # Load leads
    with open(input_path) as f:
        leads = json.load(f)
    
    print(f"Processing {len(leads)} leads...")
    
    results = []
    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] Analyzing: {lead.get('role_title')} at {lead.get('company')}")
        
        if client and use_llm:
            try:
                result = detect_signals_with_llm(client, lead)
                result['method'] = 'llm'
            except Exception as e:
                print(f"    LLM failed: {e}, falling back to keyword")
                result = detect_signals_keyword(lead)
        else:
            result = detect_signals_keyword(lead)
        
        result['job_id'] = lead.get('job_id')
        result['company'] = lead.get('company')
        result['role_title'] = lead.get('role_title')
        
        results.append(result)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved signal analysis to: {output_path}")
    
    # Summary
    strong = sum(1 for r in results if r.get('recommendation') == 'strong_match')
    medium = sum(1 for r in results if r.get('recommendation') == 'medium_match')
    print(f"Summary: {strong} strong, {medium} medium, {len(results) - strong - medium} weak matches")

def main():
    parser = argparse.ArgumentParser(description='Detect signals in job descriptions')
    parser.add_argument('--input', '-i', help='Input JSON file with leads')
    parser.add_argument('--output', '-o', help='Output JSON file for signals')
    parser.add_argument('--company', help='Company name')
    parser.add_argument('--role', help='Role title')
    parser.add_argument('--jd', help='Job description text')
    parser.add_argument('--no-llm', action='store_true', help='Use keyword matching only (no LLM)')
    parser.add_argument('--model', default=DEFAULT_ANALYTICAL_MODEL, help='LLM model to use')
    
    args = parser.parse_args()
    
    # Single job mode
    if args.company and args.role:
        job_data = {
            'company': args.company,
            'role_title': args.role,
            'job_description_raw': args.jd or ''
        }
        
        config = load_config()
        client = get_llm_client(config) if not args.no_llm else None
        
        if client:
            result = detect_signals_with_llm(client, job_data, args.model)
        else:
            result = detect_signals_keyword(job_data)
        
        print(json.dumps(result, indent=2))
        return
    
    # Batch mode
    if not args.input:
        parser.error("--input required for batch processing")
    
    output = args.output or args.input.replace('.json', '_signals.json')
    process_leads(args.input, output, use_llm=not args.no_llm)

if __name__ == '__main__':
    main()