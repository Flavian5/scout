#!/usr/bin/env node

/**
 * Wellfound Job Scraper (formerly AngelList Talent)
 * 
 * Scrapes job listings from Wellfound using Puppeteer with stealth plugin.
 * Uses shared C2C scraper library for signal detection and normalization.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco"
 *   node scrape.js --keywords "ML Engineer" --project-based
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
const { normalizeJobData, filterJobs, detectSignals } = require('../c2c-scrapers/shared');

// Default configuration
const DEFAULT_LOCATION = 'San Francisco';
const DEFAULT_LIMIT = 50;

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    keywords: '',
    location: DEFAULT_LOCATION,
    stage: null,
    category: null,
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
    } else if (arg === '--stage' || arg === '-s') {
      config.stage = nextArg;
      i++;
    } else if (arg === '--category' || arg === '-c') {
      config.category = nextArg;
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
 * Load cookies from secrets file
 */
async function loadWellfoundCookies() {
  const secretsPath = path.join(__dirname, '../../config/secrets.json');
  if (fs.existsSync(secretsPath)) {
    try {
      const secrets = JSON.parse(fs.readFileSync(secretsPath, 'utf8'));
      if (secrets.wellfound) {
        return secrets.wellfound;
      }
    } catch (e) {
      console.error('Error loading secrets:', e.message);
    }
  }
  return {};
}

/**
 * Build Wellfound search URL
 */
function buildSearchUrl(keywords, location, stage, category) {
  let query = '';
  
  if (keywords) {
    query = encodeURIComponent(keywords);
  }
  
  let url = 'https://wellfound.com/jobs';
  
  if (query) {
    url += `?query=${query}`;
  }
  
  if (location) {
    const locParam = location.replace(/ /g, '_');
    url += query ? `&loc=${locParam}` : `?loc=${locParam}`;
  }
  
  if (stage) {
    const stageMap = {
      'pre-seed': 'pre-seed',
      'seed': 'seed',
      'series a': 'series-a',
      'series b': 'series-b',
      'series c': 'series-c',
      'public': 'public'
    };
    const stageParam = stageMap[stage.toLowerCase()] || stage;
    url += url.includes('?') ? `&stage=${stageParam}` : `?stage=${stageParam}`;
  }
  
  return url;
}

/**
 * Scroll to load more jobs
 */
async function scrollForJobs(page, maxScrolls = 5) {
  let lastHeight = 0;
  
  for (let i = 0; i < maxScrolls; i++) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    
    if (newHeight === lastHeight) {
      break;
    }
    lastHeight = newHeight;
  }
}

/**
 * Extract job card data from Wellfound search results
 */
async function extractJobCards(page) {
  try {
    await page.waitForSelector('.job-card, .JobCard, [class*="job"]', { timeout: 10000 });
  } catch (e) {
    // Continue even if selector not found
  }
  
  const jobCards = await page.evaluate(() => {
    let cards = document.querySelectorAll('.job-card, .JobCard, [class*="JobCard"], [class*="job-card"], article[class*="job"], .job-listing, [data-testid*="job"]');
    
    if (cards.length === 0) {
      cards = document.querySelectorAll('main a[href*="/jobs/"]');
    }
    
    return Array.from(cards).map(card => {
      const titleEl = card.querySelector('h2, h3, [class*="title"], [class*="Title"], a[href*="/jobs/"]');
      const companyEl = card.querySelector('[class*="company"], [class*="Company"], [class*="employer"], a[href*="/company/"]');
      const locationEl = card.querySelector('[class*="location"], [class*="Location"], [class*="region"]');
      const linkEl = card.querySelector('a[href*="/jobs/"]');
      const tagsEl = card.querySelectorAll('[class*="tag"], [class*="Tag"], [class*="skill"], span[class*="tag"]');
      const salaryEl = card.querySelector('[class*="salary"], [class*="Salary"], [class*="pay"], [class*="comp"]');
      const equityEl = card.querySelector('[class*="equity"], [class*="Equity"]');
      
      const tags = Array.from(tagsEl).map(t => t.textContent.trim()).filter(t => t && t.length < 30);
      
      let title = titleEl ? titleEl.textContent.trim() : '';
      if (!title && linkEl) {
        title = linkEl.textContent.trim() || linkEl.href.split('/jobs/')[1]?.split('-').join(' ') || '';
      }
      
      let company = companyEl ? companyEl.textContent.trim() : '';
      let location = locationEl ? locationEl.textContent.trim() : '';
      
      let link = linkEl && linkEl.href ? linkEl.href : '';
      if (link && !link.startsWith('http')) {
        link = 'https://wellfound.com' + link;
      }
      
      return {
        title: title,
        company: company,
        location: location,
        link: link,
        tags: tags,
        salary: salaryEl ? salaryEl.textContent.trim() : '',
        equity: equityEl ? equityEl.textContent.trim() : ''
      };
    }).filter(card => card.title && card.link && card.title.length > 2);
  });
  
  return jobCards;
}

