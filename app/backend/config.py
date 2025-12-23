from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5-mini"
    
    # Session management
    MIN_MESSAGES_IN_SESSION: int = 10       # Keep at least this many messages in active session
    MAX_MESSAGES_BEFORE_ARCHIVE: int = 20   # Archive oldest messages when this limit is reached
    SUMMARIES_IN_CONTEXT: int = 3           # Number of previous session summaries to include
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
        env_file_encoding = 'utf-8'

settings = Settings()
