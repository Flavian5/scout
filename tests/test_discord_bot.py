#!/usr/bin/env python3
"""
Tests for Discord Bot Skill (skills/discord-bot/check.py)

Covers:
- Configuration loading
- API key retrieval
- LLM config construction
- Request parsing to ticket details
- Ticket creation (with mocked Linear API)
- Notion linking (with mocked Notion API)
- Command line parsing
"""
import pytest
import json
import os
import sys
import importlib.util
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Dynamically load the discord-bot module
def load_discord_bot_module():
    """Load discord-bot module dynamically due to hyphenated folder name"""
    check_file = os.path.join(PROJECT_ROOT, "skills", "discord-bot", "check.py")
    spec = importlib.util.spec_from_file_location("discord_bot_check", check_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["discord_bot_check"] = module
    spec.loader.exec_module(module)
    return module

discord_bot = load_discord_bot_module()

load_config = discord_bot.load_config
load_api_key = discord_bot.load_api_key
get_headers = discord_bot.get_headers
get_llm_config = discord_bot.get_llm_config
parse_discord_request = discord_bot.parse_discord_request
create_linear_ticket = discord_bot.create_linear_ticket
link_notion_to_ticket = discord_bot.link_notion_to_ticket
create_notion_deliverable = discord_bot.create_notion_deliverable
send_discord_confirmation = discord_bot.send_discord_confirmation


class TestConfiguration:
    """Tests for configuration loading"""
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_load_config_success(self, mock_json, mock_open):
        """Test loading valid config file"""
        mock_json.return_value = {"discord": {"channel_id": "123"}, "llm_api": {"api_key": "test"}}
        
        result = load_config()
        
        assert result["discord"]["channel_id"] == "123"
        assert result["llm_api"]["api_key"] == "test"
    
    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_load_config_file_not_found(self, mock_open):
        """Test loading config when file doesn't exist"""
        result = load_config()
        assert result == {}
    
    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_load_api_key_from_env(self, mock_open):
        """Test loading API key from environment"""
        with patch.dict(os.environ, {"LINEAR_API_KEY": "env_test_key"}):
            result = load_api_key()
            assert result == "env_test_key"
    
    @patch("builtins.open", side_effect=FileNotFoundError())
    @patch.dict(os.environ, {}, clear=True)
    def test_load_api_key_missing(self, mock_open):
        """Test loading API key when none exists"""
        result = load_api_key()
        assert result is None


class TestLLMConfig:
    """Tests for LLM configuration"""
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    @patch.dict(os.environ, {"MINIMAX_API_KEY": "minimax_key"})
    def test_get_llm_config_defaults(self, mock_json, mock_open):
        """Test LLM config with defaults"""
        mock_json.return_value = {}
        
        config = get_llm_config()
        
        assert config["api_key"] == "minimax_key"
        assert config["endpoint"] == "https://api.minimax.io/v1/text/chatcompletion_v2"
        assert config["model"] == "MiniMax-M2.7"
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_get_llm_config_from_config(self, mock_json, mock_open):
        """Test LLM config from secrets file"""
        mock_json.return_value = {
            "llm_api": {
                "api_key": "config_key",
                "endpoint": "https://custom.endpoint/v1",
                "model": "Custom-Model"
            }
        }
        
        config = get_llm_config()
        
        assert config["api_key"] == "config_key"
        assert config["endpoint"] == "https://custom.endpoint/v1"
        assert config["model"] == "Custom-Model"


class TestDiscordRequestParsing:
    """Tests for Discord request parsing"""
    
    @patch("discord_bot_check.call_llm")
    def test_parse_discord_request_success(self, mock_call_llm):
        """Test successful parsing of Discord request"""
        mock_call_llm.return_value = '{"title": "Test Ticket", "description": "Test desc", "priority": 1, "labels": ["test"]}'
        
        llm_config = {"api_key": "test", "endpoint": "http://test", "model": "test"}
        result = parse_discord_request("create a test ticket", llm_config)
        
        assert result["title"] == "Test Ticket"
        assert result["priority"] == 1
        assert "test" in result["labels"]
    
    @patch("discord_bot_check.call_llm")
    def test_parse_discord_request_fallback(self, mock_call_llm):
        """Test fallback when JSON parsing fails"""
        mock_call_llm.return_value = "This is not JSON"
        
        llm_config = {"api_key": "test", "endpoint": "http://test", "model": "test"}
        result = parse_discord_request("create a ticket", llm_config)
        
        # Should fallback to generated values
        assert result["title"] == "create a ticket"[:60]
        assert result["description"].startswith("Request from Discord")
        assert result["priority"] == 2


class TestLinearTicketCreation:
    """Tests for Linear ticket creation"""
    
    @patch("discord_bot_check.run_query")
    def test_create_linear_ticket_success(self, mock_query):
        """Test successful ticket creation"""
        mock_query.return_value = {
            "issueCreate": {
                "success": True,
                "issue": {
                    "id": "test-id",
                    "identifier": "SEM-123",
                    "title": "Test",
                    "url": "https://linear.app/test"
                }
            }
        }
        
        result = create_linear_ticket("Test Title", "Test Description", priority=1)
        
        assert result["success"] is True
        assert result["identifier"] == "SEM-123"
        assert result["id"] == "test-id"
        assert "linear.app" in result["url"]
    
    @patch("discord_bot_check.run_query")
    def test_create_linear_ticket_failure(self, mock_query):
        """Test failed ticket creation"""
        mock_query.return_value = {"issueCreate": {"success": False}}
        
        result = create_linear_ticket("Test", "Desc")
        assert result["success"] is False
    
    def test_create_linear_ticket_no_headers(self):
        """Test ticket creation when headers unavailable"""
        # Mock run_query to return None (simulating get_headers returning None internally)
        with patch("discord_bot_check.run_query", return_value=None):
            result = create_linear_ticket("Test", "Desc")
            assert result["success"] is False


class TestNotionLinking:
    """Tests for Notion linking functionality"""
    
    @patch("discord_bot_check.run_query")
    def test_link_notion_to_ticket_success(self, mock_query):
        """Test successful Notion linking"""
        mock_query.side_effect = [
            # First call: Get issue
            {"issue": {"identifier": "SEM-123", "title": "Test", "description": "Original"}},
            # Second call: Update issue
            {"issueUpdate": {"success": True}}
        ]
        
        result = link_notion_to_ticket("test-id", "https://notion.so/page", "Test Page")
        
        assert result is True
    
    @patch("discord_bot_check.run_query")
    def test_link_notion_to_ticket_failure(self, mock_query):
        """Test failed Notion linking"""
        mock_query.return_value = {"issue": {"description": "Test"}}
        mock_query.side_effect = [
            {"issue": {"identifier": "SEM-123", "title": "Test", "description": "Original"}},
            {"issueUpdate": {"success": False}}
        ]
        
        result = link_notion_to_ticket("test-id", "https://notion.so/page", "Test Page")
        
        assert result is False
    
    @patch("discord_bot_check.run_query")
    def test_link_notion_to_ticket_missing_issue(self, mock_query):
        """Test linking when issue not found"""
        mock_query.return_value = {}
        
        result = link_notion_to_ticket("nonexistent", "https://notion.so/page", "Test")
        
        assert result is False


class TestNotionDeliverable:
    """Tests for Notion deliverable creation"""
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_create_notion_deliverable_synthetic(self, mock_json, mock_open):
        """Test deliverable creation when Notion not configured"""
        mock_json.return_value = {}
        
        result = create_notion_deliverable(
            database_id="test-db",
            title="Test Deliverable",
            ticket_id="test-ticket",
            ticket_identifier="SEM-123"
        )
        
        assert result["success"] is True
        assert result["synthetic"] is True
        assert "notion.so" in result["url"]
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_create_notion_deliverable_success(self, mock_json, mock_open):
        """Test successful deliverable creation"""
        mock_json.return_value = {"notion": {"token": "test-token"}}
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                "id": "notion-page-id",
                "url": "https://notion.so/test"
            }
            
            result = create_notion_deliverable(
                database_id="test-db",
                title="Test Deliverable",
                ticket_id="test-ticket",
                ticket_identifier="SEM-123"
            )
            
            assert result["success"] is True
            assert result["id"] == "notion-page-id"
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_create_notion_deliverable_api_error(self, mock_json, mock_open):
        """Test deliverable creation API error"""
        mock_json.return_value = {"notion": {"token": "test-token"}}
        
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.text = "Bad Request"
            
            result = create_notion_deliverable(
                database_id="test-db",
                title="Test",
                ticket_id="test-ticket",
                ticket_identifier="SEM-123"
            )
            
            assert result["success"] is False


