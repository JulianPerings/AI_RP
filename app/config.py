"""Application configuration — loads .env and exposes settings."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CAMPAIGNS_DIR = DATA_DIR / "campaigns"
SAVES_DIR = DATA_DIR / "saves"

# Ensure data directories exist
CAMPAIGNS_DIR.mkdir(parents=True, exist_ok=True)
SAVES_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv(PROJECT_ROOT / ".env")

LLMProvider = Literal["openai", "xai", "gemini"]


class LLMConfig(BaseModel):
    """Configuration for a single LLM provider."""

    api_key: str = ""
    model: str = ""
    base_url: str | None = None


def _get_provider_config(provider: LLMProvider) -> LLMConfig:
    """Build an LLMConfig from environment variables for the given provider."""
    if provider == "openai":
        return LLMConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    elif provider == "xai":
        return LLMConfig(
            api_key=os.getenv("XAI_API_KEY", ""),
            model=os.getenv("XAI_MODEL", "grok-2"),
            base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
        )
    elif provider == "gemini":
        return LLMConfig(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        )
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


DEFAULT_PROVIDER: LLMProvider = os.getenv("DEFAULT_LLM_PROVIDER", "openai")  # type: ignore[assignment]


def get_llm_config(provider: LLMProvider | None = None) -> LLMConfig:
    """Return the LLM config for the requested (or default) provider."""
    return _get_provider_config(provider or DEFAULT_PROVIDER)
