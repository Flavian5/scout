# Tool Registry Skill - SEM-82

Core daemon with in-process tool registry for the Discord bot architecture.

## Overview

This skill provides a `ToolRegistry` class that:
- Maps function names to skill modules
- Supports sync and async tool execution
- Uses `asyncio.wait_for` for timeout protection
- Provides structured error handling

## Usage

```python
from tool_registry import ToolRegistry

registry = ToolRegistry()

# Register a tool
def my_tool(arg1, arg2):
    return {"result": arg1 + arg2}

registry.register("add", my_tool)

# Execute a tool
result = registry.execute("add", arg1=1, arg2=2)
```

## Architecture

```
┌─────────────────────────────────────────┐
│           ToolRegistry                   │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│  │ Skill 1│  │ Skill 2│  │ Skill N││
│  └─────────┘  └─────────┘  └─────────┘│
│                                         │
│  ┌─────────────────────────────────────┐│
│  │     Tool Execution (async)          ││
│  │     - Timeout protection            ││
│  │     - Error handling                ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

## Timeout Behavior

All tool executions are wrapped with `asyncio.wait_for`:
- Default timeout: 30 seconds
- Configurable per-call
- Raises `ToolTimeoutError` on timeout

## Error Handling

Tool execution errors are caught and returned as structured results:

```python
{
    "success": False,
    "error": "Error message",
    "tool": "tool_name"
}
```

## Skill Modules

Tools are loaded from existing skill directories:
- `skills/calendar-check/`
- `skills/email-check/`
- `skills/linear-tickets/`
- `skills/notion/`