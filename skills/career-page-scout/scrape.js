#!/usr/bin/env node

/**
 * Career Page Scraper
 * 
 * Scrapes career pages for target companies to find ML/RecSys job openings.
 * Uses config/sourcing.json to get target companies.
 * 
 * Usage:
 *   node scrape.js --keywords "Machine Learning" --category "traditional_tech"
 *   node scrape.js --keywords "ML Engineer" --category "bio_ai"
 *   node scrape.js --all
 * 
 * Output: JSON array of job objects to stdout
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Enable stealth plugin
puppeteer.use(StealthPlugin());

// Default configuration
const DEFAULT_KEYWORDS = ['Machine Learning', 'ML Engineer', 'Recommendation', 'RecSys'];
const DEFAULT_CATEGORY = 'all';

/**
 * Parse command line arguments
 */
function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    keywords: DEFAULT_KEYWORDS,
    category: DEFAULT_CATEGORY,
    outputFile: null,
    verifyOnly: false,
    limit: 50
  };
  
  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    const nextArg = args[i + 1];
    
    if (arg === '--keywords' || arg === '-k') {
      config.keywords = [nextArg];
      i++;
    } else if (arg === '--category' || arg === '-c') {
      config.category = nextArg;
      i++;
    } else if (arg === '--output' || arg === '-o') {
      config.outputFile = nextArg;
      i++;
    } else if (arg === '--verify' || arg === '-v') {
      config.verifyOnly = true;
    } else if (arg === '--all' || arg === '-a') {
      config.category = 'all';
    } else if (arg === '--limit' || arg === '-L') {
      config.limit = parseInt(nextArg, 10);
      i++;
    }
  }
  
  return config;
}

/**
 * Load target companies from config
 */
function loadTargetCompanies() {
  const configPath = path.join(__dirname, '../../config/sourcing.json');
  if (fs.existsSync(configPath)) {
    try {
      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      return config.target_companies || {};
    } catch (e) {
      console.error('Error loading config:', e.message);
    }
  }
  return {};
}

/**
 * Common career page URL patterns
 */
function getCareerPageUrls(companyName, knownUrl) {
  const urls = [];
  const slug = companyName.toLowerCase().replace(/[^a-z0-9]/g, '-');
  
  // Add known URL if provided
  if (knownUrl) {
    urls.push(knownUrl);
  }
  
  // Common patterns
  urls.push(`https://careers.${slug}.com`);
  urls.push(`https://www.${slug}.com/careers`);
  urls.push(`https://${slug}.com/jobs`);
  urls.push(`https://jobs.${slug}.com`);
  urls.push(`https://lifeat${slug}.com/jobs`);
  urls.push(`https://apply.${slug}.com`);
  
  return [...new Set(urls)];
}

/**
 * Check if a URL is valid and returns a career page
 */
async function checkCareerPage(url) {
  try {
    const response = await axios.head(url, {
      timeout: 10000,
      maxRedirects: 5,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
      }
    });
    return response.status >= 200 && response.status < 400;
  } catch (e) {
    return false;
  }
}

/**
 * ATS-specific selectors for different career page systems
 */
