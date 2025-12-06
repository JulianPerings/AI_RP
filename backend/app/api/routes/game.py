"""Game interaction routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.player import Player
from app.models.quest import Quest, QuestStatus
from app.schemas.game import ChatRequest, ChatResponse, GameStateResponse
from app.schemas.player import PlayerStats
from app.schemas.quest import QuestResponse
from app.services.llm.game_master import game_master
from app.core.logging import log

router = APIRouter(prefix="/game", tags=["game"])


@router.post("/{player_id}/chat", response_model=ChatResponse)
async def chat_with_game_master(
    player_id: int,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """Send a message to the game master AI."""
    # Get player
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Get active quests
    quests_result = await db.execute(
        select(Quest).where(
            (Quest.player_id == player_id) & 
            (Quest.status == QuestStatus.IN_PROGRESS)
        )
    )
    active_quests = quests_result.scalars().all()
    quest_titles = [q.title for q in active_quests]
    
    # Generate AI response
    try:
        response_text = await game_master.generate_response(
            player_message=chat_request.message,
            character_name=player.character_name,
            level=player.level,
            current_location=player.current_location,
            active_quests=quest_titles,
            conversation_history=chat_request.context.get("history") if chat_request.context else None
        )
        
        log.info(f"Generated chat response for player {player_id}")
        
        return ChatResponse(
            message=response_text,
            actions=["Continue", "Check Inventory", "View Quests"],
            state_changes={}
        )
        
    except Exception as e:
        log.error(f"Error generating chat response: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate response"
        )


@router.get("/{player_id}/state", response_model=GameStateResponse)
async def get_game_state(
    player_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get complete game state for a player."""
    # Get player
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Get active quests
    quests_result = await db.execute(
        select(Quest).where(
            (Quest.player_id == player_id) & 
            (Quest.status == QuestStatus.IN_PROGRESS)
        )
    )
    active_quests = quests_result.scalars().all()
    
    # Build response
    player_stats = PlayerStats(
        level=player.level,
        experience=player.experience,
        health=player.health,
        max_health=player.max_health,
        mana=player.mana,
        max_mana=player.max_mana,
        current_location=player.current_location
    )
    
    return GameStateResponse(
        player=player_stats,
        active_quests=[QuestResponse.model_validate(q) for q in active_quests],
        current_location=player.current_location,
        available_actions=["Explore", "Talk to NPC", "Check Inventory", "Rest"]
    )


@router.post("/{player_id}/location", response_model=dict)
async def change_location(
    player_id: int,
    location: str,
    db: AsyncSession = Depends(get_db)
):
    """Change player's location."""
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Update location
    player.current_location = location
    await db.commit()
    
    # Generate location description
    try:
        description = await game_master.describe_location(location)
        
        log.info(f"Player {player_id} moved to {location}")
        
        return {
            "location": location,
            "description": description
        }
        
    except Exception as e:
        log.error(f"Error generating location description: {str(e)}")
        return {
            "location": location,
            "description": f"You have arrived at {location}."
        }
