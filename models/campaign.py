"""Campaign schema — defines the structure of a campaign YAML file.

These models are used both for validation and as a reference for the
Campaign Creator agent when generating new campaigns.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CampaignNPC(BaseModel):
    """NPC definition within a campaign file."""

    id: str
    name: str
    title: str = ""
    description: str = ""
    personality: str = ""
    location: str = ""
    greeting: str = ""
    topics: list[str] = Field(default_factory=list)
    merchant: bool = False
    shop_items: list[str] = Field(default_factory=list)
    quest_giver: bool = False
    is_hostile: bool = False
    max_hp: int = 10
    strength: int = 5
    agility: int = 5
    mind: int = 5
    charisma: int = 5


class CampaignItem(BaseModel):
    """Item definition within a campaign file."""

    id: str
    name: str
    description: str = ""
    item_type: str = "misc"
    value: int = 0
    damage: int = 0
    armor_bonus: int = 0
    heal_amount: int = 0
    equippable: bool = False
    consumable: bool = False
    quest_item: bool = False


class CampaignLocation(BaseModel):
    """A location in the campaign world."""

    id: str
    name: str
    description: str = ""
    connections: list[str] = Field(default_factory=list)  # IDs of connected locations
    npcs: list[str] = Field(default_factory=list)  # NPC IDs present here
    items: list[str] = Field(default_factory=list)  # Item IDs findable here


class CampaignQuest(BaseModel):
    """A quest or objective in the campaign."""

    id: str
    name: str
    description: str = ""
    giver_npc: str = ""  # NPC ID that gives this quest
    objectives: list[str] = Field(default_factory=list)
    rewards: list[str] = Field(default_factory=list)  # item IDs or "gold:50"


class CampaignPlayer(BaseModel):
    """Default player configuration for a campaign."""

    name: str = "Adventurer"
    max_hp: int = 20
    starting_items: list[str] = Field(default_factory=list)
    starting_gold: int = 10


class Campaign(BaseModel):
    """Top-level campaign definition — maps directly to a campaign YAML file."""

    name: str
    description: str = ""
    setting: str = ""  # world flavour text for the GM
    starting_location: str = ""

    player: CampaignPlayer = Field(default_factory=CampaignPlayer)
    locations: list[CampaignLocation] = Field(default_factory=list)
    npcs: list[CampaignNPC] = Field(default_factory=list)
    items: list[CampaignItem] = Field(default_factory=list)
    quests: list[CampaignQuest] = Field(default_factory=list)

    def to_yaml(self) -> str:
        """Serialize the campaign to a YAML string."""
        import yaml

        return yaml.dump(
            self.model_dump(exclude_defaults=True),
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
