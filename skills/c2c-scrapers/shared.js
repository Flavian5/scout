/**
 * C2C Scraper Shared Library
 * 
 * Common utilities for C2C/contract job scrapers:
 * - Signal detection (project-based vs staff augmentation)
 * - Rate extraction
 * - Job data normalization
 * 
 * Usage:
 *   const { detectSignals, extractRate, normalizeJobData } = require('./c2c-scrapers/shared');
 */

const { v4: uuidv4 } = require('uuid');

// ============================================================
// SIGNAL DETECTION
// ============================================================

/**
 * Detect signals in job description for filtering
 * Returns array of signal tags
 */
function detectSignals(description, company, title) {
  const signals = [];
  const text = (description + ' ' + company + ' ' + title).toLowerCase();
  
  // --- ML/RecSys Signals ---
  if (text.includes('recommendation') || text.includes('recsys')) signals.push('recsys');
  if (text.includes('two-stage') || text.includes('two stage')) signals.push('two_stage_ranking');
  if (text.includes('generation') || text.includes('genrec')) signals.push('genrec');
  if (text.includes('foundation model') || text.includes('llm') || text.includes('transformer')) signals.push('foundation_models');
  
  // --- Bio-AI Signals ---
  if (text.includes('virtual cell') || text.includes('cell')) signals.push('virtual_cell');
  if (text.includes('digital twin')) signals.push('digital_twin');
  if (text.includes('drug discovery')) signals.push('drug_discovery');
  if (text.includes('bioai') || text.includes('bio-ai')) signals.push('bio_ai');
  
  // --- Infrastructure Signals ---
  if (text.includes('ml platform') || text.includes('ml infrastructure')) signals.push('ml_platform');
  if (text.includes('feature store')) signals.push('feature_store');
  if (text.includes('ml pipeline')) signals.push('ml_pipeline');
  
  // --- PROJECT-BASED SIGNALS (GOOD - Filter FOR) ---
  if (text.includes('statement of work') || text.includes(' sow ') || text.includes('sow,')) signals.push('project_sow');
  if (text.includes('fixed-price') || text.includes('fixed price') || text.includes('fixed fee')) signals.push('project_fixed_price');
  if (text.includes('deliverable') || text.includes('deliverable-based')) signals.push('project_deliverable');
  if (text.includes('project-based') || text.includes('project based')) signals.push('project_based');
  if (text.includes('consulting') && !text.includes('staffing')) signals.push('consulting');
  if (text.includes('implementation') && !text.includes('augmentation')) signals.push('implementation');
  if (text.includes('corp-to-corp') || text.includes('c2c')) signals.push('c2c');
  if (text.includes('independent contractor')) signals.push('independent_contractor');
  
  // --- STAFF AUGMENTATION SIGNALS (BAD - Filter OUT) ---
  if (text.includes('staff augmentation') || text.includes('augmentation')) signals.push('staff_augmentation');
  if (text.includes('staffing') && !text.includes('consulting')) signals.push('staffing');
  if (text.includes('time and materials') || text.includes('t&m')) signals.push('time_and_materials');
  if (text.includes('w2') || text.includes('employee')) signals.push('w2_employee');
  if (text.includes('1085') || text.includes('1099')) signals.push('staffing_1099');
  if (text.includes('through agency') || text.includes('via staffing') || text.includes('through staffing')) signals.push('through_agency');
  
  return signals;
}

/**
 * Check if job is likely project-based (good) vs staff augmentation (bad)
 */
function isProjectBased(signals) {
  const projectSignals = ['project_sow', 'project_fixed_price', 'project_deliverable', 'project_based', 'consulting', 'c2c'];
  const badSignals = ['staff_augmentation', 'staffing', 'w2_employee', 'through_agency'];
  
  const hasProjectSignal = signals.some(s => projectSignals.includes(s));
  const hasBadSignal = signals.some(s => badSignals.includes(s));
  
  return hasProjectSignal && !hasBadSignal;
}

/**
 * Check if job meets minimum rate requirements
 */
function meetsRateRequirements(signals, rateMin, rateMax) {
  // If no rate info, assume it might meet requirements
  if (!rateMin && !rateMax) return true;
  
  const minRate = rateMin || rateMax;
  return minRate >= 100; // $100/hour minimum
}

