#!/usr/bin/env node

/**
 * Dice Job Scraper - C2C/Contract Focus
 * 
 * Scrapes Dice.com for contract and C2C job opportunities.
 * Uses shared C2C scraper library for signal detection and normalization.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco, CA"
 *   node scrape.js --keywords "ML Platform" --contract-only
 * 
 * Output: JSON array of job objects to stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');

// Enable stealth plugin
puppeteer.use(StealthPlugin());

// Import shared C2C utilities
const { detectSignals, extractRate, normalizeJobData, filterJobs } = require('../c2c-scrapers/shared');

// Default configuration
const DEFAULT_LOCATION = 'San Francisco, CA';
const DEFAULT_LIMIT = 50;

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    keywords: '',
    location: DEFAULT_LOCATION,
    contractOnly: true,
    remoteOnly: false,
    postedWithin: 3,
    limit: DEFAULT_LIMIT,
    outputFile: null,
    filterProjectBased: false
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--keywords' || arg === '-k') {
      config.keywords = nextArg;
      i++;
    } else if (arg === '--location' || arg === '-l') {
      config.location = nextArg;
      i++;
    } else if (arg === '--contract-only' || arg === '-c') {
      config.contractOnly = true;
    } else if (arg === '--remote-only' || arg === '-r') {
      config.remoteOnly = true;
    } else if (arg === '--posted-within' || arg === '-d') {
      config.postedWithin = parseInt(nextArg, 10);
      i++;
    } else if (arg === '--limit' || arg === '-L') {
      config.limit = parseInt(nextArg, 10);
      i++;
    } else if (arg === '--output' || arg === '-o') {
      config.outputFile = nextArg;
      i++;
    } else if (arg === '--project-based') {
      config.filterProjectBased = true;
    }
  }
  
  return config;
}

/**
 * Load Dice cookies from secrets file if available
 */
async function loadDiceCookies() {
  const secretsPath = path.join(__dirname, '../../config/secrets.json');
  if (fs.existsSync(secretsPath)) {
    try {
      const secrets = JSON.parse(fs.readFileSync(secretsPath, 'utf8'));
      if (secrets.dice) {
        return secrets.dice;
      }
    } catch (e) {
      console.error('Error loading secrets:', e.message);
    }
  }
  return null;
}

/**
 * Build Dice search URL
 */
function buildDiceUrl(keywords, location, contractOnly, remoteOnly, postedWithin) {
  const encodedKeywords = encodeURIComponent(keywords);
  const encodedLocation = remoteOnly ? 'Remote' : encodeURIComponent(location);
  
  let url = `https://www.dice.com/jobs?q=${encodedKeywords}&location=${encodedLocation}`;
  
  const filters = [];
  
  if (contractOnly) {
    filters.push('filters.employmentType=CONTRACTS');
  }
  
  const postedDateMap = { 1: 'ONE', 3: 'THREE', 7: 'SEVEN', 30: 'THIRTY' };
  const postedDateValue = postedDateMap[postedWithin] || 'SEVEN';
  filters.push(`filters.postedDate=${postedDateValue}`);
  
  if (remoteOnly) {
    filters.push('filters.remote=Remote');
  }
  
  filters.push('pageSize=100');
  
  if (filters.length > 0) {
    url += '&' + filters.join('&');
  }
  
  return url;
}

/**
 * Extract job cards from Dice search results
 */
async function extractJobCards(page) {
  try {
    await page.waitForSelector('[data-cy="search-result-card"], .search-card, .job-card', { timeout: 15000 });
  } catch (e) {
    console.error('Warning: Could not find job cards with primary selectors');
  }
  
  await new Promise(resolve => setTimeout(resolve, 3000));
  
  const jobs = await page.evaluate(() => {
    const results = [];
    const cardSelectors = [
      '[data-cy="search-result-card"]',
      '.search-card',
      '.job-card',
      '[class*="search-result"]',
      '[class*="job-card"]'
    ];
    
    let cards = [];
    for (const selector of cardSelectors) {
      cards = document.querySelectorAll(selector);
      if (cards.length > 0) break;
    }
    
    cards.forEach(card => {
      const titleEl = card.querySelector('a[data-cy="job-title"], .job-title a, h5 a, a[href*="/jobs/"]');
      const companyEl = card.querySelector('[data-cy="company-name"], .company-name, [class*="company"]');
      const locationEl = card.querySelector('[data-cy="location"], .location, [class*="location"]');
      const postedEl = card.querySelector('[data-cy="posted-date"], .posted-date, time');
      const typeEl = card.querySelector('[data-cy="employment-type"], .employment-type, [class*="type"]');
      const rateEl = card.querySelector('[data-cy="pay-rate"], .pay-rate, [class*="salary"], [class*="rate"]');
      
      if (titleEl) {
        const link = titleEl.href || '';
        results.push({
          title: titleEl.textContent.trim(),
          company: companyEl ? companyEl.textContent.trim() : '',
          location: locationEl ? locationEl.textContent.trim() : '',
          posted: postedEl ? postedEl.textContent.trim() : '',
          employmentType: typeEl ? typeEl.textContent.trim() : '',
          rate: rateEl ? rateEl.textContent.trim() : '',
          link: link.startsWith('http') ? link : `https://www.dice.com${link}`
        });
      }
    });
    
    return results;
  });
  
  const seen = new Set();
  return jobs.filter(job => {
    if (!job.link || seen.has(job.link)) return false;
    seen.add(job.link);
    return true;
  });
}

