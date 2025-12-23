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


GAME_MASTER_SYSTEM_PROMPT = """You are the Game Master for an immersive fantasy RPG.

## Core Loop
1. Use tools to query current state (player, location, NPCs, relationships)
2. Narrate the scene in second person ("You see...")
3. Use tools to apply consequences (damage, gold, relationship changes)
4. Create meaningful story events when opportunities arise
5. Give enemies in fight scenes chances to retaliate

## Tools Available
- Query: player info, locations, NPCs, items, relationships, memories
- Modify: health, gold, inventory, quests, relationships, NPC state
- Create: items (with buffs/flaws), NPCs, quests, locations

## Items - Templates and Instances
Templates = generic blueprints (e.g., "Hammer", "Sword", "Potion")
Instances = specific items with custom_name, buffs, flaws

WORKFLOW to create items:
1. list_item_templates(search="\{keyword(Name|Type)\}") → find existing template for Name or templates for Type
2. If none: create template first with generic_name
3. create the specific item with link to generic template and custom name and unique buffs/flaws

Buff/flaw examples: "sharp: +1 damage", "heirloom: +1 morale", "rusty: -1 durability", "heavy: +1 weight"

## NPCs
React based on relationship values (-100 to 100) and behavior states:
passive, defensive, aggressive, hostile, protective

## Combat
- elaborate fight scenes
- intercept player actions to create opportunities for conflict if they are unreasonable
- give players oportunities to succeed if they are creative 

## Style
- Vivid but concise descriptions
- Consequences matter - combat can kill
- Balance drama with lighter moments"""


class GameMasterAgent:
    """LangGraph-based Game Master agent for the RPG."""
    
    def __init__(self, model_name: Optional[str] = None, reasoning_effort: str = "low"):
        self.model_name = model_name or settings.OPENAI_MODEL
        self.reasoning_effort = reasoning_effort
        self.tools = get_game_tools()
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.8,
            reasoning_effort=reasoning_effort
        ).bind_tools(self.tools)
        # Separate LLM for summarization (no tools needed)
        self.summary_llm = ChatOpenAI(
            model=self.model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.3
        )
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _generate_summary(self, messages_text: str) -> tuple[str, str, str]:
        """Generate a summary, title, and keywords for archived messages.
        
        Returns:
            Tuple of (summary, title, keywords)
        """
        prompt = f"""Summarize this RPG session conversation concisely. Extract:
1. A short title (max 50 chars)
2. A brief summary (3-5 sentences capturing key events)
3. Keywords (comma-separated: character names, locations, items, events)

Conversation:
{messages_text}

Respond in this exact format:
TITLE: <title>
SUMMARY: <summary>
KEYWORDS: <keywords>"""
        
        try:
            response = self.summary_llm.invoke([HumanMessage(content=prompt)])
            content = response.content
            
            # Parse response
            title = ""
            summary = ""
            keywords = ""
            
            for line in content.split("\n"):
                if line.startswith("TITLE:"):
                    title = line[6:].strip()[:200]
                elif line.startswith("SUMMARY:"):
                    summary = line[8:].strip()
                elif line.startswith("KEYWORDS:"):
                    keywords = line[9:].strip()
            
            return summary or content, title or "Session Archive", keywords
        except Exception as e:
            logger.error(f"[SUMMARY] Failed to generate: {e}")
            return "Session archived", "Session Archive", ""
    
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
        
        # Add session context
        if state.get("session_context"):
            ctx = state["session_context"]
            system_content += f"\n\n## Current Session\n- Player ID: {state.get('player_id')}"
            if ctx.get("player_name"):
                system_content += f"\n- Player Name: {ctx['player_name']}"
            if ctx.get("location"):
                system_content += f"\n- Current Location: {ctx['location']}"
        
        # Add previous session summaries for long-term memory
        if state.get("previous_summaries"):
            system_content += "\n\n## Previous Session Memories"
            for summary in state["previous_summaries"]:
                if summary.get("title"):
                    system_content += f"\n### {summary['title']}"
                if summary.get("summary"):
                    system_content += f"\n{summary['summary']}"
                if summary.get("keywords"):
                    system_content += f"\n(Keywords: {summary['keywords']})"
        
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
        
        # Check if we need to archive old messages
        history_manager.check_and_archive_if_needed(
            player_id, session_id, 
            summarize_callback=self._generate_summary
        )
        
        # Load recent history for context
        history_messages = history_manager.get_langchain_messages(
            session_id, limit=settings.MIN_MESSAGES_IN_SESSION
        )
        
        # Load previous session summaries for long-term memory
        previous_summaries = history_manager.get_previous_summaries(player_id)
        
        # Build initial state with history context
        initial_state = {
            "messages": history_messages[:-1] + [HumanMessage(content=message)] if len(history_messages) > 1 else [HumanMessage(content=message)],
            "player_id": player_id,
            "current_location_id": session_context.get("location_id") if session_context else None,
            "session_context": session_context or {},
            "previous_summaries": previous_summaries
        }
        
        logger.info(f"[CHAT] Session {session_id} | Player {player_id} | History: {len(history_messages)} msgs | Summaries: {len(previous_summaries)} | Message: {message[:100]}...")
        
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
- **Items they own**: give them those items with your tool calls
  Example: "carries his father's sword" → create template for sword if not already created, then create his sword with exemplary buffs/flaws
- **NPCs they know**: Use create_npc to spawn those characters at appropriate locations
  Example: "best friend Marcus" → create_npc for Marcus with appropriate personality
- **Relationships**: Use update_relationship to establish those connections

After setup:
1. Describe their current location
2. Mention any active quests if they have one
3. Set the scene and wait for their move
"""
        
        return self.chat(intro_prompt, player_id, session_id, {"player_name": None})


_game_master_instance: Optional[GameMasterAgent] = None


def create_game_master() -> GameMasterAgent:
    """Create or return the singleton Game Master agent."""
    global _game_master_instance
    if _game_master_instance is None:
        _game_master_instance = GameMasterAgent()
    return _game_master_instance
