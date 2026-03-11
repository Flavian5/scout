#!/usr/bin/env node

/**
 * LinkedIn Recommended Jobs Scraper
 * 
 * Uses fresh browser with authenticated session cookies.
 * Anti-detection measures:
 * - Fresh browser each run (no cached fingerprint)
 * - Human-like delays and mouse movements
 * - Realistic navigation flow
 * 
 * Usage:
 *   node scrape.js --max-jd 10
 *   node scrape.js --max-jd 5 --output jobs.json
 * 
 * Output: JSON array of job objects to stdout
 */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// Default configuration
const DEFAULT_MAX_JOBS = 15;

// Secrets path
const SECRETS_PATH = path.join(__dirname, '..', '..', 'config', 'secrets.json');

/**
 * Load secrets from config/secrets.json
 */
function loadSecrets() {
  try {
    if (fs.existsSync(SECRETS_PATH)) {
      const content = fs.readFileSync(SECRETS_PATH, 'utf8');
      return JSON.parse(content);
    }
  } catch (e) {
    console.error('Warning: Could not load secrets.json:', e.message);
  }
  return null;
}

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    maxJobs: DEFAULT_MAX_JOBS,
    outputFile: null
  };
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--max-jd' && args[i + 1]) {
      config.maxJobs = parseInt(args[i + 1], 10);
      i++;
    } else if (args[i] === '--output' && args[i + 1]) {
      config.outputFile = args[i + 1];
      i++;
    }
  }
  
  return config;
}

/**
 * Random delay to mimic human behavior
 */
function randomDelay(minMs = 1000, maxMs = 3000) {
  const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
  return new Promise(resolve => setTimeout(resolve, delay));
}

/**
 * Move mouse naturally to random position
 */
async function humanMouseMovement(page) {
  const viewport = page.viewportSize();
  if (!viewport) return;
  
  const targetX = Math.floor(Math.random() * viewport.width);
  const targetY = Math.floor(Math.random() * viewport.height);
  
  for (let i = 0; i < 5; i++) {
    const x = Math.floor((targetX / 5) * (i + 1) + Math.random() * 50 - 25);
    const y = Math.floor((targetY / 5) * (i + 1) + Math.random() * 50 - 25);
    await page.mouse.move(x, y);
    await randomDelay(50, 150);
  }
}

/**
 * Extract job data from the right panel
 */
async function extractJobFromRightPanel(page) {
  return await page.evaluate(() => {
    const titleEl = document.querySelector('.job-details-jobs-unified-top-card__job-title h1 a, .job-details-jobs-unified-top-card__job-title h1');
    const title = titleEl ? titleEl.textContent.trim() : '';
    
    const companyEl = document.querySelector('.job-details-jobs-unified-top-card__company-name a');
    const company = companyEl ? companyEl.textContent.trim() : '';
    
    const locationEl = document.querySelector('.job-details-jobs-unified-top-card__tertiary-description-container');
    const location = locationEl ? locationEl.textContent.trim().replace(/\s+/g, ' ').trim() : '';
    
    const jdSelectors = [
      '#job-details',
      '.jobs-description__content',
      '.jobs-box__html-content',
      '.job-details-module .jobs-description__container',
      '.jobs-description__container .jobs-description__content'
    ];
    
    let jdText = '';
    for (const sel of jdSelectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent.trim().length > 100) {
        jdText = el.textContent.trim();
        break;
      }
    }
    
    if (!jdText) {
      const mainContent = document.querySelector('.jobs-details__main-content');
      if (mainContent) {
        jdText = mainContent.textContent.trim().substring(0, 15000);
      }
    }
    
    const salaryEl = document.querySelector('#SALARY, .jobs-details__salary-main-rail-card');
    const salary = salaryEl ? salaryEl.textContent.trim() : null;
    
    const applyButton = document.querySelector('button[data-live-test-job-apply-button], a[href*="/jobs/view/"]');
    const applyUrl = applyButton ? applyButton.href || applyButton.getAttribute('data-job-apply-url') : null;
    
    return { title, company, location, jdText, salary, applyUrl };
  });
}

/**
 * Detect signals in job description
 */
function detectSignals(description, company) {
  const signals = [];
  const text = (description + ' ' + company).toLowerCase();
  
  if (text.includes('recommendation') || text.includes('recsys')) signals.push('recsys');
  if (text.includes('two-stage') || text.includes('two stage')) signals.push('two_stage_ranking');
  if (text.includes('generative recommendation') || text.includes('genrec')) signals.push('genrec');
  if (text.includes('foundation model') || text.includes('llm') || text.includes('transformer')) signals.push('foundation_models');
  if (text.includes('virtual cell') || text.includes('cellular')) signals.push('virtual_cell');
  if (text.includes('digital twin')) signals.push('digital_twin');
  if (text.includes('drug discovery')) signals.push('drug_discovery');
  if (text.includes('phenomics')) signals.push('phenomics');
  if (text.includes('bioai') || text.includes('bio-ai') || text.includes('computational biology')) signals.push('bio_ai');
  if (text.includes('ml platform') || text.includes('ml infrastructure')) signals.push('ml_platform');
  if (text.includes('feature store')) signals.push('feature_store');
  if (text.includes('ml pipeline') || text.includes('pipeline')) signals.push('ml_pipeline');
  if (text.includes('voice agent') || text.includes('voice ai')) signals.push('voice_agent');
  if (text.includes('customer experience') || text.includes('cx automation')) signals.push('cx_automation');
  
  return [...new Set(signals)];
}

/**
 * Main scraper function
 */
