"""NPC agent — handles dialogue and behaviour for a single NPC."""

from __future__ import annotations

from typing import Any

from agents.base_agent import BaseAgent
from models.npc import NPC
from services.llm_service import LLMService


class NPCAgent(BaseAgent):
    """An agent that speaks and acts as a specific NPC."""

    prompt_file = "npc.md"

    def __init__(self, llm: LLMService, npc: NPC, **kwargs: Any) -> None:
        super().__init__(llm, **kwargs)
        self.npc = npc

    def _npc_context(self) -> str:
        """Build the NPC-specific context block."""
        return self.npc.get_context_block()

    def process(self, input_text: str, **kwargs: Any) -> str:
        """Respond to the player as this NPC.

        ``input_text`` is the context/question from the GM or the player's
        direct dialogue.
        """
        context = self._npc_context()

        # Build recent exchange history for the NPC
        history: list[dict[str, str]] = []
        for mem in self.npc.recent_memories[-5:]:
            if mem.raw_exchange:
                history.append({"role": "assistant", "content": mem.raw_exchange})

        return self._chat(
            user_message=input_text,
            history=history,
            extra_system=f"## Your Character Profile\n\n{context}",
        )
