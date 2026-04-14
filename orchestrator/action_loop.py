"""
Scout Action Loop

Core orchestrator: REASON → ACT → OBSERVE
Receives message → Hydrates context → Calls LLM → Routes tool calls or text response
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from daemon.registry import ToolRegistry, get_registry
from memory_layer import MemoryStore, hydrate_context
from orchestrator.llm import LLMResponse, ScoutLLM, ToolCall

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    response: str
    tool_results: list[dict] = field(default_factory=list)
    memory_summary: dict = field(default_factory=dict)


class ActionLoop:
    """
    Main orchestrator implementing REASON → ACT → OBSERVE.

    Receives a message, hydrates context from memory, calls the LLM,
    executes any tool calls, and returns the response.
    """

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        tool_registry: ToolRegistry | None = None,
        llm: ScoutLLM | None = None,
        system_prompt: str | None = None,
    ):
        self.memory_store = memory_store or MemoryStore()
        self.tool_registry = tool_registry or get_registry()
        self.llm = llm or ScoutLLM()
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return """You are Scout, a personal AI assistant.
You help with tasks, research, and daily coordination.
Be concise, helpful, and genuine.
When responding on Discord: no markdown tables, use bullet lists for structured info."""

    def get_tool_definitions(self) -> list[dict]:
        """Convert registered tools to OpenAI function-calling format."""
        tools = []
        for name in self.tool_registry.list_tools():
            # Generate minimal tool definition with just the name
            # TODO: Enhance by extracting docstrings/parameters from skill modules
            tool_def = {
                "type": "function",
                "function": {
                    "name": name,
                    "description": f"Tool: {name}",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            }
            tools.append(tool_def)
        return tools

    async def execute_tool_call(self, tool_call: ToolCall) -> dict:
        """Execute a single tool call via the daemon registry."""
        try:
            result = await self.tool_registry.execute(
                tool_call.name,
                tool_call.arguments,
            )
            return {
                "tool_call_id": tool_call.id,
                "tool_name": tool_call.name,
                "result": result,
                "success": True,
            }
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_call.name} - {e}")
            return {
                "tool_call_id": tool_call.id,
                "tool_name": tool_call.name,
                "error": str(e),
                "success": False,
            }

    async def execute_tool_calls(
        self, tool_calls: list[ToolCall]
    ) -> list[dict]:
        """Execute multiple tool calls concurrently."""
        tasks = [self.execute_tool_call(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, dict) else {"error": str(r), "success": False} for r in results]

    def build_follow_up_message(
        self, original_messages: list[dict], tool_results: list[dict]
    ) -> list[dict]:
        """Build follow-up message array with tool results injected."""
        messages = list(original_messages)

        # Add assistant message with tool calls (if any)
        last_msg = messages[-1]
        if last_msg.get("role") == "assistant" and "tool_calls" in last_msg:
            messages.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tr["tool_call_id"],
                            "function": {
                                "name": tr["tool_name"],
                                "arguments": "{}",
                            },
                            "type": "function",
                        }
                        for tr in tool_results
                        if tr.get("success")
                    ],
                }
            )

        # Add tool result messages
        for tr in tool_results:
            if tr.get("success"):
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr["tool_call_id"],
                        "content": str(tr.get("result", "")),
                    }
                )
            else:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.get("tool_call_id", ""),
                        "content": f"Error: {tr.get('error', 'Unknown error')}",
                    }
                )

        return messages

    async def run(
        self,
        channel_id: str,
        user_message: str,
        user_info: dict | None = None,
        tools: list[dict] | None = None,
        max_tool_rounds: int = 3,
    ) -> ActionResult:
        """
        Execute the full action loop.

        Args:
            channel_id: Discord channel ID
            user_message: The user's message
            user_info: User context for system prompt
            tools: Optional tool definitions (defaults to registered tools)
            max_tool_rounds: Max tool-call iterations (prevents infinite loops)

        Returns:
            ActionResult with response text, tool results, and memory summary
        """
        # Hydrate context from memory layers
        context = hydrate_context(
            self.memory_store,
            channel_id,
            user_message,
            user_info=user_info,
        )

        messages = context["messages"]
        memory_summary = context["memory_summary"]

        # Use registered tools if none provided
        tool_defs = tools or self.get_tool_definitions()

        # Track tool execution rounds
        tool_rounds = 0
        all_tool_results: list[dict] = []

        while tool_rounds < max_tool_rounds:
            # Call LLM
            llm_response = self.llm.chat(messages=messages, tools=tool_defs if tool_defs else None)

            # If no tool calls, return text response
            if not llm_response.tool_calls:
                text_response = llm_response.content or "No response generated."
                return ActionResult(
                    response=text_response,
                    tool_results=all_tool_results,
                    memory_summary=memory_summary,
                )

            # Execute tool calls
            tool_results = await self.execute_tool_calls(llm_response.tool_calls)
            all_tool_results.extend(tool_results)

            # Build follow-up messages with results
            messages = self.build_follow_up_message(messages, tool_results)

            tool_rounds += 1

        # Max rounds reached
        return ActionResult(
            response="I tried several times but need more context to complete that request.",
            tool_results=all_tool_results,
            memory_summary=memory_summary,
        )


# Convenience function for sync usage
def create_action_loop() -> ActionLoop:
    """Factory function to create a configured ActionLoop."""
    return ActionLoop()