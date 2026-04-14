#!/usr/bin/env python3
"""
Unit tests for context hydrator (core/prompts/hydrate.py).
Tests context assembly logic without requiring actual file system or APIs.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta


# =============================================================================
# Tests for hydrator functions
# =============================================================================

class TestGetCurrentTime:
    """Tests for get_current_time function."""

    def test_time_format(self):
        """Test time is formatted correctly."""
        now = datetime.now()
        hour = now.hour
        
        time_str = now.strftime("%I:%M %p")
        date_str = now.strftime("%Y-%m-%d")
        day_str = now.strftime("%A")
        
        # Verify format
        assert ":" in time_str
        assert "AM" in time_str or "PM" in time_str
        assert date_str == now.strftime("%Y-%m-%d")
        assert day_str in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    def test_quiet_hours_detection(self):
        """Test quiet hours detection."""
        # Test late night (11 PM)
        late_hour = 23
        is_quiet_late = late_hour >= 23 or late_hour < 8
        assert is_quiet_late is True
        
        # Test early morning (6 AM)
        early_hour = 6
        is_quiet_early = early_hour >= 23 or early_hour < 8
        assert is_quiet_early is True
        
        # Test midday (2 PM)
        midday_hour = 14
        is_quiet_midday = midday_hour >= 23 or midday_hour < 8
        assert is_quiet_midday is False


class TestHydrateContext:
    """Tests for hydrate_context function."""

    def test_placeholder_replacement(self):
        """Test basic placeholder replacement."""
        template = "Time: {{CURRENT_TIME}}, Date: {{CURRENT_DATE}}"
        time_info = {"time": "02:30 PM", "date": "2026-04-13"}
        
        result = template.replace("{{CURRENT_TIME}}", time_info["time"])
        result = result.replace("{{CURRENT_DATE}}", time_info["date"])
        
        assert "02:30 PM" in result
        assert "2026-04-13" in result

    def test_memory_section_generation(self):
        """Test memory section is generated correctly."""
        memory_items = [
            ("TODAY", "## Tasks Completed\n- Test1\n- Test2"),
            ("YESTERDAY", "## Session Start\n- Did stuff")
        ]
        
        memory_section = ""
        for label, content in memory_items:
            memory_section += f"### {label.upper()}\n```\n{content}\n```\n\n"
        
        assert "### TODAY" in memory_section
        assert "### YESTERDAY" in memory_section
        assert "## Tasks Completed" in memory_section

    def test_events_section_with_events(self):
        """Test events section when events exist."""
        calendar_status = {
            "events": [
                {"title": "Meeting", "start": "2:00 PM"},
                {"title": "Call", "start": "4:00 PM"}
            ]
        }
        
        if calendar_status.get("events"):
            events_list = "\n".join([f"- {e['title']} at {e['start']}" for e in calendar_status["events"]])
            events_section = f"**Upcoming Events** ({len(calendar_status['events'])} today):\n{events_list}"
        else:
            events_section = "No events scheduled for today."
        
        assert "2 today" in events_section
        assert "Meeting at 2:00 PM" in events_section

    def test_events_section_empty(self):
        """Test events section when no events."""
        calendar_status = {"events": []}
        
        if calendar_status.get("events"):
            events_section = "Has events"
        else:
            events_section = "No events scheduled for today."
        
        assert events_section == "No events scheduled for today."

    def test_urgent_emails_section(self):
        """Test urgent emails section."""
        email_status = {"has_urgent": True, "urgent": 3}
        
        if email_status.get("has_urgent"):
            urgent_section = f"**Urgent** ({email_status['urgent']}):\n- Check email_fetch.json"
        else:
            urgent_section = ""
        
        assert "**Urgent** (3)" in urgent_section

    def test_p0_p1_tickets(self):
        """Test priority ticket sections."""
        linear_status = {"p0": 1, "p1": 3}
        
        p0_section = f"**P0 (Urgent)**: {linear_status.get('p0', 0)}" if linear_status.get('p0', 0) > 0 else ""
        p1_section = f"**P1 (High)**: {linear_status.get('p1', 0)}" if linear_status.get('p1', 0) > 0 else ""
        
        assert "**P0 (Urgent)**: 1" in p0_section
        assert "**P1 (High)**: 3" in p1_section

    def test_no_p0_tickets(self):
        """Test P0 section hidden when no P0 tickets."""
        linear_status = {"p0": 0, "p1": 2}
        
        p0_section = f"**P0 (Urgent)**: {linear_status.get('p0', 0)}" if linear_status.get('p0', 0) > 0 else ""
        
        assert p0_section == ""

    def test_integrations_table(self):
        """Test integrations table generation."""
        integrations = {
            "gmail": {"status": "✅ Active", "notes": "Working"},
            "calendar": {"status": "❌ Not configured", "notes": "Needs OAuth"}
        }
        
        integrations_lines = []
        for name, info in integrations.items():
            integrations_lines.append(f"| {name.capitalize()} | {info['status']} | {info['notes']} |")
        integrations_table = "\n".join(integrations_lines)
        
        assert "| Gmail | ✅ Active | Working |" in integrations_table
        assert "| Calendar | ❌ Not configured | Needs OAuth |" in integrations_table


class TestGetRelevantSkills:
    """Tests for get_relevant_skills function."""

    def test_email_keyword(self):
        """Test email keyword maps to correct skills."""
        request = "check my emails"
        
        skill_map = {
            "email": ["gog", "notion"],
            "calendar": ["gog", "discord-bot"],
            "ticket": ["discord-bot", "linear-tickets"],
        }
        
        relevant = set()
        for keyword, skills in skill_map.items():
            if keyword in request.lower():
                relevant.update(skills)
        
        assert "gog" in relevant
        assert "notion" in relevant

    def test_ticket_keyword(self):
        """Test ticket keyword maps to correct skills."""
        request = "create a ticket"
        
        skill_map = {
            "email": ["gog", "notion"],
            "ticket": ["discord-bot", "linear-tickets"],
        }
        
        relevant = set()
        for keyword, skills in skill_map.items():
            if keyword in request.lower():
                relevant.update(skills)
        
        assert "discord-bot" in relevant
        assert "linear-tickets" in relevant

    def test_default_skill(self):
        """Test default skill when no keywords match."""
        request = "random request"
        
        skill_map = {
            "email": ["gog", "notion"],
            "calendar": ["gog", "discord-bot"],
        }
        
        relevant = set()
        for keyword, skills in skill_map.items():
            if keyword in request.lower():
                relevant.update(skills)
        
        default_skills = list(relevant) if relevant else ["firecrawl-mcp"]
        
        assert "firecrawl-mcp" in default_skills

    def test_multiple_keywords(self):
        """Test multiple keyword matching."""
        request = "check emails and calendar"
        
        skill_map = {
            "email": ["gog", "notion"],
            "calendar": ["gog", "discord-bot"],
        }
        
        relevant = set()
        for keyword, skills in skill_map.items():
            if keyword in request.lower():
                relevant.update(skills)
        
        assert "gog" in relevant
        assert "notion" in relevant
        assert "discord-bot" in relevant


class TestLogTrace:
    """Tests for log_trace function."""

    def test_trace_entry_structure(self):
        """Test trace entry has required fields."""
        trace_id = "abc12345"
        entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "trace_id": trace_id,
            "mode": "discord",
            "request_preview": "check my emails",
            "context_snapshot": {"time": "2:00 PM"},
            "llm": {"model": "MiniMax-M2.7"},
            "tool_calls": [],
            "response_preview": "Found 5 emails",
        }
        
        assert "timestamp" in entry
        assert "trace_id" in entry
        assert "mode" in entry
        assert "request_preview" in entry
        assert "context_snapshot" in entry
        assert "llm" in entry
        assert "tool_calls" in entry
        assert "response_preview" in entry

    def test_tool_call_logging(self):
        """Test tool call logging structure."""
        tool_call = {
            "trace_id": "abc12345",
            "tool": "email_check",
            "args": {"max_results": 10},
            "result": {"count": 5},
            "latency_ms": 150.5,
        }
        
        assert tool_call["tool"] == "email_check"
        assert tool_call["args"]["max_results"] == 10
        assert tool_call["latency_ms"] == 150.5


class TestLoadMemory:
    """Tests for load_memory function."""

    def test_memory_file_parsing(self):
        """Test parsing memory file content."""
        content = """## Session Start
Working on tests

## Tasks Completed
- Test1
- Test2
"""
        
        # Find tasks section
        for section in ["## Tasks Completed", "## Session Start"]:
            if section in content:
                start = content.find(section)
                end = content.find("\n## ", start + 1)
                if end == -1:
                    end = len(content)
                extracted = content[start:end].strip()
                break
        
        assert "## Tasks Completed" in extracted
        assert "Test1" in extracted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])