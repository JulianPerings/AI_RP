"""
Autocomplete handler for player action input.

Provides context-aware suggestions or polishes rough input into narrative prose.
Uses the same tools as the Game Master for database queries.
"""
import logging
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from config import settings
from .tools import get_player_info, get_location_info, get_npc_info, list_races
from .story_manager import get_story_manager
from .prompts import AUTOCOMPLETE_PROMPT

logger = logging.getLogger(__name__)


# Subset of tools useful for autocomplete context gathering
AUTOCOMPLETE_TOOLS = [
    get_player_info,
    get_location_info,
    get_npc_info,
    list_races,
]


def autocomplete_action(
    player_id: int,
    user_input: str = "",
    session_context: Optional[dict] = None,
    llm_provider: Optional[str] = None
) -> str:
    """
    Generate or polish a player action based on context.
    
    Args:
        player_id: The player's ID
        user_input: Rough idea from player (can be empty)
        session_context: Pre-built session context from context_builder
    
    Returns:
        Polished action text
    """
    # Build player info string from context
    player_info = "Unknown player"
    if session_context:
        player_info = f"{session_context.get('player_name', 'Unknown')}, "
        player_info += f"{session_context.get('player_class', 'Adventurer')} "
        player_info += f"(Level {session_context.get('player_level', 1)})"
        player_info += f"\nHealth: {session_context.get('player_health', 0)}/{session_context.get('player_max_health', 100)}"
        player_info += f", Gold: {session_context.get('player_gold', 0)}"
    
    # Build rich context string (similar to GM context)
    context_parts = []
    
    if session_context:
        # Location
        if session_context.get('location_name'):
            context_parts.append(f"**Location**: {session_context['location_name']}")
            if session_context.get('location_description'):
                context_parts.append(f"  {session_context['location_description'][:200]}")
        
        # Region
        if session_context.get('region_name'):
            context_parts.append(f"**Region**: {session_context['region_name']} ({session_context.get('region_climate', 'temperate')} climate)")
            if session_context.get('region_danger'):
                context_parts.append(f"  Danger level: {session_context['region_danger']}")
        
        # NPCs present (all of them)
        if session_context.get('npcs_here'):
            npc_list = []
            for npc in session_context['npcs_here']:
                npc_list.append(f"{npc.get('name', 'Unknown')} ({npc.get('type', 'unknown')}, {npc.get('behavior', 'passive')})")
            context_parts.append(f"**NPCs present**: {', '.join(npc_list)}")
        
        # Companions
        if session_context.get('companions'):
            comp_names = [c.get('name', 'Unknown') for c in session_context['companions']]
            context_parts.append(f"**Companions**: {', '.join(comp_names)}")
        
        # Items on ground
        if session_context.get('items_here'):
            item_names = [i.get('name', 'Unknown') for i in session_context['items_here'][:5]]
            context_parts.append(f"**Items nearby**: {', '.join(item_names)}")
        
        # Active quests
        if session_context.get('active_quests'):
            quest_titles = [q.get('title', 'Unknown') for q in session_context['active_quests'][:3]]
            context_parts.append(f"**Active quests**: {', '.join(quest_titles)}")
        
        # Inventory highlights (equipped items)
        if session_context.get('inventory'):
            equipped = [i for i in session_context['inventory'] if '[EQUIPPED]' in i]
            if equipped:
                context_parts.append(f"**Equipped**: {', '.join(equipped[:3])}")
    
    context_str = "\n".join(context_parts) if context_parts else "No context available"
    
    # Get last 5 messages from story
    story_manager = get_story_manager()
    messages = story_manager.get_messages(player_id, limit=10)
    
    recent_messages = []
    for msg in messages[-5:]:  # Last 5 messages
        role = "GM" if msg.get("role") == "gm" else "Player"
        content = msg.get("content", "")[:300]  # Truncate long messages
        recent_messages.append(f"**{role}**: {content}")
    
    last_messages_str = "\n\n".join(recent_messages) if recent_messages else "No previous messages"
    
    # Format prompt
    prompt = AUTOCOMPLETE_PROMPT.format(
        player_info=player_info,
        context=context_str,
        last_gm_message=last_messages_str,
        user_input=user_input or "(empty - suggest an action)"
    )
    
    try:
        provider = (llm_provider or settings.DEFAULT_LLM_PROVIDER or "openai").lower()
        if provider not in {"openai", "xai", "gemini", "kimi", "claude"}:
            raise ValueError(f"Unsupported llm_provider: {provider}")

        api_key = (settings.OPENAI_API_KEY or "").strip()
        base_url = None
        model_name = settings.OPENAI_MODEL

        if provider == "gemini":
            raise ValueError("llm_provider 'gemini' is not implemented")
        if provider == "kimi":
            raise ValueError("llm_provider 'kimi' is not implemented")
        if provider == "claude":
            raise ValueError("llm_provider 'claude' is not implemented")

        if provider == "xai":
            api_key = (settings.XAI_API_KEY or "").strip()
            if not api_key:
                raise ValueError("XAI_API_KEY is required when llm_provider is 'xai'")
            base_url = (settings.XAI_BASE_URL or "").strip() or None
            model_name = settings.XAI_MODEL or model_name

        llm_kwargs = {
            "model": model_name,
            "api_key": api_key,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.AUTOCOMPLETE_MAX_TOKENS,
        }
        if provider == "openai":
            llm_kwargs["reasoning_effort"] = settings.LLM_REASONING_EFFORT
        if base_url:
            llm_kwargs["base_url"] = base_url

        llm = ChatOpenAI(
            **llm_kwargs
        )
        
        logger.debug(f"[AUTOCOMPLETE] Sending prompt to LLM, user_input='{user_input}'")
        response = llm.invoke([HumanMessage(content=prompt)])
        suggestion = response.content.strip() if response.content else ""
        logger.debug(f"[AUTOCOMPLETE] Generated suggestion ({len(suggestion)} chars)")
        
        # Clean up any quotes that might wrap the response
        if suggestion.startswith('"') and suggestion.endswith('"'):
            suggestion = suggestion[1:-1]
        if suggestion.startswith("'") and suggestion.endswith("'"):
            suggestion = suggestion[1:-1]
        
        return suggestion
        
    except Exception as e:
        logger.exception(f"Autocomplete error: {e}")
        raise
