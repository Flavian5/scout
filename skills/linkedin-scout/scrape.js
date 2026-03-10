#!/usr/bin/env node

/**
 * LinkedIn Job Scraper (Public Search Approach)
 * 
 * Uses Playwright to fetch and parse LinkedIn public job search.
 * Supports both FTE and Contract positions.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco Bay Area"
 *   node scrape.js --keywords "ML Engineer" --include-contract
 *   node scrape.js --keywords "ML Engineer" --output fte.json --output-contract contracts.json
 * 
 * Output: JSON array of job objects to stdout
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Default configuration
const DEFAULT_LOCATION = 'San Francisco Bay Area';
const DEFAULT_LIMIT = 50;

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    keywords: '',
    location: DEFAULT_LOCATION,
    limit: DEFAULT_LIMIT,
    outputFile: null,
    outputContractFile: null,
    includeContract: false
  };
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--keywords' && args[i + 1]) {
      config.keywords = args[i + 1];
      i++;
    } else if (args[i] === '--location' && args[i + 1]) {
      config.location = args[i + 1];
      i++;
    } else if (args[i] === '--limit' && args[i + 1]) {
      config.limit = parseInt(args[i + 1], 10);
      i++;
    } else if (args[i] === '--output' && args[i + 1]) {
      config.outputFile = args[i + 1];
      i++;
    } else if (args[i] === '--output-contract' && args[i + 1]) {
      config.outputContractFile = args[i + 1];
      i++;
    } else if (args[i] === '--include-contract') {
      config.includeContract = true;
    }
  }
  
  return config;
}

/**
 * Build LinkedIn public search URL
 * 
 * @param {string} keywords - Search keywords
 * @param {string} location - Location
 * @param {string} jobType - F (Freelance), C (Contract), P (Part-time), F (Full-time)
 * @param {number} start - Pagination start
 */
function buildPublicSearchUrl(keywords, location, jobType = 'F', start = 0) {
  const encodedKeywords = encodeURIComponent(keywords);
  const encodedLocation = encodeURIComponent(location);
  
  // LinkedIn public job search URL
  // f_TPR: r86400 (24h), r604800 (7 days), r2592000 (30 days)
  // jobType: F (Freelance), C (Contract), P (Part-time), I (Internship), F (Full-time)
  // For full-time + contract: don't specify jobType (returns all)
  if (jobType === 'F') {
    return `https://www.linkedin.com/jobs/search/?keywords=${encodedKeywords}&location=${encodedLocation}&f_TPR=r604800&start=${start}`;
  }
  return `https://www.linkedin.com/jobs/search/?keywords=${encodedKeywords}&location=${encodedLocation}&f_TPR=r604800&jobType=${jobType}&start=${start}`;
}

/**
 * Extract job card data from LinkedIn public search results
 */
async function extractJobCards(page) {
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  const jobCards = await page.evaluate(() => {
    const cards = document.querySelectorAll('.jobs-card-layout, .base-card, .base-search-card, .job-card-list__entity, .jobs-search-results__list-item');
    return Array.from(cards).map(card => {
      const titleEl = card.querySelector('.base-search-card__title, .job-search-card__title, .job-card-container__title, .job-card-title, h3.base-search-card__title, .job-card-list__title');
      const companyEl = card.querySelector('.base-search-card__subtitle, .job-search-card__company-name, .job-card-container__company-name, .job-card-container__subtitle, .job-card-company-name, h4.base-search-card__subtitle a, .job-card-list__subtitle');
      const locationEl = card.querySelector('.job-search-card__location, .job-card-container__metadata-item, .job-card-location, .job-card-container__snippet, .job-search-card__location, .job-card-list__location');
      const linkEl = card.querySelector('a.base-card__full-link, a.job-card-list__title, a.job-card-container__title, a[href*="/jobs/view/"], a[href*="/jobs/search/"]');
      const postedEl = card.querySelector('time.job-search-card__listdate, time.job-search-card__listdate--new, .job-card-container__listed-time, .job-card-posted-time, .job-card-container__bullet');
      
      return {
        title: titleEl ? titleEl.textContent.trim() : '',
        company: companyEl ? companyEl.textContent.trim() : '',
        location: locationEl ? locationEl.textContent.trim() : '',
        link: linkEl ? linkEl.href : '',
        posted: postedEl ? postedEl.getAttribute('datetime') || postedEl.textContent.trim() : ''
      };
    }).filter(card => card.title && card.link);
  });
  
  return jobCards;
}

/**
 * Detect signals in job description using keyword matching
 */
function detectSignals(description, company) {
  const signals = [];
  const text = (description + ' ' + company).toLowerCase();
  
  // ML/RecSys signals
  if (text.includes('recommendation') || text.includes('recsys') || text.includes('rec')) signals.push('recsys');
  if (text.includes('two-stage') || text.includes('two stage')) signals.push('two_stage_ranking');
  if (text.includes('generation') || text.includes('genrec')) signals.push('genrec');
  if (text.includes('foundation model') || text.includes('llm') || text.includes('transformer')) signals.push('foundation_models');
  
  // Bio-AI signals  
  if (text.includes('virtual cell') || text.includes('cell')) signals.push('virtual_cell');
  if (text.includes('digital twin')) signals.push('digital_twin');
  if (text.includes('drug discovery') || text.includes('drug')) signals.push('drug_discovery');
  if (text.includes('phenomics')) signals.push('phenomics');
  if (text.includes('bioai') || text.includes('bio-ai')) signals.push('bio_ai');
  
  // Infrastructure signals
  if (text.includes('ml platform') || text.includes('ml infrastructure')) signals.push('ml_platform');
  if (text.includes('feature store')) signals.push('feature_store');
  if (text.includes('ml pipeline') || text.includes('pipeline')) signals.push('ml_pipeline');
  
  // Other signals
  if (text.includes('voice agent') || text.includes('voice')) signals.push('voice_agent');
  if (text.includes('c automatio') || text.includes('customer experience')) signals.push('cx_automation');
  
  return signals;
}

