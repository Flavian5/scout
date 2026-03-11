# Scout - Autonomous Job Search Agent
# Makefile for common tasks

.PHONY: help install pdf pdfs pdf-fte pdf-c2c daily-run run-scout run-scout-c2c run-analyst run-analyst-c2c run-strategist run-strategist-c2c clean doctor init

# Default target
help:
	@echo "Scout - Autonomous Job Search Agent"
	@echo "====================================="
	@echo ""
	@echo "PDF Generation:"
	@echo "  make pdfs       - Generate both FTE and C2C PDFs"
	@echo "  make pdf-fte    - Generate FTE CV PDF"
	@echo "  make pdf-c2c    - Generate C2C CV PDF"
	@echo ""
	@echo "Agent Commands:"
	@echo "  make run-scout          - Run FTE Scout agent"
	@echo "  make run-scout-c2c      - Run C2C Scout agent"
	@echo "  make run-analyst        - Run FTE Analyst agent"
	@echo "  make run-analyst-c2c    - Run C2C Analyst agent"
	@echo "  make run-strategist     - Run FTE Strategist agent"
	@echo "  make run-strategist-c2c - Run C2C Strategist agent"
	@echo ""
	@echo "Daily Run:"
	@echo "  make daily-run  - Run full daily pipeline (all agents)"
	@echo ""
	@echo "Setup:"
	@echo "  make install    - Install required dependencies"
	@echo "  make doctor     - Check OpenClaw setup"
	@echo "  make init       - Initialize OpenClaw project"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean      - Clean generated PDFs and logs"

# ============================================
# PDF Generation
# ============================================

# Generate both PDFs
pdfs: pdf-fte pdf-c2c
	@echo "✓ All PDFs generated"

# Generate FTE CV PDF
pdf-fte:
	@echo "Generating FTE CV PDF..."
	markdown-pdf data/cv_fte.md -o data/cv_fte.pdf
	@echo "✓ FTE CV PDF generated: data/cv_fte.pdf"

# Generate C2C CV PDF
pdf-c2c:
	@echo "Generating C2C CV PDF..."
	markdown-pdf data/cv_c2c.md -o data/cv_c2c.pdf
	@echo "✓ C2C CV PDF generated: data/cv_c2c.pdf"

# ============================================
# Agent Commands
# ============================================

# Run FTE Scout agent (via cron)
# Job ID: 4c717471-e359-4b8a-8920-24d33cd51ccc
run-scout:
	@echo "Running FTE Scout agent..."
	openclaw cron run 4c717471-e359-4b8a-8920-24d33cd51ccc

# Run FTE Scout agent directly (alternative)
run-scout-direct:
	@echo "Running FTE Scout agent directly..."
	openclaw agent --agent main --message "Run the scout agent to find FTE job leads. Check config/sourcing.json for keywords and target companies. Write results to data/leads/raw_leads.json"

# Run C2C Scout agent (not configured in cron yet)
run-scout-c2c:
	@echo "Running C2C Scout agent..."
	@echo "ERROR: C2C Scout cron job not configured. Run 'openclaw cron add' to create it."

# Run FTE Analyst agent (via cron)
# Job ID: 5e897123-557e-4a5c-866c-fa9cd93927e2
run-analyst:
	@echo "Running FTE Analyst agent..."
	openclaw cron run 5e897123-557e-4a5c-866c-fa9cd93927e2

# Run FTE Analyst agent directly (alternative)
run-analyst-direct:
	@echo "Running FTE Analyst agent directly..."
	openclaw agent --agent main --message "Run the analyst agent to score and enrich leads from data/leads/raw_leads.json. Write results to data/leads/enriched_leads.json"

# Run C2C Analyst agent (not configured in cron yet)
run-analyst-c2c:
	@echo "Running C2C Analyst agent..."
	@echo "ERROR: C2C Analyst cron job not configured. Run 'openclaw cron add' to create it."

# Run FTE Strategist agent (via cron)
# Job ID: e91b0b24-7704-41bb-8b50-fe9771b9acd7
run-strategist:
	@echo "Running FTE Strategist agent..."
	openclaw cron run e91b0b24-7704-41bb-8b50-fe9771b9acd7

# Run FTE Strategist agent directly (alternative)
run-strategist-direct:
	@echo "Running FTE Strategist agent directly..."
	openclaw agent --agent main --message "Run the strategist agent to generate application materials for leads in data/leads/enriched_leads.json. Write CV and cover letter to applications/"

