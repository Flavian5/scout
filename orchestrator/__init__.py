"""
Scout LLM Orchestrator

Action loop: receive message → hydrate context → send to LLM → execute tool or respond
"""

from orchestrator.action_loop import ActionLoop, ActionResult, create_action_loop
from orchestrator.llm import LLMResponse, ScoutLLM, ToolCall

__all__ = [
    "ActionLoop",
    "ActionResult",
    "ScoutLLM",
    "ToolCall",
    "LLMResponse",
    "create_action_loop",
]

__version__ = "0.1.0"
