"""Player management routes."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerResponse, PlayerUpdate
from app.core.security import get_password_hash
from app.core.logging import log

router = APIRouter(prefix="/players", tags=["players"])


@router.post("/", response_model=PlayerResponse, status_code=status.HTTP_201_CREATED)
async def create_player(
    player_data: PlayerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new player account."""
    # Check if username or email already exists
    result = await db.execute(
        select(Player).where(
            (Player.username == player_data.username) | 
            (Player.email == player_data.email)
        )
    )
    existing_player = result.scalar_one_or_none()
    
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )
    
    # Create new player
    new_player = Player(
        username=player_data.username,
        email=player_data.email,
        hashed_password=get_password_hash(player_data.password),
        character_name=player_data.character_name,
        character_class=player_data.character_class,
    )
    
    db.add(new_player)
    await db.commit()
    await db.refresh(new_player)
    
    log.info(f"Created new player: {new_player.username}")
    return new_player


@router.get("/{player_id}", response_model=PlayerResponse)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get player by ID."""
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    return player


@router.patch("/{player_id}", response_model=PlayerResponse)
async def update_player(
    player_id: int,
    player_update: PlayerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update player information."""
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    # Update fields
    update_data = player_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(player, field, value)
    
    await db.commit()
    await db.refresh(player)
    
    log.info(f"Updated player: {player.username}")
    return player


@router.delete("/{player_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_player(
    player_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a player account."""
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    
    await db.delete(player)
    await db.commit()
    
    log.info(f"Deleted player: {player.username}")
    return None
