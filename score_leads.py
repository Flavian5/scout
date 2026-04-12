import json
import re

# Load data
with open('data/leads/raw_leads.json', 'r') as f:
    leads = json.load(f)

with open('config/criteria.json', 'r') as f:
    criteria = json.load(f)

with open('config/persona.md', 'r') as f:
    persona_text = f.read()

# Tier mapping for level alignment
def get_company_tier(company):
    """Determine company tier based on AI-criticality and resilience"""
    tier1_companies = criteria['categories']['level_alignment']['tier_rules']['tier1_ai_critical']['target_companies']
    tier2_companies = criteria['categories']['level_alignment']['tier_rules']['tier2_resilient']['target_companies']
    tier3_companies = criteria['categories']['level_alignment']['tier_rules']['tier3_other']['target_companies']
    
    if company in tier1_companies:
        return "tier1_ai_critical"
    elif company in tier2_companies:
        return "tier2_resilient"
    elif company in tier3_companies:
        return "tier3_other"
    return None

def check_level_alignment(role_title, company):
    """Check if role level matches company tier requirements"""
    role_lower = role_title.lower()
    tier = get_company_tier(company)
    
    if not tier:
        return 0, "unknown_tier"
    
    tier_rules = criteria['categories']['level_alignment']['tier_rules'][tier]
    
    # Check if role contains required level keywords
    is_staff = any(lvl in role_lower for lvl in ['staff', 'principal'])
    is_senior = any(lvl in role_lower for lvl in ['senior', 'lead'])
    
    if tier == "tier1_ai_critical":
        # Tier 1: Accept Senior, Staff, Principal (bonus for getting in)
        if is_senior or is_staff:
            return tier_rules.get('level_bonus', 5), tier
        return 0, tier
    
    elif tier == "tier2_resilient":
        # Tier 2: Staff OR Senior both OK
        if is_staff or is_senior:
            return 0, tier
        return 0, tier
    
    elif tier == "tier3_other":
        # Tier 3: Staff OR Senior both OK (no penalty)
        if is_staff or is_senior:
            return 0, tier
        return 0, tier
    
    return 0, tier

def score_lead(lead):
    # Handle both field name variations
    jd_text = lead.get('raw_jd_text') or lead.get('job_description_raw') or ''
    text = (jd_text + ' ' + lead.get('role_title', '')).lower()
    company = lead.get('company', '')
    role_title = lead.get('role_title', '')
    
    # Check hard filters
    for filter_rule in criteria['filter_rules']['hard_no']:
        for keyword in filter_rule['exclude_keywords']:
            if keyword.lower() in text:
                return {"meets_threshold": False, "reason": f"Failed hard filter: {keyword}"}
                
    scores = {}
    detected_signals = []
    total_score = 0
    
    for cat_name, category in criteria['categories'].items():
        # Skip level_alignment in the main loop (handled separately)
        if cat_name == 'level_alignment':
            continue
            
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
    
    # Level alignment bonus/penalty
    level_score, tier = check_level_alignment(role_title, company)
    scores['level_alignment'] = level_score
    total_score += level_score
    detected_signals.append(f"level_{tier}")
        
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
        "tier": tier,
        "financials": financials,
        "recommended_actions": ["Apply directly"] if meets_threshold else ["Skip"]
    }

enriched_leads = []
for lead in leads:
    scored = score_lead(lead)
    if "reason" not in scored: # Passed hard filters
        enriched_leads.append(scored)

# Sort by score descending
enriched_leads.sort(key=lambda x: x['total_score'], reverse=True)

with open('data/leads/enriched_leads.json', 'w') as f:
    json.dump(enriched_leads, f, indent=2)

print(f"Scored and saved {len(enriched_leads)} leads.")
print("\n=== SHORTLIST ===")
for lead in enriched_leads:
    if lead['meets_threshold']:
        print(f"✅ {lead['company']} - {lead['role_title']} (Score: {lead['total_score']}, Tier: {lead.get('tier', 'N/A')})")
    else:
        print(f"❌ {lead['company']} - {lead['role_title']} (Score: {lead['total_score']}, Tier: {lead.get('tier', 'N/A')})")
