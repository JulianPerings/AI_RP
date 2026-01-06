from .player_character import router as player_character_router
from .non_player_character import router as non_player_character_router
from .item_template import router as item_template_router
from .item_instance import router as item_instance_router
from .region import router as region_router
from .location import router as location_router
from .quest import router as quest_router
from .race import router as race_router
from .faction import router as faction_router
from .race_relationship import router as race_relationship_router
from .faction_relationship import router as faction_relationship_router
from .character_relationship import router as character_relationship_router
from .game import router as game_router

__all__ = [
    "player_character_router",
    "non_player_character_router",
    "item_template_router",
    "item_instance_router",
    "region_router",
    "location_router",
    "quest_router",
    "race_router",
    "faction_router",
    "race_relationship_router",
    "faction_relationship_router",
    "character_relationship_router",
    "game_router"
]
