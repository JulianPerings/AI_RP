from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    
    # LLM Configuration (gpt-5-mini: 400k context, 128k max output, reasoning support)
    OPENAI_MODEL: str = "gpt-5-mini"
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_MODEL: str = "grok-4-1-fast-reasoning"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-preview-09-2025"
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-haiku-4-5-latest"
    KIMI_API_KEY: str = ""
    KIMI_BASE_URL: str = "https://api.moonshot.cn/v1"
    KIMI_MODEL: str = "kimi-k2.5"
    ZAI_API_KEY: str = ""
    ZAI_BASE_URL: str = "https://open.bigmodel.cn/api/paas/v4/"
    ZAI_MODEL: str = "glm-4.7-flash"
    DEFAULT_LLM_PROVIDER: str = "openai"
    DEBUG_MODE: bool = False                   # Set to true for verbose debug logging

    LLM_TEMPERATURE: float = 0.8            # Creativity (0.0-2.0), higher = more creative
    LLM_MAX_TOKENS: int = 8192              # Max response tokens (model supports up to 128k)
    LLM_REASONING_EFFORT: str = "low"       # Reasoning depth: "low", "medium", "high"
    SUMMARY_LLM_TEMPERATURE: float = 0.3    # Lower temp for consistent summaries
    SUMMARY_LLM_MAX_TOKENS: int = 500       # Summary responses are short
    AUTOCOMPLETE_MAX_TOKENS: int = 1024     # Tokens for autocomplete (needs room for reasoning)
    
    # TTS (Text-to-Speech) — Gemini only for now
    # TODO: When adding non-Gemini TTS providers, refactor TTS_DIRECTOR_MODEL
    # to support other providers (currently assumes Gemini via google-genai SDK).
    TTS_MODEL: str = "gemini-2.5-flash-preview-tts"   # Gemini TTS model
    TTS_DIRECTOR_MODEL: str = "gemini-2.5-flash-lite"  # LLM that transforms GM text → TTS script
    TTS_NARRATOR_VOICE: str = "Charon"                 # Male, informative narrator
    TTS_CHARACTER_VOICE_FEMALE: str = "Aoede"           # Default female NPC voice
    TTS_CHARACTER_VOICE_MALE: str = "Puck"              # Default male NPC voice

    # Session management
    MIN_MESSAGES_IN_SESSION: int = 15       # Keep at least this many messages in active session
    MAX_MESSAGES_BEFORE_ARCHIVE: int = 30   # Archive oldest messages when this limit is reached
    SUMMARIES_IN_CONTEXT: int = 5           # Number of previous session summaries to include
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = 'utf-8'

settings = Settings()
