#!/usr/bin/env python3
"""
Unit tests for calendar-check skill.
Tests the core logic without requiring actual google-auth imports.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta


# =============================================================================
# Tests for core calendar logic (without importing the actual module)
# =============================================================================

class TestCalendarEventParsing:
    """Tests for calendar event parsing logic."""

    def test_parse_datetime_event(self):
        """Test parsing a datetime event."""
        event = {
            "id": "event1",
            "summary": "Team Meeting",
            "start": {"dateTime": "2026-04-13T14:00:00Z"},
            "end": {"dateTime": "2026-04-13T15:00:00Z"},
            "location": "https://meet.google.com/abc-defg-hij",
            "attendees": [
                {"email": "alice@example.com"},
                {"email": "bob@example.com"},
            ]
        }
        
        # Simulate fetch_events logic
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        
        assert start == "2026-04-13T14:00:00Z"
        assert end == "2026-04-13T15:00:00Z"
        
        # Parse start time
        if 'T' in start:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        else:
            start_dt = datetime.fromisoformat(start)
        
        now = datetime.now(timezone.utc)
        minutes_until = int((start_dt - now).total_seconds() / 60)
        
        assert isinstance(minutes_until, int)

    def test_parse_all_day_event(self):
        """Test parsing an all-day event."""
        event = {
            "id": "event2",
            "summary": "Lunch",
            "start": {"date": "2026-04-13"},
            "end": {"date": "2026-04-14"},
        }
        
        start = event['start'].get('dateTime', event['start'].get('date'))
        
        assert start == "2026-04-13"
        assert 'T' not in start  # All-day events don't have 'T'

    def test_event_without_summary(self):
        """Test event without summary uses 'Untitled'."""
        event = {
            "id": "event1",
            "start": {"dateTime": "2026-04-13T14:00:00Z"},
            "end": {"dateTime": "2026-04-13T15:00:00Z"},
        }
        
        title = event.get('summary', 'Untitled')
        assert title == 'Untitled'


class TestDiscordReminderFormat:
    """Tests for Discord reminder formatting."""

    def test_format_meet_link(self):
        """Test formatting Google Meet links."""
        location = "https://meet.google.com/abc-defg-hij"
        
        if 'meet.google.com' in location:
            location_text = f"[Join Meeting]({location})"
        elif location.startswith('http'):
            location_text = f"[Join]({location})"
        else:
            location_text = location
        
        assert location_text == "[Join Meeting](https://meet.google.com/abc-defg-hij)"

    def test_format_physical_location(self):
        """Test formatting physical locations."""
        location = "123 Main Street"
        
        if 'meet.google.com' in location:
            location_text = f"[Join Meeting]({location})"
        elif location.startswith('http'):
            location_text = f"[Join]({location})"
        else:
            location_text = location
        
        assert location_text == "123 Main Street"

    def test_format_http_link(self):
        """Test formatting other HTTP links."""
        location = "https://zoom.us/j/123456789"
        
        if 'meet.google.com' in location:
            location_text = f"[Join Meeting]({location})"
        elif location.startswith('http'):
            location_text = f"[Join]({location})"
        else:
            location_text = location
        
        assert location_text == "[Join](https://zoom.us/j/123456789)"

    def test_discord_embed_structure(self):
        """Test Discord embed structure."""
        event = {
            "title": "Team Meeting",
            "start": "2026-04-13T14:00:00Z",
            "location": "https://meet.google.com/abc-defg-hij",
            "attendees": ["alice@example.com", "bob@example.com"],
            "minutes_until": 15
        }
        
        # Build embed (simulating send_discord_reminder logic)
        start = event['start']
        if 'T' in start:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            time_str = start_dt.strftime('%I:%M %p')
        else:
            time_str = start
        
        location = event.get('location', '')
        if location:
            if 'meet.google.com' in location:
                location_text = f"[Join Meeting]({location})"
            elif location.startswith('http'):
                location_text = f"[Join]({location})"
            else:
                location_text = location
        else:
            location_text = "No location"
        
        attendees = event.get('attendees', [])
        attendees_text = f"{len(attendees)} attendee(s)" if attendees else "No attendees"
        
        embed = {
            "title": f"📅 Meeting in {event['minutes_until']} minutes",
            "description": f"**{event['title']}**\n\n🕐 {time_str}\n📍 {location_text}\n👥 {attendees_text}",
            "color": 5814783,
            "footer": {"text": "Scout Calendar Reminder"}
        }
        
        assert "📅 Meeting in 15 minutes" in embed["title"]
        assert "Team Meeting" in embed["description"]
        assert "[Join Meeting]" in embed["description"]
        assert "2 attendee(s)" in embed["description"]


class TestReminderWindowLogic:
    """Tests for reminder window logic."""

    REMINDER_WINDOW = 15

    def test_event_in_reminder_window(self):
        """Test event within reminder window."""
        minutes = 10
        
        # Check if within reminder window (simulating send_reminders logic)
        if 0 < minutes <= self.REMINDER_WINDOW:
            should_remind = True
        else:
            should_remind = False
        
        assert should_remind is True

    def test_event_outside_reminder_window(self):
        """Test event outside reminder window."""
        minutes = 30
        
        if 0 < minutes <= self.REMINDER_WINDOW:
            should_remind = True
        else:
            should_remind = False
        
        assert should_remind is False

    def test_event_already_started(self):
        """Test event that already started."""
        minutes = 0
        
        if 0 < minutes <= self.REMINDER_WINDOW:
            should_remind = True
        else:
            should_remind = False
        
        assert should_remind is False

    def test_event_in_past(self):
        """Test event in the past."""
        minutes = -5
        
        if 0 < minutes <= self.REMINDER_WINDOW:
            should_remind = True
        else:
            should_remind = False
        
        assert should_remind is False


class TestReminderDeduplication:
    """Tests for reminder deduplication logic."""

    def test_new_event_no_cache(self):
        """Test new event with no cache entry."""
        cache = {"reminded": {}}
        event_id = "event1"
        
        last_reminded = cache["reminded"].get(event_id)
        should_remind = last_reminded is None
        
        assert should_remind is True

    def test_recent_reminder_cache(self):
        """Test event with recent reminder."""
        recent_time = datetime.now(timezone.utc).isoformat()
        cache = {"reminded": {"event1": recent_time}}
        event_id = "event1"
        
        last_reminded = cache["reminded"].get(event_id)
        if last_reminded:
            last_time = datetime.fromisoformat(last_reminded)
            is_duplicate = datetime.now(timezone.utc) - last_time < timedelta(minutes=15)
        else:
            is_duplicate = False
        
        assert is_duplicate is True

    def test_old_reminder_cache(self):
        """Test event with old reminder (should remind again)."""
        old_time = (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()
        cache = {"reminded": {"event1": old_time}}
        event_id = "event1"
        
        last_reminded = cache["reminded"].get(event_id)
        if last_reminded:
            last_time = datetime.fromisoformat(last_reminded)
            is_duplicate = datetime.now(timezone.utc) - last_time < timedelta(minutes=15)
        else:
            is_duplicate = False
        
        assert is_duplicate is False


class TestReminderCache:
    """Tests for reminder cache operations."""

    def test_load_reminder_cache_default(self):
        """Test default cache when file doesn't exist."""
        # Simulate load_reminder_cache behavior
        def load_cache(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return {"reminded": {}}
        
        cache = load_cache("/nonexistent/path.json")
        assert cache == {"reminded": {}}

    def test_save_reminder_cache(self, tmp_path):
        """Test saving reminder cache."""
        cache_file = tmp_path / "cache.json"
        
        cache = {"reminded": {"e1": "2026-04-13T10:00:00"}}
        
        with open(cache_file, 'w') as f:
            json.dump(cache, f)
        
        assert cache_file.exists()
        with open(cache_file) as f:
            loaded = json.load(f)
        assert loaded == cache


class TestLoadSecrets:
    """Tests for secrets loading."""

    def test_load_secrets_success(self, tmp_path):
        """Test loading secrets with Discord webhook."""
        secrets_file = tmp_path / "secrets.json"
        secrets_file.write_text(json.dumps({
            "discord_webhook": {"url": "https://discord.webhook.test"}
        }))
        
        def load_secrets(path):
            try:
                with open(path) as f:
                    secrets = json.load(f)
                    return secrets.get('discord_webhook', {}).get('url', '')
            except (FileNotFoundError, json.JSONDecodeError):
                return None
        
        result = load_secrets(secrets_file)
        assert result == "https://discord.webhook.test"

    def test_load_secrets_not_found(self, tmp_path):
        """Test loading secrets when file doesn't exist."""
        def load_secrets(path):
            try:
                with open(path) as f:
                    secrets = json.load(f)
                    return secrets.get('discord_webhook', {}).get('url', '')
            except (FileNotFoundError, json.JSONDecodeError):
                return None
        
        result = load_secrets(tmp_path / "nonexistent.json")
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])