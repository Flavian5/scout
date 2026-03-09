#!/usr/bin/env node

/**
 * Wellfound Job Scraper (formerly AngelList Talent)
 * 
 * Scrapes job listings from Wellfound using Puppeteer with stealth plugin.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning Engineer" --location "San Francisco"
 *   node scrape.js --stage "Series A" --category "Biotech"
 * 
 * Output: JSON array of job objects to stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

// Enable stealth plugin
puppeteer.use(StealthPlugin());

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
    outputFile: null
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    // Support both --flag and -f formats
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
  
  // Build URL with filters
  let url = 'https://wellfound.com/jobs';
  
  if (query) {
    url += `?query=${query}`;
  }
  
  if (location) {
    const locParam = location.replace(/ /g, '_');
    url += query ? `&loc=${locParam}` : `?loc=${locParam}`;
  }
  
  // Stage filter can be added if specified
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
 * Scroll to load more jobs (infinite scroll)
 */
async function scrollForJobs(page, maxScrolls = 5) {
  let lastHeight = 0;
  
  for (let i = 0; i < maxScrolls; i++) {
    // Scroll down
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Get new height
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    
    if (newHeight === lastHeight) {
      // No more content to load
      break;
    }
    lastHeight = newHeight;
  }
}

/**
 * Extract job card data from Wellfound search results
 */