class TestDiscordConfirmation:
    """Tests for Discord confirmation"""
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    @patch("requests.post")
    def test_send_discord_confirmation_success(self, mock_post, mock_json, mock_open):
        """Test successful Discord confirmation"""
        mock_json.return_value = {"discord_webhook": "https://discord.webhook"}
        mock_post.return_value.status_code = 200
        
        ticket = {"identifier": "SEM-123", "url": "https://linear.app/test", "title": "Test"}
        result = send_discord_confirmation(ticket, "channel123")
        
        assert result is True
    
    @patch("builtins.open", create=True)
    @patch("json.load")
    def test_send_discord_confirmation_no_webhook(self, mock_json, mock_open):
        """Test confirmation when webhook not configured"""
        mock_json.return_value = {}
        
        ticket = {"identifier": "SEM-123", "url": "https://linear.app/test"}
        result = send_discord_confirmation(ticket, "channel123")
        
        # Should indicate MCP usage
        assert result is True


class TestGetHeaders:
    """Tests for HTTP headers"""
    
    @patch("discord_bot_check.load_api_key")
    def test_get_headers_success(self, mock_load_api_key):
        """Test getting headers with API key"""
        mock_load_api_key.return_value = "test_key_123"
        
        headers = get_headers()
        
        assert headers["Authorization"] == "test_key_123"
        assert headers["Content-Type"] == "application/json"
    
    @patch("discord_bot_check.load_api_key")
    def test_get_headers_no_api_key(self, mock_load_api_key):
        """Test getting headers without API key"""
        mock_load_api_key.return_value = None
        
        headers = get_headers()
        
        assert headers is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])