import logging
from typing import Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from config import settings
from .state import GameState
from .tools import get_game_tools
from .chat_history_manager import get_history_manager

logger = logging.getLogger(__name__)


GAME_MASTER_SYSTEM_PROMPT = """You are the Game Master (GM) for an immersive fantasy RPG. Your role is to:

1. **Narrate the World**: Describe scenes, environments, and events with vivid, atmospheric detail.
2. **Control NPCs**: Give voice to non-player characters based on their personality traits, faction, and relationship with the player.
3. **Manage Game State**: Use your tools to track and modify player stats, inventory, relationships, and quests.
4. **Create Drama**: Introduce challenges, moral dilemmas, and meaningful choices.
5. **Be Fair but Challenging**: The world has consequences. Combat can be deadly. Choices matter.

## Your Tools
You have access to tools that let you:
- Query player info, locations, NPCs, and relationships
- Modify player health, gold, and inventory
- Create and manage quests
- Update relationships between characters
- Move players between locations
- Search past session memories for long-term continuity

## Item Uniqueness
When creating items, add minor buffs/flaws to make each instance unique:
- **Buffs**: Small advantages like "sharp_edge: +2 damage", "lightweight: easier to wield", "heirloom: +1 morale"
- **Flaws**: Minor drawbacks like "rusty: -1 durability per use", "chipped: less effective", "heavy: harder to carry"
- Keep descriptions readable and meaningful - the system will interpret them narratively
- Items from backstories should reflect their history (e.g., father's sword = heirloom buff)

## Guidelines
- ALWAYS use tools to check current game state before narrating
- Keep responses immersive - describe actions and outcomes narratively
- When the player attempts something risky, use tools to apply consequences
- NPCs should react based on their relationship values and personality
- Track relationship changes when meaningful interactions occur
- Create quests organically based on player interactions and world events
- Mention item buffs/flaws in narrative when relevant (e.g., "your father's well-balanced blade")

## Combat
- Describe combat cinematically
- Use update_player_health for damage
- Consider NPC behavior states (passive, defensive, aggressive, hostile, protective)

## Tone
Write in second person ("You see...", "You hear..."). Be descriptive but concise.
Balance serious moments with lighter ones. Make the world feel alive and reactive.

Current session context will be provided with each message."""


