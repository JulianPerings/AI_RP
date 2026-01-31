import logging
import uuid
import json
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from config import settings
from .state import GameState
from .tools import get_game_tools
from .story_manager import get_story_manager
from .prompts import GAME_MASTER_SYSTEM_PROMPT, format_session_start
from .context_builder import format_context_for_prompt

logger = logging.getLogger(__name__)


class GameMasterAgent:
    """LangGraph-based Game Master agent for the RPG."""

    def _normalize_message_content(self, msg: Any) -> None:
        if not hasattr(msg, "content"):
            return
        content = getattr(msg, "content")

        if isinstance(content, str):
            if content.strip():
                return
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                msg.content = "(tool call)"
                return
            msg.content = "(empty)"
            return

        if content is None:
            msg.content = "(empty)"
            return

        try:
            msg.content = json.dumps(content, ensure_ascii=False)
        except TypeError:
            msg.content = str(content)

        if not (msg.content or "").strip():
            msg.content = "(empty)"
    
    def __init__(self, model_name: Optional[str] = None, llm_provider: Optional[str] = None):
        provider = (llm_provider or settings.DEFAULT_LLM_PROVIDER or "openai").lower()
        if provider not in {"openai", "xai", "gemini", "kimi", "claude"}:
            raise ValueError(f"Unsupported llm_provider: {provider}")

        self.llm_provider = provider

        api_key = (settings.OPENAI_API_KEY or "").strip()
        base_url = None

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
            self.model_name = (settings.XAI_MODEL or "").strip() or settings.OPENAI_MODEL
        else:
            self.model_name = (model_name or "").strip() or settings.OPENAI_MODEL

        self.tools = get_game_tools()

        llm_kwargs = {
            "model": self.model_name,
            "api_key": api_key,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        }
        if provider == "openai":
            llm_kwargs["reasoning_effort"] = settings.LLM_REASONING_EFFORT
        if base_url:
            llm_kwargs["base_url"] = base_url

        self.llm = ChatOpenAI(**llm_kwargs).bind_tools(self.tools)

        # Separate LLM for summarization (no tools needed)
        summary_kwargs = {
            "model": self.model_name,
            "api_key": api_key,
            "temperature": settings.SUMMARY_LLM_TEMPERATURE,
            "max_tokens": settings.SUMMARY_LLM_MAX_TOKENS,
        }
        if base_url:
            summary_kwargs["base_url"] = base_url

        self.summary_llm = ChatOpenAI(**summary_kwargs)
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _generate_summary(self, messages_text: str) -> tuple[str, str, str]:
        """Generate a summary, title, and keywords for archived messages.
        
        Returns:
            Tuple of (summary, title, keywords)
        """
        prompt = format_archive_summary(messages_text)
        
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

        for m in messages:
            self._normalize_message_content(m)
        
        system_content = GAME_MASTER_SYSTEM_PROMPT
        
        # Add rich session context (inventory, NPCs, items, quests)
        if state.get("session_context"):
            context_str = format_context_for_prompt(state["session_context"])
            system_content += f"\n\n{context_str}"
        
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

        for msg in result.get("messages", []):
            if isinstance(msg, ToolMessage):
                if not isinstance(msg.content, str):
                    try:
                        msg.content = json.dumps(msg.content, ensure_ascii=False)
                    except TypeError:
                        msg.content = str(msg.content)
                if not (msg.content or "").strip():
                    msg.content = "(empty)"
        
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
    
    def chat(self, message: str, player_id: int,
             session_context: Optional[dict] = None) -> tuple[str, List[dict]]:
        """Send a message to the Game Master and get a response.
        
        Returns:
            Tuple of (response_text, tool_calls_made)
        """
        # Use unique thread_id per invocation to prevent tool call accumulation
        config = {
            "configurable": {"thread_id": f"{player_id}-{uuid.uuid4().hex[:8]}"},
            "recursion_limit": 50
        }
        
        story_manager = get_story_manager()
        
        # Load recent story messages for context
        recent_messages = story_manager.get_context_messages(player_id, limit=20)
        
        # Convert to LangChain messages
        history_messages = []
        for msg in recent_messages:
            if msg["role"] == "player":
                history_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "gm":
                history_messages.append(AIMessage(content=msg["content"]))
        
        # Build initial state with history context
        initial_state = {
            "messages": history_messages + [HumanMessage(content=message)],
            "player_id": player_id,
            "current_location_id": session_context.get("location_id") if session_context else None,
            "session_context": session_context or {},
            "previous_summaries": []  # TODO: Implement new memory system
        }
        
        logger.info(f"[CHAT] Player {player_id} | History: {len(history_messages)} msgs | Message: {message[:100]}...")
        
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
        
        logger.info(f"[RESPONSE] {len(tool_calls_made)} tool calls | Response length: {len(response_text)}")
        
        return response_text, tool_calls_made
    
    def start_session(self, player_id: int,
                       session_context: Optional[dict] = None) -> tuple[str, List[dict]]:
        """Start a new game session with an introductory message.
        
        Analyzes the player's description/backstory and spawns relevant items and NPCs.
        
        Returns:
            Tuple of (response_text, tool_calls_made)
        """
        intro_prompt = format_session_start(player_id)
        return self.chat(intro_prompt, player_id, session_context)


_game_master_instances: Dict[str, GameMasterAgent] = {}


def create_game_master(llm_provider: Optional[str] = None) -> GameMasterAgent:
    provider = (llm_provider or settings.DEFAULT_LLM_PROVIDER or "openai").lower()
    if provider not in {"openai", "xai", "gemini", "kimi", "claude"}:
        raise ValueError(f"Unsupported llm_provider: {provider}")
    if provider not in _game_master_instances:
        _game_master_instances[provider] = GameMasterAgent(llm_provider=provider)
    return _game_master_instances[provider]
