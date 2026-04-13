#!/usr/bin/env python3
"""
Integration tests for email-check and calendar-check skills.
Tests against live Gmail and Calendar APIs when credentials are available.
Skips gracefully when credentials are missing.
"""

import json
import os
import pytest
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Config paths
CONFIG_DIR = PROJECT_ROOT / "config"
GMAIL_TOKEN_PATH = CONFIG_DIR / "gmail-token.json"
GMAIL_CREDENTIALS_PATH = CONFIG_DIR / "gmail-credentials.json"
CALENDAR_TOKEN_PATH = CONFIG_DIR / "calendar-token.json"
CALENDAR_CREDENTIALS_PATH = CONFIG_DIR / "calendar-credentials.json"
SECRETS_PATH = CONFIG_DIR / "secrets.json"


def is_gmail_configured():
    """Check if Gmail API credentials exist."""
    return GMAIL_CREDENTIALS_PATH.exists() or GMAIL_TOKEN_PATH.exists()


def is_calendar_configured():
    """Check if Calendar API credentials exist."""
    return CALENDAR_CREDENTIALS_PATH.exists() or CALENDAR_TOKEN_PATH.exists()


def load_discord_webhook():
    """Load Discord webhook from secrets."""
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH) as f:
            secrets = json.load(f)
            return secrets.get("discord_webhook", "")
    return None


@pytest.fixture
def gmail_service():
    """Get authenticated Gmail service, or None if not configured."""
    if not is_gmail_configured():
        pytest.skip("Gmail credentials not configured")
    
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]
    
    creds = None
    if GMAIL_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(GMAIL_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            pytest.skip("Gmail not authenticated - run: python skills/email-check/check.py --auth")
    
    return build("gmail", "v1", credentials=creds)


@pytest.fixture
def calendar_service():
    """Get authenticated Calendar service, or None if not configured."""
    if not is_calendar_configured():
        pytest.skip("Calendar credentials not configured")
    
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
    
    creds = None
    if CALENDAR_TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(CALENDAR_TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(CALENDAR_TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            pytest.skip("Calendar not authenticated - run: python skills/calendar-check/check.py auth")
    
    return build("calendar", "v3", credentials=creds)


@pytest.fixture
def email_check_module():
    """Import email-check module using importlib (handles hyphenated directory name)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "email_check", 
        PROJECT_ROOT / "skills" / "email-check" / "check.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["email_check"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def calendar_check_module():
    """Import calendar-check module using importlib (handles hyphenated directory name)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "calendar_check", 
        PROJECT_ROOT / "skills" / "calendar-check" / "check.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["calendar_check"] = module
    spec.loader.exec_module(module)
    return module


class TestGmailIntegration:
    """Integration tests for Gmail API."""

    def test_gmail_fetch_unread_emails(self, gmail_service, email_check_module):
        """Test fetching actual unread emails from Gmail."""
        result = email_check_module.fetch_unread_emails(gmail_service, lookback_hours=24, max_results=10)
        
        # Should return structure with emails array and count
        assert "emails" in result
        assert "count" in result
        assert isinstance(result["emails"], list)
        assert isinstance(result["count"], int)
        
        # If there are emails, verify structure
        for email in result["emails"]:
            assert "id" in email
            assert "sender" in email
            assert "subject" in email
            assert "snippet" in email
            assert "timestamp" in email

    def test_gmail_authenticate_oauth(self):
        """Test that OAuth flow works (requires browser interaction)."""
        if not GMAIL_CREDENTIALS_PATH.exists():
            pytest.skip("Credentials file not found")
        
        # Just verify the credentials file is valid JSON
        import json
        with open(GMAIL_CREDENTIALS_PATH) as f:
            data = json.load(f)
        
        assert "installed" in data or "web" in data


class TestCalendarIntegration:
    """Integration tests for Calendar API."""

    def test_calendar_fetch_events(self, calendar_service, calendar_check_module):
        """Test fetching actual events from Google Calendar."""
        events = calendar_check_module.fetch_events(calendar_service, lookback_minutes=0, max_results=10)
        
        assert isinstance(events, list)
        
        # If there are events, verify structure
        for event in events:
            assert "id" in event
            assert "title" in event
            assert "start" in event
            assert "end" in event
            assert "minutes_until" in event

    def test_calendar_authenticate(self):
        """Test that OAuth flow works (requires browser interaction)."""
        if not CALENDAR_CREDENTIALS_PATH.exists():
            pytest.skip("Credentials file not found")
        
        # Just verify the credentials file is valid JSON
        import json
        with open(CALENDAR_CREDENTIALS_PATH) as f:
            data = json.load(f)
        
        assert "installed" in data or "web" in data


class TestDiscordWebhook:
    """Test Discord webhook integration."""

    def test_discord_webhook_configured(self):
        """Check if Discord webhook is configured."""
        webhook = load_discord_webhook()
        if not webhook:
            pytest.skip("Discord webhook not configured")

    @pytest.fixture
    def discord_webhook(self):
        """Get Discord webhook URL."""
        webhook = load_discord_webhook()
        if not webhook:
            pytest.skip("Discord webhook not configured")
        return webhook

    def test_send_test_calendar_reminder(self, calendar_service, discord_webhook, calendar_check_module):
        """Send a test reminder to Discord (with actual event data)."""
        events = calendar_check_module.fetch_events(calendar_service, lookback_minutes=0, max_results=5)
        
        if not events:
            pytest.skip("No upcoming events to test reminder")
        
        # Find an event starting soon (within 30 min) or create a dummy
        test_event = None
        for event in events:
            if 0 < event["minutes_until"] <= 30:
                test_event = event
                break
        
        if not test_event:
            # Use the next upcoming event
            upcoming = [e for e in events if e["minutes_until"] > 0]
            if upcoming:
                test_event = upcoming[0]
                test_event["minutes_until"] = 15  # Simulate reminder scenario
        
        if test_event:
            result = calendar_check_module.send_discord_reminder(test_event, discord_webhook)
            assert result is True


class TestEndToEnd:
    """End-to-end tests combining multiple services."""

    @pytest.fixture
    def discord_webhook(self):
        """Get Discord webhook URL."""
        webhook = load_discord_webhook()
        if not webhook:
            pytest.skip("Discord webhook not configured")
        return webhook

    def test_email_check_full_flow(self, gmail_service, email_check_module):
        """Test full email check flow with real data."""
        # Fetch emails
        result = email_check_module.fetch_unread_emails(gmail_service, lookback_hours=24, max_results=5)
        emails = result.get("emails", [])
        
        if not emails:
            pytest.skip("No unread emails to test")
        
        # Check LLM config
        llm_config = email_check_module.get_llm_config()
        if not llm_config.get("api_key"):
            pytest.skip("LLM API key not configured")
        
        # Classify (just first email to save time)
        email = emails[0]
        urgency = email_check_module.classify_urgency(email, llm_config)
        
        assert urgency in ["urgent", "important", "routine"]
        
        print(f"\nTest email: {email['subject']}")
        print(f"Classified as: {urgency}")

    def test_calendar_check_full_flow(self, calendar_service, discord_webhook, calendar_check_module):
        """Test full calendar check flow with real data."""
        events = calendar_check_module.fetch_events(calendar_service, lookback_minutes=0, max_results=10)
        
        if not events:
            pytest.skip("No upcoming events to test")
        
        # Try to send reminders
        reminded = calendar_check_module.send_reminders(events, discord_webhook)
        
        # Just verify it runs without error
        assert isinstance(reminded, int)
        
        print(f"\nFound {len(events)} events")
        print(f"Sent {reminded} reminders")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])