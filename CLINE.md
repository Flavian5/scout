# Cline Best Practices

## Script Execution

**Critical Rule:** When running scripts, always write to a file first (e.g. `linear-tickets/*.py`), then execute via `python3 linear-tickets/script.py`. Never embed multi-line Python scripts inline in `execute_command` — escaped quotes and special characters cause failures.

### Why
- Inline scripts require escaping of quotes, newlines, and special characters
- Escape sequences often get mangled in shell parsing
- Debugging inline script failures is difficult
- File-based scripts are easier to review, edit, and debug

### How
```bash
# Write script to file first
write_to_file path=linear-tickets/my_script.py content=... 

# Execute via python3
execute_command command=python3 linear-tickets/my_script.py requires_approval=false
```

### Common Patterns
- Python scripts: Use `python3 script.py`
- Shell scripts: Use `./script.sh` with shebang
- Node scripts: Use `node script.js`

## Linear API Notes
- Done state ID: `39e1f571-b346-48db-9814-d18351bbedfd`
- Team ID: `791b6072-2693-4b7d-bb59-873cc116795a`
- GraphQL URL: `https://api.linear.app/graphql`
- API key stored in `.env` as `LINEAR_API_KEY`