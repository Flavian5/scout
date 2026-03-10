#!/usr/bin/env node

/**
 * CTO Search - Find technical decision makers at companies with C2C budget
 * 
 * Usage:
 *   node search.js --company "Recursion Pharmaceuticals"
 *   node search.js --industry "bio-ai"
 *   node search.js --list companies.json
 */

const { chromium } = require('playwright');
const https = require('https');
const http = require('http');
const { URL } = require('url');

// Configuration
const CONFIG = {
  // Known target companies by industry
  INDUSTRIES: {
    'bio-ai': [
      'Chan Zuckerberg Initiative',
      'Recursion Pharmaceuticals', 
      'Insitro',
      'Genentech',
      'Arc Institute',
      'Recursion',
      'Exscientia',
      'Absci',
      'Generate:Biomedicines',
      'Erasca'
    ],
    'voice-ai': [
      'Anthropic',
      'OpenAI',
      'AssemblyAI',
      'Deepgram',
      'Sonix',
      'Respeecher',
      'Murf AI'
    ],
    'recsys': [
      'TikTok',
      'Netflix',
      'Spotify',
      'Uber',
      'Airbnb',
      'Pinterest',
      'Snap',
      'Twitter'
    ],
    'large-tech': [
      'Amazon',
      'Meta',
      'Google',
      'Microsoft',
      'Apple',
      'NVIDIA'
    ]
  },
  
  // Target roles (priority order)
  ROLES: [
    'CTO',
    'VP Engineering',
    'VP of Engineering',
    'Head of ML',
    'Head of AI',
    'Chief AI Officer',
    'VP Data Science',
    'Chief Data Officer'
  ],
  
  // Minimum company stage for C2C budget
  MIN_SERIES: 'C',
  MIN_EMPLOYEES: 100,
  MIN_FUNDING_Millions: 50
};

// Simple HTTP request helper
function httpGet(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    client.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

// Web search using DuckDuckGo (no API key required)
async function webSearch(query) {
  console.log(`🔍 Searching: ${query}`);
  
  const encodedQuery = encodeURIComponent(query);
  const url = `https://html.duckduckgo.com/html/?q=${encodedQuery}`;
  
  try {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2000);
    
    // Extract search results
    const results = await page.evaluate(() => {
      const items = document.querySelectorAll('.result__body');
      return Array.from(items).slice(0, 10).map(item => {
        const titleEl = item.querySelector('.result__a');
        const snippetEl = item.querySelector('.result__snippet');
        return {
          title: titleEl ? titleEl.textContent : '',
          url: titleEl ? titleEl.href : '',
          snippet: snippetEl ? snippetEl.textContent : ''
        };
      });
    });
    
    await browser.close();
    return results;
  } catch (error) {
    console.error('Search error:', error.message);
    return [];
  }
}

// Search for company funding information
async function getCompanyFunding(companyName) {
  const results = await webSearch(`${companyName} funding raised Series`);
  
  // Parse funding from results
  let funding = null;
  let stage = null;
  
  for (const result of results) {
    const text = result.title + ' ' + result.snippet;
    
    // Match funding amounts
    const amountMatch = text.match(/\$(\d+(?:\.\d+)?)\s*(million|billion|M|B)/i);
    if (amountMatch) {
      const amount = parseFloat(amountMatch[1]);
      const unit = amountMatch[2].toLowerCase();
      funding = unit.startsWith('b') ? amount * 1000 : amount;
    }
    
    // Match series
    const stageMatch = text.match(/series\s+([A-Z])/i);
    if (stageMatch) {
      stage = stageMatch[1].toUpperCase();
    }
  }
  
  return { funding, stage };
}

// Search for company employee count
async function getCompanyEmployees(companyName) {
  const results = await webSearch(`${companyName} employees LinkedIn`);
  
  let employees = null;
  for (const result of results) {
    const text = result.title + ' ' + result.snippet;
    const empMatch = text.match(/(\d+(?:,\d+)*)\s*employees/i);
    if (empMatch) {
      employees = parseInt(empMatch[1].replace(/,/g, ''));
      break;
    }
  }
  
  return employees;
}

// Search for technical leadership
async function findTechnicalLeadership(companyName) {
  const contacts = [];
  
  // Search for each role
  for (const role of CONFIG.ROLES) {
    const query = `site:linkedin.com/in "${companyName}" ${role}`;
    const results = await webSearch(query);
    
    for (const result of results) {
      // Extract LinkedIn profile URL
      const linkedinMatch = result.url.match(/linkedin\.com\/in\/[a-zA-Z0-9_-]+/);
      if (linkedinMatch) {
        contacts.push({
          name: result.title.split('|')[0].trim(),
          title: role,
          linkedin_url: 'https://' + linkedinMatch[0],
          found_via: 'web_search'
        });
      }
    }
  }
  
  return contacts;
}

// Alternative: Search company website for leadership
async function findLeadershipOnCompanySite(companyName, domain) {
  const contacts = [];
  
  try {
    const url = `https://${domain}/about` || `https://${domain}/team`;
    const html = await httpGet(url).catch(() => '');
    
    // Look for leadership/team page links
    const leadershipPatterns = [
      /<a[^>]*href="[^"]*leader[^"]*"[^>]*>([^<]+)/gi,
      /<a[^>]*href="[^"]*team[^"]*"[^>]*>([^<]+)/gi,
      /<a[^>]*href="[^"]*about[^"]*"[^>]*>([^<]+)/gi
    ];
    
    // For now, return empty - would need more sophisticated parsing
  } catch (e) {
    // Ignore errors
  }
  
  return contacts;
}

