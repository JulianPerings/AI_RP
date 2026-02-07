"""
Centralized LLM factory for all providers.

Supports: OpenAI, xAI (Grok), Google Gemini, Anthropic Claude, Moonshot Kimi, Z.AI (ZhipuAI)

All providers except Claude use the OpenAI-compatible API via ChatOpenAI.
Claude uses ChatAnthropic from langchain-anthropic.
"""
import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel

from config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
# Each entry maps a provider id to its configuration.
#   - label:              Human-readable name shown in the frontend
#   - key_attr:           Settings attribute holding the API key
#   - model_attr:         Settings attribute holding the model name
#   - base_url:           Fixed base URL (optional, for providers with a known endpoint)
#   - base_url_attr:      Settings attribute for a user-configurable base URL (optional)
#   - supports_reasoning: Whether the provider accepts the reasoning_effort kwarg
#   - backend:            "openai" (ChatOpenAI) or "anthropic" (ChatAnthropic)
# ---------------------------------------------------------------------------

PROVIDER_CONFIG: dict[str, dict] = {
    "openai": {
        "label": "OpenAI",
        "key_attr": "OPENAI_API_KEY",
        "model_attr": "OPENAI_MODEL",
        "supports_reasoning": True,
        "backend": "openai",
    },
    "xai": {
        "label": "xAI (Grok)",
        "key_attr": "XAI_API_KEY",
        "model_attr": "XAI_MODEL",
        "base_url_attr": "XAI_BASE_URL",
        "supports_reasoning": False,
        "backend": "openai",
    },
    "gemini": {
        "label": "Google Gemini",
        "key_attr": "GEMINI_API_KEY",
        "model_attr": "GEMINI_MODEL",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "supports_reasoning": False,
        "backend": "openai",
    },
    "claude": {
        "label": "Anthropic Claude",
        "key_attr": "CLAUDE_API_KEY",
        "model_attr": "CLAUDE_MODEL",
        "supports_reasoning": False,
        "backend": "anthropic",
    },
    "kimi": {
        "label": "Moonshot Kimi",
        "key_attr": "KIMI_API_KEY",
        "model_attr": "KIMI_MODEL",
        "base_url_attr": "KIMI_BASE_URL",
        "supports_reasoning": False,
        "backend": "openai",
    },
    "zai": {
        "label": "Z.AI (ZhipuAI)",
        "key_attr": "ZAI_API_KEY",
        "model_attr": "ZAI_MODEL",
        "base_url_attr": "ZAI_BASE_URL",
        "supports_reasoning": False,
        "backend": "openai",
    },
}

SUPPORTED_PROVIDERS = set(PROVIDER_CONFIG.keys())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_setting(attr: str) -> str:
    """Read a string setting, returning '' if missing."""
    return (getattr(settings, attr, "") or "").strip()


def get_provider_key(provider: str) -> str:
    """Return the API key for *provider*, or '' if not configured."""
    cfg = PROVIDER_CONFIG.get(provider)
    if not cfg:
        return ""
    return _get_setting(cfg["key_attr"])


def get_available_providers() -> list[dict]:
    """Return a list of providers that have an API key configured."""
    available = []
    for pid, cfg in PROVIDER_CONFIG.items():
        key = get_provider_key(pid)
        if key:
            available.append({
                "id": pid,
                "label": cfg["label"],
                "model": _get_setting(cfg["model_attr"]),
            })
    return available


def resolve_provider(provider: Optional[str] = None) -> str:
    """Validate and return a provider id, falling back to the default."""
    provider = (provider or settings.DEFAULT_LLM_PROVIDER or "openai").lower()
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported llm_provider: {provider}. "
            f"Supported: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )
    key = get_provider_key(provider)
    if not key:
        raise ValueError(
            f"No API key configured for provider '{provider}'. "
            f"Set {PROVIDER_CONFIG[provider]['key_attr']} in .env"
        )
    return provider


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def build_llm(
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
) -> BaseChatModel:
    """
    Build a LangChain chat model for the given provider.

    Args:
        provider:    Provider id (openai, xai, gemini, claude, kimi, zai).
                     Defaults to DEFAULT_LLM_PROVIDER from settings.
        temperature: Override temperature. Defaults to settings.LLM_TEMPERATURE.
        max_tokens:  Override max tokens. Defaults to settings.LLM_MAX_TOKENS.

    Returns:
        A BaseChatModel instance (ChatOpenAI or ChatAnthropic).
        Call ``.bind_tools(tools)`` on the result if tool calling is needed.
    """
    provider = resolve_provider(provider)
    cfg = PROVIDER_CONFIG[provider]

    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

    api_key = get_provider_key(provider)
    model_name = _get_setting(cfg["model_attr"])
    if not model_name:
        raise ValueError(
            f"No model configured for provider '{provider}'. "
            f"Set {cfg['model_attr']} in .env"
        )

    if cfg["backend"] == "anthropic":
        return _build_anthropic(api_key, model_name, temp, tokens)

    # --- OpenAI-compatible backend ---
    base_url = cfg.get("base_url")
    if not base_url and "base_url_attr" in cfg:
        base_url = _get_setting(cfg["base_url_attr"]) or None

    llm_kwargs: dict = {
        "model": model_name,
        "api_key": api_key,
        "temperature": temp,
        "max_tokens": tokens,
    }

    if cfg.get("supports_reasoning"):
        llm_kwargs["reasoning_effort"] = settings.LLM_REASONING_EFFORT

    if base_url:
        llm_kwargs["base_url"] = base_url

    logger.info(f"[LLM] Building ChatOpenAI for provider={provider} model={model_name}")
    return ChatOpenAI(**llm_kwargs)


def _build_anthropic(
    api_key: str, model: str, temperature: float, max_tokens: int,
) -> BaseChatModel:
    """Build a ChatAnthropic instance for the Claude provider."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic is required for the Claude provider. "
            "Install it with: pip install langchain-anthropic"
        )

    logger.info(f"[LLM] Building ChatAnthropic model={model}")
    return ChatAnthropic(
        model=model,
        anthropic_api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
    )
