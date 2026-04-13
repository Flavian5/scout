#!/usr/bin/env python3
"""
Context Hydrator - Assembles prompt context for OpenClaw LLM calls.

Loads:
- core/prompts/SYSTEM.md (static)
- core/prompts/CONTEXT.md (template, hydrated with current data)
- core/prompts/SKILLS.md (relevant skills based on request)

Usage:
    python core/prompts/hydrate.py --request "check my emails"
    python core/prompts/hydrate.py --heartbeat
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "core" / "prompts"
CONFIG_DIR = PROJECT_ROOT / "config"
SECRETS_PATH = CONFIG_DIR / "secrets.json"


def load_json(path):
    """Load JSON file."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def get_current_time():
    """Get current time info."""
    now = datetime.now()
    hour = now.hour
    is_quiet = hour >= 23 or hour < 8
    return {
        "time": now.strftime("%I:%M %p"),
        "date": now.strftime("%Y-%m-%d"),
        "day": now.strftime("%A"),
        "is_quiet": "ACTIVE" if not is_quiet else "QUIET",
    }


def load_memory():
    """Load recent memory files."""
    memory_dir = PROJECT_ROOT / "memory"
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now().replace(hour=0, minute=0, second=0)).strftime("%Y-%m-%d")
    
    # Try to find yesterday's file
    try:
        from datetime import timedelta
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    except:
        yesterday_date = yesterday
    
    memory_files = {
        "today": memory_dir / f"{today}.md",
        "yesterday": memory_dir / f"{yesterday_date}.md",
    }
    
    memory_md = PROJECT_ROOT / "memory" / "MEMORY.md"
    recent_items = []
    
    # Load today's memory
    if memory_files["today"].exists():
        with open(memory_files["today"]) as f:
            content = f.read()
            # Extract tasks section (look for ## Tasks Completed or ## Session Start)
            for section in ["## Tasks Completed", "## Session Start"]:
                if section in content:
                    start = content.find(section)
                    end = content.find("\n## ", start + 1)
                    if end == -1:
                        end = len(content)
                    recent_items.append(("today", content[start:end].strip()))
                    break
            if not any(s[0] == "today" for s in recent_items) and content.strip():
                recent_items.append(("today", content[:200].strip()))
    
    # Load yesterday's memory
    if memory_files["yesterday"].exists():
        with open(memory_files["yesterday"]) as f:
            content = f.read()
            for section in ["## Tasks Completed", "## Session Start"]:
                if section in content:
                    start = content.find(section)
                    end = content.find("\n## ", start + 1)
                    if end == -1:
                        end = len(content)
                    recent_items.append(("yesterday", content[start:end].strip()))
                    break
    
    return recent_items


def load_email_status():
    """Load email status from last fetch."""
    email_file = PROJECT_ROOT / "data" / "email_fetch.json"
    if email_file.exists():
        data = load_json(email_file)
        emails = data.get("emails", [])
        summary = data.get("summary", {})
        return {
            "count": len(emails),
            "urgent": summary.get("urgent", 0),
            "important": summary.get("important", 0),
            "routine": summary.get("routine", 0),
            "has_urgent": summary.get("urgent", 0) > 0,
        }
    return {"count": 0, "urgent": 0, "important": 0, "routine": 0, "has_urgent": False}


def load_calendar_status():
    """Load calendar status."""
    # Check if calendar is configured
    calendar_token = CONFIG_DIR / "calendar-token.json"
    if not calendar_token.exists():
        return {"configured": False, "events": []}
    
    # TODO: Load from cache if available
    return {"configured": True, "events": []}


def get_linear_tickets():
    """Get open Linear tickets (P0/P1)."""
    # TODO: Call Linear API or check cached data
    return {"open": 0, "p0": 0, "p1": 0}


def get_integration_status():
    """Get integration status."""
    gmail_token = (CONFIG_DIR / "gmail-token.json").exists()
    calendar_token = (CONFIG_DIR / "calendar-token.json").exists()
    secrets = load_json(SECRETS_PATH)
    
    return {
        "gmail": {
            "status": "✅ Active" if gmail_token else "❌ Not configured",
            "notes": "OAuth working" if gmail_token else "Needs OAuth setup",
        },
        "calendar": {
            "status": "✅ Active" if calendar_token else "❌ Not configured",
            "notes": "OAuth working" if calendar_token else "Needs OAuth setup",
        },
    }