// ============================================================
// RATE EXTRACTION
// ============================================================

/**
 * Extract rate information from job posting text
 */
function extractRate(rateStr) {
  if (!rateStr) return { rate_min: null, rate_max: null, rate_type: null };
  
  // Match hourly rates like "$100 - $150/hr" or "$120/hour" or "$150hr"
  const hourlyMatch = rateStr.match(/\$(\d+(?:,\d{3})*)(?:\s*-\s*\$(\d+(?:,\d{3})*))?\s*\/?hr/i);
  if (hourlyMatch) {
    return {
      rate_min: parseInt(hourlyMatch[1].replace(/,/g, ''), 10),
      rate_max: hourlyMatch[2] ? parseInt(hourlyMatch[2].replace(/,/g, ''), 10) : parseInt(hourlyMatch[1].replace(/,/g, ''), 10),
      rate_type: 'hourly'
    };
  }
  
  // Match project/fixed rates like "$50,000" or "$50k"
  const projectMatch = rateStr.match(/\$(\d+(?:,\d{3})*)(?:\s*(?:k|K|000))?/);
  if (projectMatch) {
    let value = parseInt(projectMatch[1].replace(/,/g, ''), 10);
    // Handle "k" suffix
    if (rateStr.match(/\d+k\b/i)) {
      value = value * 1000;
    }
    return {
      rate_min: value,
      rate_max: value,
      rate_type: 'project'
    };
  }
  
  return { rate_min: null, rate_max: null, rate_type: null };
}

// ============================================================
// JOB DATA NORMALIZATION
// ============================================================

/**
 * Normalize job data to standard format
 */
function normalizeJobData(rawJob, source) {
  const signals = detectSignals(
    rawJob.description || '',
    rawJob.company || '',
    rawJob.title || rawJob.role_title || ''
  );
  
  const rateInfo = extractRate(rawJob.rate || rawJob.salary || '');
  
  return {
    source: source,
    job_id: `${source}_${uuidv4().substring(0, 8)}`,
    role_title: rawJob.title || rawJob.role_title || '',
    company: rawJob.company || '',
    location: rawJob.location || '',
    application_url: rawJob.link || rawJob.url || rawJob.application_url || '',
    job_description_raw: rawJob.description || rawJob.job_description_raw || '',
    contract_details: {
      rate_type: rateInfo.rate_type,
      rate_min: rateInfo.rate_min,
      rate_max: rateInfo.rate_max,
      duration: rawJob.duration || rawJob.posted || '',
      engagement_type: rawJob.employmentType || rawJob.contractType || 'Contract'
    },
    skills: rawJob.skills || [],
    detected_signals: signals,
    is_project_based: isProjectBased(signals),
    meets_rate_requirement: meetsRateRequirements(signals, rateInfo.rate_min, rateInfo.rate_max),
    scraped_at: new Date().toISOString()
  };
}

// ============================================================
// FILTERING
// ============================================================

/**
 * Filter jobs based on C2C criteria
 */
function filterJobs(jobs, options = {}) {
  const {
    minRate = 100,
    requireProjectBased = false,
    excludeStaffAugmentation = true
  } = options;
  
  return jobs.filter(job => {
    // Check rate requirement
    const rateMin = job.contract_details?.rate_min;
    if (rateMin && rateMin < minRate) {
      return false;
    }
    
    // Check project-based requirement
    if (requireProjectBased && !job.is_project_based) {
      return false;
    }
    
    // Check for staff augmentation signals
    if (excludeStaffAugmentation) {
      const badSignals = ['staff_augmentation', 'staffing', 'w2_employee', 'through_agency'];
      if (job.detected_signals?.some(s => badSignals.includes(s))) {
        return false;
      }
    }
    
    return true;
  });
}

// ============================================================
// EXPORTS
// ============================================================

module.exports = {
  // Signal detection
  detectSignals,
  isProjectBased,
  meetsRateRequirements,
  
  // Rate extraction
  extractRate,
  
  // Data normalization
  normalizeJobData,
  
  // Filtering
  filterJobs
};