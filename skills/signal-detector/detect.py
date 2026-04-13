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
import re
import sys
import requests
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Model selection: Minimax M2.7 for all tasks (migrated from OpenRouter)
DEFAULT_MODEL = "MiniMax-M2.7"
DEFAULT_ENDPOINT = "https://api.minimax.io/v1/text/chatcompletion_v2"

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

def get_llm_config(config):
    """Get LLM configuration from config"""
    secrets = config.get('secrets', {})
    llm_config = secrets.get('llm_api', {})
    
    api_key = llm_config.get('api_key') or os.environ.get('OPENAI_API_KEY')
    endpoint = llm_config.get('endpoint', DEFAULT_ENDPOINT)
    model = llm_config.get('model', DEFAULT_MODEL)
    
    if not api_key:
        print("Warning: No LLM API key found", file=sys.stderr)
        return None
    
    return {
        'api_key': api_key,
        'endpoint': endpoint,
        'model': model
    }

def call_minimax_llm(api_key, endpoint, model, messages, temperature=0.3, max_tokens=2000):
    """
    Call minimax.io API using native REST format.
    
    Args:
        api_key: Minimax API key
        endpoint: Full API endpoint URL
        model: Model name (e.g., "MiniMax-M2.7")
        messages: List of message dicts with role and content
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
    
    Returns:
        Response text from the model
    """
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': model,
        'messages': messages,
        'stream': False,
        'temperature': temperature,
        'top_p': 0.95
    }
    
    if max_tokens:
        payload['max_tokens'] = max_tokens
    
    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")
    
    result = response.json()
    
    # Extract message content from minimax response format
    choices = result.get('choices', [])
    if choices and len(choices) > 0:
        return choices[0].get('message', {}).get('content', '')
    
    # Check for base_resp error
    base_resp = result.get('base_resp', {})
    if base_resp.get('status_code') != 0:
        raise Exception(f"API error: {base_resp.get('status_msg', 'Unknown error')}")
    
    return ''

def extract_json_from_response(response_text: str) -> dict | None:
    """
    Robustly extract JSON from LLM response.
    Handles: markdown code blocks, truncated JSON, partial responses.
    """
    if not response_text:
        return None
    
    # Strategy 1: Try to find JSON in markdown code block
    json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
    if json_block_match:
        try:
            return json.loads(json_block_match.group(1))
        except json.JSONDecodeError:
            pass  # Try next strategy
    
    # Strategy 2: Find first { and last } and try to parse
    start = response_text.find('{')
    end = response_text.rfind('}')
    
    if start >= 0 and end > start:
        json_str = response_text[start:end+1]
        
        # Try direct parse first
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Strategy 3: Try to repair common JSON issues
        # Remove trailing commas
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
        
        # Try again after repair
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            # Strategy 4: Try to extract just the detected_signals part
            signals_match = re.search(r'"detected_signals"\s*:\s*\{.*\}', json_str, re.DOTALL)
            if signals_match:
                # Return partial structure with what we can parse
                pass
    
    return None

