from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    
    # LLM Configuration (gpt-5-mini: 400k context, 128k max output, reasoning support)
    OPENAI_MODEL: str = "gpt-5-mini"
    LLM_TEMPERATURE: float = 0.8            # Creativity (0.0-2.0), higher = more creative
    LLM_MAX_TOKENS: int = 8192              # Max response tokens (model supports up to 128k)
    LLM_REASONING_EFFORT: str = "low"       # Reasoning depth: "low", "medium", "high"
    SUMMARY_LLM_TEMPERATURE: float = 0.3    # Lower temp for consistent summaries
    SUMMARY_LLM_MAX_TOKENS: int = 500       # Summary responses are short
    
    # Session management
    MIN_MESSAGES_IN_SESSION: int = 15       # Keep at least this many messages in active session
    MAX_MESSAGES_BEFORE_ARCHIVE: int = 30   # Archive oldest messages when this limit is reached
    SUMMARIES_IN_CONTEXT: int = 5           # Number of previous session summaries to include
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = 'utf-8'

settings = Settings()
