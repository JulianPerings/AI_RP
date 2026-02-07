"""Structured action and result objects used between agents and services."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ActionType(str, Enum):
    NARRATE = "narrate"
    NPC_DIALOGUE = "npc_dialogue"
    COMBAT_ATTACK = "combat_attack"
    COMBAT_DEFEND = "combat_defend"
    SKILL_CHECK = "skill_check"
    UPDATE_INVENTORY = "update_inventory"
    UPDATE_RELATIONSHIP = "update_relationship"
    MOVE = "move"
    REST = "rest"
    EXAMINE = "examine"
    CUSTOM = "custom"


class Action(BaseModel):
    """A structured action emitted by the GM agent."""

    action_type: ActionType
    target: str = ""  # NPC id, item id, location id, etc.
    details: dict[str, Any] = Field(default_factory=dict)
    raw_player_input: str = ""


class ActionResult(BaseModel):
    """The outcome of processing an Action."""

    success: bool = True
    narrative: str = ""  # text to show the player
    mechanical_summary: str = ""  # e.g. "Rolled 7 + 3 STR = 10 vs DC 8 → hit, 5 dmg"
    state_changes: dict[str, Any] = Field(default_factory=dict)
    follow_up_actions: list[Action] = Field(default_factory=list)
