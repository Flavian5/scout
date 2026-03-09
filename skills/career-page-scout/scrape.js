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
    verifyOnly: false
  };
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--keywords' && args[i + 1]) {
      config.keywords = [args[i + 1]];
      i++;
    } else if (args[i] === '--category' && args[i + 1]) {
      config.category = args[i + 1];
      i++;
    } else if (args[i] === '--output' && args[i + 1]) {
      config.outputFile = args[i + 1];
      i++;
    } else if (args[i] === '--verify') {
      config.verifyOnly = true;
    } else if (args[i] === '--all') {
      config.category = 'all';
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
 * Search for jobs on a career page using Puppeteer
 */
async function searchCareerPage(page, url, keywords) {
  const jobs = [];
  
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Try to find search input and search for each keyword
    for (const keyword of keywords) {
      try {
        // Look for search input
        const searchInput = await page.$('input[type="text"], input[name*="search"], input[placeholder*="Search"], input[aria-label*="Search"]');
        
        if (searchInput) {
          await searchInput.click();
          await searchInput.type(keyword);
          await searchInput.press('Enter');
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Extract job listings
        const pageJobs = await page.evaluate(() => {
          const results = [];
          
          // Common job card selectors
          const jobCards = document.querySelectorAll('.job-card, .job-listing, .position, .job-opening, [data-testid*="job"], .career-job, .opening');
          
          jobCards.forEach(card => {
            const titleEl = card.querySelector('h2, h3, .title, .job-title, [class*="title"]');
            const locationEl = card.querySelector('.location, .job-location, [class*="location"]');
            const linkEl = card.querySelector('a[href*="job"], a[href*="position"], a[href*="apply"]');
            
            if (titleEl) {
              results.push({
                title: titleEl.textContent.trim(),
                location: locationEl ? locationEl.textContent.trim() : '',
                link: linkEl ? (linkEl.href.startsWith('http') ? linkEl.href : new URL(linkEl.href, window.location.origin).href) : ''
              });
            }
          });
          
          return results;
        });
        
        jobs.push(...pageJobs.map(job => ({
          ...job,
          keyword_searched: keyword
        })));
        
        // Clear search for next keyword
        if (searchInput) {
          await searchInput.click({ clickCount: 3 });
          await page.keyboard.press('Backspace');
        }
        
      } catch (e) {
        // Continue with next keyword
      }
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