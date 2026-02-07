import logging
import random
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from database import get_db
from models import PlayerCharacter, CombatSession, NonPlayerCharacter
from agents import create_game_master, get_story_manager, get_memory_manager, autocomplete_action
from agents.context_builder import build_session_context
from agents.llm_factory import get_available_providers
from agents.tts_service import generate_tts_stream, is_tts_available
from config import settings

router = APIRouter(prefix="/game", tags=["game"])


class ChatRequest(BaseModel):
    message: str
    player_id: int
    tags: Optional[list] = None  # Optional tags for the message (e.g., dice roll)
    llm_provider: Optional[str] = None
    model: Optional[str] = None
    thinking: Optional[bool] = None


class ChatResponse(BaseModel):
    response: str
    tool_calls: list = []


class StartSessionRequest(BaseModel):
    player_id: int
    llm_provider: Optional[str] = None
    model: Optional[str] = None
    thinking: Optional[bool] = None


class StartSessionResponse(BaseModel):
    intro: str
    player_name: str
    tool_calls: list = []


class AutocompleteRequest(BaseModel):
    player_id: int
    user_input: str = ""  # Can be empty for suggestion
    llm_provider: Optional[str] = None
    model: Optional[str] = None
    thinking: Optional[bool] = None


class AutocompleteResponse(BaseModel):
    suggestion: str


class DiceRollRequest(BaseModel):
    player_id: int
    use_luck: bool = False  # If true, spend luck to reroll


class DiceRollResponse(BaseModel):
    roll: int
    luck_remaining: int
    is_critical: bool  # 20 = critical success, 1 = critical fail
    is_fumble: bool


class CombatStateResponse(BaseModel):
    in_combat: bool
    combat_id: Optional[int] = None
    status: Optional[str] = None
    description: Optional[str] = None
    player_team: list = []
    enemy_team: list = []


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
    
    story_manager = get_story_manager()
    
    # Check for active combat to add combat tag
    active_combat = db.query(CombatSession).filter(
        CombatSession.player_id == request.player_id,
        CombatSession.status == "active"
    ).first()
    
    # Build tags (include combat tag if in combat)
    message_tags = list(request.tags or [])
    if active_combat:
        message_tags.append(f"combat:{active_combat.id}")
    
    # Save player message
    story_manager.add_player_message(request.player_id, request.message, message_tags if message_tags else None)
    
    # Build rich session context with inventory, NPCs, items, quests
    session_context = build_session_context(db, request.player_id)
    
    try:
        gm = create_game_master(
            llm_provider=request.llm_provider,
            model=request.model,
            thinking=request.thinking,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    try:
        response, tool_calls = gm.chat(
            message=request.message,
            player_id=request.player_id,
            session_context=session_context
        )
        
        # Save GM response (re-check combat status - it might have ended during this turn)
        active_combat_after = db.query(CombatSession).filter(
            CombatSession.player_id == request.player_id,
            CombatSession.status == "active"
        ).first()

        # If combat was initiated during this turn, retroactively tag the triggering player message
        # so that end_combat compression can replace the full combat exchange.
        if (not active_combat) and active_combat_after:
            combat_tag = f"combat:{active_combat_after.id}"
            new_player_tags = list(message_tags or [])
            if combat_tag not in new_player_tags:
                new_player_tags.append(combat_tag)
            story_manager.update_message_tags(request.player_id, -1, new_player_tags)
        
        gm_tags = []
        if active_combat_after:
            gm_tags.append(f"combat:{active_combat_after.id}")

        # If combat ended this turn, the end_combat tool compresses tagged combat messages into
        # a single summary. In that case we do NOT persist this last GM response message,
        # otherwise the story would contain an extra post-combat message beyond the summary.
        ended_combat_this_turn = any(
            isinstance(tc, dict) and tc.get("tool") == "end_combat" for tc in (tool_calls or [])
        )
        if not ended_combat_this_turn:
            story_manager.add_gm_message(request.player_id, response, gm_tags if gm_tags else None)
        
        return ChatResponse(response=response, tool_calls=tool_calls)
    except Exception as e:
        logger.exception(f"Game Master error: {e}")
        raise HTTPException(status_code=500, detail=f"Game Master error: {str(e)}")


@router.post("/start-session", response_model=StartSessionResponse)
def start_game_session(request: StartSessionRequest, db: Session = Depends(get_db)):
    """
    Start a new game session for a player.
    
    Generates an intro based on player's backstory and current state.
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {request.player_id} not found")
    
    story_manager = get_story_manager()
    try:
        gm = create_game_master(
            llm_provider=request.llm_provider,
            model=request.model,
            thinking=request.thinking,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Build rich session context
    session_context = build_session_context(db, request.player_id)
    
    try:
        intro, tool_calls = gm.start_session(
            player_id=request.player_id,
            session_context=session_context
        )
        
        # Save intro as first GM message
        story_manager.add_gm_message(request.player_id, intro, tags=["session_start"])
        
        return StartSessionResponse(
            intro=intro,
            player_name=player.name,
            tool_calls=tool_calls
        )
    except Exception as e:
        logger.exception(f"Game Master error in start_session: {e}")
        raise HTTPException(status_code=500, detail=f"Game Master error: {str(e)}")


@router.post("/autocomplete", response_model=AutocompleteResponse)
def handle_autocomplete(request: AutocompleteRequest, db: Session = Depends(get_db)):
    """
    Generate or polish a player action based on context.
    
    - Empty input: suggests a contextually appropriate action
    - With input: polishes rough idea into narrative prose
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {request.player_id} not found")
    
    # Build rich session context (same as GM gets)
    session_context = build_session_context(db, request.player_id)
    
    try:
        suggestion = autocomplete_action(
            player_id=request.player_id,
            user_input=request.user_input,
            session_context=session_context,
            llm_provider=request.llm_provider,
            model=request.model,
            thinking=request.thinking,
        )
        return AutocompleteResponse(suggestion=suggestion)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=f"Autocomplete error: {str(e)}")


