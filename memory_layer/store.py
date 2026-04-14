"""
Scout Memory Store

Short-term: rolling window per-channel (last 20 messages)
Long-term: semantic storage with embeddings (simple embedding fallback)
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


class ShortTermMemory:
    """Rolling window memory per channel (last 20 messages)."""

    MAX_MESSAGES = 20

    def __init__(self, channel_id: str):
        self.channel_id = channel_id
        self.messages: list[Message] = []

    def add(self, role: str, content: str, metadata: dict | None = None):
        msg = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages.pop(0)

    def get_context(self, limit: int = 10) -> list[dict]:
        recent = self.messages[-limit:]
        return [
            {"role": m.role, "content": m.content, "timestamp": m.timestamp}
            for m in recent
        ]

    def clear(self):
        self.messages.clear()

    def to_dict(self) -> dict:
        return {
            "channel_id": self.channel_id,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp, "metadata": m.metadata}
                for m in self.messages
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShortTermMemory":
        store = cls(channel_id=data["channel_id"])
        store.messages = [
            Message(**m) for m in data.get("messages", [])
        ]
        return store


class LongTermMemory:
    """Semantic storage with embeddings."""

    def __init__(self, storage_path: Path | None = None):
        self.storage_path = storage_path or Path("data/memory/long_term.jsonl")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._entries: list[dict] = []
        self._load()

    def _load(self):
        if self.storage_path.exists():
            self._entries = []
            with open(self.storage_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._entries.append(json.loads(line))

    def _save(self):
        with open(self.storage_path, "w") as f:
            for entry in self._entries:
                f.write(json.dumps(entry) + "\n")

    def add(self, key: str, value: str, importance: int = 5):
        """Store a fact with a simple hash-based importance signal."""
        entry = {
            "key": key,
            "value": value,
            "importance": importance,  # 1-10
            "timestamp": time.time(),
        }
        self._entries.append(entry)
        self._save()

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """
        Simple keyword match search.
        For production, replace with actual embeddings + cosine similarity.
        """
        query_lower = query.lower()
        results = []
        for entry in reversed(self._entries):
            key_lower = entry["key"].lower()
            value_lower = entry["value"].lower()
            score = 0
            for word in query_lower.split():
                if word in key_lower:
                    score += 2
                if word in value_lower:
                    score += 1
            if score > 0:
                results.append({**entry, "score": score})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_all(self) -> list[dict]:
        return list(self._entries)

    def clear(self):
        self._entries.clear()
        self._save()


class MemoryStore:
    """Facade for both short-term and long-term memory."""

    def __init__(self, storage_dir: Path | None = None):
        self.storage_dir = storage_dir or Path("data/memory")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._short_term: dict[str, ShortTermMemory] = {}
        self._long_term = LongTermMemory(storage_path=self.storage_dir / "long_term.jsonl")

    def short_term(self, channel_id: str) -> ShortTermMemory:
        if channel_id not in self._short_term:
            path = self.storage_dir / f"short_term_{channel_id}.json"
            if path.exists():
                with open(path) as f:
                    data = json.load(f)
                self._short_term[channel_id] = ShortTermMemory.from_dict(data)
            else:
                self._short_term[channel_id] = ShortTermMemory(channel_id)
        return self._short_term[channel_id]

    @property
    def long_term(self) -> LongTermMemory:
        return self._long_term

    def persist_short_term(self, channel_id: str):
        if channel_id in self._short_term:
            path = self.storage_dir / f"short_term_{channel_id}.json"
            with open(path, "w") as f:
                json.dump(self._short_term[channel_id].to_dict(), f, indent=2)

    def persist_all(self):
        for cid in self._short_term:
            self.persist_short_term(cid)