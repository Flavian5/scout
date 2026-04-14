#!/usr/bin/env python3
"""
Tests for Tool Registry (skills/tool-registry/tool_registry.py)

Covers:
- Tool registration/unregistration
- Sync and async tool execution  
- Timeout handling
- Error handling (ToolNotFoundError, ToolTimeoutError, ToolExecutionError)
- load_skills_from_directory function
"""
import pytest
import asyncio
import time
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

import importlib.util
import sys
import os

# Dynamically load the tool-registry module
def load_tool_registry_module():
    """Load tool-registry module dynamically due to hyphenated folder name"""
    check_file = os.path.join(PROJECT_ROOT, "skills", "tool-registry", "tool_registry.py")
    spec = importlib.util.spec_from_file_location("tool_registry_module", check_file)
    module = importlib.util.module_from_spec(spec)
    sys.modules["tool_registry_module"] = module
    spec.loader.exec_module(module)
    return module

tool_registry_module = load_tool_registry_module()

ToolRegistry = tool_registry_module.ToolRegistry
ToolResult = tool_registry_module.ToolResult
ToolNotFoundError = tool_registry_module.ToolNotFoundError
ToolTimeoutError = tool_registry_module.ToolTimeoutError
ToolExecutionError = tool_registry_module.ToolExecutionError
load_skills_from_directory = tool_registry_module.load_skills_from_directory


class TestToolResult:
    """Tests for ToolResult dataclass"""
    
    def test_tool_result_success(self):
        """Test successful result"""
        result = ToolResult(success=True, result={"data": "test"}, tool="test_tool", duration_ms=100.5)
        assert result.success is True
        assert result.result == {"data": "test"}
        assert result.error is None
        assert result.tool == "test_tool"
        assert result.duration_ms == 100.5
    
    def test_tool_result_failure(self):
        """Test failure result"""
        result = ToolResult(success=False, error="Test error", tool="test_tool", duration_ms=50.0)
        assert result.success is False
        assert result.result is None
        assert result.error == "Test error"
    
    def test_tool_result_to_dict(self):
        """Test conversion to dict"""
        result = ToolResult(success=True, result=42, tool="calc", duration_ms=10.0)
        d = result.to_dict()
        assert d["success"] is True
        assert d["result"] == 42
        assert d["tool"] == "calc"
        assert d["duration_ms"] == 10.0
        assert d["error"] is None


class TestToolRegistryRegistration:
    """Tests for tool registration"""
    
    def test_register_sync_tool(self):
        """Test registering a synchronous tool"""
        registry = ToolRegistry()
        def test_func():
            return "hello"
        
        registry.register("test", test_func, "A test function")
        
        assert "test" in registry.list_tools()
        metadata = registry.list_tools()["test"]
        assert metadata["description"] == "A test function"
        assert metadata["is_async"] is False
    
    def test_register_async_tool(self):
        """Test registering an async tool"""
        registry = ToolRegistry()
        async def async_func():
            return "hello async"
        
        registry.register("async_test", async_func, "An async function")
        
        metadata = registry.list_tools()["async_test"]
        assert metadata["is_async"] is True
    
    def test_register_non_callable_raises(self):
        """Test that registering non-callable raises TypeError"""
        registry = ToolRegistry()
        with pytest.raises(TypeError, match="Tool must be callable"):
            registry.register("bad", "not a function")
    
    def test_unregister_existing_tool(self):
        """Test unregistering existing tool"""
        registry = ToolRegistry()
        def test_func():
            pass
        registry.register("test", test_func)
        
        result = registry.unregister("test")
        assert result is True
        assert "test" not in registry.list_tools()
    
    def test_unregister_nonexistent_tool(self):
        """Test unregistering non-existent tool returns False"""
        registry = ToolRegistry()
        result = registry.unregister("nonexistent")
        assert result is False


