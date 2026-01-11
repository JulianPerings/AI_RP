"""
Simplified story manager - stores messages directly in PlayerCharacter.story_messages.

No sessions, no archiving, no foreign keys. Just a JSON list.
"""
import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal
from models import PlayerCharacter

logger = logging.getLogger(__name__)


class StoryManager:
    """Manages story messages stored directly in PlayerCharacter."""
    
    def _get_db(self) -> Session:
        return SessionLocal()
    
    def get_messages(self, player_id: int, limit: Optional[int] = None) -> List[dict]:
        """Get story messages for a player.
        
        Args:
            player_id: The player ID
            limit: Optional limit (returns last N messages)
        
        Returns:
            List of message dicts
        """
        db = self._get_db()
        try:
            player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
            if not player or not player.story_messages:
                return []
            
            messages = player.story_messages
            if limit:
                messages = messages[-limit:]
            return messages
        finally:
            db.close()
    
    def add_message(self, player_id: int, role: str, content: str, 
                    tags: Optional[List[str]] = None) -> dict:
        """Add a message to the player's story.
        
        Args:
            player_id: The player ID
            role: 'gm' or 'player'
            content: Message content
            tags: Optional tags (e.g., ['combat', 'dice:15', 'critical'])
        
        Returns:
            The added message dict
        """
        db = self._get_db()
        try:
            player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
            if not player:
                raise ValueError(f"Player {player_id} not found")
            
            message = {
                "role": role,
                "content": content,
                "tags": tags or [],
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Initialize if None
            if player.story_messages is None:
                player.story_messages = []
            
            # Append message (need to reassign for SQLAlchemy to detect change)
            messages = list(player.story_messages)
            messages.append(message)
            player.story_messages = messages
            
            db.commit()
            logger.debug(f"[STORY] Added {role} message for player {player_id}")
            return message
        finally:
            db.close()
    
    def add_player_message(self, player_id: int, content: str, 
                           tags: Optional[List[str]] = None) -> dict:
        """Add a player message."""
        return self.add_message(player_id, "player", content, tags)
    
    def add_gm_message(self, player_id: int, content: str,
                       tags: Optional[List[str]] = None) -> dict:
        """Add a GM message."""
        return self.add_message(player_id, "gm", content, tags)
    
    def get_context_messages(self, player_id: int, limit: int = 20) -> List[dict]:
        """Get recent messages for GM context."""
        return self.get_messages(player_id, limit=limit)
    
    def clear_messages(self, player_id: int) -> int:
        """Clear all messages for a player. Returns count deleted."""
        db = self._get_db()
        try:
            player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
            if not player:
                return 0
            
            count = len(player.story_messages) if player.story_messages else 0
            player.story_messages = []
            db.commit()
            logger.info(f"[STORY] Cleared {count} messages for player {player_id}")
            return count
        finally:
            db.close()
    
    def update_message_tags(self, player_id: int, message_index: int, 
                            tags: List[str]) -> bool:
        """Update tags on a specific message by index.
        
        Args:
            player_id: The player ID
            message_index: Index of message to update (negative for from end)
            tags: New tags list
        
        Returns:
            True if updated, False if not found
        """
        db = self._get_db()
        try:
            player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
            if not player or not player.story_messages:
                return False
            
            messages = list(player.story_messages)
            if abs(message_index) > len(messages):
                return False
            
            messages[message_index]["tags"] = tags
            player.story_messages = messages
            db.commit()
            return True
        finally:
            db.close()
    
    def get_messages_by_tag(self, player_id: int, tag: str) -> List[dict]:
        """Get all messages with a specific tag."""
        messages = self.get_messages(player_id)
        return [m for m in messages if tag in m.get("tags", [])]
    
    def compress_tagged_messages(self, player_id: int, tag: str, 
                                  summary: str, summary_tags: Optional[List[str]] = None) -> int:
        """Replace all messages with a specific tag with a single summary message.
        
        Useful for combat compression: all 'combat:123' tagged messages → one summary.
        
        Args:
            player_id: The player ID
            tag: Tag to match (e.g., 'combat:123')
            summary: Summary content to replace with
            summary_tags: Tags for the summary message
        
        Returns:
            Number of messages replaced
        """
        db = self._get_db()
        try:
            player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
            if not player or not player.story_messages:
                return 0
            
            messages = list(player.story_messages)
            
            # Find messages with this tag
            tagged_indices = [i for i, m in enumerate(messages) if tag in m.get("tags", [])]
            if not tagged_indices:
                return 0
            
            # Get position of first tagged message
            first_idx = tagged_indices[0]
            
            # Remove tagged messages (reverse order to preserve indices)
            for idx in reversed(tagged_indices):
                messages.pop(idx)
            
            # Insert summary at original position
            summary_msg = {
                "role": "gm",
                "content": summary,
                "tags": summary_tags or [f"{tag}:summary"],
                "timestamp": datetime.utcnow().isoformat()
            }
            messages.insert(first_idx, summary_msg)
            
            player.story_messages = messages
            db.commit()
            
            replaced = len(tagged_indices)
            logger.info(f"[STORY] Compressed {replaced} messages with tag '{tag}' for player {player_id}")
            return replaced
        finally:
            db.close()


# Singleton instance
_story_manager: Optional[StoryManager] = None


def get_story_manager() -> StoryManager:
    """Get or create the singleton story manager."""
    global _story_manager
    if _story_manager is None:
        _story_manager = StoryManager()
    return _story_manager