async function extractJobCards(page) {
  // Wait for job cards to load
  try {
    await page.waitForSelector('.job-card, .JobCard, [class*="job"], article', { timeout: 10000 });
  } catch (e) {
    // Continue even if selector not found
  }
  
  // Get all job cards - use more generic selectors
  const jobCards = await page.evaluate(() => {
    // Try multiple selector patterns
    let cards = document.querySelectorAll('.job-card, .JobCard, [class*="JobCard"], [class*="job-card"], article[class*="job"], .job-listing, [data-testid*="job"]');
    
    // If no cards found, try even more generic
    if (cards.length === 0) {
      cards = document.querySelectorAll('main a[href*="/jobs/"]');
    }
    
    return Array.from(cards).map(card => {
      // Try various selectors for job info - be very flexible
      const titleEl = card.querySelector('h2, h3, [class*="title"], [class*="Title"], a[href*="/jobs/"]');
      const companyEl = card.querySelector('[class*="company"], [class*="Company"], [class*="employer"], a[href*="/company/"]');
      const locationEl = card.querySelector('[class*="location"], [class*="Location"], [class*="region"]');
      const linkEl = card.querySelector('a[href*="/jobs/"]');
      const tagsEl = card.querySelectorAll('[class*="tag"], [class*="Tag"], [class*="skill"], span[class*="tag"]');
      const salaryEl = card.querySelector('[class*="salary"], [class*="Salary"], [class*="pay"], [class*="comp"]');
      const equityEl = card.querySelector('[class*="equity"], [class*="Equity"]');
      
      const tags = Array.from(tagsEl).map(t => t.textContent.trim()).filter(t => t && t.length < 30);
      
      // Get title - try multiple approaches
      let title = '';
      if (titleEl) {
        title = titleEl.textContent.trim();
      }
      // If title is empty but we have a link, use the link text
      if (!title && linkEl) {
        title = linkEl.textContent.trim() || linkEl.href.split('/jobs/')[1]?.split('-').join(' ') || '';
      }
      
      // Get company
      let company = '';
      if (companyEl) {
        company = companyEl.textContent.trim();
      }
      
      // Get location
      let location = '';
      if (locationEl) {
        location = locationEl.textContent.trim();
      }
      
      // Get link
      let link = '';
      if (linkEl && linkEl.href) {
        const href = linkEl.href;
        link = href.startsWith('http') ? href : 'https://wellfound.com' + href;
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
    
    // Extract job details from the job view page
    const details = await page.evaluate(() => {
      const result = {
        description: '',
        teamSize: null,
        funding: null,
        stage: null,
        techStack: [],
        benefits: []
      };
      
      // Get job description
      const descEl = document.querySelector('[data-testid="job-description"], .job-description, .job-detail-description');
      if (descEl) {
        result.description = descEl.textContent.trim().substring(0, 5000);
      }
      
      // Get company info
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
      
      // Get tech stack
      const techEls = document.querySelectorAll('[data-testid="tech-stack"] span, .tech-stack span, .job-tech-stack span');
      result.techStack = Array.from(techEls).map(el => el.textContent.trim()).filter(t => t);
      
      // Get benefits
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
 * Detect signals in job description using keyword matching
 */
function detectSignals(description, company, tags, techStack) {
  const signals = [];
  const text = (description + ' ' + company + ' ' + tags.join(' ') + ' ' + techStack.join(' ')).toLowerCase();
  
  // ML/RecSys signals
  if (text.includes('recommendation') || text.includes('recsys') || text.includes('recommender')) signals.push('recsys');
  if (text.includes('two-stage') || text.includes('two stage')) signals.push('two_stage_ranking');
  if (text.includes('generation') || text.includes('genrec')) signals.push('genrec');
  if (text.includes('foundation model') || text.includes('llm') || text.includes('transformer')) signals.push('foundation_models');
  
  // Bio-AI signals  
  if (text.includes('virtual cell') || text.includes('cell') || text.includes('cell biology')) signals.push('virtual_cell');
  if (text.includes('digital twin')) signals.push('digital_twin');
  if (text.includes('drug discovery') || text.includes('drug')) signals.push('drug_discovery');
  if (text.includes('phenomics')) signals.push('phenomics');
  if (text.includes('bioai') || text.includes('bio-ai') || text.includes('computational biology')) signals.push('bio_ai');
  if (text.includes('genomics')) signals.push('genomics');
  
  // Infrastructure signals
  if (text.includes('ml platform') || text.includes('ml infrastructure')) signals.push('ml_platform');
  if (text.includes('feature store')) signals.push('feature_store');
  if (text.includes('ml pipeline') || text.includes('pipeline')) signals.push('ml_pipeline');
  
  // Other signals
  if (text.includes('voice agent') || text.includes('voice')) signals.push('voice_agent');
  if (text.includes('c automatio') || text.includes('customer experience')) signals.push('cx_automation');
  
  // Startup stage signals
  if (text.includes('seed')) signals.push('seed_stage');
  if (text.includes('series a')) signals.push('series_a');
  if (text.includes('series b')) signals.push('series_b');
  
  return signals;
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
  if (config.category) console.error(`Category filter: ${config.category}`);
  
  // Load cookies from secrets
  const wellfoundCookies = await loadWellfoundCookies();
  const hasAuth = wellfoundCookies.auth_token || wellfoundCookies.cf_clearance || wellfoundCookies.datadome;
  if (hasAuth) {
    console.error('Using authenticated session');
  }
  
  // Launch browser with stealth plugin
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
  
  // Create a new browser context (incognito)
  const context = await browser.createBrowserContext();
  
  // Set all the critical cookies for Wellfound
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
  
  // First, visit the main site to establish session
  console.error('Visiting main site first...');
  await page.goto('https://wellfound.com', { waitUntil: 'domcontentloaded', timeout: 15000 });
  await new Promise(resolve => setTimeout(resolve, 2000));
  console.error('Main site visited, URL:', page.url());
  
  // Set realistic viewport
  await page.setViewport({ width: 1920, height: 1080 });
  
  // Set more complete user agent and headers
  await page.setUserAgent('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
  
  // Set additional headers to appear more like a real browser
  await page.setExtraHTTPHeaders({
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"macOS"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1'
  });
  
  try {
    // Navigate to search results
    const searchUrl = buildSearchUrl(config.keywords, config.location, config.stage, config.category);
    console.error(`Navigating to: ${searchUrl}`);
    
    // Try with domcontentloaded and wait for network idle
    const response = await page.goto(searchUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
    
    console.error('Response status:', response?.status());
    console.error('Final URL:', page.url());
    
    // Wait for content to render
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Debug: Get page title and some content
    const pageInfo = await page.evaluate(() => {
      return {
        title: document.title,
        url: window.location.href,
        bodyText: document.body.innerText.substring(0, 500),
        hasJobs: document.body.innerText.includes('job'),
        linksCount: document.querySelectorAll('a').length,
        mainContent: document.querySelector('main')?.innerText?.substring(0, 300) || 'No main found'
      };
    });
    console.error('Page info:', JSON.stringify(pageInfo));
    
    // Handle potential login wall
    const loginWall = await page.$('text=Sign in');
    if (loginWall) {
      console.error('Warning: Encountered login wall. Some results may not be available without authentication.');
    }
    
    // Try scrolling to load more
    await scrollForJobs(page, 3);
    
    // Extract job cards
    const jobs = await extractJobCards(page);
    console.error(`Found ${jobs.length} job cards`);
    
    const results = [];
    const limit = Math.min(config.limit, jobs.length);
    
    for (let i = 0; i < limit; i++) {
      const job = jobs[i];
      
      // Get additional details (only for first 10 to avoid rate limiting)
      let details = { description: '', teamSize: null, funding: null, stage: null, techStack: [], benefits: [] };
      if (i < 10) {
        details = await getJobDetails(page, job.link);
        
        // Go back to search results
        await page.goBack({ waitUntil: 'domcontentloaded' });
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
      
      // Detect signals
      const signals = detectSignals(details.description, job.company, job.tags, details.techStack);
      
      // Build job object
      const jobData = {
        source: 'wellfound',
        job_id: `wellfound_${uuidv4().substring(0, 8)}`,
        role_title: job.title,
        company: job.company,
        location: job.location || config.location,
        application_url: job.link,
        job_description_raw: details.description,
        salary_range: job.salary || null,
        equity: job.equity || null,
        startup_stage: getStartupStage(details.stage, details.funding),
        team_size: details.teamSize || null,
        funding: details.funding || null,
        detected_signals: signals,
        scraped_at: new Date().toISOString()
      };
      
      results.push(jobData);
      console.error(`Processed: ${job.title} at ${job.company}`);
      
      // Rate limiting - be respectful
      await new Promise(resolve => setTimeout(resolve, 800));
    }
    
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