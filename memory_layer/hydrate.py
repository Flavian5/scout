"""
Scout Context Hydration

Combines short-term + long-term memory into LLM-ready context.
"""

from memory_layer.store import MemoryStore


def build_system_prompt(user_info: dict | None = None) -> str:
    """Build system prompt with user context."""
    base = """You are Scout, a personal AI assistant. You help with tasks, research, and daily coordination."""
    if user_info:
        name = user_info.get("name", "the user")
        base += f" You are assisting {name}."
    return base


def hydrate_context(
    memory_store: MemoryStore,
    channel_id: str,
    current_message: str,
    user_info: dict | None = None,
    short_term_limit: int = 10,
    long_term_limit: int = 5,
) -> dict:
    """
    Build full LLM context from memory layers.

    Returns:
        dict with keys: system_prompt, messages, memory_summary
    """
    # Short-term: recent conversation
    stm = memory_store.short_term(channel_id)
    stm_context = stm.get_context(limit=short_term_limit)

    # Long-term: semantic search on current message
    ltm = memory_store.long_term
    relevant_facts = ltm.search(current_message, limit=long_term_limit)

    # Build messages array (for OpenAI-compatible format)
    messages = []

    # System prompt
    system_content = build_system_prompt(user_info)
    if relevant_facts:
        facts_text = "\n".join(
            f"- {f['key']}: {f['value']}" for f in relevant_facts
        )
        system_content += f"\n\nRelevant facts from memory:\n{facts_text}"
    messages.append({"role": "system", "content": system_content})

    # Short-term history
    for msg in stm_context:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Current message
    messages.append({"role": "user", "content": current_message})

    # Memory summary for debugging/logging
    memory_summary = {
        "short_term_count": len(stm_context),
        "long_term_hits": len(relevant_facts),
        "channel_id": channel_id,
    }

    return {
        "messages": messages,
        "memory_summary": memory_summary,
    }