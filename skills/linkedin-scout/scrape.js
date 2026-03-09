#!/usr/bin/env node

/**
 * LinkedIn Job Scraper (Public Search Approach)
 * 
 * Uses Playwright to fetch and parse the initial HTML of LinkedIn public job search.
 * This approach is less prone to bot detection than full head-loaded page.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco Bay Area"
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
    outputFile: null
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
    }
  }
  
  return config;
}

/**
 * Build LinkedIn public search URL with pagination
 */
function buildPublicSearchUrl(keywords, location, start = 0) {
  const encodedKeywords = encodeURIComponent(keywords);
  const encodedLocation = encodeURIComponent(location);
  
  // LinkedIn public job search URL with f_TPR filter for daily posts
  // f_TPR values: r86400 (24h), r604800 (7 days), r2592000 (30 days)
  return `https://www.linkedin.com/jobs/search/?keywords=${encodedKeywords}&location=${encodedLocation}&f_TPR=r604800&start=${start}`;
}

/**
 * Extract job card data from LinkedIn public search results
 */
async function extractJobCards(page) {
  // Wait for job cards to load
  await page.waitForSelector('.job-card-container, .base-card, .base-search-card__title', { timeout: 15000 }).catch(() => {
     // fallback selector
    return page.waitForSelector('.job-card-title, h3.base-search-card__title', { timeout: 5000 }).catch(() => {});
  });
  
  // Get all job cards
  const jobCards = await page.evaluate(() => {
     // selectors for public public job search
    const cards = document.querySelectorAll('.jobs-card-layout, .base-card, .base-search-card');
    return Array.from(cards).map(card => {
      
      const titleEl = card.querySelector('.base-search-card__title, .job-search-card__title, .job-card-container__title, .job-card-title, h3.base-search-card__title');
      const companyEl = card.querySelector('.base-search-card__subtitle, .job-search-card__company-name, .job-card-container__company-name, .job-card-container__subtitle, .job-card-company-name, h4.base-search-card__subtitle a');
      const locationEl = card.querySelector('.job-search-card__location, .job-card-container__metadata-item, .job-card-location, .job-card-container__snippet, .job-search-card__location');
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
  
  console.error(`Searching LinkedIn (Public Search) for: "${config.keywords}" in ${config.location}`);
  console.error(`Date filter: Last 7 days (f_TPR=r604800)`);
  
  // Launch browser in headless mode for automation
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
  
  const results = [];
  const seenLinks = new Set();
  let pageStart = 0;
  const pageSize = 25; // LinkedIn shows 25 jobs per page
  let hasMorePages = true;
  let pageCount = 0;
  
  try {
    while (hasMorePages && results.length < config.limit) {
      pageCount++;
      console.error(`\n=== Page ${pageCount} (start=${pageStart}) ===`);
      
      // Navigate to search results with pagination
      const searchUrl = buildPublicSearchUrl(config.keywords, config.location, pageStart);
      console.error(`Navigating to: ${searchUrl}`);
      
      await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
      
      // Wait for jobs to load
      await page.waitForTimeout(5000);
      
      // Extract job cards
      const jobs = await extractJobCards(page);
      console.error(`Found ${jobs.length} job cards on this page`);
      
      if (jobs.length === 0) {
        hasMorePages = false;
        break;
      }
      
      // Process each job
      for (const job of jobs) {
        // Skip duplicates
        if (seenLinks.has(job.link)) {
          continue;
        }
        seenLinks.add(job.link);
        
        // Build job object
        const jobData = {
          source: 'linkedin_public',
          job_id: `linkedin_${uuidv4().substring(0, 8)}`,
          role_title: job.title,
          company: job.company,
          location: job.location,
          application_url: job.link,
          job_description_raw: '',
          salary_range: null,
          posted_date: job.posted,
          detected_signals: detectSignals('', job.company),
          scraped_at: new Date().toISOString()
        };
        
        results.push(jobData);
        console.error(`Processed: ${job.title} at ${job.company}`);
        
        // Stop if we've reached the limit
        if (results.length >= config.limit) {
          break;
        }
      }
      
      // Check if there are more pages
      // LinkedIn typically has 1000+ results but limits pagination
      if (jobs.length < pageSize) {
        hasMorePages = false;
      } else if (pageStart >= 1000) {
        // LinkedIn public search typically limits to ~1000 results (40 pages)
        console.error('Reached LinkedIn pagination limit (~1000 results)');
        hasMorePages = false;
      } else {
        pageStart += pageSize;
        // Rate limiting between pages
        await page.waitForTimeout(2000);
      }
    }
    
    console.error(`\n=== Summary ===`);
    console.error(`Total pages scraped: ${pageCount}`);
    console.error(`Total jobs collected: ${results.length}`);
    
    // Output results
    const output = JSON.stringify(results, null, 2);
    
    if (config.outputFile) {
       fs.writeFileSync(config.outputFile, output);
       console.error(`Results written to: ${config.outputFile}`);
    } else {
       console.log(output);
    }
    
  } catch (e) {
     console.error('Scraping error:', e.message);
     process.exit(1);
  } finally {
     await browser.close();
  }
}

// Run the scraper
scrape().catch(e => {
   console.error('Fatal error:', e);
   process.exit(1);
});