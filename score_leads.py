import json
import re

# Load data
with open('data/leads/raw_leads.json', 'r') as f:
    leads = json.load(f)

with open('config/criteria.json', 'r') as f:
    criteria = json.load(f)

with open('config/persona.md', 'r') as f:
    persona_text = f.read()

def score_lead(lead):
    # Handle both field name variations
    jd_text = lead.get('raw_jd_text') or lead.get('job_description_raw') or ''
    text = (jd_text + ' ' + lead.get('role_title', '')).lower()
    
    # Check hard filters
    for filter_rule in criteria['filter_rules']['hard_no']:
        for keyword in filter_rule['exclude_keywords']:
            if keyword.lower() in text:
                return {"meets_threshold": False, "reason": f"Failed hard filter: {keyword}"}
                
    scores = {}
    detected_signals = []
    total_score = 0
    
    for cat_name, category in criteria['categories'].items():
        cat_score = 0
        cat_max = sum(s['points'] for s in category['signals'])
        
        for signal in category['signals']:
            for keyword in signal['keywords']:
                if keyword.lower() in text:
                    cat_score += signal['points']
                    detected_signals.append(signal['name'])
                    break
                    
        # Normalize category score by weight
        normalized_cat_score = (cat_score / cat_max) * category['weight'] if cat_max > 0 else 0
        scores[cat_name] = round(min(normalized_cat_score, category['weight']), 2)
        total_score += scores[cat_name]
        
    # Bonus points
    bonus_score = 0
    for bonus in criteria['bonus_signals']['bonuses']:
        for keyword in bonus['keywords']:
            if keyword.lower() in text:
                bonus_score += bonus['bonus_points']
                detected_signals.append(bonus['name'])
                break
                
    total_score = min(round(total_score + bonus_score, 2), 100)
    
    meets_threshold = total_score >= criteria['scoring_model']['passing_threshold']
    priority = "High" if total_score >= criteria['scoring_model']['high_priority_threshold'] else "Medium" if meets_threshold else "Low"
    
    # Financial research mockup (would normally be an API call)
    financials = {"estimated_base": "$200k-$300k", "public_company": lead['company'] in ['Netflix', 'Spotify']}
    
    return {
        "job_id": lead['job_id'],
        "company": lead['company'],
        "role_title": lead['role_title'],
        "location": lead['location'],
        "application_url": lead['application_url'],
        "raw_jd_text": jd_text,
        "detected_signals": list(set(detected_signals)),
        "category_scores": scores,
        "total_score": total_score,
        "meets_threshold": meets_threshold,
        "priority_level": priority,
        "financials": financials,
        "recommended_actions": ["Apply directly"] if meets_threshold else ["Skip"]
    }

enriched_leads = []
for lead in leads:
    scored = score_lead(lead)
    if "reason" not in scored: # Passed hard filters
        enriched_leads.append(scored)

with open('data/leads/enriched_leads.json', 'w') as f:
    json.dump(enriched_leads, f, indent=2)

print(f"Scored and saved {len(enriched_leads)} leads.")