def hydrate_context(template, time_info, memory_items, email_status, calendar_status, linear_status, integrations):
    """Fill in CONTEXT.md template with actual data."""
    
    # Build memory section
    memory_section = ""
    for label, content in memory_items:
        memory_section += f"### {label.upper()} ({label})\n```\n{content}\n```\n\n"
    
    # Build events section
    if calendar_status.get("events"):
        events_list = "\n".join([f"- {e['title']} at {e['start']}" for e in calendar_status["events"]])
        events_section = f"**Upcoming Events** ({len(calendar_status['events'])} today):\n{events_list}"
    else:
        events_section = "No events scheduled for today."
    
    # Build urgent emails section
    if email_status.get("has_urgent"):
        urgent_section = f"**Urgent** ({email_status['urgent']}):\n- Check email_fetch.json for details"
    else:
        urgent_section = ""
    
    # Build P0/P1 tickets section
    p0_section = f"**P0 (Urgent)**: {linear_status.get('p0', 0)}" if linear_status.get('p0', 0) > 0 else ""
    p1_section = f"**P1 (High)**: {linear_status.get('p1', 0)}" if linear_status.get('p1', 0) > 0 else ""
    
    # Build integrations table
    integrations_lines = []
    for name, info in integrations.items():
        integrations_lines.append(f"| {name.capitalize()} | {info['status']} | {info['notes']} |")
    integrations_table = "\n".join(integrations_lines)
    
    # Replace placeholders
    replacements = {
        "{{CURRENT_TIME}}": time_info["time"],
        "{{CURRENT_DATE}}": time_info["date"],
        "{{DAY_OF_WEEK}}": time_info["day"],
        "{{IS_QUIET_HOURS}}": time_info["is_quiet"],
        "{{TODAY_DATE}}": time_info["date"],
        "{{YESTERDAY_DATE}}": "2026-04-12",  # TODO: compute properly
        "{{TODAY_MEMORY}}": memory_section or "No recent memory.",
        "{{YESTERDAY_MEMORY}}": "",
        "{{HAS_EVENTS_TODAY}}": "true" if calendar_status.get("events") else "false",
        "{{EVENT_COUNT}}": str(len(calendar_status.get("events", []))),
        "{{EVENTS_LIST}}": events_section,
        "{{UNREAD_EMAIL_COUNT}}": str(email_status.get("count", 0)),
        "{{HAS_URGENT_EMAILS}}": "true" if email_status.get("has_urgent") else "false",
        "{{URGENT_EMAIL_COUNT}}": str(email_status.get("urgent", 0)),
        "{{URGENT_EMAILS}}": urgent_section,
        "{{OPEN_TICKET_COUNT}}": str(linear_status.get("open", 0)),
        "{{HAS_P0_TICKETS}}": "true" if linear_status.get("p0", 0) > 0 else "false",
        "{{P0_TICKETS}}": p0_section,
        "{{HAS_P1_TICKETS}}": "true" if linear_status.get("p1", 0) > 0 else "false",
        "{{P1_TICKETS}}": p1_section,
        "{{GMAIL_STATUS}}": integrations.get("gmail", {}).get("status", "❌ Unknown"),
        "{{GMAIL_NOTES}}": integrations.get("gmail", {}).get("notes", ""),
        "{{CALENDAR_STATUS}}": integrations.get("calendar", {}).get("status", "❌ Unknown"),
        "{{CALENDAR_NOTES}}": integrations.get("calendar", {}).get("notes", ""),
        "{{RECENT_ACTIVITY}}": "See memory files for details.",
        "{{HYDRATION_TIMESTAMP}}": datetime.now().isoformat(),
    }
    
    result = template
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    
    return result


def get_relevant_skills(request):
    """Determine which skills are relevant for this request."""
    request_lower = request.lower() if request else ""
    
    skill_map = {
        "email": ["email-check", "notion"],
        "calendar": ["calendar-check", "discord-bot"],
        "ticket": ["discord-bot", "linear-tickets"],
        "notion": ["notion"],
        "search": ["ddg-web-search", "openclaw-tavily-search"],
        "job": ["signal-detector", "ddg-web-search"],
        "research": ["ddg-web-search", "openclaw-tavily-search", "notion"],
    }
    
    relevant = set()
    for keyword, skills in skill_map.items():
        if keyword in request_lower:
            relevant.update(skills)
    
    return list(relevant) if relevant else ["ddg-web-search"]  # default


def main():
    parser = argparse.ArgumentParser(description="Context Hydrator for OpenClaw")
    parser.add_argument("--request", type=str, help="User request to determine relevant skills")
    parser.add_argument("--heartbeat", action="store_true", help="Running in heartbeat mode")
    parser.add_argument("--output", type=str, help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    # Load templates
    system_md = (PROMPTS_DIR / "SYSTEM.md").read_text()
    context_template = (PROMPTS_DIR / "CONTEXT.md").read_text()
    skills_md = (PROMPTS_DIR / "SKILLS.md").read_text()
    
    # Gather context data
    time_info = get_current_time()
    memory_items = load_memory()
    email_status = load_email_status()
    calendar_status = load_calendar_status()
    linear_status = get_linear_tickets()
    integrations = get_integration_status()
    
    # Hydrate context
    hydrated_context = hydrate_context(
        context_template, time_info, memory_items,
        email_status, calendar_status, linear_status, integrations
    )
    
    # Get relevant skills
    relevant_skills = get_relevant_skills(args.request) if args.request else []
    skills_section = f"\n\n## Relevant Skills\n\n{', '.join(relevant_skills)}\n" if relevant_skills else ""
    
    # Assemble full prompt
    full_prompt = f"""{system_md}

---

{hydrated_context}

---

{skills_md}

{skills_section}
---
_Assembled: {datetime.now().isoformat()}_
"""
    
    if args.output:
        Path(args.output).write_text(full_prompt)
        print(f"Prompt written to {args.output}")
    else:
        print(full_prompt)


if __name__ == "__main__":
    main()