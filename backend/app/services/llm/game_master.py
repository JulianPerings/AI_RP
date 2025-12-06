"""Game Master service for managing AI-driven gameplay."""

from typing import List, Dict, Optional
from app.services.llm.client import llm_client
from app.services.llm.prompts import (
    SYSTEM_PROMPT,
    NPC_DIALOGUE_PROMPT,
    QUEST_GENERATION_PROMPT,
    WORLD_DESCRIPTION_PROMPT,
)
from app.core.logging import log


class GameMasterService:
    """Service for AI-driven game master interactions."""

    def __init__(self):
        """Initialize the Game Master service."""
        self.llm = llm_client

    async def generate_response(
        self,
        player_message: str,
        character_name: str,
        level: int,
        current_location: str,
        active_quests: List[str],
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a game master response to player input.
        
        Args:
            player_message: Player's message or action
            character_name: Player's character name
            level: Player's level
            current_location: Current game location
            active_quests: List of active quest titles
            conversation_history: Previous conversation messages
            
        Returns:
            Game master's response
        """
        # Build system prompt with context
        system_prompt = SYSTEM_PROMPT.format(
            character_name=character_name,
            level=level,
            current_location=current_location,
            active_quests=", ".join(active_quests) if active_quests else "None"
        )

        if conversation_history:
            # Continue existing conversation
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": player_message})
            
            response = await self.llm.chat_completion(messages)
        else:
            # Start new conversation
            response = await self.llm.generate_with_system_prompt(
                system_prompt=system_prompt,
                user_message=player_message
            )

        log.info(f"Generated GM response for player action: {player_message[:50]}...")
        return response

    async def generate_npc_dialogue(
        self,
        npc_name: str,
        npc_role: str,
        npc_background: str,
        player_message: str,
        character_name: str,
        location: str,
    ) -> str:
        """
        Generate NPC dialogue in response to player.
        
        Args:
            npc_name: NPC's name
            npc_role: NPC's role (merchant, guard, etc.)
            npc_background: NPC's background/personality
            player_message: What the player said
            character_name: Player's character name
            location: Current location
            
        Returns:
            NPC's response
        """
        prompt = NPC_DIALOGUE_PROMPT.format(
            npc_name=npc_name,
            npc_role=npc_role,
            npc_background=npc_background,
            player_message=player_message,
            character_name=character_name,
            location=location,
        )

        response = await self.llm.generate_with_system_prompt(
            system_prompt="You are a helpful NPC in a fantasy RPG.",
            user_message=prompt,
            temperature=0.8,  # More creative for NPC personality
        )

        log.info(f"Generated NPC dialogue for {npc_name}")
        return response

    async def generate_quest(
        self,
        quest_type: str,
        level: int,
        location: str,
        context: str = "",
    ) -> Dict[str, any]:
        """
        Generate a new quest using LLM.
        
        Args:
            quest_type: Type of quest (main, side, daily)
            level: Player's level
            location: Current location
            context: Additional context
            
        Returns:
            Quest data dictionary
        """
        prompt = QUEST_GENERATION_PROMPT.format(
            quest_type=quest_type,
            level=level,
            location=location,
            context=context or "No additional context"
        )

        response = await self.llm.generate_with_system_prompt(
            system_prompt="You are a quest designer for a fantasy RPG. Generate structured quest data.",
            user_message=prompt,
            temperature=0.7,
        )

        # TODO: Parse structured output using instructor or JSON mode
        # For now, return raw response
        log.info(f"Generated {quest_type} quest for level {level}")
        
        return {
            "raw_response": response,
            "quest_type": quest_type,
            "level": level,
        }

    async def describe_location(
        self,
        location: str,
        time_of_day: str = "day",
        weather: str = "clear",
    ) -> str:
        """
        Generate a description of a location.
        
        Args:
            location: Location name
            time_of_day: Time of day
            weather: Weather conditions
            
        Returns:
            Location description
        """
        context = f"Time: {time_of_day}, Weather: {weather}"
        prompt = WORLD_DESCRIPTION_PROMPT.format(location=location) + f"\n\n{context}"

        response = await self.llm.generate_with_system_prompt(
            system_prompt="You are a world-builder for a fantasy RPG. Create vivid location descriptions.",
            user_message=prompt,
            temperature=0.8,
        )

        log.info(f"Generated description for location: {location}")
        return response


# Global Game Master service instance
game_master = GameMasterService()