// Check for ML hiring signals
async function checkMLHiringSignals(companyName) {
  const signals = {
    ml_job_postings: false,
    ml_team_mentioned: false,
    ml_blog_posts: 0
  };
  
  // Search for ML job postings
  const jobResults = await webSearch(`${companyName} "ML Engineer" OR "Machine Learning" hiring jobs`);
  signals.ml_job_postings = jobResults.length > 0;
  
  // Search for ML team
  const teamResults = await webSearch(`${companyName} ML Platform team OR ML Infrastructure team`);
  signals.ml_team_mentioned = teamResults.length > 0;
  
  // Search for ML blog posts
  const blogResults = await webSearch(`${companyName} ML engineering blog OR machine learning technical`);
  signals.ml_blog_posts = blogResults.length;
  
  return signals;
}

// Score target based on C2C budget potential
function scoreTarget(companyData) {
  let score = 0;
  
  // Company stage (30%)
  if (companyData.stage) {
    const stageOrder = ['A', 'B', 'C', 'D', 'E'];
    const stageIndex = stageOrder.indexOf(companyData.stage);
    if (stageIndex >= 2) { // Series C or later
      score += 30;
    } else if (stageIndex >= 1) {
      score += 20;
    } else {
      score += 10;
    }
  } else if (companyData.employees && companyData.employees >= 100) {
    score += 25;
  }
  
  // Funding (25%)
  if (companyData.funding && companyData.funding >= CONFIG.MIN_FUNDING_Millions) {
    score += 25;
  } else if (companyData.funding && companyData.funding >= 20) {
    score += 15;
  }
  
  // ML signals (25%)
  if (companyData.ml_signals.ml_job_postings) score += 15;
  if (companyData.ml_signals.ml_team_mentioned) score += 10;
  
  // Has contact (20%)
  if (companyData.contacts && companyData.contacts.length > 0) {
    score += 20;
  }
  
  return Math.min(score, 100);
}

// Main search function
async function searchCompany(companyName) {
  console.log(`\n=== Searching for ${companyName} ===\n`);
  
  // Step 1: Get company funding info
  console.log('📊 Checking funding...');
  const funding = await getCompanyFunding(companyName);
  console.log(`   Funding: ${funding.funding ? '$' + funding.funding + 'M' : 'Unknown'}`);
  console.log(`   Stage: ${funding.stage || 'Unknown'}`);
  
  // Step 2: Get employee count
  console.log('\n👥 Checking company size...');
  const employees = await getCompanyEmployees(companyName);
  console.log(`   Employees: ${employees ? employees.toLocaleString() : 'Unknown'}`);
  
  // Step 3: Check ML hiring signals
  console.log('\n🔬 Checking ML signals...');
  const ml_signals = await checkMLHiringSignals(companyName);
  console.log(`   ML Job Postings: ${ml_signals.ml_job_postings ? 'Yes' : 'No'}`);
  console.log(`   ML Team: ${ml_signals.ml_team_mentioned ? 'Yes' : 'No'}`);
  
  // Step 4: Find technical leadership
  console.log('\n👤 Finding technical leadership...');
  const contacts = await findTechnicalLeadership(companyName);
  console.log(`   Found ${contacts.length} contacts`);
  
  // Compile results
  const companyData = {
    company: companyName,
    stage: funding.stage,
    funding: funding.funding,
    employees: employees,
    ml_signals: ml_signals,
    contacts: contacts,
    qualification_score: 0
  };
  
  // Calculate score
  companyData.qualification_score = scoreTarget(companyData);
  console.log(`\n📈 Qualification Score: ${companyData.qualification_score}/100`);
  
  return companyData;
}

// Search by industry
async function searchIndustry(industry) {
  const companies = CONFIG.INDUSTRIES[industry] || [];
  console.log(`Searching ${industry}: ${companies.length} companies`);
  
  const results = [];
  for (const company of companies) {
    const data = await searchCompany(company);
    if (data.qualification_score >= 70) {
      results.push(data);
    }
  }
  
  return results;
}

// CLI handling
async function main() {
  const args = process.argv.slice(2);
  const options = {};
  
  // Parse arguments
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--company' && args[i + 1]) {
      options.company = args[i + 1];
      i++;
    } else if (args[i] === '--industry' && args[i + 1]) {
      options.industry = args[i + 1];
      i++;
    } else if (args[i] === '--output' || args[i] === '-o') {
      options.output = args[i + 1];
      i++;
    }
  }
  
  let results = [];
  
  if (options.company) {
    results = [await searchCompany(options.company)];
  } else if (options.industry) {
    results = await searchIndustry(options.industry);
  } else {
    console.log('Usage:');
    console.log('  node search.js --company "Company Name"');
    console.log('  node search.js --industry "bio-ai"');
    console.log('  node search.js --industry "recsys"');
    console.log('\nAvailable industries: bio-ai, voice-ai, recsys, large-tech');
    process.exit(1);
  }
  
  // Filter to qualified targets
  const qualified = results.filter(r => r.qualification_score >= 70);
  console.log(`\n=== Summary ===`);
  console.log(`Total searched: ${results.length}`);
  console.log(`Qualified targets (score >= 70): ${qualified.length}`);
  
  // Output results
  if (options.output) {
    const fs = require('fs');
    fs.writeFileSync(options.output, JSON.stringify(qualified, null, 2));
    console.log(`Results saved to ${options.output}`);
  } else {
    console.log('\nQualified Targets:');
    console.log(JSON.stringify(qualified, null, 2));
  }
}

main().catch(console.error);