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
const DEFAULT_MAX_JOBS = 50;

// Paths
const SECRETS_PATH = path.join(__dirname, '..', '..', 'config', 'secrets.json');
const COOKIES_PATH = path.join(__dirname, 'cookies.json');

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
 * Save cookies to file for persistence
 */
function saveCookies(context) {
  try {
    const cookies = context.cookies();
    fs.writeFileSync(COOKIES_PATH, JSON.stringify(cookies, null, 2));
    console.error('Cookies saved to:', COOKIES_PATH);
  } catch (e) {
    console.error('Warning: Could not save cookies:', e.message);
  }
}

/**
 * Load cookies from file if available
 */
async function loadSavedCookies(context) {
  try {
    if (fs.existsSync(COOKIES_PATH)) {
      const cookies = JSON.parse(fs.readFileSync(COOKIES_PATH, 'utf8'));
      await context.addCookies(cookies);
      console.error('Loaded saved cookies from:', COOKIES_PATH);
      return true;
    }
  } catch (e) {
    console.error('Warning: Could not load saved cookies:', e.message);
  }
  return false;
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
  
  // Try to connect to existing Chrome first, otherwise launch fresh browser
  let browser;
  let page;
  let context;
  try {
    console.error('Trying to connect to existing Chrome via CDP...');
    browser = await chromium.connectOverCDP('http://localhost:9222');
    context = browser.contexts()[0];
    const pages = context.pages();
    page = pages.length > 0 ? pages[0] : await context.newPage();
    console.error('Connected to existing Chrome');
  } catch (e) {
    console.error('Could not connect to existing Chrome, launching fresh browser...');
    // Launch fresh browser with cookies
    browser = await chromium.launch({
      headless: false,
      args: ['--disable-blink-features=AutomationControlled']
    });
    
    context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    
    // Set LinkedIn cookies - try saved cookies first, then fall back to secrets
    let cookiesLoaded = await loadSavedCookies(context);
    
    if (!cookiesLoaded && secrets?.linkedin?.li_at) {
      // Use cookies from secrets.json
      await context.addCookies([
        {
          name: 'li_at',
          value: secrets.linkedin.li_at,
          domain: '.linkedin.com',
          path: '/',
          httpOnly: true,
          secure: true,
          sameSite: 'None'
        },
        {
          name: 'jsessionid',
          value: secrets.linkedin.jsessionid,
          domain: '.linkedin.com',
          path: '/',
          httpOnly: true,
          secure: true,
          sameSite: 'None'
        }
      ]);
      console.error('Using cookies from secrets.json');
    }
    
    page = await context.newPage();
    console.error('Launched fresh browser with session cookies');
  }
  
  // Go to recommended jobs with location and date filters
  console.error('Navigating to recommended jobs with filters...');
  await randomDelay(1500, 2500);
  await humanMouseMovement(page);
  
  // URL for recommended jobs (no time filter - higher quality)
  const jobsUrl = 'https://www.linkedin.com/jobs/collections/recommended/';
  
  try {
    await page.goto(jobsUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  } catch (e) {
    console.error('Warning: Initial navigation failed, retrying...');
    await page.goto('https://www.linkedin.com/jobs/', { waitUntil: 'domcontentloaded', timeout: 60000 });
    await randomDelay(2000, 4000);
    await page.goto(jobsUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  }
  
  await randomDelay(4000, 6000);
  
  // Check if logged in
  const currentUrl = page.url();
  console.error(`Current URL: ${currentUrl}`);
  
  if (currentUrl.includes('/login') || currentUrl.includes('authwall')) {
    console.error('Error: Not logged in. Cookies may be invalid or expired.');
    console.error('Please update li_at and jsessionid in config/secrets.json');
    await browser.close();
    process.exit(1);
  }
  
  // Save cookies after successful login for next run
  console.error('Saving cookies for future runs...');
  saveCookies(context);
  
  // Debug: check page content
  console.error('Debug: Checking page content...');
  const bodyText = await page.evaluate(() => document.body.innerText);
  console.error('Page body text (first 500 chars):', bodyText.substring(0, 500));
  
  // Collect all job cards across multiple pages
  const allJobCards = [];
  let currentPage = 1;
  const maxPages = 10; // Allow up to 10 pages for 200+ jobs
  
  while (allJobCards.length < config.maxJobs && currentPage <= maxPages) {
    console.error(`\n=== Page ${currentPage} ===`);
    
    // Scroll the sidebar to load more jobs on current page
    console.error('Scrolling sidebar to load more jobs...');
    
    let previousJobCount = 0;
    let noChangeCount = 0;
    const maxScrolls = 20;
    
    for (let scroll = 0; scroll < maxScrolls; scroll++) {
      // Method 1: Use mouse wheel for more realistic scrolling
      // First hover over the scroll container area
      await page.mouse.move(400, 300 + (scroll * 100));
      await page.mouse.wheel(0, 1000);
      
      // Method 2: Also try scrolling last job card into view
      const lastCard = await page.locator('div[data-job-id]').last();
      const isVisible = await lastCard.isVisible().catch(() => false);
      if (isVisible) {
        await lastCard.scrollIntoViewIfNeeded();
      }
      
      // Method 3: Fallback to JavaScript scrollTop (more reliable than scrollBy)
      await page.evaluate(() => {
        const sentinel = document.querySelector('[data-results-list-top-scroll-sentinel]');
        const scrollContainer = sentinel?.nextElementSibling;
        if (scrollContainer) {
          scrollContainer.scrollTop = scrollContainer.scrollHeight;
        }
      });
      // Longer delay to let content load (more human-like)
      await randomDelay(3000, 5000);
      
      // Check current job count - look for div[data-job-id] inside the scroll container
      const currentCards = await page.evaluate(() => {
        const sentinel = document.querySelector('[data-results-list-top-scroll-sentinel]');
        const scrollContainer = sentinel?.nextElementSibling;
        if (scrollContainer) {
          const cards = scrollContainer.querySelectorAll('div[data-job-id]');
          return cards.length;
        }
        // Fallback: look anywhere on page
        return document.querySelectorAll('div[data-job-id]').length;
      });
      
      console.error(`  Scroll ${scroll + 1}: Found ${currentCards} job cards...`);
      
      // Check if we've reached our target or stopped loading new jobs
      if (currentCards >= config.maxJobs) {
        console.error(`  Reached target of ${config.maxJobs} jobs!`);
        break;
      }
      
      // If count hasn't changed, increment noChange counter (more tolerance)
      if (currentCards === previousJobCount) {
        noChangeCount++;
        if (noChangeCount >= 5) {
          console.error(`  No more jobs to load on this page (${noChangeCount} scrolls without change)`);
          break;
        }
      } else {
        noChangeCount = 0;
      }
      
      previousJobCount = currentCards;
    }
    
    // Extract job cards from current page - use the correct structure
    const jobCards = await page.evaluate(() => {
      const sentinel = document.querySelector('[data-results-list-top-scroll-sentinel]');
      const scrollContainer = sentinel?.nextElementSibling;
      
      let cards = [];
      if (scrollContainer) {
        cards = scrollContainer.querySelectorAll('div[data-job-id]');
      }
      
      // Fallback: search anywhere
      if (cards.length === 0) {
        cards = document.querySelectorAll('div[data-job-id]');
      }
      
      return Array.from(cards).map(card => ({
        jobId: card.getAttribute('data-job-id'),
        title: card.querySelector('.job-card-list__title--link')?.textContent?.trim() || 
               card.querySelector('a[href*="/jobs/view/"]')?.textContent?.trim() || '',
        company: card.querySelector('.artdeco-entity-lockup__subtitle')?.textContent?.trim() || '',
        location: card.querySelector('.job-card-container__metadata-wrapper')?.textContent?.trim() || ''
      }));
    });
    
    console.error(`Found ${jobCards.length} job cards on page ${currentPage}`);
    
    // Add unique jobs to our collection
    const existingIds = new Set(allJobCards.map(j => j.jobId));
    for (const card of jobCards) {
      if (!existingIds.has(card.jobId)) {
        allJobCards.push(card);
        existingIds.add(card.jobId);
      }
    }
    
    console.error(`Total unique jobs collected: ${allJobCards.length}`);
    
    // Check if we have enough jobs
    if (allJobCards.length >= config.maxJobs) {
      console.error(`Reached target of ${config.maxJobs} jobs!`);
      break;
    }
    
    // Try to go to next page
    console.error('Checking for next page...');
    const hasNextPage = await page.evaluate(() => {
      const nextBtn = document.querySelector('.jobs-search-pagination__button--next');
      return nextBtn && !nextBtn.disabled;
    });
    
    if (hasNextPage) {
      console.error('Clicking next page...');
      try {
        await humanMouseMovement(page);
        await randomDelay(2000, 4000);
        await page.click('.jobs-search-pagination__button--next');
        // Longer wait for page to load (more human-like)
        await randomDelay(5000, 8000);
        currentPage++;
      } catch (e) {
        console.error(`  Could not click next: ${e.message}`);
        break;
      }
    } else {
      console.error('No more pages available');
      break;
    }
  }
  
  const jobCards = allJobCards;
  
  console.error(`Found ${jobCards.length} total unique job cards`);
  
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
    
    // Skip cards with no title
    if (!card.title) {
      console.error(`[${i+1}/${maxJobs}] Skipping - no title`);
      continue;
    }
    
    console.error(`[${i+1}/${maxJobs}] Clicking: ${card.title} at ${card.company}`);
    
    try {
      // More human-like: move mouse and pause before clicking
      await humanMouseMovement(page);
      await randomDelay(2000, 4000);
      
      // Try different click selectors
      try {
        await page.click(`div[data-job-id="${card.jobId}"]`);
      } catch (e) {
        await page.click(`.job-card-container:has-text("${card.company}")`);
      }
      
      // Wait longer for JD panel to load
      await randomDelay(4000, 6000);
      
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