const ATS_SELECTORS = {
  // Greenhouse
  greenhouse: {
    jobCard: '.job-post', // Greenhouse uses .job-post
    title: '.job-post__title, .title a, h2 a',
    location: '.job-post__location, .location',
    link: 'a[href*="/jobs/"]',
    pagination: '.pagination a.next, .pagination__next, a[rel="next"]',
    searchInput: 'input[name="query"], input#search-query'
  },
  // Lever
  lever: {
    jobCard: '.posting-list-item, .posting-card',
    title: '.posting-title a, h3 a',
    location: '.posting-info__location, .location',
    link: 'a[href*="/jobs/"]',
    pagination: '.pagination a.next, .pagination-next a, a[data-test="pagination-next"]',
    searchInput: 'input[type="search"], input[name="q"]'
  },
  // Workday
  workday: {
    jobCard: '[data-automation-id="jobCard"]',
    title: '[data-automation-id="jobTitle"] a, h2 a',
    location: '[data-automation-id="jobLocation"]',
    link: 'a[href*="/jobs/"]',
    pagination: 'button[data-automation-id="loadMoreJobs"], a[data-automation-id="nextPage"]',
    searchInput: 'input[placeholder*="Search"], input[data-automation-id="searchInput"]'
  },
  // Ashby
  ashby: {
    jobCard: '.job-listing, .jobs-list-item',
    title: '.job-title a, h3 a',
    location: '.job-location, .location',
    link: 'a[href*="/jobs/"]',
    pagination: 'a[href*="page="], button:contains("Load more")',
    searchInput: 'input[name="search"], input[placeholder*="Search"]'
  },
  // SmartRecruiters
  smartrecruiters: {
    jobCard: '.job-item, .posting-list__item',
    title: '.posting-title a, h3 a',
    location: '.posting-info__location',
    link: 'a[href*="/jobs/"]',
    pagination: '.pagination__next a, button[data-test="next-page"]',
    searchInput: 'input[name="q"], input[placeholder*="Search"]'
  },
  // Default/generic
  default: {
    jobCard: '.job-card, .job-listing, .position, .job-opening, [data-testid*="job"], .career-job, .opening, .posting-card, .job-post',
    title: 'h2, h3, .title, .job-title, [class*="title"], a[href*="/jobs/"]',
    location: '.location, .job-location, [class*="location"], .posting-info__location',
    link: 'a[href*="/jobs/"], a[href*="/position/"], a[href*="/apply/"]',
    pagination: '.pagination a.next, .pagination__next, a[rel="next"], button:contains("Load more"), button:contains("Show more")',
    searchInput: 'input[type="text"], input[name*="search"], input[placeholder*="Search"], input[aria-label*="Search"]'
  }
};

/**
 * Detect ATS type from page content
 */
async function detectATSType(page) {
  const atsType = await page.evaluate(() => {
    // Check for ATS-specific elements
    if (document.querySelector('.greenhouse-app, #grnhse_app, .job-board')) return 'greenhouse';
    if (document.querySelector('.lever-app, #lever-app, .posting-list')) return 'lever';
    if (document.querySelector('.workday-app, [data-automation-id*="workday"]')) return 'workday';
    if (document.querySelector('.ashby-app, .ashby-jobs')) return 'ashby';
    if (document.querySelector('.smartrecruiters-app, .sr-app')) return 'smartrecruiters';
    return 'default';
  });
  return atsType;
}

/**
 * Scroll for pagination (infinite scroll)
 */
