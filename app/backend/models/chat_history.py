from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from database import Base


class ChatSession(Base):
    """Represents a game session/conversation thread.
    
    Session ID format: {player_id}-{session_number}
    - session_number 0 = current active session
    - session_number 1, 2, 3... = archived sessions (higher = older)
    """
    __tablename__ = "chat_session"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    player_id = Column(Integer, ForeignKey("player_character.id"), nullable=False, index=True)
    session_number = Column(Integer, default=0, nullable=False)  # 0=active, 1+=archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # Long-term memory fields
    summary = Column(Text, default=None)  # LLM-generated summary of session
    keywords = Column(Text, default=None)  # Comma-separated searchable keywords
    title = Column(String(200), default=None)  # Short title for the session


class ChatMessage(Base):
    """Stores individual messages in a chat session."""
    __tablename__ = "chat_message"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey("chat_session.session_id"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'human', 'ai', 'tool', 'tool_result'
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, default=None)  # For AI messages with tool calls
    tool_name = Column(String(100), default=None)  # For tool result messages
    created_at = Column(DateTime(timezone=True), server_default=func.now())