@router.post("/roll-dice", response_model=DiceRollResponse)
def roll_dice(request: DiceRollRequest, db: Session = Depends(get_db)):
    """
    Roll a d20 for the player's action.
    
    - Regular roll: Just returns the dice result
    - Use luck: Spends 1 luck point to reroll (requires luck > 0)
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == request.player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {request.player_id} not found")
    
    # Check if using luck for reroll
    if request.use_luck:
        if player.luck <= 0:
            raise HTTPException(status_code=400, detail="No luck remaining for reroll")
        player.luck -= 1
        db.commit()
        logger.info(f"Player {player.name} used luck to reroll. Luck remaining: {player.luck}")
    
    # Roll d20
    roll = random.randint(1, 20)
    
    return DiceRollResponse(
        roll=roll,
        luck_remaining=player.luck,
        is_critical=(roll == 20),
        is_fumble=(roll == 1)
    )


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


@router.get("/combat/{player_id}", response_model=CombatStateResponse)
def get_combat_state(player_id: int, db: Session = Depends(get_db)):
    """Get the current active combat state for a player.

    Used by the frontend to render a combat HUD (teams, HP bars, down/alive).
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")

    combat = db.query(CombatSession).filter(
        CombatSession.player_id == player_id,
        CombatSession.status == "active"
    ).first()

    if not combat:
        return CombatStateResponse(in_combat=False)

    def hydrate_member(member: dict) -> dict:
        if not isinstance(member, dict):
            return {}

        char_type = member.get("type")
        char_id = member.get("id")
        role = member.get("role")

        name = member.get("name")
        hp = member.get("hp", member.get("health"))
        max_hp = member.get("max_hp", member.get("max_health"))

        if char_type == "PC" and isinstance(char_id, int):
            pc = db.query(PlayerCharacter).filter(PlayerCharacter.id == char_id).first()
            if pc:
                name = pc.name
                hp = pc.health
                max_hp = pc.max_health
        elif char_type == "NPC" and isinstance(char_id, int):
            npc = db.query(NonPlayerCharacter).filter(NonPlayerCharacter.id == char_id).first()
            if npc:
                name = npc.name
                hp = npc.health
                max_hp = npc.max_health

        return {
            "type": char_type,
            "id": char_id,
            "name": name,
            "hp": int(hp) if isinstance(hp, (int, float)) else 0,
            "max_hp": int(max_hp) if isinstance(max_hp, (int, float)) and int(max_hp) > 0 else 1,
            "role": role,
        }

    def hydrate_team(team: list) -> list:
        hydrated = []
        for m in (team or []):
            hm = hydrate_member(m)
            if hm.get("type") and hm.get("id"):
                hydrated.append(hm)
        return hydrated

    return CombatStateResponse(
        in_combat=True,
        combat_id=combat.id,
        status=combat.status,
        description=combat.description,
        player_team=hydrate_team(combat.team_player),
        enemy_team=hydrate_team(combat.team_enemy)
    )


