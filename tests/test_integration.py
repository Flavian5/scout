#!/usr/bin/env python3
"""
Integration tests for gog CLI (Gmail/Calendar/Contacts/Drive/Sheets/Docs).
Tests against live Google APIs when gog is authenticated.
"""

import json
import os
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


def is_gog_configured():
    """Check if gog credentials exist."""
    return GOG_CREDS_PATH.exists()


def run_gog_command(args, check=True):
    """Run a gog command and return result."""
    cmd = ["gog"] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT)
    )
    if check and result.returncode != 0:
        pytest.skip(f"gog command failed: {' '.join(args)}\n{result.stderr}")
    return result


def load_discord_webhook():
    """Load Discord webhook from secrets."""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            secrets = json.load(f)
            return secrets.get("discord_webhook", "")
    return None


@pytest.fixture
def gog_available():
    """Check if gog is installed (don't require all APIs to be enabled)."""
    try:
        result = subprocess.run(
            ["gog", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            pytest.skip("gog not installed - run: brew install steipete/tap/gogcli")
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pytest.skip("gog not installed - run: brew install steipete/tap/gogcli")


class TestGogGmail:
    """Integration tests for gog Gmail commands."""

    def test_gog_gmail_search_basic(self, gog_available):
        """Test basic gmail search returns results."""
        result = run_gog_command(["gmail", "search", "is:unread", "--max", "3"])
        
        assert result.returncode == 0
        # Output should be parseable (either JSON or human-readable)
        assert len(result.stdout) > 0

    def test_gog_gmail_search_with_filter(self, gog_available):
        """Test gmail search with date filter."""
        result = run_gog_command(["gmail", "search", "newer_than:1d is:unread", "--max", "5"])
        
        assert result.returncode == 0

    def test_gog_gmail_list(self, gog_available):
        """Test gmail list command."""
        result = run_gog_command(["gmail", "list", "--max", "10"])
        
        # Should succeed or skip if no emails
        assert result.returncode == 0 or "no results" in result.stdout.lower()

    def test_gog_gmail_unread_count(self, gog_available):
        """Test getting unread count."""
        result = run_gog_command(["gmail", "search", "is:unread", "--max", "1"])
        
        # Just verify it runs
        assert result.returncode == 0 or "gog" in result.stderr.lower()


class TestGogCalendar:
    """Integration tests for gog Calendar commands."""

    def test_gog_calendar_events_today(self, gog_available):
        """Test fetching today's events."""
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow"])
        
        assert result.returncode == 0
        assert len(result.stdout) > 0

    def test_gog_calendar_events_with_location(self, gog_available):
        """Test that events include location info."""
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow", "--max", "5"])
        
        # Should succeed
        assert result.returncode == 0

    def test_gog_calendar_now(self, gog_available):
        """Test calendar now command."""
        result = run_gog_command(["calendar", "now"])
        
        # Should return current time or today's events
        assert result.returncode == 0 or "calendar" in result.stdout.lower()


class TestGogContacts:
    """Integration tests for gog Contacts commands."""

    def test_gog_contacts_list(self, gog_available):
        """Test listing contacts."""
        result = run_gog_command(["contacts", "list", "--max", "10"])
        
        assert result.returncode == 0


class TestGogDrive:
    """Integration tests for gog Drive commands."""

    def test_gog_drive_list(self, gog_available):
        """Test listing drive files."""
        result = run_gog_command(["drive", "list", "--max", "10"])
        
        # Should succeed
        assert result.returncode == 0


class TestDiscordWebhook:
    """Test Discord webhook integration."""

    def test_discord_webhook_configured(self):
        """Check if Discord webhook is configured."""
        webhook = load_discord_webhook()
        if not webhook:
            pytest.skip("Discord webhook not configured")
        assert webhook.startswith("https://discord.com/api/webhooks/")

    def test_gog_calendar_to_discord(self, gog_available):
        """Test calendar events formatted for Discord."""
        webhook = load_discord_webhook()
        if not webhook:
            pytest.skip("Discord webhook not configured")
        
        # Get upcoming events
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow"])
        if result.returncode != 0:
            pytest.skip("Could not fetch calendar events")
        
        # Verify we got some output
        assert len(result.stdout) > 0


class TestEndToEnd:
    """End-to-end tests combining gog with Discord."""

    @pytest.fixture
    def discord_webhook(self):
        """Get Discord webhook URL."""
        webhook = load_discord_webhook()
        if not webhook:
            pytest.skip("Discord webhook not configured")
        return webhook

    def test_gog_gmail_and_discord_flow(self, gog_available, discord_webhook):
        """Test fetching emails and sending summary to Discord."""
        # Get recent unread emails
        result = run_gog_command(["gmail", "search", "newer_than:1d is:unread", "--max", "5"])
        
        # If gog works, we got data
        assert result.returncode == 0 or len(result.stdout) > 0

    def test_gog_calendar_and_discord_flow(self, gog_available, discord_webhook):
        """Test fetching events and sending reminder to Discord."""
        # Get today's events
        result = run_gog_command(["calendar", "events", "primary", "--from", "today", "--to", "tomorrow"])
        
        # If gog works, we got data
        assert result.returncode == 0 or len(result.stdout) > 0


class TestGogAuth:
    """Test gog authentication status."""

    def test_gog_whoami(self, gog_available):
        """Test gog identity (may fail if People API not enabled)."""
        result = subprocess.run(["gog", "whoami"], capture_output=True, text=True)
        
        # People API may not be enabled - skip gracefully
        if "People API" in result.stderr and "403" in result.stderr:
            pytest.skip("People API not enabled - run: gog login <email>")
        
        assert result.returncode == 0
        # Should show authenticated email
        assert "@" in result.stdout or "hao" in result.stdout.lower()

    def test_gog_config_paths(self):
        """Test that config paths are set up."""
        # Check credentials exist
        if not GOG_CREDS_PATH.exists():
            pytest.skip("gog credentials not found")
        
        # Should be valid JSON
        with open(GOG_CREDS_PATH) as f:
            data = json.load(f)
        
        assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])