/**
 * Get detailed job information
 */
async function getJobDetails(page, jobLink) {
  try {
    await page.goto(jobLink, { waitUntil: 'domcontentloaded', timeout: 15000 });
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const details = await page.evaluate(() => {
      const result = {
        description: '',
        teamSize: null,
        funding: null,
        stage: null,
        techStack: [],
        benefits: []
      };
      
      const descEl = document.querySelector('[data-testid="job-description"], .job-description, .job-detail-description');
      if (descEl) {
        result.description = descEl.textContent.trim().substring(0, 5000);
      }
      
      const stageEl = document.querySelector('[data-testid="stage"], .stage, [data-testid="company-stage"]');
      if (stageEl) {
        result.stage = stageEl.textContent.trim();
      }
      
      const teamSizeEl = document.querySelector('[data-testid="team-size"], .team-size, [data-testid="company-size"]');
      if (teamSizeEl) {
        result.teamSize = teamSizeEl.textContent.trim();
      }
      
      const fundingEl = document.querySelector('[data-testid="funding"], .funding, [data-testid="company-funding"]');
      if (fundingEl) {
        result.funding = fundingEl.textContent.trim();
      }
      
      const techEls = document.querySelectorAll('[data-testid="tech-stack"] span, .tech-stack span, .job-tech-stack span');
      result.techStack = Array.from(techEls).map(el => el.textContent.trim()).filter(t => t);
      
      const benefitEls = document.querySelectorAll('[data-testid="benefits"] li, .benefits li, .job-benefits li');
      result.benefits = Array.from(benefitEls).map(el => el.textContent.trim()).filter(t => t);
      
      return result;
    });
    
    return details;
  } catch (e) {
    console.error('Error getting job details:', e.message);
    return { description: '', teamSize: null, funding: null, stage: null, techStack: [], benefits: [] };
  }
}

/**
 * Determine startup stage from company info
 */
function getStartupStage(stageInfo, funding) {
  const text = (stageInfo + ' ' + funding).toLowerCase();
  
  if (text.includes('pre-seed') || text.includes('pre seed')) return 'Pre-seed';
  if (text.includes('seed')) return 'Seed';
  if (text.includes('series a') || text.includes('series-a')) return 'Series A';
  if (text.includes('series b') || text.includes('series-b')) return 'Series B';
  if (text.includes('series c') || text.includes('series-c')) return 'Series C';
  if (text.includes('public') || text.includes('ipo')) return 'Public';
  
  return stageInfo || 'Unknown';
}

/**
 * Main scraper function
 */
