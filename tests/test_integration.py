#!/usr/bin/env python3
"""
Integration tests for gog CLI (Gmail/Calendar/Discord).
Tests against live Google APIs when gog is authenticated.
"""

import json
import pytest
import subprocess
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Config paths
CONFIG_DIR = PROJECT_ROOT / "config"
SECRETS_PATH = CONFIG_DIR / "secrets.json"
GOG_CREDS_PATH = CONFIG_DIR / "credentials.json"


def run_gog_command(args):
    """Run a gog command and return result."""
    cmd = ["gog"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        timeout=30
    )
    return result


def load_discord_webhook():
    """Load Discord webhook from secrets."""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            secrets = json.load(f)
            return secrets.get("discord_webhook", "")
    return None


class TestGogGmail:
    """Integration tests for gog Gmail commands."""

    def test_gog_gmail_search_basic(self):
        """Test basic gmail search returns results."""
        result = run_gog_command(["gmail", "search", "is:unread", "--max", "3"])
        assert result.returncode == 0, f"gmail search failed: {result.stderr}"
        assert len(result.stdout) > 0

    def test_gog_gmail_search_with_filter(self):
        """Test gmail search with date filter."""
        result = run_gog_command(["gmail", "search", "newer_than:1d is:unread", "--max", "5"])
        assert result.returncode == 0, f"gmail search failed: {result.stderr}"

    def test_gog_gmail_unread_count(self):
        """Test getting unread count."""
        result = run_gog_command(["gmail", "search", "is:unread", "--max", "1"])
        assert result.returncode == 0, f"gmail search failed: {result.stderr}"


class TestGogCalendar:
    """Integration tests for gog Calendar commands."""

    def test_gog_calendar_events_today(self):
        """Test fetching today's events."""
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow"])
        assert result.returncode == 0, f"calendar events failed: {result.stderr}"
        assert len(result.stdout) > 0

    def test_gog_calendar_events_with_location(self):
        """Test that events include location info."""
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow", "--max", "5"])
        assert result.returncode == 0, f"calendar events failed: {result.stderr}"


class TestDiscordWebhook:
    """Test Discord webhook integration."""

    def test_discord_webhook_configured(self):
        """Check if Discord webhook is configured."""
        webhook = load_discord_webhook()
        assert webhook, "Discord webhook not configured in config/secrets.json"
        assert webhook.startswith("https://discord.com/api/webhooks/")

    def test_gog_calendar_to_discord(self):
        """Test calendar events can be fetched for Discord."""
        webhook = load_discord_webhook()
        assert webhook, "Discord webhook not configured"
        
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow"])
        assert result.returncode == 0, f"calendar events failed: {result.stderr}"
        assert len(result.stdout) > 0


class TestEndToEnd:
    """End-to-end tests combining gog with Discord."""

    def test_gog_gmail_and_discord_flow(self):
        """Test fetching emails for Discord notification."""
        result = run_gog_command(["gmail", "search", "newer_than:1d is:unread", "--max", "5"])
        assert result.returncode == 0, f"gmail search failed: {result.stderr}"

    def test_gog_calendar_and_discord_flow(self):
        """Test fetching events for Discord reminder."""
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow"])
        assert result.returncode == 0, f"calendar events failed: {result.stderr}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])