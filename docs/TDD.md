# **TDD: Autonomous Job Search Assistant (OpenClaw Implementation)**

## **1\. Architectural Overview**

We are utilizing a **Multi-Agent Orchestration** pattern within the OpenClaw ecosystem. The system is designed to be decentralized, where "Skills" act as the interface to the external world and "Agents" act as the logical decision-makers.

### **Core Philosophy**

* **Skills:** Stateless, I/O bound, technical wrappers (The "Hands").  
* **Agents:** Stateful, goal-oriented, logic-driven (The "Brain").  
* **State:** Managed via the local filesystem using Markdown and JSON (The "Memory").

## **2\. Agent Definitions (The "Who")**

We will deploy three specialized agents, each with a scoped agent.md and dedicated workspace.

### **A. The Scout (agents/scout.md)**

* **Role:** High-volume top-of-funnel discovery.  
* **Tools:** linkedin-scout, web-browser.  
* **Logic:** Periodically scrapes configured boards. It focuses on extraction accuracy over evaluation.  
* **Output:** Saves "Raw Leads" to data/raw\_leads.json.

### **B. The Analyst (agents/analyst.md)**

* **Role:** Deep vetting and financial estimation.  
* **Tools:** tavily-search, comp-researcher.  
* **Logic:** Takes raw leads and performs web searches for funding, Glassdoor trends, and Levels.fyi data.  
* **Output:** Updates leads with "Enrichment Data" in data/enriched\_leads.json.

### **C. The Strategist (agents/strategist.md)**

* **Role:** Scoring, asset tailoring, and notification.  
* **Tools:** asset-generator (Custom), local-file-access.  
* **Logic:** Performs the final 0-100 scoring. If a score \> 85, it triggers the asset generation workflow.  
* **Output:** Generates applications/\[Company\]\_Package.zip and sends the Daily Heartbeat notification.

## **3\. Skill Definitions (The "How")**

### **Existing/Standard OpenClaw Skills (Leveraged)**

1. **openclaw-skill-browser**: Used for navigating authenticated sessions.  
2. **openclaw-skill-tavily**: Used for real-time web research on company financials.  
3. **openclaw-skill-file-system**: Used for reading the user's base persona.md and cv\_base.tex.

### **Custom Source Code (To be Built)**

These are the areas where we write custom logic vs. just configuring OpenClaw.

| Skill / Component | Build vs. Leverage | Description |
| :---- | :---- | :---- |
| **linkedin-scout** | **Build (Extension)** | Custom Playwright script to handle LinkedIn's specific DOM for "Jobs" search using session cookies. |
| **evaluator-logic** | **Build (Logic)** | A specific prompt-template and scoring function that maps JD requirements to persona.md. |
| **asset-generator** | **Build (Tool)** | A custom skill that wraps pdflatex or pandoc to compile the tailored LaTeX CV. |
| **heartbeat-notifier** | **Leverage** | Use the standard OpenClaw Discord/Telegram webhook skill. |

## **4\. Data Flow & State Management**

Following the "Markdown State Management" tradeoff, the filesystem is our DB.

1. **config/persona.md**: User-defined skills, target TC, and "hard nos".  
2. **config/sourcing.json**: List of URLs and search keywords.  
3. **data/leads/**: One folder per job.  
   * jd.md: The raw job description.  
   * meta.json: Score, company financial estimation, and status (New, Reviewed, Applied).  
   * tailored\_cv.pdf: The generated asset.

## **5\. Implementation Roadmap (The "Src" vs "Structure")**

### **Phase 1: OpenClaw Structure (Configuration)**

* Initialize project: openclaw init job-scout.  
* Configure openclaw.json with LinkedIn cookies and Tavily API keys.  
* Setup folders for persona and applications.

### **Phase 2: Custom Skill Development (Source Code)**

* **skill-linkedin**: Write the JavaScript logic to navigate to /jobs and extract the JSON payload from the page.  
* **skill-pdf-engine**: Write a small shell wrapper that takes a Markdown string and runs it through a LaTeX template.

### **Phase 3: Agent Prompt Engineering (Source Code)**

* Draft the agent.md for the **Strategist**. This is the most critical "source code"—the logical instructions that prevent the agent from hallucinating fit.

### **Phase 4: The Heartbeat (Orchestration)**

* Define a cron schedule in openclaw.json to trigger the **Scout** at 02:00 AM daily.

## **6\. Success Metrics for MVP**

* **Precision:** 80% of "Top 3" recommendations are actually roles the user wants to apply for.  
* **Speed:** Full pipeline (Discovery to Artifact) completes in under 60 minutes.  
* **Reliability:** LinkedIn session cookies remain valid for at least 7 days without re-auth.