"""
Scout Memory Layer

Provides short-term and long-term memory for conversation context.
"""

from memory_layer.hydrate import build_system_prompt, hydrate_context
from memory_layer.store import LongTermMemory, MemoryStore, Message, ShortTermMemory

__all__ = [
    "MemoryStore",
    "ShortTermMemory",
    "LongTermMemory",
    "Message",
    "hydrate_context",
    "build_system_prompt",
]

__version__ = "0.1.0"