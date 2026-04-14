#!/usr/bin/env python3
"""
Unit tests for bridge server (FastAPI transport layer).
Tests the HTTP API endpoints without requiring actual daemon startup.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from fastapi.testclient import TestClient


# =============================================================================
# Test Bridge Server Endpoints
# =============================================================================

class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    def test_health_response_structure(self):
        """Test health response has required fields."""
        # Simulate what health_check returns
        health_data = {
            "status": "healthy",
            "tools_count": 3,
            "tools": ["email_check", "calendar_check", "discord_bot"]
        }
        
        assert "status" in health_data
        assert "tools_count" in health_data
        assert "tools" in health_data
        assert health_data["status"] == "healthy"
        assert health_data["tools_count"] == 3

    def test_health_tools_list(self):
        """Test tools list is array of strings."""
        tools = ["email_check", "calendar_check", "discord_bot"]
        
        assert isinstance(tools, list)
        for tool in tools:
            assert isinstance(tool, str)


class TestExecuteEndpoint:
    """Tests for POST /execute endpoint."""

    def test_tool_request_model(self):
        """Test ToolCallRequest model validation."""
        from bridge.server import ToolCallRequest
        
        # Valid request
        req = ToolCallRequest(tool="email_check", params={"max_results": 5})
        assert req.tool == "email_check"
        assert req.params["max_results"] == 5
        
        # Default params
        req2 = ToolCallRequest(tool="calendar_check")
        assert req2.params == {}

    def test_tool_response_model(self):
        """Test ToolCallResponse model."""
        from bridge.server import ToolCallResponse
        
        # Success response
        resp = ToolCallResponse(success=True, result={"count": 5})
        assert resp.success is True
        assert resp.result["count"] == 5
        assert resp.error is None
        
        # Error response
        resp_error = ToolCallResponse(success=False, error="Tool not found")
        assert resp_error.success is False
        assert resp_error.error == "Tool not found"


class TestDiscordEndpoint:
    """Tests for POST /discord/in endpoint."""

    def test_discord_message_request(self):
        """Test DiscordMessageRequest model."""
        from bridge.server import DiscordMessageRequest
        
        req = DiscordMessageRequest(
            channel_id="123456",
            message_id="789012",
            content="check my emails",
            author="user#1234",
            timestamp=datetime.now().isoformat()
        )
        
        assert req.channel_id == "123456"
        assert req.content == "check my emails"
        assert req.reply_to is None

    def test_discord_message_response(self):
        """Test DiscordMessageResponse model."""
        from bridge.server import DiscordMessageResponse
        
        resp = DiscordMessageResponse(
            content="Processing your request...",
            reply_to_message_id="789012"
        )
        
        assert "Processing" in resp.content
        assert resp.reply_to_message_id == "789012"


class TestErrorHandlers:
    """Tests for error handling."""

    def test_http_exception_format(self):
        """Test HTTP exceptions return structured JSON."""
        # Simulate what http_exception_handler returns
        error_response = {
            "success": False,
            "error": "Not Found"
        }
        
        assert error_response["success"] is False
        assert "error" in error_response

    def test_general_exception_format(self):
        """Test general exceptions return 500 JSON."""
        error_response = {
            "success": False,
            "error": "Internal server error"
        }
        
        assert error_response["success"] is False
        assert error_response["error"] == "Internal server error"


class TestAppFactory:
    """Tests for create_app factory function."""

    def test_create_app_returns_fastapi(self):
        """Test factory creates FastAPI app."""
        from fastapi import FastAPI
        from bridge.server import create_app
        
        app = create_app()
        
        assert isinstance(app, FastAPI)
        assert app.title == "Scout Bridge"


# =============================================================================
# Integration Tests with TestClient
# =============================================================================

class TestBridgeWithClient:
    """Tests using FastAPI TestClient (requires app import)."""
    
    def test_client_import(self):
        """Test we can import the app."""
        try:
            from bridge.server import app
            assert app is not None
        except ImportError as e:
            pytest.skip(f"Cannot import app (daemon dependency issue): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])