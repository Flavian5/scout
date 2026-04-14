"""
Tool Registry for Scout Core Daemon

Maps function names to skill modules and handles tool execution.
"""

import asyncio
import importlib
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

# Default timeout for tool execution (seconds)
DEFAULT_TIMEOUT = 30.0


class ToolResult:
    """Result of a tool execution."""

    def __init__(self, success: bool, result: Any = None, error: str = None):
        self.success = success
        self.result = result
        self.error = error

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
        }


class ToolRegistry:
    """
    Registry that maps tool names to callable functions.
    
    Tools can be:
    - Python functions directly registered
    - Skill modules loaded dynamically
    - Async or sync callables
    """

    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._modules: dict[str, Any] = {}

    def register(self, name: str, func: Callable) -> None:
        """Register a tool with a given name."""
        self._tools[name] = func
        logger.info(f"Registered tool: {name}")

    def unregister(self, name: str) -> None:
        """Unregister a tool."""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def load_skill_module(self, skill_path: str) -> None:
        """
        Dynamically load a skill module.
        
        Args:
            skill_path: Dot-separated path to skill module (e.g., 'skills.email_check.check')
        """
        try:
            module = importlib.import_module(skill_path)
            self._modules[skill_path] = module
            logger.info(f"Loaded skill module: {skill_path}")
            
            # Auto-register any 'execute' or 'run' functions
            if hasattr(module, 'execute'):
                self.register(skill_path.split('.')[-1], module.execute)
            elif hasattr(module, 'run'):
                self.register(skill_path.split('.')[-1], module.run)
        except ImportError as e:
            logger.error(f"Failed to load skill module {skill_path}: {e}")
            raise

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """
        Execute a tool by name with given arguments.
        
        Args:
            name: Tool name to execute
            **kwargs: Arguments to pass to the tool
            
        Returns:
            ToolResult with success status, result, or error
        """
        if name not in self._tools:
            return ToolResult(success=False, error=f"Unknown tool: {name}")

        func = self._tools[name]
        
        try:
            # Check if function is async
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(**kwargs), timeout=DEFAULT_TIMEOUT)
            else:
                # Run sync functions in executor to avoid blocking
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: func(**kwargs)),
                    timeout=DEFAULT_TIMEOUT
                )
            return ToolResult(success=True, result=result)
        except asyncio.TimeoutError:
            return ToolResult(success=False, error=f"Tool execution timed out after {DEFAULT_TIMEOUT}s")
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return ToolResult(success=False, error=str(e))

    def execute_sync(self, name: str, **kwargs) -> ToolResult:
        """
        Synchronous version of execute for non-async contexts.
        """
        if name not in self._tools:
            return ToolResult(success=False, error=f"Unknown tool: {name}")

        func = self._tools[name]
        
        try:
            if asyncio.iscoroutinefunction(func):
                # Can't directly call async in sync context
                return ToolResult(success=False, error=f"Tool {name} is async, use execute() instead")
            else:
                result = func(**kwargs)
                return ToolResult(success=True, result=result)
        except Exception as e:
            logger.error(f"Tool execution error for {name}: {e}")
            return ToolResult(success=False, error=str(e))


# Global registry instance
_global_registry: ToolRegistry | None = None


def get_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(name: str, func: Callable) -> None:
    """Register a tool with the global registry."""
    get_registry().register(name, func)


def execute_tool(name: str, **kwargs) -> ToolResult:
    """Execute a tool using the global registry."""
    return get_registry().execute(name, **kwargs)