/**
 * Get detailed job information from job page
 */
async function getJobDetails(page, jobUrl) {
  try {
    await page.goto(jobUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    const details = await page.evaluate(() => {
      const result = {
        description: '',
        skills: [],
        rate: '',
        duration: '',
        contractType: ''
      };
      
      const descEl = document.querySelector('#jobdescSec, .job-desc, [data-cy="job-description"], .description');
      if (descEl) {
        result.description = descEl.textContent.trim().substring(0, 5000);
      }
      
      const skillEls = document.querySelectorAll('[data-cy="skill"], .skill-tag, [class*="skill"] span');
      result.skills = Array.from(skillEls).map(el => el.textContent.trim()).filter(s => s);
      
      const rateEl = document.querySelector('[data-cy="pay-rate"], .pay-rate, [class*="rate"]');
      if (rateEl) {
        result.rate = rateEl.textContent.trim();
      }
      
      const durationEl = document.querySelector('[data-cy="duration"], .duration, [class*="duration"]');
      if (durationEl) {
        result.duration = durationEl.textContent.trim();
      }
      
      const contractEl = document.querySelector('[data-cy="contract-type"], .contract-type, [class*="contract"]');
      if (contractEl) {
        result.contractType = contractEl.textContent.trim();
      }
      
      return result;
    });
    
    return details;
  } catch (e) {
    console.error('Error getting job details:', e.message);
    return { description: '', skills: [], rate: '', duration: '', contractType: '' };
  }
}

/**
 * Main scraper function
 */
async function scrape() {
  const config = parseArgs();
  
  if (!config.keywords) {
    console.error('Error: --keywords is required');
    console.error('Usage: node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco, CA"');
    process.exit(1);
  }
  
  console.error(`Searching Dice for: "${config.keywords}" in ${config.location}`);
  console.error(`Contract only: ${config.contractOnly}, Remote: ${config.remoteOnly}, Posted: ${config.postedWithin} days`);
  if (config.filterProjectBased) {
    console.error('Filtering for project-based opportunities only');
  }
  
  const diceCookies = await loadDiceCookies();
  if (diceCookies) {
    console.error('Using authenticated session');
  }
  
  const browser = await puppeteer.launch({
    headless: true,
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--disable-gpu'
    ]
  });
  
  const context = await browser.createBrowserContext();
  
  if (diceCookies && diceCookies.session) {
    await context.setCookie({
      name: 'JSESSIONID',
      value: diceCookies.session,
      domain: '.dice.com',
      path: '/'
    });
  }
  
  const page = await context.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    const searchUrl = buildDiceUrl(config.keywords, config.location, config.contractOnly, config.remoteOnly, config.postedWithin);
    console.error(`Navigating to: ${searchUrl}`);
    
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const pageInfo = await page.evaluate(() => ({
      title: document.title,
      url: window.location.href,
      jobCount: document.querySelectorAll('[class*="job-card"], .search-card').length
    }));
    console.error('Page info:', JSON.stringify(pageInfo));
    
    const jobs = await extractJobCards(page);
    console.error(`Found ${jobs.length} job cards`);
    
    const results = [];
    const limit = Math.min(config.limit, jobs.length);
    
    for (let i = 0; i < limit; i++) {
      const job = jobs[i];
      
      let details = { description: '', skills: [], rate: '', duration: '', contractType: '' };
      if (i < 10) {
        details = await getJobDetails(page, job.link);
        await page.goBack({ waitUntil: 'domcontentloaded' });
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
      
      // Use shared normalizeJobData
      const rawJob = {
        ...job,
        description: details.description,
        skills: details.skills,
        duration: details.duration || job.posted
      };
      
      const normalizedJob = normalizeJobData(rawJob, 'dice');
      results.push(normalizedJob);
      
      const signalInfo = normalizedJob.is_project_based ? '[PROJECT-BASED]' : '[STAFF AUG]';
      console.error(`Processed: ${signalInfo} ${job.title} at ${job.company}`);
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Apply filtering if requested
    let finalResults = results;
    if (config.filterProjectBased) {
      finalResults = filterJobs(results, { requireProjectBased: true });
      console.error(`\n=== Filtering ===`);
      console.error(`After project-based filter: ${finalResults.length} jobs (from ${results.length})`);
    }
    
    const output = JSON.stringify(finalResults, null, 2);
    
    if (config.outputFile) {
      fs.writeFileSync(config.outputFile, output);
      console.error(`Results written to: ${config.outputFile}`);
    } else {
      console.log(output);
    }
    
    console.error(`\n=== Summary ===`);
    console.error(`Total jobs found: ${results.length}`);
    console.error(`Project-based jobs: ${results.filter(j => j.is_project_based).length}`);
    
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