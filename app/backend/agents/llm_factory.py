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
#   - label:           Human-readable name shown in the frontend
#   - key_attr:        Settings attribute holding the API key
#   - model_attr:      Settings attribute holding the *default* model name
#   - base_url:        Fixed base URL (optional)
#   - base_url_attr:   Settings attribute for a user-configurable base URL
#   - thinking_method: How to enable thinking for this provider:
#                      "reasoning_effort" | "extended_thinking" | None
#   - backend:         "openai" (ChatOpenAI) or "anthropic" (ChatAnthropic)
# ---------------------------------------------------------------------------

PROVIDER_CONFIG: dict[str, dict] = {
    "openai": {
        "label": "OpenAI",
        "key_attr": "OPENAI_API_KEY",
        "model_attr": "OPENAI_MODEL",
        "thinking_method": "reasoning_effort",
        "backend": "openai",
    },
    "xai": {
        "label": "xAI (Grok)",
        "key_attr": "XAI_API_KEY",
        "model_attr": "XAI_MODEL",
        "base_url_attr": "XAI_BASE_URL",
        "thinking_method": None,
        "backend": "openai",
    },
    "gemini": {
        "label": "Google Gemini",
        "key_attr": "GEMINI_API_KEY",
        "model_attr": "GEMINI_MODEL",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "thinking_method": "reasoning_effort",
        "backend": "openai",
    },
    "claude": {
        "label": "Anthropic Claude",
        "key_attr": "CLAUDE_API_KEY",
        "model_attr": "CLAUDE_MODEL",
        "thinking_method": "extended_thinking",
        "backend": "anthropic",
    },
    "kimi": {
        "label": "Moonshot Kimi",
        "key_attr": "KIMI_API_KEY",
        "model_attr": "KIMI_MODEL",
        "base_url_attr": "KIMI_BASE_URL",
        "thinking_method": None,
        "backend": "openai",
    },
    "zai": {
        "label": "Z.AI (ZhipuAI)",
        "key_attr": "ZAI_API_KEY",
        "model_attr": "ZAI_MODEL",
        "base_url_attr": "ZAI_BASE_URL",
        "thinking_method": None,
        "backend": "openai",
    },
}

SUPPORTED_PROVIDERS = set(PROVIDER_CONFIG.keys())


# ---------------------------------------------------------------------------
# Model registry  — defines the selectable models per provider.
# Each model entry:
#   - id:       API model identifier
#   - label:    Human-friendly display name
#   - thinking: Whether this model supports a thinking / reasoning toggle
# ---------------------------------------------------------------------------

MODEL_REGISTRY: dict[str, list[dict]] = {
    "openai": [
        {"id": "gpt-5-mini",                    "label": "GPT-5 Mini",              "thinking": True},
        {"id": "gpt-5-nano",                    "label": "GPT-5 Nano",              "thinking": True},
        {"id": "o4-mini",                       "label": "o4 Mini",                 "thinking": True},
        {"id": "gpt-4o-mini-realtime-preview",  "label": "GPT-4o Mini Realtime",    "thinking": False},
        {"id": "gpt-realtime-mini",             "label": "GPT Realtime Mini",       "thinking": False},
    ],
    "xai": [
        {"id": "grok-4-1-fast-reasoning",       "label": "Grok 4.1 Fast",           "thinking": False},
        {"id": "grok-3-mini",                   "label": "Grok 3 Mini",             "thinking": False},
    ],
    "gemini": [
        {"id": "gemini-2.5-flash-preview-09-2025", "label": "Gemini 2.5 Flash",     "thinking": True},
        {"id": "gemini-3.0-flash",              "label": "Gemini 3 Flash",          "thinking": True},
        {"id": "gemini-2.5-flash-lite",         "label": "Gemini 2.5 Flash Lite",   "thinking": False},
    ],
    "claude": [
        {"id": "claude-haiku-4-5-latest",       "label": "Claude Haiku 4.5",        "thinking": True},
    ],
    "kimi": [
        {"id": "kimi-k2.5",                     "label": "Kimi K2.5",               "thinking": False},
    ],
    "zai": [
        {"id": "glm-4.7-flash",                 "label": "GLM-4.7 Flash",           "thinking": False},
    ],
}


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
    """Return providers that have an API key configured, with their models."""
    available = []
    for pid, cfg in PROVIDER_CONFIG.items():
        key = get_provider_key(pid)
        if key:
            default_model = _get_setting(cfg["model_attr"])
            models = MODEL_REGISTRY.get(pid, [])
            available.append({
                "id": pid,
                "label": cfg["label"],
                "default_model": default_model,
                "models": models,
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
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    thinking: Optional[bool] = None,
) -> BaseChatModel:
    """
    Build a LangChain chat model for the given provider.

    Args:
        provider:    Provider id (openai, xai, gemini, claude, kimi, zai).
                     Defaults to DEFAULT_LLM_PROVIDER from settings.
        model:       Override model name.  Falls back to the provider default.
        temperature: Override temperature. Defaults to settings.LLM_TEMPERATURE.
        max_tokens:  Override max tokens.  Defaults to settings.LLM_MAX_TOKENS.
        thinking:    Enable reasoning / thinking mode for capable models.
                     True = low thinking, False = off, None = off.

    Returns:
        A BaseChatModel instance (ChatOpenAI or ChatAnthropic).
        Call ``.bind_tools(tools)`` on the result if tool calling is needed.
    """
    provider = resolve_provider(provider)
    cfg = PROVIDER_CONFIG[provider]

    temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
    tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

    api_key = get_provider_key(provider)
    model_name = (model or "").strip() or _get_setting(cfg["model_attr"])
    if not model_name:
        raise ValueError(
            f"No model configured for provider '{provider}'. "
            f"Set {cfg['model_attr']} in .env"
        )

    use_thinking = bool(thinking) and cfg.get("thinking_method") is not None

    if cfg["backend"] == "anthropic":
        return _build_anthropic(api_key, model_name, temp, tokens, use_thinking)

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

    if use_thinking and cfg["thinking_method"] == "reasoning_effort":
        llm_kwargs["reasoning_effort"] = settings.LLM_REASONING_EFFORT

    if base_url:
        llm_kwargs["base_url"] = base_url

    logger.debug(
        f"[LLM] ChatOpenAI kwargs: {', '.join(f'{k}={v!r}' for k, v in llm_kwargs.items() if k != 'api_key')}"
    )
    logger.info(f"[LLM] {provider}/{model_name} thinking={use_thinking}")
    return ChatOpenAI(**llm_kwargs)


def _build_anthropic(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    thinking: bool = False,
) -> BaseChatModel:
    """Build a ChatAnthropic instance for the Claude provider."""
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        raise ImportError(
            "langchain-anthropic is required for the Claude provider. "
            "Install it with: pip install langchain-anthropic"
        )

    kwargs: dict = {
        "model": model,
        "anthropic_api_key": api_key,
        "max_tokens": max_tokens,
    }

    if thinking:
        # Extended thinking requires temperature=1 and a budget_tokens allocation.
        kwargs["temperature"] = 1
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": 2048}
        logger.info(f"[LLM] claude/{model} thinking=ON")
    else:
        kwargs["temperature"] = temperature
        logger.info(f"[LLM] claude/{model} thinking=OFF")

    return ChatAnthropic(**kwargs)