class GameMasterAgent:
    """LangGraph-based Game Master agent for the RPG."""
    
    def __init__(self, model_name: Optional[str] = None, reasoning_effort: str = "medium"):
        self.model_name = model_name or settings.OPENAI_MODEL
        self.reasoning_effort = reasoning_effort
        self.tools = get_game_tools()
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.8,
            model_kwargs={"reasoning_effort": reasoning_effort}
        ).bind_tools(self.tools)
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _should_continue(self, state: GameState) -> str:
        """Determine if the agent should continue or end."""
        messages = state["messages"]
        last_message = messages[-1]
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    def _call_model(self, state: GameState) -> dict:
        """Call the LLM with current state."""
        messages = state["messages"]
        
        system_content = GAME_MASTER_SYSTEM_PROMPT
        if state.get("session_context"):
            ctx = state["session_context"]
            system_content += f"\n\n## Current Session\n- Player ID: {state.get('player_id')}"
            if ctx.get("player_name"):
                system_content += f"\n- Player Name: {ctx['player_name']}"
            if ctx.get("location"):
                system_content += f"\n- Current Location: {ctx['location']}"
        
        messages_with_system = [SystemMessage(content=system_content)] + list(messages)
        response = self.llm.invoke(messages_with_system)
        
        # Log tool calls if any
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                logger.info(f"[TOOL CALL] {tc['name']}({tc['args']})")
        
        return {"messages": [response]}
    
    def _log_tool_results(self, state: GameState) -> dict:
        """Wrapper to log tool results."""
        tool_node = ToolNode(self.tools)
        result = tool_node.invoke(state)
        
        # Log tool results
        for msg in result.get("messages", []):
            if isinstance(msg, ToolMessage):
                logger.info(f"[TOOL RESULT] {msg.name}: {msg.content[:200]}..." if len(str(msg.content)) > 200 else f"[TOOL RESULT] {msg.name}: {msg.content}")
        
        return result
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(GameState)
        
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", self._log_tool_results)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "tools": "tools",
                END: END
            }
        )
        
        workflow.add_edge("tools", "agent")
        
        return workflow.compile(checkpointer=self.memory)
    
    def chat(self, message: str, player_id: int, session_id: str, 
             session_context: Optional[dict] = None) -> tuple[str, List[dict]]:
        """Send a message to the Game Master and get a response.
        
        Returns:
            Tuple of (response_text, tool_calls_made)
        """
        config = {"configurable": {"thread_id": session_id}}
        history_manager = get_history_manager()
        
        # Ensure session exists in database
        history_manager.get_or_create_session(session_id, player_id)
        
        # Save incoming human message
        history_manager.save_human_message(session_id, message)
        
        # Load recent history for context
        history_messages = history_manager.get_langchain_messages(session_id, limit=10)
        
        # Build initial state with history context
        initial_state = {
            "messages": history_messages[:-1] + [HumanMessage(content=message)] if len(history_messages) > 1 else [HumanMessage(content=message)],
            "player_id": player_id,
            "current_location_id": session_context.get("location_id") if session_context else None,
            "session_context": session_context or {}
        }
        
        logger.info(f"[CHAT] Session {session_id} | Player {player_id} | History: {len(history_messages)} msgs | Message: {message[:100]}...")
        
        # Track how many messages we started with
        initial_message_count = len(initial_state["messages"])
        
        result = self.graph.invoke(initial_state, config)
        
        # Collect tool calls ONLY from NEW messages (after initial state)
        tool_calls_made = []
        new_messages = result["messages"][initial_message_count:]
        for msg in new_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_made.append({"tool": tc["name"], "args": tc["args"]})
        
        final_message = result["messages"][-1]
        response_text = final_message.content if isinstance(final_message, AIMessage) else str(final_message)
        
        # Save AI response to database
        history_manager.save_ai_message(session_id, response_text, tool_calls_made if tool_calls_made else None)
        
        logger.info(f"[RESPONSE] {len(tool_calls_made)} tool calls | Response length: {len(response_text)}")
        
        return response_text, tool_calls_made
    
    def start_session(self, player_id: int, session_id: str) -> tuple[str, List[dict]]:
        """Start a new game session with an introductory message.
        
        Analyzes the player's description/backstory and spawns relevant items and NPCs.
        
        Returns:
            Tuple of (response_text, tool_calls_made)
        """
        intro_prompt = f"""A player (ID: {player_id}) is starting a new session. 

First, use get_player_info to learn about this character.

IMPORTANT - Backstory Setup:
If the player has a description/backstory that mentions:
- **Items they own**: Use create_item_for_player to give them those items with unique buffs/flaws
  Example: "carries his father's sword" → create_item_for_player with buffs=["heirloom: +1 morale", "well-balanced"]
- **NPCs they know**: Use create_npc to spawn those characters at appropriate locations
  Example: "best friend Marcus" → create_npc for Marcus with appropriate personality
- **Relationships**: Use update_relationship to establish those connections

After setup:
1. Describe their current location
2. Mention any active quests
3. Set the scene and invite them to begin

Make items feel unique with minor buffs/flaws that reflect their history."""
        
        return self.chat(intro_prompt, player_id, session_id, {"player_name": None})


_game_master_instance: Optional[GameMasterAgent] = None


def create_game_master() -> GameMasterAgent:
    """Create or return the singleton Game Master agent."""
    global _game_master_instance
    if _game_master_instance is None:
        _game_master_instance = GameMasterAgent()
    return _game_master_instance
