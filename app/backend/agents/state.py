from typing import Annotated, TypedDict, List, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GameState(TypedDict):
    """State for the Game Master agent graph."""
    messages: Annotated[List[BaseMessage], add_messages]
    player_id: int
    current_location_id: Optional[int]
    session_context: dict
    previous_summaries: Optional[List[dict]]  # Summaries from archived sessions