async function scrollForPagination(page, maxScrolls = 5) {
  let lastHeight = 0;
  
  for (let i = 0; i < maxScrolls; i++) {
    // Try clicking "Load More" button using text matching
    const loadMoreButtons = await page.$$('button');
    for (const btn of loadMoreButtons) {
      try {
        const text = await btn.evaluate(el => el.textContent.toLowerCase());
        if (text.includes('load more') || text.includes('show more') || text.includes('view more') || text.includes('see more')) {
          await btn.click();
          await new Promise(resolve => setTimeout(resolve, 2000));
          break;
        }
      } catch (e) {}
    }
    
    // Also try data-automation-id
    try {
      const dataBtn = await page.$('[data-automation-id="loadMoreJobs"]');
      if (dataBtn) {
        await dataBtn.click();
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    } catch (e) {}
    
    // Then try scrolling
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    if (newHeight === lastHeight) break;
    lastHeight = newHeight;
  }
}

/**
 * Extract jobs with more generic approach
 */
async function extractJobsWithATS(page, atsType) {
  // First try ATS-specific selectors
  const selectors = ATS_SELECTORS[atsType] || ATS_SELECTORS.default;
  
  let jobs = await page.evaluate((sel) => {
    const results = [];
    const cards = document.querySelectorAll(sel.jobCard);
    
    cards.forEach(card => {
      const titleEl = card.querySelector(sel.title);
      const locationEl = card.querySelector(sel.location);
      const linkEl = card.querySelector(sel.link);
      
      if (titleEl) {
        let link = '';
        if (linkEl && linkEl.href) {
          link = linkEl.href.startsWith('http') ? linkEl.href : new URL(linkEl.href, window.location.origin).href;
        } else if (titleEl.tagName === 'A') {
          link = titleEl.href.startsWith('http') ? titleEl.href : new URL(titleEl.href, window.location.origin).href;
        }
        
        results.push({
          title: titleEl.textContent.trim(),
          location: locationEl ? locationEl.textContent.trim() : '',
          link: link
        });
      }
    });
    
    return results;
  }, selectors);
  
  // If no jobs found, try more generic extraction
  if (jobs.length === 0) {
    jobs = await page.evaluate(() => {
      const results = [];
      
      // Look for any links that point to job pages
      const allLinks = document.querySelectorAll('a[href*="job"], a[href*="position"], a[href*="career"], a[href*="/jobs/"]');
      
      allLinks.forEach(link => {
        const text = link.textContent.trim();
        // Filter for likely job titles (not navigation links)
        if (text && text.length > 5 && text.length < 150 && 
            !text.toLowerCase().includes('view all') && 
            !text.toLowerCase().includes('learn more') &&
            !text.toLowerCase().includes('apply now') &&
            !text.toLowerCase().includes('submit') &&
            !text.toLowerCase().includes('sign in')) {
          results.push({
            title: text,
            location: '',
            link: link.href.startsWith('http') ? link.href : new URL(link.href, window.location.origin).href
          });
        }
      });
      
      return results;
    });
  }
  
  // Deduplicate by link
  const seen = new Set();
  return jobs.filter(job => {
    if (!job.link || seen.has(job.link)) return false;
    seen.add(job.link);
    return true;
  });
}

/**
 * Search for jobs on a career page using Puppeteer
 */
async function searchCareerPage(page, url, keywords) {
  const jobs = [];
  
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Detect ATS type
    const atsType = await detectATSType(page);
    console.error(`Detected ATS: ${atsType}`);
    
    // Debug: Get page content info
    const pageInfo = await page.evaluate(() => {
      return {
        title: document.title,
        url: window.location.href,
        bodyText: document.body.innerText.substring(0, 300),
        linksCount: document.querySelectorAll('a').length,
        buttonsCount: document.querySelectorAll('button').length,
        inputsCount: document.querySelectorAll('input').length,
        h2Count: document.querySelectorAll('h2').length,
        h3Count: document.querySelectorAll('h3').length
      };
    });
    console.error('Page info:', JSON.stringify(pageInfo));
    
    // Try to find search input and search for each keyword
    for (const keyword of keywords) {
      try {
        // Look for search input using ATS-specific selectors
        const selectors = ATS_SELECTORS[atsType] || ATS_SELECTORS.default;
        const searchInput = await page.$(`${selectors.searchInput}, input[type="text"], input[name*="search"]`);
        
        if (searchInput) {
          await searchInput.click();
          await searchInput.type(keyword);
          await searchInput.press('Enter');
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Scroll for pagination after search
          await scrollForPagination(page, 3);
        }
        
        // Extract job listings with ATS-specific selectors
        const pageJobs = await extractJobsWithATS(page, atsType);
        
        jobs.push(...pageJobs.map(job => ({
          ...job,
          keyword_searched: keyword,
          ats_type: atsType
        })));
        
        // Clear search for next keyword
        if (searchInput) {
          await searchInput.click({ clickCount: 3 });
          await page.keyboard.press('Backspace');
          await new Promise(resolve => setTimeout(resolve, 500));
        }
        
      } catch (e) {
        // Continue with next keyword
      }
    }
    
    // If no jobs found with search, try extracting all jobs on page
    if (jobs.length === 0) {
      await scrollForPagination(page, 3);
      const allJobs = await extractJobsWithATS(page, atsType);
      jobs.push(...allJobs.map(job => ({
        ...job,
        keyword_searched: 'all',
        ats_type: atsType
      })));
    }
    
  } catch (e) {
    console.error(`Error searching ${url}:`, e.message);
  }
  
  return jobs;
}