# Run C2C Strategist agent (not configured in cron yet)
run-strategist-c2c:
	@echo "Running C2C Strategist agent..."
	@echo "ERROR: C2C Strategist cron job not configured. Run 'openclaw cron add' to create it."

# ============================================
# Daily Run - Full Pipeline
# ============================================

# Run full daily pipeline (FTE)
daily-run-fte:
	@echo "=== Starting FTE Daily Run ==="
	openclaw cron run 4c717471-e359-4b8a-8920-24d33cd51ccc
	openclaw cron run 5e897123-557e-4a5c-866c-fa9cd93927e2
	openclaw cron run e91b0b24-7704-41bb-8b50-fe9771b9acd7
	@echo "=== FTE Daily Run Complete ==="

# Run full daily pipeline (C2C)
daily-run-c2c:
	@echo "=== Starting C2C Daily Run ==="
	@echo "ERROR: C2C cron jobs not configured. Run 'openclaw cron add' to create them."
	@echo "=== C2C Daily Run Complete ==="

# Run full daily pipeline (both FTE and C2C)
daily-run: daily-run-c2c daily-run-fte
	@echo "✓ Daily run complete"

# ============================================
# Setup & Utilities
# ============================================

# Install dependencies
install:
	@echo "Installing dependencies..."
	@echo "Make sure you have installed:"
	@echo "  - markdown-pdf: npm install -g markdown-pdf"
	@echo "  - OpenClaw: curl -fsSL https://openclaw.ai/install.sh | bash"
	@which markdown-pdf > /dev/null 2>&1 && echo "✓ markdown-pdf installed" || echo "✗ markdown-pdf not found - run: npm install -g markdown-pdf"
	@which openclaw > /dev/null 2>&1 && echo "✓ OpenClaw installed" || echo "✗ OpenClaw not found - run: curl -fsSL https://openclaw.ai/install.sh | bash"

# Check OpenClaw setup
doctor:
	@echo "Running OpenClaw doctor..."
	openclaw doctor

# Initialize OpenClaw project
init:
	@echo "Initializing OpenClaw project..."
	openclaw init

# ============================================
# Skill Testing Commands
# ============================================

# Test LinkedIn scraper with auth and full JD extraction
test-linkedin:
	@echo "Testing LinkedIn scraper with authenticated session..."
	cd skills/linkedin-scout && node scrape.js --keywords "Senior Machine Learning Engineer" --location "San Francisco Bay Area" --limit 10 --max-jd 5 --output ../../data/leads/raw_leads.json

# Test signal detector
test-signals:
	@echo "Testing signal detector..."
	python3 skills/signal-detector/detect.py --input data/leads/raw_leads.json --output data/leads/signals.json --no-llm

# Test signal detector with LLM
test-signals-llm:
	@echo "Testing signal detector with LLM..."
	python3 skills/signal-detector/detect.py --input data/leads/raw_leads.json --output data/leads/signals.json

# Test company research
test-company-research:
	@echo "Testing company research..."
	python3 skills/company-research/research.py --input data/leads/enriched_leads.json --max 5

# Test asset generator
test-assets:
	@echo "Testing asset generator..."
	python3 skills/asset-generator/generate.py --input data/leads/enriched_leads.json --top 3

# Test full pipeline (scraping to asset generation)
test-pipeline:
	@echo "=== Testing Full Pipeline ==="
	@echo ""
	@echo "Step 1: Scraping LinkedIn..."
	make test-linkedin
	@echo ""
	@echo "Step 2: Scoring leads..."
	python3 score_leads.py
	@echo ""
	@echo "Step 3: Detecting signals..."
	make test-signals
	@echo ""
	@echo "Step 4: Researching companies..."
	make test-company-research
	@echo ""
	@echo "Step 5: Generating assets..."
	make test-assets
	@echo ""
	@echo "=== Pipeline Test Complete ==="

# ============================================
# Clean generated files
# ============================================

clean:
	@echo "Cleaning generated files..."
	rm -f data/cv_fte.pdf data/cv_c2c.pdf
	rm -rf logs/
	rm -f data/leads/signals.json
	rm -rf data/companies/
	rm -rf applications/*/
	@echo "✓ Clean complete"
