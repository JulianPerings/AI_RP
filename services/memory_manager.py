"""Memory manager — handles NPC memory summarisation to keep context small."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.npc import NPC
    from services.llm_service import LLMService

SUMMARISE_PROMPT = (
    "You are a memory summariser for an RPG NPC. "
    "Given the NPC's existing long-term memory summary and a list of recent "
    "interaction summaries, produce an updated long-term summary. "
    "Be concise but preserve important facts, promises, emotional shifts, "
    "and quest-relevant information. "
    "Output ONLY the updated summary, nothing else."
)


class MemoryManager:
    """Compresses NPC memory when recent entries exceed a threshold."""

    def __init__(self, llm: LLMService, threshold: int = 8) -> None:
        self.llm = llm
        self.threshold = threshold

    def should_summarise(self, npc: NPC) -> bool:
        """Check if the NPC's recent memory list needs compression."""
        return len(npc.recent_memories) >= npc.max_recent_memories

    def summarise(self, npc: NPC) -> str:
        """Compress older memories into the long-term summary.

        Keeps the most recent `threshold` entries intact and summarises the
        rest into `npc.memory_summary`.
        Returns the new summary.
        """
        if not self.should_summarise(npc):
            return npc.memory_summary

        # Split: old entries to summarise, recent to keep
        to_summarise = npc.recent_memories[: -self.threshold]
        to_keep = npc.recent_memories[-self.threshold :]

        # Build input for the LLM
        old_summaries = "\n".join(f"- {m.summary}" for m in to_summarise)
        user_msg = (
            f"Existing long-term summary:\n{npc.memory_summary or '(none yet)'}\n\n"
            f"New interactions to incorporate:\n{old_summaries}"
        )

        new_summary = self.llm.chat(
            messages=[
                {"role": "system", "content": SUMMARISE_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.3,
            max_tokens=512,
        )

        npc.memory_summary = new_summary.strip()
        npc.recent_memories = to_keep

        return npc.memory_summary

    def add_interaction(
        self,
        npc: NPC,
        summary: str,
        raw_exchange: str = "",
    ) -> None:
        """Record a new interaction and trigger summarisation if needed."""
        npc.add_memory(summary=summary, raw_exchange=raw_exchange)
        if self.should_summarise(npc):
            self.summarise(npc)
