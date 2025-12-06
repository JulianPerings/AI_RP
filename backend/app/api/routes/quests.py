"""Quest management routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.player import Player
from app.models.quest import Quest, QuestStatus
from app.schemas.quest import QuestCreate, QuestResponse, QuestUpdate
from app.core.logging import log

router = APIRouter(prefix="/quests", tags=["quests"])


@router.post("/", response_model=QuestResponse, status_code=status.HTTP_201_CREATED)
async def create_quest(
    quest_data: QuestCreate,
    player_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Create a new quest for a player."""
    # Verify player exists
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Create quest
    new_quest = Quest(
        player_id=player_id,
        title=quest_data.title,
        description=quest_data.description,
        quest_type=quest_data.quest_type,
        objectives=quest_data.objectives,
        rewards=quest_data.rewards,
        max_progress=quest_data.max_progress,
        status=QuestStatus.NOT_STARTED
    )
    
    db.add(new_quest)
    await db.commit()
    await db.refresh(new_quest)
    
    log.info(f"Created quest '{new_quest.title}' for player {player_id}")
    return new_quest


@router.get("/player/{player_id}", response_model=List[QuestResponse])
async def get_player_quests(
    player_id: int,
    status_filter: QuestStatus = None,
    db: AsyncSession = Depends(get_db)
):
    """Get all quests for a player, optionally filtered by status."""
    query = select(Quest).where(Quest.player_id == player_id)
    
    if status_filter:
        query = query.where(Quest.status == status_filter)
    
    result = await db.execute(query)
    quests = result.scalars().all()
    
    return quests


@router.get("/{quest_id}", response_model=QuestResponse)
async def get_quest(
    quest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get quest by ID."""
    result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = result.scalar_one_or_none()
    
    if not quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found"
        )
    
    return quest


@router.patch("/{quest_id}", response_model=QuestResponse)
async def update_quest(
    quest_id: int,
    quest_update: QuestUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update quest progress or status."""
    result = await db.execute(select(Quest).where(Quest.id == quest_id))
    quest = result.scalar_one_or_none()
    
    if not quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found"
        )
    
    # Update fields
    update_data = quest_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quest, field, value)
    
    # Handle quest completion
    if quest_update.status == QuestStatus.COMPLETED:
        from datetime import datetime
        quest.completed_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(quest)
    
    log.info(f"Updated quest {quest_id}: {quest.title}")
    return quest