async function scrape() {
  const config = parseArgs();
  
  if (!config.keywords) {
    console.error('Error: --keywords is required');
    console.error('Usage: node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco"');
    process.exit(1);
  }
  
  console.error(`Searching Wellfound for: "${config.keywords}" in ${config.location}`);
  if (config.stage) console.error(`Stage filter: ${config.stage}`);
  if (config.filterProjectBased) {
    console.error('Filtering for project-based opportunities only');
  }
  
  const wellfoundCookies = await loadWellfoundCookies();
  const hasAuth = wellfoundCookies.auth_token || wellfoundCookies.cf_clearance || wellfoundCookies.datadome;
  if (hasAuth) {
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
  
  const cookiePromises = [];
  
  if (wellfoundCookies.auth_token) {
    cookiePromises.push(context.setCookie({
      name: '_wellfound',
      value: wellfoundCookies.auth_token,
      domain: 'wellfound.com',
      path: '/',
      httpOnly: false,
      secure: true,
      sameSite: 'None'
    }));
  }
  
  if (wellfoundCookies.cf_clearance) {
    cookiePromises.push(context.setCookie({
      name: 'cf_clearance',
      value: wellfoundCookies.cf_clearance,
      domain: '.wellfound.com',
      path: '/',
      httpOnly: false,
      secure: true,
      sameSite: 'None'
    }));
  }
  
  if (wellfoundCookies.datadome) {
    cookiePromises.push(context.setCookie({
      name: 'datadome',
      value: wellfoundCookies.datadome,
      domain: '.wellfound.com',
      path: '/',
      httpOnly: false,
      secure: true,
      sameSite: 'Lax'
    }));
  }
  
  if (wellfoundCookies.ajs_user_id) {
    cookiePromises.push(context.setCookie({
      name: 'ajs_user_id',
      value: wellfoundCookies.ajs_user_id,
      domain: '.wellfound.com',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax'
    }));
  }
  
  if (cookiePromises.length > 0) {
    console.error(`Setting ${cookiePromises.length} cookies...`);
    await Promise.all(cookiePromises);
  }
  
  const page = await context.newPage();
  
  console.error('Visiting main site first...');
  await page.goto('https://wellfound.com', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  await page.setViewport({ width: 1920, height: 1080 });
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  await page.setExtraHTTPHeaders({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache'
  });
  
  try {
    const searchUrl = buildSearchUrl(config.keywords, config.location, config.stage, config.category);
    console.error(`Navigating to: ${searchUrl}`);
    
    const response = await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    console.error('Response status:', response?.status());
    
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    const loginWall = await page.$('text=Sign in');
    if (loginWall) {
      console.error('Warning: Encountered login wall. Some results may not be available without authentication.');
    }
    
    await scrollForJobs(page, 3);
    
    const jobs = await extractJobCards(page);
    console.error(`Found ${jobs.length} job cards`);
    
    const results = [];
    const limit = Math.min(config.limit, jobs.length);
    
    for (let i = 0; i < limit; i++) {
      const job = jobs[i];
      
      let details = { description: '', teamSize: null, funding: null, stage: null, techStack: [], benefits: [] };
      if (i < 10) {
        details = await getJobDetails(page, job.link);
        await page.goBack({ waitUntil: 'domcontentloaded' });
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Use shared normalizeJobData
      const rawJob = {
        title: job.title,
        company: job.company,
        location: job.location || config.location,
        link: job.link,
        description: details.description,
        skills: details.techStack,
        rate: job.salary,
        employmentType: 'Contract'
      };
      
      const normalizedJob = normalizeJobData(rawJob, 'wellfound');
      
      // Add Wellfound-specific fields
      normalizedJob.startup_stage = getStartupStage(details.stage, details.funding);
      normalizedJob.team_size = details.teamSize;
      normalizedJob.funding = details.funding;
      normalizedJob.equity = job.equity;
      
      results.push(normalizedJob);
      
      const signalInfo = normalizedJob.is_project_based ? '[PROJECT-BASED]' : '[STAFF AUG]';
      console.error(`Processed: ${signalInfo} ${job.title} at ${job.company}`);
      
      await new Promise(resolve => setTimeout(resolve, 800));
    }
    
    // Apply filtering if requested
    let finalResults = results;
    if (config.filterProjectBased) {
      finalResults = filterJobs(results, { requireProjectBased: true });
      console.error(`\n=== Filtering ===`);
      console.error(`After project-based filter: ${finalResults.length} jobs (from ${results.length})`);
    }
    
    console.error(`\n=== Summary ===`);
    console.error(`Total jobs found: ${results.length}`);
    console.error(`Project-based jobs: ${results.filter(j => j.is_project_based).length}`);
    
    const output = JSON.stringify(finalResults, null, 2);
    
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

scrape().catch(e => {
  console.error('Fatal error:', e);
  process.exit(1);
});