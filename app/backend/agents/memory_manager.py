"""
Long-term memory system for the Game Master agent.
Provides session summaries and keyword-based memory search.
"""
import logging
from typing import List, Optional
from openai import OpenAI

from database import SessionLocal
from models import ChatSession, ChatMessage
from config import settings

logger = logging.getLogger(__name__)


SUMMARY_PROMPT = """Analyze this RPG game session conversation and provide:

1. **Title**: A short 3-8 word title for this session (e.g., "Meeting Bob the Blacksmith")
2. **Summary**: A 2-4 sentence summary of key events, decisions, and outcomes
3. **Keywords**: Important names, places, items, and events (comma-separated)

Focus on information that would be useful to recall later:
- NPC names and their roles/relationships
- Locations visited
- Quests started/completed
- Important items acquired
- Key decisions made
- Promises, debts, or unfinished business

CONVERSATION:
{conversation}

Respond in this exact format:
TITLE: [title here]
SUMMARY: [summary here]
KEYWORDS: [keyword1, keyword2, keyword3, ...]"""


class MemoryManager:
    """Manages long-term memory through session summaries and search."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.summary_model = "gpt-5-mini"  # Cheaper model for summaries
    
    def _get_db(self):
        return SessionLocal()
    
    def generate_session_summary(self, session_id: str) -> dict:
        """Generate a summary for a session using LLM."""
        db = self._get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                return {"error": f"Session {session_id} not found"}
            
            # Get all messages for this session
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at).all()
            
            if len(messages) < 3:
                return {"error": "Not enough messages to summarize (minimum 3)"}
            
            # Format conversation for the LLM
            conversation_text = ""
            for msg in messages:
                if msg.role == "human":
                    conversation_text += f"PLAYER: {msg.content}\n"
                elif msg.role == "ai":
                    conversation_text += f"GAME MASTER: {msg.content}\n"
            
            # Generate summary using LLM
            response = self.client.chat.completions.create(
                model=self.summary_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes RPG game sessions."},
                    {"role": "user", "content": SUMMARY_PROMPT.format(conversation=conversation_text[:8000])}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content
            
            # Parse the response
            title = ""
            summary = ""
            keywords = ""
            
            for line in result_text.split("\n"):
                line = line.strip()
                if line.startswith("TITLE:"):
                    title = line[6:].strip()
                elif line.startswith("SUMMARY:"):
                    summary = line[8:].strip()
                elif line.startswith("KEYWORDS:"):
                    keywords = line[9:].strip()
            
            # Update the session
            session.title = title
            session.summary = summary
            session.keywords = keywords.lower()  # Lowercase for easier search
            db.commit()
            
            logger.info(f"[MEMORY] Generated summary for session {session_id}: {title}")
            
            return {
                "session_id": session_id,
                "title": title,
                "summary": summary,
                "keywords": keywords,
                "message_count": len(messages)
            }
        finally:
            db.close()
    
    def search_memories(self, player_id: int, query: str, limit: int = 5) -> List[dict]:
        """Search through session summaries and keywords for relevant memories.
        
        Uses simple keyword matching against session keywords and summaries.
        """
        db = self._get_db()
        try:
            # Get all sessions with summaries for this player
            sessions = db.query(ChatSession).filter(
                ChatSession.player_id == player_id,
                ChatSession.summary.isnot(None)
            ).order_by(ChatSession.last_active.desc()).all()
            
            if not sessions:
                return []
            
            # Score each session based on keyword matches
            query_words = set(query.lower().split())
            scored_sessions = []
            
            for session in sessions:
                score = 0
                
                # Check keywords
                if session.keywords:
                    session_keywords = set(session.keywords.lower().split(","))
                    session_keywords = {k.strip() for k in session_keywords}
                    
                    for query_word in query_words:
                        for keyword in session_keywords:
                            if query_word in keyword or keyword in query_word:
                                score += 2
                
                # Check summary
                if session.summary:
                    summary_lower = session.summary.lower()
                    for query_word in query_words:
                        if query_word in summary_lower:
                            score += 1
                
                # Check title
                if session.title:
                    title_lower = session.title.lower()
                    for query_word in query_words:
                        if query_word in title_lower:
                            score += 1
                
                if score > 0:
                    scored_sessions.append((session, score))
            
            # Sort by score and return top results
            scored_sessions.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for session, score in scored_sessions[:limit]:
                results.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "summary": session.summary,
                    "keywords": session.keywords,
                    "relevance_score": score,
                    "last_active": session.last_active.isoformat() if session.last_active else None
                })
            
            logger.info(f"[MEMORY] Search for '{query}' found {len(results)} relevant memories")
            return results
        finally:
            db.close()
    
    def get_session_details(self, session_id: str, message_limit: int = 20) -> dict:
        """Get full details of a session including recent messages."""
        db = self._get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if not session:
                return {"error": f"Session {session_id} not found"}
            
            messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.created_at.desc()).limit(message_limit).all()
            
            messages = list(reversed(messages))
            
            return {
                "session_id": session.session_id,
                "title": session.title,
                "summary": session.summary,
                "keywords": session.keywords,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "last_active": session.last_active.isoformat() if session.last_active else None,
                "messages": [
                    {"role": msg.role, "content": msg.content}
                    for msg in messages
                    if msg.role in ("human", "ai")
                ]
            }
        finally:
            db.close()
    
    def get_all_player_memories(self, player_id: int) -> List[dict]:
        """Get all summarized sessions for a player."""
        db = self._get_db()
        try:
            sessions = db.query(ChatSession).filter(
                ChatSession.player_id == player_id,
                ChatSession.summary.isnot(None)
            ).order_by(ChatSession.last_active.desc()).all()
            
            return [
                {
                    "session_id": s.session_id,
                    "title": s.title,
                    "summary": s.summary,
                    "keywords": s.keywords,
                    "last_active": s.last_active.isoformat() if s.last_active else None
                }
                for s in sessions
            ]
        finally:
            db.close()


# Singleton instance
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """Get or create the singleton memory manager."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
