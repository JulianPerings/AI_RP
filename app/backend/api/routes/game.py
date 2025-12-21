from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import PlayerCharacter
from agents import create_game_master, get_history_manager

router = APIRouter(prefix="/game", tags=["game"])


class ChatRequest(BaseModel):
    message: str
    player_id: int
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tool_calls: list = []


class StartSessionRequest(BaseModel):
    player_id: int


class StartSessionResponse(BaseModel):
    session_id: str
    intro: str
    player_name: str
    tool_calls: list = []


@router.post("/chat", response_model=ChatResponse)
def game_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a message to the Game Master and receive a narrative response.
    
    The Game Master will:
    - Query game state using tools
    - Generate immersive narrative responses
    - Update game state (health, gold, relationships, etc.) as needed
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {request.player_id} not found")
    
    session_id = request.session_id or str(uuid.uuid4())
    
    session_context = {
        "player_name": player.name,
        "location_id": player.current_location_id
    }
    
    gm = create_game_master()
    
    try:
        response, tool_calls = gm.chat(
            message=request.message,
            player_id=request.player_id,
            session_id=session_id,
            session_context=session_context
        )
        return ChatResponse(response=response, session_id=session_id, tool_calls=tool_calls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Game Master error: {str(e)}")


@router.post("/start-session", response_model=StartSessionResponse)
def start_game_session(request: StartSessionRequest, db: Session = Depends(get_db)):
    """
    Start a new game session for a player.
    
    Returns an introductory narrative that sets the scene based on
    the player's current state, location, and active quests.
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {request.player_id} not found")
    
    session_id = str(uuid.uuid4())
    
    gm = create_game_master()
    
    try:
        intro, tool_calls = gm.start_session(
            player_id=request.player_id,
            session_id=session_id
        )
        return StartSessionResponse(
            session_id=session_id,
            intro=intro,
            player_name=player.name,
            tool_calls=tool_calls
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Game Master error: {str(e)}")


@router.get("/health")
def game_health():
    """Check if the Game Master agent is operational."""
    try:
        gm = create_game_master()
        return {
            "status": "healthy",
            "model": gm.model_name,
            "tools_count": len(gm.tools)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/history/{session_id}")
def get_chat_history(session_id: str, limit: int = 50):
    """
    Get chat history for a specific session.
    
    Returns all messages in chronological order with their roles and timestamps.
    """
    history_manager = get_history_manager()
    history = history_manager.get_history(session_id, limit=limit)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history
    }


@router.get("/sessions/{player_id}")
def get_player_sessions(player_id: int, db: Session = Depends(get_db)):
    """
    Get all chat sessions for a player.
    
    Returns sessions sorted by most recently active.
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    
    history_manager = get_history_manager()
    sessions = history_manager.get_player_sessions(player_id)
    return {
        "player_id": player_id,
        "player_name": player.name,
        "session_count": len(sessions),
        "sessions": sessions
    }


@router.post("/continue-session")
def continue_session(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Continue an existing session (same as /chat but session_id is required).
    
    Loads previous conversation history from the database.
    """
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id is required for continue-session")
    
    return game_chat(request, db)