async function scrape() {
  const config = parseArgs();
  
  const secrets = loadSecrets();
  const hasAuth = secrets?.linkedin?.li_at && secrets?.linkedin?.jsessionid;
  
  if (!hasAuth) {
    console.error('Error: LinkedIn session cookies not found in config/secrets.json');
    process.exit(1);
  }
  
  console.error(`Scraping LinkedIn recommended jobs...`);
  console.error(`Max jobs to process: ${config.maxJobs}`);
  
  // Connect to existing Chrome via CDP (must start Chrome with --remote-debugging-port=9222)
  console.error('Connecting to existing Chrome via CDP...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  
  // Get the default context
  const context = browser.contexts()[0];
  const pages = context.pages();
  const page = pages.length > 0 ? pages[0] : await context.newPage();
  
  console.error('Connected to existing Chrome - using your logged-in session');
  
  // Go straight to recommended jobs (skip feed)
  console.error('Navigating directly to recommended jobs...');
  await randomDelay(1500, 2500);
  await humanMouseMovement(page);
  
  try {
    await page.goto('https://www.linkedin.com/jobs/collections/recommended/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  } catch (e) {
    console.error('Warning: Initial navigation failed, retrying...');
    await page.goto('https://www.linkedin.com/jobs/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(2000, 4000);
    await page.goto('https://www.linkedin.com/jobs/collections/recommended/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  }
  
  await randomDelay(4000, 6000);
  
  // Check if logged in
  const currentUrl = page.url();
  console.error(`Current URL: ${currentUrl}`);
  
  if (currentUrl.includes('/login') || currentUrl.includes('authwall')) {
    console.error('Error: Not logged in. Cookies may be invalid or expired.');
    await browser.close();
    process.exit(1);
  }
  
  // Debug: check page content
  console.error('Debug: Checking page content...');
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.error('Page body text (first 500 chars):', bodyText.substring(0, 500));
  
  // Scroll to load more jobs
  console.error('Scrolling to load more jobs...');
  for (let scroll = 0; scroll < 3; scroll++) {
    await page.evaluate(() => window.scrollBy(0, 500));
    await randomDelay(1500, 2500);
  }
  
  // Extract job cards
  const jobCards = await page.evaluate(() => {
    let cards = document.querySelectorAll('div[data-job-id]');
    if (cards.length === 0) cards = document.querySelectorAll('.job-card-container');
    if (cards.length === 0) cards = document.querySelectorAll('.jobs-recommended-list__item');
    if (cards.length === 0) cards = document.querySelectorAll('.jobs-search-results__list-item');
    
    return Array.from(cards).map(card => ({
      jobId: card.getAttribute('data-job-id') || card.id || Math.random().toString(36).substr(2, 9),
      title: card.querySelector('.job-card-list__title--link')?.textContent?.trim() || 
             card.querySelector('.job-card-container__title-text')?.textContent?.trim() ||
             card.querySelector('a[href*="/jobs/view/"]')?.getAttribute('aria-label') || '',
      company: card.querySelector('.artdeco-entity-lockup__subtitle')?.textContent?.trim() || 
               card.querySelector('.job-card-container__company-name')?.textContent?.trim() || '',
      location: card.querySelector('.job-card-container__metadata-wrapper')?.textContent?.trim() || ''
    }));
  });
  
  console.error(`Found ${jobCards.length} job cards in sidebar`);
  
  if (jobCards.length === 0) {
    console.error('Error: No jobs found. Try different keywords or location.');
    await browser.close();
    process.exit(1);
  }
  
  const results = [];
  const maxJobs = Math.min(jobCards.length, config.maxJobs);
  
  // Click each job card and extract JD
  for (let i = 0; i < maxJobs; i++) {
    const card = jobCards[i];
    console.error(`[${i+1}/${maxJobs}] Clicking: ${card.title} at ${card.company}`);
    
    try {
      await humanMouseMovement(page);
      await randomDelay(500, 1000);
      
      await page.click(`div[data-job-id="${card.jobId}"]`);
      
      await randomDelay(3000, 5000);
      
      try {
        await page.waitForSelector('.jobs-description__content, #job-details, .jobs-box__html-content', { timeout: 5000 });
      } catch (e) {}
      
      const jdData = await extractJobFromRightPanel(page);
      
      const jobData = {
        source: 'linkedin',
        job_id: `linkedin_${card.jobId}`,
        role_title: jdData.title || card.title,
        company: jdData.company || card.company,
        location: jdData.location || card.location,
        application_url: jdData.applyUrl || `https://www.linkedin.com/jobs/view/${card.jobId}/`,
        job_description_raw: jdData.jdText,
        salary_range: jdData.salary,
        posted_date: null,
        job_type: 'FTE',
        detected_signals: detectSignals(jdData.jdText, jdData.company),
        scraped_at: new Date().toISOString()
      };
      
      results.push(jobData);
      console.error(`  ✓ Extracted JD (${jdData.jdText.length} chars), signals: ${jobData.detected_signals.join(', ') || 'none'}`);
      
    } catch (e) {
      console.error(`  ✗ Error: ${e.message}`);
    }
    
    await randomDelay(8000, 15000);
  }
  
  console.error(`\n=== Summary ===`);
  console.error(`Jobs processed: ${results.length}`);
  console.error(`Jobs with JD: ${results.filter(j => j.job_description_raw).length}`);
  
  const output = JSON.stringify(results, null, 2);
  if (config.outputFile) {
    fs.writeFileSync(config.outputFile, output);
    console.error(`Results written to: ${config.outputFile}`);
  } else {
    console.log(output);
  }
  
  await browser.close();
}

scrape().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});