"""NPC model — personality, memory, and stats for non-player characters."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NPCMemory(BaseModel):
    """A single memory entry for an NPC interaction."""

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    summary: str
    raw_exchange: str = ""  # verbatim log; cleared after summarisation


class NPC(BaseModel):
    """A non-player character in the game world."""

    id: str
    name: str
    title: str = ""
    description: str = ""
    personality: str = ""  # free-text personality traits for the agent prompt
    location: str = ""

    # Simple stats (NPCs use the same system, but often only partially)
    max_hp: int = 10
    current_hp: int = 10
    strength: int = 5
    agility: int = 5
    mind: int = 5
    charisma: int = 5

    # Dialogue / behaviour hints
    greeting: str = ""
    topics: list[str] = Field(default_factory=list)
    merchant: bool = False
    shop_items: list[str] = Field(default_factory=list)  # item IDs if merchant

    # Memory
    memory_summary: str = ""  # compressed long-term summary
    recent_memories: list[NPCMemory] = Field(default_factory=list)
    max_recent_memories: int = 10

    # State flags
    is_alive: bool = True
    is_hostile: bool = False
    quest_giver: bool = False

    def add_memory(self, summary: str, raw_exchange: str = "") -> None:
        """Append a new memory entry, trimming old ones if over limit."""
        self.recent_memories.append(
            NPCMemory(summary=summary, raw_exchange=raw_exchange)
        )
        # The memory_manager service handles summarisation when this overflows

    def get_context_block(self) -> str:
        """Build the context string injected into the NPC agent prompt."""
        parts = [
            f"Name: {self.name}",
            f"Title: {self.title}" if self.title else "",
            f"Personality: {self.personality}" if self.personality else "",
            f"Location: {self.location}" if self.location else "",
        ]
        if self.memory_summary:
            parts.append(f"Long-term memory: {self.memory_summary}")
        if self.recent_memories:
            recents = "\n".join(f"- {m.summary}" for m in self.recent_memories[-5:])
            parts.append(f"Recent interactions:\n{recents}")
        return "\n".join(p for p in parts if p)
