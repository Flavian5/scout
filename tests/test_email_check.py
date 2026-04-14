#!/usr/bin/env python3
"""
Unit tests for email-check skill.
Uses mocked Gmail API responses.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

# Import the module under test using importlib to avoid name collision
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
EMAIL_CHECK_PATH = PROJECT_ROOT / "skills" / "email-alerts" / "check.py"

# Mock google imports before loading the module
sys.modules['google'] = MagicMock()
sys.modules['google.auth'] = MagicMock()
sys.modules['google.auth.transport'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()
sys.modules['googleapiclient.errors'] = MagicMock()
sys.modules['google_auth_oauthlib'] = MagicMock()
sys.modules['google_auth_oauthlib.flow'] = MagicMock()

# Now import the module
import importlib.util
spec = importlib.util.spec_from_file_location("email_check", EMAIL_CHECK_PATH)
email_module = importlib.util.module_from_spec(spec)
sys.modules["email_check"] = email_module
spec.loader.exec_module(email_module)

# Import from the module
from email_check import (
    fetch_unread_emails,
    classify_urgency,
    classify_all_emails,
    get_llm_config,
    load_config,
)


class TestFetchUnreadEmails:
    """Tests for fetch_unread_emails function."""

    def test_fetch_unread_emails_success(self):
        """Test successful email fetch with mocked service."""
        # Mock Gmail service
        mock_service = MagicMock()
        
        # Mock message list response
        mock_service.users().messages().list().execute.return_value = {
            "messages": [
                {"id": "msg1"},
                {"id": "msg2"},
            ]
        }
        
        # Mock individual message responses
        def get_msg_side_effect(userId, id):
            mock_msg = MagicMock()
            if id == "msg1":
                mock_msg.execute.return_value = {
                    "id": "msg1",
                    "internalDate": "1713000000000",
                    "snippet": "Test email snippet",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "Subject", "value": "Test Subject"},
                        ]
                    }
                }
            else:
                mock_msg.execute.return_value = {
                    "id": "msg2",
                    "internalDate": "1713003600000",
                    "snippet": "Another snippet",
                    "payload": {
                        "headers": [
                            {"name": "From", "value": "other@example.com"},
                            {"name": "Subject", "value": "Another Subject"},
                        ]
                    }
                }
            return mock_msg
        
        mock_service.users().messages().get.side_effect = get_msg_side_effect
        
        # Call function
        result = fetch_unread_emails(mock_service, lookback_hours=24, max_results=50)
        
        # Assertions
        assert result["count"] == 2
        assert len(result["emails"]) == 2
        
        # Check first email
        email1 = result["emails"][0]
        assert email1["id"] == "msg1"
        assert email1["sender"] == "sender@example.com"
        assert email1["subject"] == "Test Subject"
        assert email1["snippet"] == "Test email snippet"
        
        # Check second email
        email2 = result["emails"][1]
        assert email2["id"] == "msg2"
        assert email2["sender"] == "other@example.com"

    def test_fetch_unread_emails_empty(self):
        """Test fetch when no unread emails."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {"messages": []}
        
        result = fetch_unread_emails(mock_service)
        
        assert result["count"] == 0
        assert result["emails"] == []

    def test_fetch_unread_emails_query_format(self):
        """Test that the query string is formatted correctly."""
        mock_service = MagicMock()
        mock_service.users().messages().list().execute.return_value = {"messages": []}
        
        result = fetch_unread_emails(mock_service, lookback_hours=24, max_results=10)
        
        # Verify the API was called
        mock_service.users().messages().list.assert_called()
        call_args = mock_service.users().messages().list.call_args
        assert "is:unread after:" in call_args[1]["q"]
        assert call_args[1]["maxResults"] == 10
        assert result["count"] == 0
        assert result["emails"] == []


class TestClassifyUrgency:
    """Tests for classify_urgency function."""

    @patch("email_check.call_minimax_llm")
    def test_classify_urgent(self, mock_llm):
        """Test urgent classification."""
        mock_llm.return_value = "urgent"
        
        email = {
            "sender": "boss@company.com",
            "subject": "URGENT: Need help now",
            "snippet": "Please respond immediately"
        }
        llm_config = {"api_key": "test", "endpoint": "test", "model": "test"}
        
        result = classify_urgency(email, llm_config)
        
        assert result == "urgent"
        mock_llm.assert_called_once()

    @patch("email_check.call_minimax_llm")
    def test_classify_important(self, mock_llm):
        """Test important classification."""
        mock_llm.return_value = "important"
        
        email = {
            "sender": "client@example.com",
            "subject": "Project deadline tomorrow",
            "snippet": "Please review"
        }
        llm_config = {"api_key": "test", "endpoint": "test", "model": "test"}
        
        result = classify_urgency(email, llm_config)
        
        assert result == "important"

    @patch("email_check.call_minimax_llm")
    def test_classify_routine(self, mock_llm):
        """Test routine classification."""
        mock_llm.return_value = "routine"
        
        email = {
            "sender": "newsletter@example.com",
            "subject": "Weekly newsletter",
            "snippet": "Check out our latest updates"
        }
        llm_config = {"api_key": "test", "endpoint": "test", "model": "test"}
        
        result = classify_urgency(email, llm_config)
        
        assert result == "routine"

    @patch("email_check.call_minimax_llm")
    def test_classify_routine_fallback(self, mock_llm):
        """Test routine fallback when LLM returns unexpected response."""
        # "urgent" is checked first, so it would match "urgent" in any string containing it
        # Use a string with no keywords
        mock_llm.return_value = "unknown response"
        
        email = {
            "sender": "test@example.com",
            "subject": "Test",
            "snippet": "Test"
        }
        llm_config = {"api_key": "test", "endpoint": "test", "model": "test"}
        
        result = classify_urgency(email, llm_config)
        
        # Should fall back to routine when neither "urgent" nor "important" in response
        assert result == "routine"


class TestClassifyAllEmails:
    """Tests for classify_all_emails function."""

    @patch("email_check.classify_urgency")
    def test_classify_all_emails(self, mock_classify):
        """Test classifying multiple emails."""
        # Mock different urgency levels
        mock_classify.side_effect = ["urgent", "important", "routine", "important"]
        
        emails = [
            {"id": "1", "sender": "a@test.com", "subject": "A", "snippet": "a"},
            {"id": "2", "sender": "b@test.com", "subject": "B", "snippet": "b"},
            {"id": "3", "sender": "c@test.com", "subject": "C", "snippet": "c"},
            {"id": "4", "sender": "d@test.com", "subject": "D", "snippet": "d"},
        ]
        llm_config = {"api_key": "test"}
        
        result = classify_all_emails(emails, llm_config)
        
        assert result["summary"]["urgent"] == 1
        assert result["summary"]["important"] == 2
        assert result["summary"]["routine"] == 1
        assert len(result["emails"]) == 4
        
        # Check each email got urgency assigned
        for email in result["emails"]:
            assert "urgency" in email


class TestConfig:
    """Tests for configuration functions."""

    def test_load_config_not_exists(self, tmp_path, monkeypatch):
        """Test load_config when file doesn't exist."""
        # Override SECRETS_PATH before importing
        secrets_path = tmp_path / "nonexistent.json"
        monkeypatch.setattr("email_check.SECRETS_PATH", secrets_path)
        
        config = load_config()
        assert config == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])