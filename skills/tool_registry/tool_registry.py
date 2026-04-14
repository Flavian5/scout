#!/usr/bin/env python3
"""
Tool Registry - SEM-82
Core daemon with in-process tool registry for the Discord bot architecture.

Provides:
- ToolRegistry class that maps function names to skill modules
- Sync and async tool execution
- asyncio.wait_for timeout protection
- Structured error handling
"""
import asyncio
import inspect
import importlib
import importlib.util
import os
import sys
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass


# =============================================================================
# Exceptions
# =============================================================================

class ToolRegistryError(Exception):
    """Base exception for tool registry errors"""
    pass


class ToolNotFoundError(ToolRegistryError):
    """Raised when a tool is not found in the registry"""
    pass


class ToolTimeoutError(ToolRegistryError):
    """Raised when a tool execution times out"""
    pass


class ToolExecutionError(ToolRegistryError):
    """Raised when a tool execution fails"""
    pass


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class ToolResult:
    """Structured result from tool execution"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    tool: Optional[str] = None
    duration_ms: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "tool": self.tool,
            "duration_ms": self.duration_ms
        }


# =============================================================================
# Tool Registry
# =============================================================================

class ToolRegistry:
    """
    In-process tool registry for executing skill functions.
    
    Features:
    - Register/unregister tools at runtime
    - Sync and async tool support
    - Timeout protection via asyncio.wait_for
    - Structured error handling
    """
    
    def __init__(self, default_timeout: float = 30.0):
        """
        Initialize the tool registry.
        
        Args:
            default_timeout: Default timeout in seconds for tool execution
        """
        self._tools: Dict[str, Callable] = {}
        self._default_timeout = default_timeout
        self._metadata: Dict[str, Dict] = {}
    
    def register(
        self,
        name: str,
        func: Callable,
        description: Optional[str] = None,
        parameters: Optional[Dict] = None
    ) -> None:
        """
        Register a tool function.
        
        Args:
            name: Tool name (used to call the tool)
            func: Callable to register
            description: Human-readable description
            parameters: JSON schema for tool parameters
        """
        if not callable(func):
            raise TypeError(f"Tool must be callable, got {type(func)}")
        
        self._tools[name] = func
        self._metadata[name] = {
            "description": description or func.__doc__ or "",
            "parameters": parameters or {},
            "is_async": asyncio.iscoroutinefunction(func)
        }
        print(f"  ✓ Registered tool: {name}" + (" (async)" if asyncio.iscoroutinefunction(func) else ""))
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a tool.
        
        Args:
            name: Tool name to unregister
            
        Returns:
            True if tool was unregistered, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            del self._metadata[name]
            print(f"  ✓ Unregistered tool: {name}")
            return True
        return False
    
    def get_tool(self, name: str) -> Callable:
        """
        Get a registered tool function.
        
        Args:
            name: Tool name
            
        Returns:
            The registered callable
            
        Raises:
            ToolNotFoundError: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool not found: {name}")
        return self._tools[name]
    
    def list_tools(self) -> Dict[str, Dict]:
        """
        List all registered tools with their metadata.
        
        Returns:
            Dict mapping tool names to metadata
        """
        return dict(self._metadata)
    
    def execute(
        self,
        name: str,
        timeout: Optional[float] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute a tool synchronously.
        
        Args:
            name: Tool name to execute
            timeout: Timeout in seconds (uses default if not specified)
            **kwargs: Arguments to pass to the tool
            
        Returns:
            ToolResult with execution results
        """
        import time
        start_time = time.time()
        
        if name not in self._tools:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
                tool=name
            )
        
        func = self._tools[name]
        timeout = timeout or self._default_timeout
        
        try:
            # Check if async
            if asyncio.iscoroutinefunction(func):
                # Run async function in event loop
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(
                        asyncio.wait_for(func(**kwargs), timeout=timeout)
                    )
                finally:
                    loop.close()
            else:
                # Run sync function with timeout using thread
                loop = asyncio.new_event_loop()
                try:
                    result = loop.run_until_complete(
                        asyncio.wait_for(
                            asyncio.to_thread(func, **kwargs),
                            timeout=timeout
                        )
                    )
                finally:
                    loop.close()
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                result=result,
                tool=name,
                duration_ms=duration_ms
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Tool timed out after {timeout}s",
                tool=name,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                tool=name,
                duration_ms=duration_ms
            )
    
    async def execute_async(
        self,
        name: str,
        timeout: Optional[float] = None,
        **kwargs
    ) -> ToolResult:
        """
        Execute a tool asynchronously.
        
        Args:
            name: Tool name to execute
            timeout: Timeout in seconds (uses default if not specified)
            **kwargs: Arguments to pass to the tool
            
        Returns:
            ToolResult with execution results
        """
        import time
        start_time = time.time()
        
        if name not in self._tools:
            return ToolResult(
                success=False,
                error=f"Tool not found: {name}",
                tool=name
            )
        
        func = self._tools[name]
        timeout = timeout or self._default_timeout
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(**kwargs), timeout=timeout)
            else:
                result = await asyncio.wait_for(
                    asyncio.to_thread(func, **kwargs),
                    timeout=timeout
                )
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ToolResult(
                success=True,
                result=result,
                tool=name,
                duration_ms=duration_ms
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Tool timed out after {timeout}s",
                tool=name,
                duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                tool=name,
                duration_ms=duration_ms
            )


# =============================================================================
# Skill Loader
# =============================================================================

def load_skills_from_directory(registry: ToolRegistry, skills_dir: str) -> int:
    """
    Load tools from skill directories.
    
    Each skill directory should have a check.py with main() function
    or callable tool functions.
    
    Args:
        registry: ToolRegistry instance to register tools in
        skills_dir: Path to skills directory
        
    Returns:
        Number of tools loaded
    """
    count = 0
    
    if not os.path.isdir(skills_dir):
        print(f"Skills directory not found: {skills_dir}")
        return 0
    
    for entry in os.listdir(skills_dir):
        skill_path = os.path.join(skills_dir, entry)
        
        # Skip hidden files and non-directories
        if entry.startswith('.') or not os.path.isdir(skill_path):
            continue
        
        # Check if skill has a check.py
        check_file = os.path.join(skill_path, "check.py")
        if os.path.isfile(check_file):
            try:
                # Import the skill module
                module_name = f"skills.{entry}.check"
                spec = importlib.util.spec_from_file_location(module_name, check_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    
                    # Register tool if main function exists
                    if hasattr(module, 'main'):
                        registry.register(
                            name=entry.replace('-', '_'),
                            func=module.main,
                            description=f"Skill: {entry}"
                        )
                        count += 1
                        
            except Exception as e:
                print(f"  ✗ Failed to load skill {entry}: {e}")
    
    return count


# =============================================================================
# CLI
# =============================================================================

def cmd_register(args):
    """Register and list tools"""
    registry = ToolRegistry()
    
    # Get project root (tool-registry is 3 levels deep: project/skills/tool-registry)
    script_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_path)))
    skills_dir = os.path.join(project_root, "skills")
    
    print("=== Loading Skills ===")
    count = load_skills_from_directory(registry, skills_dir)
    print(f"\nLoaded {count} tools")
    
    print("\n=== Registered Tools ===")
    for name, meta in registry.list_tools().items():
        print(f"  {name}: {meta['description'][:50]}")
    
    return 0


def cmd_execute(args):
    """Execute a tool"""
    registry = ToolRegistry()
    
    # Simple test tools for demo
    def test_add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b
    
    async def test_async_add(a: int, b: int) -> int:
        """Add two numbers asynchronously"""
        await asyncio.sleep(0.1)
        return a + b
    
    registry.register("test_add", test_add, "Add two numbers")
    registry.register("test_async_add", test_async_add, "Add two numbers async")
    
    tool_name = args.tool
    if tool_name not in registry.list_tools():
        print(f"Tool not found: {tool_name}")
        return 1
    
    # Parse arguments
    kwargs = {}
    if args.args:
        for arg in args.args:
            if "=" in arg:
                key, value = arg.split("=", 1)
                # Try to parse as int/float/bool
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
                kwargs[key] = value
    
    print(f"Executing {tool_name} with args: {kwargs}")
    result = registry.execute(tool_name, **kwargs)
    
    if result.success:
        print(f"✓ Success ({result.duration_ms:.1f}ms)")
        print(f"  Result: {result.result}")
    else:
        print(f"✗ Failed ({result.duration_ms:.1f}ms)")
        print(f"  Error: {result.error}")
    
    return 0 if result.success else 1


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Tool Registry - SEM-82")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Register command
    subparsers.add_parser("register", help="Register tools from skills directory")
    
    # Execute command
    exec_parser = subparsers.add_parser("execute", help="Execute a tool")
    exec_parser.add_argument("tool", help="Tool name to execute")
    exec_parser.add_argument("args", nargs="*", help="Arguments as key=value pairs")
    
    args = parser.parse_args()
    
    if args.command == "register":
        return cmd_register(args)
    elif args.command == "execute":
        return cmd_execute(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    exit(main())