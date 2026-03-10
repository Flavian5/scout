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
run-scout:
	@echo "Running FTE Scout agent..."
	openclaw agents run scout

# Run C2C Scout agent
run-scout-c2c:
	@echo "Running C2C Scout agent..."
	openclaw agents run scout_c2c

# Run FTE Analyst agent
run-analyst:
	@echo "Running FTE Analyst agent..."
	openclaw agents run analyst

# Run C2C Analyst agent
run-analyst-c2c:
	@echo "Running C2C Analyst agent..."
	openclaw agents run analyst_c2c

# Run FTE Strategist agent
run-strategist:
	@echo "Running FTE Strategist agent..."
	openclaw agents run strategist

# Run C2C Strategist agent
run-strategist-c2c:
	@echo "Running C2C Strategist agent..."
	openclaw agents run strategist_c2c

# ============================================
# Daily Run - Full Pipeline
# ============================================

# Run full daily pipeline (FTE)
daily-run-fte:
	@echo "=== Starting FTE Daily Run ==="
	openclaw agents run scout
	openclaw agents run analyst
	openclaw agents run strategist
	@echo "=== FTE Daily Run Complete ==="

# Run full daily pipeline (C2C)
daily-run-c2c:
	@echo "=== Starting C2C Daily Run ==="
	openclaw agents run scout_c2c
	openclaw agents run analyst_c2c
	openclaw agents run strategist_c2c
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