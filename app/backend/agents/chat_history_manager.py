"""
Database-backed chat history manager for persistent conversation storage.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from database import SessionLocal
from models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """Manages chat history persistence in the database."""
    
    def __init__(self):
        pass
    
    def _get_db(self) -> Session:
        """Get a database session."""
        return SessionLocal()
    
    def get_or_create_session(self, session_id: str, player_id: int) -> ChatSession:
        """Get existing session or create a new one."""
        db = self._get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                session = ChatSession(session_id=session_id, player_id=player_id)
                db.add(session)
                db.commit()
                db.refresh(session)
                logger.info(f"[HISTORY] Created new session: {session_id} for player {player_id}")
            return session
        finally:
            db.close()
    
    def save_message(self, session_id: str, role: str, content: str, 
                     tool_calls: Optional[list] = None, tool_name: Optional[str] = None):
        """Save a message to the database."""
        db = self._get_db()
        try:
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                tool_calls=tool_calls,
                tool_name=tool_name
            )
            db.add(message)
            db.commit()
            logger.debug(f"[HISTORY] Saved {role} message to session {session_id}")
        finally:
            db.close()
    
    def save_human_message(self, session_id: str, content: str):
        """Save a human/user message."""
        self.save_message(session_id, "human", content)
    
    def save_ai_message(self, session_id: str, content: str, tool_calls: Optional[list] = None):
        """Save an AI response message."""
        self.save_message(session_id, "ai", content, tool_calls=tool_calls)
    
    def save_tool_result(self, session_id: str, tool_name: str, content: str):
        """Save a tool result message."""
        self.save_message(session_id, "tool_result", content, tool_name=tool_name)
    
    def get_history(self, session_id: str, limit: int = 50) -> List[dict]:
        """Get chat history for a session."""
        db = self._get_db()
        try:
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(limit).all()
            
            # Reverse to get chronological order
            messages = list(reversed(messages))
            
            return [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_name": msg.tool_name,
                    "created_at": msg.created_at.isoformat() if msg.created_at else None
                }
                for msg in messages
            ]
        finally:
            db.close()
    
    def get_langchain_messages(self, session_id: str, limit: int = 20) -> list:
        """Get history as LangChain message objects for context."""
        history = self.get_history(session_id, limit)
        messages = []
        
        for msg in history:
            if msg["role"] == "human":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                messages.append(AIMessage(content=msg["content"]))
            # Skip tool messages for context (they're intermediate)
        
        return messages
    
    def get_player_sessions(self, player_id: int) -> List[dict]:
        """Get all sessions for a player."""
        db = self._get_db()
        try:
            sessions = db.query(ChatSession).filter(
                ChatSession.player_id == player_id
            ).order_by(ChatSession.last_active.desc()).all()
            
            return [
                {
                    "session_id": s.session_id,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "last_active": s.last_active.isoformat() if s.last_active else None
                }
                for s in sessions
            ]
        finally:
            db.close()
    
    def clear_session(self, session_id: str):
        """Clear all messages in a session."""
        db = self._get_db()
        try:
            db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            db.commit()
            logger.info(f"[HISTORY] Cleared session: {session_id}")
        finally:
            db.close()


# Singleton instance
_history_manager: Optional[ChatHistoryManager] = None


def get_history_manager() -> ChatHistoryManager:
    """Get or create the singleton history manager."""
    global _history_manager
    if _history_manager is None:
        _history_manager = ChatHistoryManager()
    return _history_manager
