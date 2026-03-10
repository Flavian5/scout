#!/usr/bin/env node

/**
 * Gun.io Job Scraper
 * 
 * Gun.io is an elite freelance network for senior developers.
 * Requires account approval, but can check for available opportunities.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning"
 * 
 * Output: JSON array of job objects to stdout
 * 
 * NOTE: Gun.io requires platform membership for most opportunities.
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
 * Load Gun.io cookies from secrets file
 */
async function loadGunioCookies() {
  const secretsPath = path.join(__dirname, '../../config/secrets.json');
  if (fs.existsSync(secretsPath)) {
    try {
      const secrets = JSON.parse(fs.readFileSync(secretsPath, 'utf8'));
      if (secrets.gunio) {
        return secrets.gunio;
      }
    } catch (e) {
      console.error('Error loading secrets:', e.message);
    }
  }
  return null;
}

/**
 * Build Gun.io job search URL
 */
function buildGunioUrl(keywords) {
  const encodedKeywords = encodeURIComponent(keywords);
  return `https://gun.io/jobs?q=${encodedKeywords}`;
}

/**
 * Extract job opportunities from Gun.io
 */
async function extractJobs(page) {
  await page.waitForTimeout(3000);
  
  const jobs = await page.evaluate(() => {
    const results = [];
    
    // Look for any job-related content
    const jobCards = document.querySelectorAll('[class*="job"], [class*="project"], [class*="opportunity"], article, .listing');
    
    jobCards.forEach(card => {
      const titleEl = card.querySelector('h2, h3, h4, a');
      const companyEl = card.querySelector('[class*="company"], [class*="client"], [class*="employer"]');
      const descEl = card.querySelector('p, [class*="description"], [class*="summary"]');
      const linkEl = card.querySelector('a[href*="/jobs"], a[href*="/projects"], a[href*="/apply"]');
      const rateEl = card.querySelector('[class*="rate"], [class*="price"], [class*="budget"]');
      
      if (titleEl) {
        results.push({
          title: titleEl.textContent.trim(),
          company: companyEl ? companyEl.textContent.trim() : 'Gun.io Client',
          description: descEl ? descEl.textContent.trim().substring(0, 500) : '',
          rate: rateEl ? rateEl.textContent.trim() : '',
          link: linkEl ? linkEl.href : '',
          isPublic: true
        });
      }
    });
    
    return results;
  });
  
  // If no jobs found, return info about Gun.io's model
  if (jobs.length === 0) {
    return [{
      title: 'Gun.io Freelance Opportunities',
      company: 'Gun.io',
      description: 'Gun.io is an elite network - clients post projects and Gun.io matches with vetted freelancers. Not a traditional job board.',
      link: 'https://gun.io/freelance',
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
 * Extract rate from job details
 */
function extractRate(rateStr) {
  if (!rateStr) return { rate_min: null, rate_max: null, rate_type: null };
  
  // Match hourly rates
  const hourlyMatch = rateStr.match(/\$(\d+)(?:\s*-\s*\$(\d+))?\s*\/?hr/i);
  if (hourlyMatch) {
    return {
      rate_min: parseInt(hourlyMatch[1], 10),
      rate_max: hourlyMatch[2] ? parseInt(hourlyMatch[2], 10) : parseInt(hourlyMatch[1], 10),
      rate_type: 'hourly'
    };
  }
  
  // Match project rates
  const projectMatch = rateStr.match(/\$(\d+(?:,\d{3})*)/);
  if (projectMatch) {
    return {
      rate_min: parseInt(projectMatch[1].replace(/,/g, ''), 10),
      rate_max: parseInt(projectMatch[1].replace(/,/g, ''), 10),
      rate_type: 'project'
    };
  }
  
  return { rate_min: null, rate_max: null, rate_type: null };
}

/**
 * Main scraper function
 */
async function scrape() {
  const config = parseArgs();
  
  console.error(`Searching Gun.io for: "${config.keywords}"`);
  console.error('Note: Gun.io requires platform membership for most opportunities');
  
  // Load cookies
  const gunioCookies = await loadGunioCookies();
  const hasAuth = gunioCookies && (gunioCookies.session || gunioCookies.token);
  
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
  if (gunioCookies) {
    if (gunioCookies.session) {
      await context.setCookie({
        name: 'gunio_session',
        value: gunioCookies.session,
        domain: '.gun.io',
        path: '/'
      });
    }
    if (gunioCookies.token) {
      await context.setCookie({
        name: 'auth_token',
        value: gunioCookies.token,
        domain: '.gun.io',
        path: '/'
      });
    }
  }
  
  const page = await context.newPage();
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  try {
    // Navigate to Gun.io jobs
    const searchUrl = buildGunioUrl(config.keywords);
    console.error(`Navigating to: ${searchUrl}`);
    
    await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(5000);
    
    // Extract jobs
    const jobs = await extractJobs(page);
    console.error(`Found ${jobs.length} opportunities`);
    
    const results = [];
    
    for (const job of jobs.slice(0, config.limit)) {
      const signals = detectSignals(job.description, job.title);
      const rateInfo = extractRate(job.rate);
      
      const jobData = {
        source: 'gunio',
        job_id: `gunio_${uuidv4().substring(0, 8)}`,
        role_title: job.title,
        company: job.company,
        location: 'Remote',
        application_url: job.link || 'https://gun.io/freelance',
        job_description_raw: job.description,
        contract_details: {
          rate_type: rateInfo.rate_type || 'hourly',
          rate_min: rateInfo.rate_min || 100,
          rate_max: rateInfo.rate_max || 200,
          engagement_type: job.requiresMembership ? 'Requires Gun.io Membership' : 'Freelance',
          notes: job.requiresMembership ? 'Must apply through Gun.io platform' : ''
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
    console.error(`Note: Most Gun.io opportunities require platform membership`);
    
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