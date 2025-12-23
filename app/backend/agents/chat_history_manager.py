"""
Database-backed chat history manager for persistent conversation storage.

Session ID format: {player_id}-{session_number}
- session_number 0 = current active session
- session_number 1, 2, 3... = archived sessions (higher = older)
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from database import SessionLocal
from models import ChatSession, ChatMessage
from config import settings

logger = logging.getLogger(__name__)


class ChatHistoryManager:
    """Manages chat history persistence in the database."""
    
    def __init__(self):
        pass
    
    def _get_db(self) -> Session:
        """Get a database session."""
        return SessionLocal()
    
    @staticmethod
    def make_session_id(player_id: int, session_number: int = 0) -> str:
        """Generate session ID in format: {player_id}-{session_number}"""
        return f"{player_id}-{session_number}"
    
    @staticmethod
    def parse_session_id(session_id: str) -> tuple[int, int]:
        """Parse session ID into (player_id, session_number)"""
        parts = session_id.split("-")
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0
    
    def get_or_create_session(self, session_id: str, player_id: int) -> ChatSession:
        """Get existing session or create a new one."""
        db = self._get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                _, session_number = self.parse_session_id(session_id)
                session = ChatSession(
                    session_id=session_id, 
                    player_id=player_id,
                    session_number=session_number
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                logger.info(f"[HISTORY] Created session: {session_id} (number={session_number}) for player {player_id}")
            return session
        finally:
            db.close()
    
    def get_active_session(self, player_id: int) -> Optional[ChatSession]:
        """Get the active session (number=0) for a player."""
        db = self._get_db()
        try:
            return db.query(ChatSession).filter(
                ChatSession.player_id == player_id,
                ChatSession.session_number == 0
            ).first()
        finally:
            db.close()
    
    def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session."""
        db = self._get_db()
        try:
            return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).count()
        finally:
            db.close()
    
    def get_previous_summaries(self, player_id: int, limit: int = None) -> List[dict]:
        """Get summaries from archived sessions for context.
        
        Returns summaries ordered from most recent to oldest.
        """
        limit = limit or settings.SUMMARIES_IN_CONTEXT
        db = self._get_db()
        try:
            sessions = db.query(ChatSession).filter(
                ChatSession.player_id == player_id,
                ChatSession.session_number > 0,  # Only archived sessions
                ChatSession.summary.isnot(None)
            ).order_by(ChatSession.session_number.asc()).limit(limit).all()
            
            return [
                {
                    "session_id": s.session_id,
                    "session_number": s.session_number,
                    "title": s.title,
                    "summary": s.summary,
                    "keywords": s.keywords
                }
                for s in sessions
            ]
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
    
    def check_and_archive_if_needed(self, player_id: int, session_id: str, 
                                     summarize_callback=None) -> Optional[str]:
        """Check if session needs archiving and perform it if so.
        
        When message count exceeds MAX_MESSAGES_BEFORE_ARCHIVE:
        1. Increment all existing session numbers for this player
        2. Create new archive session (number=1) with oldest messages
        3. Generate summary for the archived session
        4. Delete archived messages from active session
        
        Args:
            player_id: The player ID
            session_id: Current active session ID
            summarize_callback: Optional async function(messages) -> (summary, title, keywords)
        
        Returns:
            Archive session ID if archiving occurred, None otherwise
        """
        msg_count = self.get_message_count(session_id)
        
        if msg_count < settings.MAX_MESSAGES_BEFORE_ARCHIVE:
            return None
        
        db = self._get_db()
        try:
            # Get oldest messages to archive (keep MIN_MESSAGES_IN_SESSION)
            messages_to_archive = settings.MAX_MESSAGES_BEFORE_ARCHIVE - settings.MIN_MESSAGES_IN_SESSION
            
            oldest_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).limit(messages_to_archive).all()
            
            if not oldest_messages:
                return None
            
            # Increment all existing archive session numbers
            existing_archives = db.query(ChatSession).filter(
                ChatSession.player_id == player_id,
                ChatSession.session_number > 0
            ).order_by(ChatSession.session_number.desc()).all()
            
            for archive in existing_archives:
                old_id = archive.session_id
                new_number = archive.session_number + 1
                new_id = self.make_session_id(player_id, new_number)
                
                # Update session
                archive.session_id = new_id
                archive.session_number = new_number
                
                # Update all messages in this session
                db.query(ChatMessage).filter(
                    ChatMessage.session_id == old_id
                ).update({"session_id": new_id})
            
            # Create new archive session (number=1)
            archive_session_id = self.make_session_id(player_id, 1)
            archive_session = ChatSession(
                session_id=archive_session_id,
                player_id=player_id,
                session_number=1
            )
            db.add(archive_session)
            
            # Move oldest messages to archive
            message_ids = [m.id for m in oldest_messages]
            db.query(ChatMessage).filter(
                ChatMessage.id.in_(message_ids)
            ).update({"session_id": archive_session_id}, synchronize_session=False)
            
            db.commit()
            
            logger.info(f"[ARCHIVE] Archived {len(oldest_messages)} messages from {session_id} to {archive_session_id}")
            
            # Generate summary if callback provided
            if summarize_callback:
                try:
                    messages_text = "\n".join([
                        f"{m.role}: {m.content}" for m in oldest_messages
                    ])
                    summary, title, keywords = summarize_callback(messages_text)
                    
                    # Update archive with summary
                    db.query(ChatSession).filter(
                        ChatSession.session_id == archive_session_id
                    ).update({
                        "summary": summary,
                        "title": title,
                        "keywords": keywords
                    })
                    db.commit()
                    logger.info(f"[ARCHIVE] Generated summary for {archive_session_id}: {title}")
                except Exception as e:
                    logger.error(f"[ARCHIVE] Failed to generate summary: {e}")
            
            return archive_session_id
            
        finally:
            db.close()
    
    def get_session_with_messages(self, session_id: str) -> Optional[dict]:
        """Get a session with all its messages (for reviewing archived sessions)."""
        db = self._get_db()
        try:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            
            if not session:
                return None
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.asc()).all()
            
            return {
                "session_id": session.session_id,
                "player_id": session.player_id,
                "session_number": session.session_number,
                "summary": session.summary,
                "title": session.title,
                "keywords": session.keywords,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "messages": [
                    {
                        "role": m.role,
                        "content": m.content,
                        "tool_calls": m.tool_calls,
                        "created_at": m.created_at.isoformat() if m.created_at else None
                    }
                    for m in messages
                ]
            }
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
