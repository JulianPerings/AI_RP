"""Abstract base agent — shared logic for all LLM-powered agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from services.llm_service import LLMService
from services.logger import get_logger

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


class BaseAgent(ABC):
    """Base class that every agent inherits from.

    Subclasses must set ``prompt_file`` to the name of their system prompt
    markdown file inside ``agents/prompts/``.
    """

    prompt_file: str = ""  # e.g. "gamemaster.md"

    def __init__(self, llm: LLMService, **kwargs: Any) -> None:
        self.llm = llm
        self._system_prompt: str | None = None
        self.log = get_logger(f"agent.{self.__class__.__name__}")

    # ------------------------------------------------------------------
    # Prompt loading
    # ------------------------------------------------------------------

    def _load_prompt(self) -> str:
        """Read the system prompt from the markdown file."""
        path = PROMPTS_DIR / self.prompt_file
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        text = path.read_text(encoding="utf-8").strip()
        self.log.debug("Loaded prompt from %s (%d chars)", path.name, len(text))
        return text

    @property
    def system_prompt(self) -> str:
        if self._system_prompt is None:
            self._system_prompt = self._load_prompt()
        return self._system_prompt

    def set_system_prompt(self, prompt: str) -> None:
        """Override the file-based prompt at runtime."""
        self._system_prompt = prompt

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------

    def _chat(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_system: str = "",
        **kwargs: Any,
    ) -> str:
        """Send a message through the LLM with the agent's system prompt."""
        system = self.system_prompt
        if extra_system:
            system = f"{system}\n\n{extra_system}"
        self.log.debug(
            "_chat called | user_message=%s | history_len=%d | extra_system=%d chars",
            user_message[:200], len(history or []), len(extra_system),
        )
        result = self.llm.chat_with_history(
            system_prompt=system,
            history=history or [],
            user_message=user_message,
            **kwargs,
        )
        self.log.debug("_chat response (%d chars): %s", len(result), result[:300])
        return result

    def _chat_json(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_system: str = "",
        **kwargs: Any,
    ) -> str:
        """Like _chat but requests JSON output."""
        return self._chat(
            user_message,
            history=history,
            extra_system=extra_system,
            json_mode=True,
            **kwargs,
        )

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def process(self, input_text: str, **kwargs: Any) -> str:
        """Process an input and return the agent's response."""
        ...
