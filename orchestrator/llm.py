"""
Scout LLM Client

Handles LLM calls to minimax.io with function calling support.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    name: str
    arguments: dict = field(default_factory=dict)
    id: str | None = None


@dataclass
class LLMResponse:
    content: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: dict | None = None


class ScoutLLM:
    """LLM client for minimax.io with function calling."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.minimax.io/v1",
        model: str = "MiniMax-M2.7",
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.environ.get("MINIMAX_API_KEY", "")
        self.base_url = base_url
        self.model = model
        self.timeout = timeout

    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """
        Send a chat request to minimax.io.

        Args:
            messages: OpenAI-compatible message format
            tools: function calling tool definitions
            temperature: sampling temperature
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if tools:
            payload["tools"] = tools

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                raw = data.get("choices", [{}])[0].get("message", {})
                content = raw.get("content")

                tool_calls = []
                if raw.get("tool_calls"):
                    for tc in raw["tool_calls"]:
                        tool_calls.append(
                            ToolCall(
                                id=tc.get("id"),
                                name=tc["function"]["name"],
                                arguments=json.loads(tc["function"]["arguments"]),
                            )
                        )

                return LLMResponse(content=content, tool_calls=tool_calls, raw=data)

        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM error: {e}")
            raise