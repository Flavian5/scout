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

# Run FTE Scout agent
# Job ID: 4c717471-e359-4b8a-8920-24d33cd51ccc
run-scout:
	@echo "Running FTE Scout agent..."
	openclaw cron run 4c717471-e359-4b8a-8920-24d33cd51ccc

# Run C2C Scout agent (not configured in cron yet)
run-scout-c2c:
	@echo "Running C2C Scout agent..."
	@echo "ERROR: C2C Scout cron job not configured. Run 'openclaw cron add' to create it."

# Run FTE Analyst agent
# Job ID: 5e897123-557e-4a5c-866c-fa9cd93927e2
run-analyst:
	@echo "Running FTE Analyst agent..."
	openclaw cron run 5e897123-557e-4a5c-866c-fa9cd93927e2

# Run C2C Analyst agent (not configured in cron yet)
run-analyst-c2c:
	@echo "Running C2C Analyst agent..."
	@echo "ERROR: C2C Analyst cron job not configured. Run 'openclaw cron add' to create it."

# Run FTE Strategist agent
# Job ID: e91b0b24-7704-41bb-8b50-fe9771b9acd7
run-strategist:
	@echo "Running FTE Strategist agent..."
	openclaw cron run e91b0b24-7704-41bb-8b50-fe9771b9acd7

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

# Clean generated files
clean:
	@echo "Cleaning generated files..."
	rm -f data/cv_fte.pdf data/cv_c2c.pdf
	rm -rf logs/
	@echo "✓ Clean complete"