@router.get("/story/{player_id}")
def get_player_story(player_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """
    Get story messages for a player.
    
    Returns all messages in chronological order with their roles, tags, and timestamps.
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    
    story_manager = get_story_manager()
    messages = story_manager.get_messages(player_id, limit=limit)
    
    return {
        "player_id": player_id,
        "player_name": player.name,
        "message_count": len(messages),
        "messages": messages
    }


@router.delete("/story/{player_id}")
def clear_player_story(player_id: int, db: Session = Depends(get_db)):
    """
    Clear all story messages for a player (reset story).
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail=f"Player with id {player_id} not found")
    
    story_manager = get_story_manager()
    count = story_manager.clear_messages(player_id)
    
    return {
        "player_id": player_id,
        "messages_cleared": count
    }


class TTSRequest(BaseModel):
    text: str
    player_id: Optional[int] = None


def _build_npc_context(player_id: int, db: Session) -> list[dict]:
    """Look up NPCs at the player's current location + companions.

    Returns a list of dicts for the TTS Director:
        [{name, gender, voice, npc_id}, ...]
    """
    player = db.query(PlayerCharacter).filter(PlayerCharacter.id == player_id).first()
    if not player:
        return []

    location_id = None
    if hasattr(player, "current_location_id"):
        location_id = player.current_location_id

    # NPCs at the player's location + companions following this player
    from sqlalchemy import or_
    filters = []
    if location_id:
        filters.append(NonPlayerCharacter.location_id == location_id)
    filters.append(NonPlayerCharacter.following_player_id == player_id)

    if not filters:
        return []

    npcs = db.query(NonPlayerCharacter).filter(or_(*filters)).all()

    context = []
    for npc in npcs:
        # Infer gender from description/name heuristics or default to "male"
        gender = "male"
        desc = (npc.description or "").lower()
        name_lower = (npc.name or "").lower()
        female_hints = ("she ", "her ", "woman", "female", "lady", "queen",
                        "princess", "duchess", "maiden", "girl", "wife",
                        "barmaid", "waitress", "priestess", "sorceress")
        if any(h in desc for h in female_hints) or any(h in name_lower for h in female_hints):
            gender = "female"

        context.append({
            "name": npc.name,
            "gender": gender,
            "voice": npc.voice,
            "npc_id": npc.id,
        })
    return context


@router.post("/tts")
def text_to_speech(request: TTSRequest, db: Session = Depends(get_db)):
    """Convert Game Master text to speech using Gemini TTS (streaming).

    Returns a stream of length-prefixed WAV chunks.  Each chunk is:
      4-byte big-endian uint32 (length) + WAV bytes

    The frontend reads chunks and starts playback as soon as the first
    one arrives, giving low time-to-first-audio.

    When player_id is provided, NPCs at the player's location are used
    as speaker context.  Auto-assigned voices are persisted to the DB.

    Pipeline per chunk:
      GM text → TTS Director LLM (once) → micro-batch → Gemini TTS → WAV
    """
    if not is_tts_available():
        raise HTTPException(status_code=503, detail="TTS not available: GEMINI_API_KEY not configured")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # Build NPC voice context if player_id provided
    npc_context = None
    if request.player_id:
        npc_context = _build_npc_context(request.player_id, db)

    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        generate_tts_stream(
            request.text,
            npc_context=npc_context,
            player_id=request.player_id,
            db=db,
        ),
        media_type="application/octet-stream",
        headers={"X-TTS-Format": "chunked-wav"},
    )


@router.get("/providers")
def get_llm_providers():
    """Return LLM providers that have an API key configured.

    The frontend uses this to populate the provider selector dropdown.
    Only providers with a valid key in .env are returned.
    """
    providers = get_available_providers()
    return {
        "default": settings.DEFAULT_LLM_PROVIDER,
        "providers": providers,
        "tts_available": is_tts_available(),
    }


# ============= Long-Term Memory Endpoints =============
# TODO: Refactor memory system to work with new story_messages structure
# These endpoints are deprecated until memory system is updated
