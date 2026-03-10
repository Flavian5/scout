#!/usr/bin/env node

/**
 * Toptal Job Scraper
 * 
 * Toptal is a premium freelance network for top-tier talent.
 * Requires account approval, but can check for available opportunities.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning"
 * 
 * Output: JSON array of job objects to stdout
 * 
 * NOTE: Toptal requires authentication. This scraper checks for public
 * job listings but most opportunities require being matched as a freelancer.
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Enable stealth plugin
puppeteer.use(StealthPlugin());

// Default configuration
const DEFAULT_LIMIT = 30;

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    keywords: 'Machine Learning',
    limit: DEFAULT_LIMIT,
    outputFile: null
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--keywords' || arg === '-k') {
      config.keywords = nextArg;
      i++;
    } else if (arg === '--limit' || arg === '-L') {
      config.limit = parseInt(nextArg, 10);
      i++;
    } else if (arg === '--output' || arg === '-o') {
      config.outputFile = nextArg;
      i++;
    }
  }
  
  return config;
}

/**
 * Load Toptal cookies from secrets file
 */
async function loadToptalCookies() {
  const secretsPath = path.join(__dirname, '../../config/secrets.json');
  if (fs.existsSync(secretsPath)) {
    try {
      const secrets = JSON.parse(fs.readFileSync(secretsPath, 'utf8'));
      if (secrets.toptal) {
        return secrets.toptal;
      }
    } catch (e) {
      console.error('Error loading secrets:', e.message);
    }
  }
  return null;
}

/**
 * Build Toptal job search URL
 * 
 * Toptal doesn't have a public job board like Dice.
 * They use a matching system where clients post projects and
 * Toptal matches them with freelancers.
 * 
 * This scraper checks their public job categories and any
 * publicly listed opportunities.
 */
function buildToptalUrl(keywords) {
  const encodedKeywords = encodeURIComponent(keywords);
  
  // Toptal's public job categories page
  return `https://www.toptal.com/jobs/search?q=${encodedKeywords}`;
}

/**
 * Extract job opportunities from Toptal
 * 
 * Note: Most Toptal opportunities are not publicly listed.
 * This scraper captures what's available and notes the rest
 * requires platform membership.
 */
async function extractJobs(page) {
  await page.waitForTimeout(3000);
  
  const jobs = await page.evaluate(() => {
    const results = [];
    
    // Look for any job-related content
    const jobCards = document.querySelectorAll('[class*="job"], [class*="project"], [class*="opportunity"]');
    
    jobCards.forEach(card => {
      const titleEl = card.querySelector('h2, h3, h4, a');
      const companyEl = card.querySelector('[class*="company"], [class*="client"]');
      const descEl = card.querySelector('p, [class*="description"]');
      const linkEl = card.querySelector('a[href*="/jobs"], a[href*="/projects"], a[href*="/apply"]');
      
      if (titleEl) {
        results.push({
          title: titleEl.textContent.trim(),
          company: companyEl ? companyEl.textContent.trim() : 'Toptal Client',
          description: descEl ? descEl.textContent.trim().substring(0, 500) : '',
          link: linkEl ? linkEl.href : '',
          isPublic: true
        });
      }
    });
    
    return results;
  });
  
  // If no jobs found, return info about Toptal's model
  if (jobs.length === 0) {
    return [{
      title: 'Toptal Freelance Opportunities',
      company: 'Toptal',
      description: 'Toptal uses a matching model - clients post projects and Toptal matches with top 3% freelancers. Not a traditional job board.',
      link: 'https://www.toptal.com/freelance',
      isPublic: false,
      requiresMembership: true
    }];
  }
  
  return jobs;
}

/**
 * Detect signals in job description
 */
function detectSignals(description, title) {
  const signals = [];
  const text = (description + ' ' + title).toLowerCase();
  
  // ML/RecSys signals
  if (text.includes('recommendation') || text.includes('recsys')) signals.push('recsys');
  if (text.includes('ml platform') || text.includes('ml infrastructure')) signals.push('ml_platform');
  if (text.includes('llm') || text.includes('transformer') || text.includes('foundation model')) signals.push('foundation_models');
  
  // Contract signals
  if (text.includes('contract') || text.includes('freelance')) signals.push('freelance');
  if (text.includes('remote')) signals.push('remote');
  
  return signals;
}

/**
 * Main scraper function
 */
async function scrape() {
  const config = parseArgs();
  
  console.error(`Searching Toptal for: "${config.keywords}"`);
  console.error('Note: Toptal requires platform membership for most opportunities');
  
  // Load cookies
  const toptalCookies = await loadToptalCookies();
  const hasAuth = toptalCookies && (toptalCookies.session || toptalCookies.token);
  
  if (hasAuth) {
    console.error('Using authenticated session');
  } else {
    console.error('No authentication found - limited results expected');
  }
  
  // Launch browser
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
  
  // Set cookies if available
  if (toptalCookies) {
    if (toptalCookies.session) {
      await context.setCookie({
        name: 'toptal_session',
        value: toptalCookies.session,
        domain: '.toptal.com',
        path: '/'
      });
    }
    if (toptalCookies.token) {
      await context.setCookie({
        name: 'auth_token',
        value: toptalCookies.token,
        domain: '.toptal.com',
        path: '/'
      });
    }
  }
  
  const page = await context.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    // Navigate to Toptal jobs
    const searchUrl = buildToptalUrl(config.keywords);
    console.error(`Navigating to: ${searchUrl}`);
    
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // Check if logged in
    const isLoggedIn = await page.$('text=Sign in') === null;
    console.error(`Logged in: ${isLoggedIn}`);
    
    // Extract jobs
    const jobs = await extractJobs(page);
    console.error(`Found ${jobs.length} opportunities`);
    
    const results = [];
    
    for (const job of jobs.slice(0, config.limit)) {
      const signals = detectSignals(job.description, job.title);
      
      const jobData = {
        source: 'toptal',
        job_id: `toptal_${uuidv4().substring(0, 8)}`,
        role_title: job.title,
        company: job.company,
        location: 'Remote',
        application_url: job.link || 'https://www.toptal.com/freelance',
        job_description_raw: job.description,
        contract_details: {
          rate_type: 'hourly',
          rate_min: 100, // Toptal typically $100+/hr
          rate_max: 200,
          engagement_type: job.requiresMembership ? 'Requires Toptal Membership' : 'Freelance',
          notes: job.requiresMembership ? 'Must apply through Toptal platform' : ''
        },
        detected_signals: signals,
        requires_platform_membership: job.requiresMembership || !job.isPublic,
        scraped_at: new Date().toISOString()
      };
      
      results.push(jobData);
      console.error(`Processed: ${job.title}`);
    }
    
    // Output results
    const output = JSON.stringify(results, null, 2);
    
    if (config.outputFile) {
      fs.writeFileSync(config.outputFile, output);
      console.error(`Results written to: ${config.outputFile}`);
    } else {
      console.log(output);
    }
    
    console.error(`\n=== Summary ===`);
    console.error(`Total opportunities: ${results.length}`);
    console.error(`Note: Most Toptal opportunities require platform membership`);
    
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