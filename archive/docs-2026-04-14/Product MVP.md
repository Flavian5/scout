# **Product MVP Document: Autonomous Job Search Agent**

## **1\. Product Vision & Objective**

To build a highly configurable, autonomous job search assistant that handles the entire top-of-funnel recruitment process. The agent will discover, evaluate, rank, and prepare tailored application materials for high-fit roles, leaving the user with only the final "review and submit" action.

## **2\. Target Audience (MVP)**

* **Primary User:** The creator (Dogfooding phase).  
* **Secondary Users:** Tech professionals (Engineers, Product Managers, Data Scientists) who want to passively hunt for high-tier roles without the daily grind of scrolling job boards and tweaking resumes.

## **3\. Core Features (MVP Scope)**

1. **Markdown-Based Persona Ingestion:** Users define their core skills, work history, target compensation, and ideal company stage in simple markdown files.  
2. **Configurable Sourcing:** A parameter-driven list of job boards (e.g., LinkedIn, Wellfound, specific company career pages) and search queries.  
3. **Intelligent Parsing & Enrichment:** Extraction of JD requirements paired with an LLM-driven estimation of company financials (funding stage, base comp ranges, runway).  
4. **Multi-Dimensional Scoring:** Evaluating the fit between the JD and the user's persona based on hard skills, culture, and financial requirements.  
5. **Artifact Generation:** Automated, hyper-tailored rewriting of the base CV and Cover Letter for the top-ranked jobs.  
6. **Interview Prep Package:** A generated summary of the company, the "Hiring Manager Vibe", likelihood of success, and potential skill gaps to prep for.  
7. **Delivery Mechanism:** A daily "Job Action Package" delivered via a preferred channel (e.g., Discord webhook, Email, or a local Markdown summary file).

## **4\. Key Tradeoffs & MVP Decisions**

### **Tradeoff 1: Automated Application vs. Human-in-the-Loop**

* **Decision:** Human-in-the-Loop (Stop at Artifact Generation).  
* **Rationale:** Fully automated applying is highly brittle due to varying ATS forms (Workday vs. Greenhouse) and carries the risk of hallucinated CV details. The MVP maximizes value by doing 95% of the work (finding and tailoring) but leaves the final 5% (clicking apply) to the user to ensure quality control.

### **Tradeoff 2: Traditional Scraping vs. Authenticated LLM Browser Agents**

* **Decision:** Direct scraping via an LLM-driven browser using user-provided session cookies (specifically for LinkedIn).  
* **Rationale:** Maintaining traditional DOM-based scrapers for LinkedIn is notoriously difficult due to aggressive anti-bot measures. For the MVP, we will require the user to provide their active LinkedIn session cookies. The agent will then spawn a browser window (via Playwright) and utilize the LLM's vision/DOM-parsing capabilities to navigate and extract job postings exactly as an authenticated human would, bypassing standard scraper blocks.

### **Tradeoff 3: Deep Research vs. Heuristic Financial Estimation**

* **Decision:** LLM-driven heuristic estimation based on web search snippets.  
* **Rationale:** Integrating Crunchbase or PitchBook APIs is expensive. Instead, the agent will use OpenClaw search skills to query "![][image1]  
  funding" or "![][image1]  
  levels.fyi" and use an LLM to estimate the financial health and compensation bands.

### **Tradeoff 4: Complex Database vs. Markdown State Management**

* **Decision:** File-system Markdown State Management.  
* **Rationale:** Aligning with OpenClaw's philosophy, all configurations, personas, and output logs will be markdown files. This requires zero database setup, makes it inherently version-controllable (via Git), and is easily human-readable.

## **5\. User Journey (The "Daily Heartbeat")**

1. **02:00 AM:** Agent wakes up and reads persona.md and config.md.  
2. **02:05 AM:** Agent queries target job boards for postings in the last 24 hours.  
3. **02:30 AM:** Agent enriches the top 50 raw postings with estimated financials and company context.  
4. **03:00 AM:** Agent scores the 50 postings against the persona, filtering down to the "Top 3".  
5. **03:30 AM:** Agent generates tailored CVs (cv\_companyA.md) and gap analyses for the Top 3\.  
6. **08:00 AM:** User wakes up to a notification: *"3 High-Fit Roles Found. Packages generated."* User reviews, copies the tailored text, and applies.

[image1]: <data:image/png;base64,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>