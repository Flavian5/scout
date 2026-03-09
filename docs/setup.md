# **Local Setup Guide: OpenClaw Job Assistant**

This guide walks you through the 2026 "standard" installation for OpenClaw on your local machine, optimized for the **Autonomous Job Search Assistant** architecture.

## **1\. Prerequisites**

Before starting, ensure your environment meets the minimum requirements for agentic workflows:

* **Node.js:** v22.0.0 or newer (Required for the Gateway and CLI).  
* **Git:** For skill management and workspace versioning.  
* **Hardware:** 8GB+ RAM recommended (16GB+ if running local LLMs via Ollama).  
* **Homebrew (macOS/Linux):** Recommended for dependency management.

## **2\. One-Line Installation**

Open your terminal and run the official installer. This script handles the CLI binary, basic dependencies, and environment pathing.

**macOS / Linux / WSL2:**

curl \-fsSL \[https://openclaw.ai/install.sh\](https://openclaw.ai/install.sh) | bash

**Windows (PowerShell Admin):**

iwr \-useb \[https://openclaw.ai/install.ps1\](https://openclaw.ai/install.ps1) | iex

## **3\. Interactive Onboarding**

Run the onboarding wizard to initialize your configuration and the background "Daemon" service.

openclaw onboard \--install-daemon

### **Wizard Checklist:**

1. **AI Provider:** Select **Anthropic (Claude 3.5/4.5)** for complex job evaluation or **Ollama** for private, local processing.  
2. **Gateway Port:** Default is 18789\. Keep this unless you have a conflict.  
3. **Workspace Path:** Set this to your project folder (e.g., \~/projects/job-scout).  
4. **Channel:** Connect **Telegram** or **Signal** so the agent can send you the "Daily Action Package."

## **4\. Project Structure (TDD Alignment)**

Navigate to your workspace and initialize the specific folder structure defined in your Technical Design Document.

mkdir \-p job-scout/{agents,skills,config,data/leads,applications}  
cd job-scout

### **Key Initialization Commands:**

* **Add Agents:**  
  openclaw agents add scout \--description "Job discovery agent"  
  openclaw agents add analyst \--description "Company health & comp researcher"  
  openclaw agents add strategist \--description "Final scoring and asset tailor"

* **Install Core Skills:**  
  npx clawhub@latest install browser    \# For scraping  
  npx clawhub@latest install tavily     \# For research  
  npx clawhub@latest install webhook    \# For notifications

## **5\. Configuration (openclaw.json)**

Your configuration file is located at \~/.openclaw/openclaw.json. For the Job Assistant, ensure the following sections are tuned:

{  
  "agents": {  
    "defaults": {  
      "sandbox": { "mode": "non-main" },  
      "heartbeat": { "every": "24h", "at": "02:00" }  
    }  
  },  
  "skills": {  
    "entries": {  
      "linkedin-scout": {  
        "enabled": true,  
        "cookies": { "li\_at": "YOUR\_COOKIE", "JSESSIONID": "YOUR\_ID" }  
      }  
    }  
  }  
}

## **6\. Verification**

Run the diagnostic tool to ensure your local environment is ready for autonomous operation:

openclaw doctor

If everything is green, launch your dashboard:

openclaw dashboard

You can now access the Control UI at http://127.0.0.1:18789.

## **Troubleshooting Common 2026 Issues**

* **"Command not found":** Restart your terminal or run source \~/.zshrc (or \~/.bashrc) to refresh your PATH.  
* **Browser Sandbox Errors:** Ensure you have the latest Chrome/Chromium installed. If using Linux, run sudo openclaw install-deps browser.  
* **Cookie Expiry:** LinkedIn session cookies typically expire every 7–14 days. You can automate the refresh by using a dedicated Chrome profile in the OpenClaw settings.