"""Unified LLM interface — wraps OpenAI, xAI, and Gemini behind one API."""

from __future__ import annotations

from typing import Any

from litellm import completion

from app.config import LLMProvider, get_llm_config
from services.logger import get_logger


class LLMService:
    """Provider-agnostic LLM wrapper using LiteLLM."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.config = get_llm_config(provider)
        self.provider = provider or "openai"
        self.log = get_logger("llm")

    def _model_name(self) -> str:
        """Return the LiteLLM-compatible model string."""
        prefix_map: dict[str, str] = {
            "openai": "",          # LiteLLM uses bare model names for OpenAI
            "xai": "openai/",      # xAI is OpenAI-compatible; route via openai/ prefix
            "gemini": "gemini/",
        }
        prefix = prefix_map.get(self.provider, "")
        return f"{prefix}{self.config.model}"

    def _extra_kwargs(self) -> dict[str, Any]:
        """Build provider-specific kwargs for litellm.completion."""
        kwargs: dict[str, Any] = {"api_key": self.config.api_key}
        if self.config.base_url:
            kwargs["api_base"] = self.config.base_url
        return kwargs

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.8,
        max_tokens: int = 2048,
        json_mode: bool = False,
    ) -> str:
        """Send a chat completion request and return the assistant message."""
        kwargs: dict[str, Any] = {
            "model": self._model_name(),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **self._extra_kwargs(),
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        self.log.debug(
            "LLM REQUEST  provider=%s model=%s tokens=%d temp=%.1f json=%s",
            self.provider, self._model_name(), max_tokens, temperature, json_mode,
        )
        for i, msg in enumerate(messages):
            self.log.debug("  msg[%d] role=%s content=%s", i, msg["role"], msg["content"][:500])

        response = completion(**kwargs)
        result = response.choices[0].message.content or ""

        self.log.debug("LLM RESPONSE (%d chars): %s", len(result), result[:800])
        return result

    def chat_with_history(
        self,
        system_prompt: str,
        history: list[dict[str, str]],
        user_message: str,
        **kwargs: Any,
    ) -> str:
        """Convenience: build messages from system + history + new user msg."""
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        return self.chat(messages, **kwargs)