/**
 * Verify career page URLs for a company
 */
async function verifyCareerPage(browser, company) {
  const urls = getCareerPageUrls(company.name, company.career_url);
  
  for (const url of urls) {
    try {
      const page = await browser.newPage();
      const isValid = await checkCareerPage(url);
      
      if (isValid) {
        await page.close();
        return { verified: true, url, company: company.name };
      }
      
      await page.close();
    } catch (e) {
      // Continue to next URL
    }
  }
  
  return { verified: false, url: null, company: company.name };
}

/**
 * Main scraper function
 */
async function scrape() {
  const config = parseArgs();
  
  // Load target companies
  const targetCompanies = loadTargetCompanies();
  const companies = [];
  
  if (config.category === 'all') {
    // Add all companies from all categories
    for (const category of Object.values(targetCompanies)) {
      companies.push(...category);
    }
  } else if (targetCompanies[config.category]) {
    companies.push(...targetCompanies[config.category]);
  } else {
    console.error(`Error: Unknown category "${config.category}"`);
    console.error('Available categories:', Object.keys(targetCompanies).join(', '));
    process.exit(1);
  }
  
  console.error(`Searching career pages for ${companies.length} companies in category "${config.category}"`);
  console.error(`Keywords: ${config.keywords.join(', ')}`);
  
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
  
  const results = [];
  const verifiedCompanies = [];
  
  try {
    // First, verify career page URLs
    console.error('\n=== Verifying Career Pages ===\n');
    
    for (const company of companies) {
      process.stdout.write(`Verifying ${company.name}... `);
      
      const result = await verifyCareerPage(browser, company);
      
      if (result.verified) {
        console.error(`✓ ${result.url}`);
        verifiedCompanies.push({ ...company, verified_career_url: result.url });
      } else {
        console.error('✗ Not found');
        verifiedCompanies.push({ ...company, verified_career_url: null });
      }
      
      // Rate limiting
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // If verify only mode, output verified companies
    if (config.verifyOnly) {
      const output = JSON.stringify(verifiedCompanies.filter(c => c.verified_career_url), null, 2);
      console.log(output);
      return;
    }
    
    // Search for jobs on verified career pages
    console.error('\n=== Searching for Jobs ===\n');
    
    for (const company of verifiedCompanies) {
      if (!company.verified_career_url) continue;
      
      process.stdout.write(`Searching ${company.name}... `);
      
      const page = await browser.newPage();
      const jobs = await searchCareerPage(page, company.verified_career_url, config.keywords);
      
      if (jobs.length > 0) {
        console.error(`✓ Found ${jobs.length} jobs`);
        
        jobs.forEach(job => {
          results.push({
            source: 'career_page',
            company: company.name,
            career_page: company.verified_career_url,
            role_title: job.title,
            location: job.location,
            application_url: job.link,
            keyword_searched: job.keyword_searched,
            scraped_at: new Date().toISOString()
          });
        });
      } else {
        console.error('No jobs found');
      }
      
      await page.close();
      
      // Rate limiting
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    // Output results
    const output = JSON.stringify(results, null, 2);
    
    if (config.outputFile) {
      fs.writeFileSync(config.outputFile, output);
      console.error(`\nResults written to: ${config.outputFile}`);
    } else {
      console.log(output);
    }
    
    console.error(`\n=== Summary ===`);
    console.error(`Companies searched: ${verifiedCompanies.length}`);
    console.error(`Companies with verified career pages: ${verifiedCompanies.filter(c => c.verified_career_url).length}`);
    console.error(`Jobs found: ${results.length}`);
    
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