def detect_signals_with_llm(llm_config, job_data, max_retries=2):
    """Use LLM to detect signals from job description with robust error handling"""
    
    # Safe extraction with null checks
    raw_jd = job_data.get('job_description_raw') or job_data.get('raw_jd_text') or ''
    company = job_data.get('company') or ''
    role = job_data.get('role_title') or ''
    
    # Ensure we have string (not None)
    jd_text = str(raw_jd) if raw_jd else ''
    
    if not jd_text.strip():
        # Fall back to company + role if no JD
        jd_text = f"Role: {role} at {company}"
    
    prompt = f"""You are an expert ML career advisor. Analyze this job description for a Senior/Staff ML Engineer position.

Company: {company}
Role: {role}

Job Description:
{jd_text[:5000]}

Analyze and identify the following signals. Return ONLY valid JSON (no markdown, no explanation):

{{
    "detected_signals": {{
        "ml_architecture": {{
            "foundation_models": true,
            "transformers": false,
            "generative_recommendation": false,
            "two_stage_ranking": false,
            "causal_ml": false,
            "production_ml": true
        }},
        "domain_alignment": {{
            "recsys": false,
            "virtual_cell": false,
            "bio_ai": false,
            "voice_agent": false,
            "healthcare_ai": false
        }},
        "career_impact": {{
            "scientific_impact": false,
            "hyperscale": true,
            "publication_opportunity": false,
            "leadership_growth": true,
            "cutting_edge": true
        }},
        "infrastructure": {{
            "gpu_compute": true,
            "data_scale": true,
            "ml_platform": false
        }}
    }},
    "signal_strength": {{
        "overall": 0.75,
        "technical": 0.8,
        "domain": 0.2,
        "career": 0.8
    }},
    "recommendation": "strong_match",
    "reasoning": "Brief explanation here",
    "key_requirements": ["req1", "req2"],
    "nice_to_have": ["nice1"]
}}

Focus on:
1. Does this role involve building recommendation systems, ML infrastructure, or AI for science?
2. Is this a research-heavy or production-heavy role?
3. What scale of data/compute is mentioned?
4. Any mention of virtual cells, drug discovery, GenRec, foundation models?

Return ONLY valid JSON - no markdown code blocks, no explanation.
"""

    messages = [
        {"role": "user", "content": prompt}
    ]
    
    for attempt in range(max_retries):
        try:
            result_text = call_minimax_llm(
                llm_config['api_key'],
                llm_config['endpoint'],
                llm_config['model'],
                messages,
                temperature=0.3,
                max_tokens=2000
            )
            
            # Try to extract and parse JSON
            parsed = extract_json_from_response(result_text)
            
            if parsed:
                return parsed
            
            # If we got here, JSON extraction failed
            print(f"    Warning: Could not parse JSON on attempt {attempt + 1}, trying again...")
            
            # Add a hint to the prompt for the next attempt
            prompt = prompt.replace(
                "Return ONLY valid JSON (no markdown, no explanation):",
                "CRITICAL: Return ONLY raw JSON object. No markdown fences. No text before or after."
            )
            messages = [{"role": "user", "content": prompt}]
            
        except Exception as e:
            print(f"    Error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return {"error": str(e)}
    
    # All retries exhausted
    return {"error": "Failed to parse LLM response after retries", "method": "llm_failed"}

def detect_signals_keyword(job_data):
    """Fallback: Detect signals using keyword matching with null safety"""
    
    # Safe extraction with null checks
    raw_jd = job_data.get('job_description_raw') or job_data.get('raw_jd_text') or ''
    role = job_data.get('role_title') or ''
    company = job_data.get('company') or ''
    
    # Ensure we have strings
    jd_text = str(raw_jd) + ' ' + str(role) + ' ' + str(company)
    jd_text_lower = jd_text.lower()
    
    signals = {
        "ml_architecture": {
            "foundation_models": any(k in jd_text_lower for k in ['foundation model', 'llm', 'gpt', 'transformer', 'bert', 'large language']),
            "transformers": 'transformer' in jd_text_lower,
            "generative_recommendation": any(k in jd_text_lower for k in ['genrec', 'generative rec', 'vae', 'diffusion']),
            "two_stage_ranking": any(k in jd_text_lower for k in ['two-stage', 'two stage', 'candidate generation', 're-ranking']),
            "causal_ml": any(k in jd_text_lower for k in ['causal', 'uplift', 'counterfactual']),
            "production_ml": any(k in jd_text_lower for k in ['feature store', 'mlops', 'model serving', 'production'])
        },
        "domain_alignment": {
            "recsys": any(k in jd_text_lower for k in ['recommendation', 'recsys', 'personalization']),
            "virtual_cell": any(k in jd_text_lower for k in ['virtual cell', 'cell', 'biological']),
            "bio_ai": any(k in jd_text_lower for k in ['bio-ai', 'drug discovery', 'computational biology']),
            "voice_agent": any(k in jd_text_lower for k in ['voice agent', 'voice ai', 'conversational']),
            "healthcare_ai": any(k in jd_text_lower for k in ['healthcare', 'medical', 'clinical'])
        },
        "career_impact": {
            "scientific_impact": any(k in jd_text_lower for k in ['drug discovery', 'research', 'scientific']),
            "hyperscale": any(k in jd_text_lower for k in ['petabyte', 'hyperscale', 'billion', 'trillion']),
            "publication_opportunity": any(k in jd_text_lower for k in ['publish', 'conference', 'research', 'paper']),
            "leadership_growth": any(k in jd_text_lower for k in ['staff', 'senior', 'lead', 'mentor', 'principal']),
            "cutting_edge": any(k in jd_text_lower for k in ['cutting edge', 'state of the art', 'innovation', 'advanced'])
        },
        "infrastructure": {
            "gpu_compute": any(k in jd_text_lower for k in ['gpu', 'h100', 'a100', 'nvidia', 'tpu']),
            "data_scale": any(k in jd_text_lower for k in ['petabyte', 'large scale', 'massive', 'exabyte']),
            "ml_platform": any(k in jd_text_lower for k in ['ml platform', 'ml infrastructure', 'feature store'])
        }
    }
    
    # Calculate scores
    total_signals = sum(1 for cat in signals.values() for v in cat.values() if v)
    max_signals = sum(1 for cat in signals.values() for v in cat.values())
    
    return {
        "detected_signals": signals,
        "signal_strength": {
            "overall": round(total_signals / max_signals, 2) if max_signals > 0 else 0,
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
    llm_config = get_llm_config(config) if use_llm else None
    
    # Load leads
    with open(input_path) as f:
        leads = json.load(f)
    
    print(f"Processing {len(leads)} leads...")
    
    results = []
    llm_success = 0
    llm_failed = 0
    
    for i, lead in enumerate(leads):
        print(f"  [{i+1}/{len(leads)}] Analyzing: {lead.get('role_title', 'Unknown')} at {lead.get('company', 'Unknown')}")
        
        if llm_config and use_llm:
            try:
                result = detect_signals_with_llm(llm_config, lead)
                
                # Check if we got valid result or error
                if 'error' in result:
                    print(f"    LLM failed: {result.get('error')}, using keyword fallback")
                    result = detect_signals_keyword(lead)
                    llm_failed += 1
                else:
                    result['method'] = 'llm'
                    llm_success += 1
                    
            except Exception as e:
                print(f"    Exception: {e}, falling back to keyword")
                result = detect_signals_keyword(lead)
                llm_failed += 1
        else:
            result = detect_signals_keyword(lead)
        
        # Ensure we always have required fields
        result['job_id'] = lead.get('job_id', f'unknown_{i}')
        result['company'] = lead.get('company', 'Unknown')
        result['role_title'] = lead.get('role_title', 'Unknown')
        
        results.append(result)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nSaved signal analysis to: {output_path}")
    print(f"LLM success: {llm_success}, LLM failed (keyword used): {llm_failed}")
    
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
    parser.add_argument('--model', default=DEFAULT_MODEL, help='LLM model to use')
    
    args = parser.parse_args()
    
    # Single job mode
    if args.company and args.role:
        job_data = {
            'company': args.company,
            'role_title': args.role,
            'job_description_raw': args.jd or ''
        }
        
        config = load_config()
        llm_config = get_llm_config(config) if not args.no_llm else None
        
        if llm_config:
            result = detect_signals_with_llm(llm_config, job_data)
            if 'error' in result:
                print(f"LLM failed: {result.get('error')}")
                result = detect_signals_keyword(job_data)
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