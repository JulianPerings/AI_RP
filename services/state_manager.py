"""State manager — CRUD operations on the WorldState."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

from models.item import Item
from models.npc import NPC
from models.relationship import Relationship

if TYPE_CHECKING:
    from models.world_state import WorldState


class StateManager:
    """Provides convenience methods for reading and mutating world state."""

    def __init__(self, world: WorldState) -> None:
        self.world = world

    # ------------------------------------------------------------------
    # Player helpers
    # ------------------------------------------------------------------

    @property
    def player(self):
        return self.world.player

    def move_player(self, location: str) -> None:
        self.world.player.current_location = location
        self.world.current_location = location
        if location not in self.world.visited_locations:
            self.world.visited_locations.append(location)

    # ------------------------------------------------------------------
    # Inventory
    # ------------------------------------------------------------------

    def add_item(self, item_id: str) -> bool:
        """Add an item to the player's inventory. Returns False if item unknown."""
        if item_id not in self.world.items:
            return False
        if item_id not in self.world.player.inventory:
            self.world.player.inventory.append(item_id)
        return True

    def remove_item(self, item_id: str) -> bool:
        if item_id in self.world.player.inventory:
            self.world.player.inventory.remove(item_id)
            return True
        return False

    def get_item(self, item_id: str) -> Item | None:
        return self.world.items.get(item_id)

    def register_item(self, item: Item) -> None:
        """Add an item to the world registry."""
        self.world.items[item.id] = item

    # ------------------------------------------------------------------
    # NPCs
    # ------------------------------------------------------------------

    def get_npc(self, npc_id: str) -> NPC | None:
        return self.world.npcs.get(npc_id)

    def get_npcs_at_location(self, location: str) -> list[NPC]:
        return [n for n in self.world.npcs.values() if n.location == location and n.is_alive]

    def register_npc(self, npc: NPC) -> None:
        """Add or update an NPC in the world."""
        self.world.npcs[npc.id] = npc
        if npc.id not in self.world.relationships:
            self.world.relationships[npc.id] = Relationship(npc_id=npc.id)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    def get_relationship(self, npc_id: str) -> Relationship | None:
        return self.world.relationships.get(npc_id)

    def adjust_relationship(self, npc_id: str, delta: int, note: str = "") -> None:
        rel = self.world.relationships.get(npc_id)
        if rel:
            rel.adjust(delta, note)

    # ------------------------------------------------------------------
    # Quest flags
    # ------------------------------------------------------------------

    def set_flag(self, flag: str, value: bool = True) -> None:
        self.world.quest_flags[flag] = value

    def get_flag(self, flag: str) -> bool:
        return self.world.quest_flags.get(flag, False)

    # ------------------------------------------------------------------
    # Display helpers (Rich)
    # ------------------------------------------------------------------

    def print_status(self, console: Console) -> None:
        p = self.world.player
        table = Table(title=f"{p.name} — Level {p.level}")
        table.add_column("Stat", style="bold")
        table.add_column("Value", justify="right")
        table.add_row("HP", f"{p.current_hp}/{p.max_hp}")
        table.add_row("Strength", str(p.stats.strength.total))
        table.add_row("Agility", str(p.stats.agility.total))
        table.add_row("Mind", str(p.stats.mind.total))
        table.add_row("Charisma", str(p.stats.charisma.total))
        table.add_row("Gold", str(p.gold))
        table.add_row("XP", f"{p.xp}/{p.xp_to_next_level}")
        table.add_row("Location", self.world.current_location or "???")
        console.print(table)

    def print_inventory(self, console: Console) -> None:
        p = self.world.player
        if not p.inventory:
            console.print("[dim]Your pack is empty.[/dim]")
            return
        table = Table(title="Inventory")
        table.add_column("Item", style="bold")
        table.add_column("Type")
        table.add_column("Description")
        for item_id in p.inventory:
            item = self.world.items.get(item_id)
            if item:
                table.add_row(item.name, item.item_type.value, item.description)
            else:
                table.add_row(item_id, "?", "Unknown item")
        console.print(table)