class TestToolRegistryExecution:
    """Tests for tool execution"""
    
    def test_execute_sync_function(self):
        """Test executing a sync function"""
        registry = ToolRegistry()
        def add(a, b):
            return a + b
        
        registry.register("add", add, "Add two numbers")
        result = registry.execute("add", a=5, b=3)
        
        assert result.success is True
        assert result.result == 8
        assert result.tool == "add"
        assert result.duration_ms >= 0
    
    def test_execute_async_function(self):
        """Test executing an async function"""
        registry = ToolRegistry()
        async def add_async(a, b):
            await asyncio.sleep(0.01)
            return a + b
        
        registry.register("add_async", add_async, "Add two numbers async")
        result = registry.execute("add_async", a=10, b=20)
        
        assert result.success is True
        assert result.result == 30
    
    def test_execute_nonexistent_tool(self):
        """Test executing non-existent tool returns failure"""
        registry = ToolRegistry()
        result = registry.execute("nonexistent")
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_execute_with_timeout(self):
        """Test execution with timeout"""
        registry = ToolRegistry(default_timeout=0.1)
        def slow_func():
            time.sleep(1)  # Will exceed 0.1s timeout
            return "done"
        
        registry.register("slow", slow_func, "Slow function")
        result = registry.execute("slow", timeout=0.1)
        
        assert result.success is False
        assert "timed out" in result.error.lower()
    
    def test_execute_raises_exception(self):
        """Test handling of tool exceptions"""
        registry = ToolRegistry()
        def failing_func():
            raise ValueError("Test error")
        
        registry.register("fail", failing_func, "Failing function")
        result = registry.execute("fail")
        
        assert result.success is False
        assert "ValueError" in result.error
        assert "Test error" in result.error
    
    def test_get_tool(self):
        """Test get_tool method"""
        registry = ToolRegistry()
        def test_func():
            return "test"
        registry.register("test", test_func)
        
        func = registry.get_tool("test")
        assert callable(func)
        assert func() == "test"
    
    def test_get_tool_not_found(self):
        """Test get_tool raises ToolNotFoundError"""
        registry = ToolRegistry()
        with pytest.raises(ToolNotFoundError, match="Tool not found"):
            registry.get_tool("nonexistent")


class TestToolRegistryAsync:
    """Tests for async execution methods using sync execute() which wraps asyncio"""
    
    def test_execute_async_method_sync(self):
        """Test execute() with sync function (wraps async)"""
        registry = ToolRegistry()
        def add(a, b):
            return a + b
        
        registry.register("add", add)
        result = registry.execute("add", a=2, b=3)
        
        assert result.success is True
        assert result.result == 5
    
    def test_execute_async_method_async(self):
        """Test execute() with async function via asyncio.run()"""
        registry = ToolRegistry()
        async def multiply(a, b):
            await asyncio.sleep(0.01)
            return a * b
        
        registry.register("multiply", multiply)
        result = registry.execute("multiply", a=4, b=5)
        
        assert result.success is True
        assert result.result == 20
    
    def test_execute_async_timeout(self):
        """Test execute() with timeout on async function"""
        registry = ToolRegistry(default_timeout=0.05)
        async def slow():
            await asyncio.sleep(10)  # Long sleep
            return "done"
        
        registry.register("slow", slow)
        result = registry.execute("slow", timeout=0.05)
        
        assert result.success is False
        assert "timed out" in result.error.lower()


class TestLoadSkillsFromDirectory:
    """Tests for skill directory loading"""
    
    def test_load_skills_from_directory_missing(self, tmp_path):
        """Test loading from non-existent directory"""
        registry = ToolRegistry()
        count = load_skills_from_directory(registry, str(tmp_path / "nonexistent"))
        assert count == 0
    
    def test_load_skills_from_directory_empty(self, tmp_path):
        """Test loading from empty directory"""
        registry = ToolRegistry()
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        count = load_skills_from_directory(registry, str(empty_dir))
        assert count == 0
    
    def test_load_skills_skips_hidden(self, tmp_path):
        """Test that hidden files/dirs are skipped"""
        registry = ToolRegistry()
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        
        # Create hidden directory
        hidden_dir = skills_dir / ".hidden_skill"
        hidden_dir.mkdir()
        check_file = hidden_dir / "check.py"
        check_file.write_text("def main(): pass\n")
        
        count = load_skills_from_directory(registry, str(skills_dir))
        # Should skip hidden directory
        assert count == 0


class TestToolRegistryEdgeCases:
    """Edge case tests"""
    
    def test_default_timeout(self):
        """Test default timeout is applied"""
        registry = ToolRegistry(default_timeout=60.0)
        assert registry._default_timeout == 60.0
    
    def test_tool_result_default_values(self):
        """Test ToolResult defaults"""
        result = ToolResult(success=True)
        assert result.result is None
        assert result.error is None
        assert result.tool is None
        assert result.duration_ms is None
    
    def test_list_tools_returns_new_dict(self):
        """Test that list_tools returns a new dict (not the same reference)"""
        registry = ToolRegistry()
        def test():
            pass
        registry.register("test", test)
        
        tools = registry.list_tools()
        original_id = id(tools)
        new_tools = registry.list_tools()
        
        # Should be a different dict object
        assert id(new_tools) != original_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])