/**
 * Main scraper function with pagination
 */
async function scrape() {
  const config = parseArgs();
  
  if (!config.keywords) {
    console.error('Error: --keywords is required');
    console.error('Usage: node scrape.js --keywords "Machine Learning Engineer"');
    process.exit(1);
  }
  
  console.error(`Searching LinkedIn for: "${config.keywords}" in ${config.location}`);
  console.error(`Date filter: Last 7 days`);
  console.error(`Include contract: ${config.includeContract}`);
  
  const browser = await chromium.launch({ 
    headless: true,
    args: [
      '--disable-blink-features=AutomationControlled',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu'
    ]
  });
  
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
  });
  const page = await context.newPage();
  
  const fteResults = [];
  const contractResults = [];
  const seenLinks = new Set();
  let pageStart = 0;
  const pageSize = 25;
  let hasMorePages = true;
  let pageCount = 0;
  
  try {
    // First, search for FTE jobs
    console.error(`\n=== Phase 1: FTE Jobs ===`);
    while (hasMorePages && fteResults.length < config.limit) {
      pageCount++;
      console.error(`Page ${pageCount} (start=${pageStart})`);
      
      const searchUrl = buildPublicSearchUrl(config.keywords, config.location, 'F', pageStart);
      await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      const jobs = await extractJobCards(page);
      console.error(`Found ${jobs.length} job cards`);
      
      if (jobs.length === 0) {
        break;
      }
      
      for (const job of jobs) {
        if (seenLinks.has(job.link)) continue;
        seenLinks.add(job.link);
        
        const jobData = {
          source: 'linkedin',
          job_id: `linkedin_${uuidv4().substring(0, 8)}`,
          role_title: job.title,
          company: job.company,
          location: job.location,
          application_url: job.link,
          job_description_raw: '',
          salary_range: null,
          posted_date: job.posted,
          job_type: 'FTE',
          detected_signals: detectSignals('', job.company),
          scraped_at: new Date().toISOString()
        };
        
        fteResults.push(jobData);
        console.error(`  FTE: ${job.title} at ${job.company}`);
        
        if (fteResults.length >= config.limit) break;
      }
      
      if (jobs.length < pageSize || pageStart >= 1000) {
        break;
      }
      pageStart += pageSize;
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Then, search for Contract jobs if requested
    if (config.includeContract) {
      console.error(`\n=== Phase 2: Contract Jobs ===`);
      pageStart = 0;
      pageCount = 0;
      
      while (hasMorePages && contractResults.length < config.limit) {
        pageCount++;
        console.error(`Page ${pageCount} (start=${pageStart})`);
        
        // Search for contract/freelance jobs
        const searchUrl = buildPublicSearchUrl(config.keywords, config.location, 'C', pageStart);
        await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await new Promise(resolve => setTimeout(resolve, 5000));
        
        const jobs = await extractJobCards(page);
        console.error(`Found ${jobs.length} contract job cards`);
        
        if (jobs.length === 0) {
          break;
        }
        
        for (const job of jobs) {
          // Skip if already in FTE results
          if (seenLinks.has(job.link)) continue;
          seenLinks.add(job.link);
          
          const jobData = {
            source: 'linkedin',
            job_id: `linkedin_${uuidv4().substring(0, 8)}`,
            role_title: job.title,
            company: job.company,
            location: job.location,
            application_url: job.link,
            job_description_raw: '',
            salary_range: null,
            posted_date: job.posted,
            job_type: 'Contract',
            detected_signals: detectSignals('', job.company),
            scraped_at: new Date().toISOString()
          };
          
          contractResults.push(jobData);
          console.error(`  Contract: ${job.title} at ${job.company}`);
          
          if (contractResults.length >= config.limit) break;
        }
        
        if (jobs.length < pageSize || pageStart >= 1000) {
          break;
        }
        pageStart += pageSize;
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    
    console.error(`\n=== Summary ===`);
    console.error(`FTE jobs: ${fteResults.length}`);
    console.error(`Contract jobs: ${contractResults.length}`);
    
    // Output FTE results
    const fteOutput = JSON.stringify(fteResults, null, 2);
    if (config.outputFile) {
      fs.writeFileSync(config.outputFile, fteOutput);
      console.error(`FTE results written to: ${config.outputFile}`);
    } else {
      console.log(fteOutput);
    }
    
    // Output Contract results if requested
    if (config.outputContractFile && contractResults.length > 0) {
      const contractOutput = JSON.stringify(contractResults, null, 2);
      fs.writeFileSync(config.outputContractFile, contractOutput);
      console.error(`Contract results written to: ${config.outputContractFile}`);
    }
    
  } catch (e) {
    console.error('Scraping error:', e.message);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

scrape().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});