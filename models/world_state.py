"""World state — the top-level container for all game state."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from models.character import Character
from models.npc import NPC
from models.item import Item
from models.relationship import Relationship


class WorldState(BaseModel):
    """Everything about the current game world that must be persisted."""

    # Campaign metadata
    campaign_name: str = ""
    campaign_file: str = ""

    # Player
    player: Character = Field(default_factory=Character)

    # NPCs indexed by id
    npcs: dict[str, NPC] = Field(default_factory=dict)

    # Items registry (all known items, indexed by id)
    items: dict[str, Item] = Field(default_factory=dict)

    # Relationships indexed by npc_id
    relationships: dict[str, Relationship] = Field(default_factory=dict)

    # World tracking
    current_location: str = ""
    visited_locations: list[str] = Field(default_factory=list)
    quest_flags: dict[str, bool] = Field(default_factory=dict)
    narrative_log: list[str] = Field(default_factory=list)
    turn_count: int = 0

    # GM conversation history (kept trimmed)
    gm_history: list[dict[str, str]] = Field(default_factory=list)
    max_gm_history: int = 30

    def add_narrative(self, text: str) -> None:
        """Append a line to the narrative log and increment the turn counter."""
        self.narrative_log.append(text)
        self.turn_count += 1

    def trim_gm_history(self) -> None:
        """Keep only the most recent messages in GM history."""
        if len(self.gm_history) > self.max_gm_history:
            self.gm_history = self.gm_history[-self.max_gm_history :]

    # ------------------------------------------------------------------
    # Factory: build world state from a campaign YAML
    # ------------------------------------------------------------------

    @classmethod
    def from_campaign(cls, campaign_path: str | Path) -> "WorldState":
        """Load a campaign YAML and construct initial world state."""
        path = Path(campaign_path)
        with open(path, "r") as f:
            data = yaml.safe_load(f)

        world = cls(
            campaign_name=data.get("name", path.stem),
            campaign_file=str(path),
        )

        world.current_location = data.get("starting_location", "")

        # Items registry (must be populated before player inventory)
        for item_data in data.get("items", []):
            item = Item(**item_data)
            world.items[item.id] = item

        # Player defaults from campaign
        player_data = data.get("player", {})
        world.player = Character(
            name=player_data.get("name", "Adventurer"),
            max_hp=player_data.get("max_hp", 20),
            current_hp=player_data.get("max_hp", 20),
            current_location=data.get("starting_location", ""),
            gold=player_data.get("starting_gold", 0),
        )

        # Apply starting inventory
        for item_id in player_data.get("starting_items", []):
            if item_id in world.items:
                world.player.inventory.append(item_id)

        # NPCs
        for npc_data in data.get("npcs", []):
            npc = NPC(**npc_data)
            world.npcs[npc.id] = npc
            # Initialize neutral relationship
            world.relationships[npc.id] = Relationship(npc_id=npc.id)

        # Quest flags
        for quest in data.get("quests", []):
            flag_id = quest.get("id", quest.get("name", ""))
            world.quest_flags[flag_id] = False

        return world
