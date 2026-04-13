#!/bin/bash
# Push Scout tickets to Linear via API
# Usage: LINEAR_API_KEY=your_key ./push_tickets.sh

set -e

LINEAR_API_KEY="${LINEAR_API_KEY:-}"
if [ -z "$LINEAR_API_KEY" ]; then
    echo "Error: LINEAR_API_KEY environment variable not set"
    echo "Usage: LINEAR_API_KEY=your_key ./push_tickets.sh"
    exit 1
fi

LINEAR_ENDPOINT="https://api.linear.app/graphql"
PROJECT_ID="8ccf1d0d-dc13-4b61-9aa2-d8278113e83f"

echo "Creating tickets in Linear..."
echo "Project ID: $PROJECT_ID"
echo ""

# Epic 1: LLM Migration
declare -A TICKETS=(
    ["scout-INFRA-001"]="Update openclaw.json model config to minimax m2.7"
    ["scout-INFRA-002"]="Update signal-detector to use minimax.io client"
    ["scout-INFRA-003"]="Verify minimax.io API key works"
    ["scout-INFRA-004"]="Audit skills for OpenRouter references"
    ["scout-INFRA-005"]="Test signal-detector end-to-end with new model"
)

# Rate limit
for id in "${!TICKETS[@]}"; do
    echo "[$id] ${TICKETS[$id]}..."
    curl -s -X POST "$LINEAR_ENDPOINT" \
        -H "Authorization: $LINEAR_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"query\":\"mutation { issueCreate(input: {title: \\\"[$id] ${TICKETS[$id]}\\\", priority: 2, projectId: \\\"$PROJECT_ID\\\"}) { issue { identifier } } }\"}"
    echo ""
    sleep 0.3
done

echo "Done!"