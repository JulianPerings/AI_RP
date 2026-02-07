"""Tests for the state manager."""

import pytest

from models.world_state import WorldState
from models.item import Item, ItemType
from models.npc import NPC
from services.state_manager import StateManager


@pytest.fixture
def world() -> WorldState:
    w = WorldState(campaign_name="test", current_location="town")
    w.items["sword"] = Item(id="sword", name="Sword", item_type=ItemType.WEAPON)
    w.items["potion"] = Item(id="potion", name="Potion", item_type=ItemType.CONSUMABLE)
    w.npcs["bob"] = NPC(id="bob", name="Bob", location="town")
    return w


@pytest.fixture
def mgr(world: WorldState) -> StateManager:
    return StateManager(world)


class TestInventory:
    def test_add_item(self, mgr: StateManager):
        assert mgr.add_item("sword") is True
        assert "sword" in mgr.world.player.inventory

    def test_add_unknown_item(self, mgr: StateManager):
        assert mgr.add_item("unicorn") is False

    def test_remove_item(self, mgr: StateManager):
        mgr.add_item("sword")
        assert mgr.remove_item("sword") is True
        assert "sword" not in mgr.world.player.inventory

    def test_remove_missing_item(self, mgr: StateManager):
        assert mgr.remove_item("sword") is False


class TestNPCs:
    def test_get_npc(self, mgr: StateManager):
        assert mgr.get_npc("bob") is not None
        assert mgr.get_npc("bob").name == "Bob"

    def test_get_npcs_at_location(self, mgr: StateManager):
        npcs = mgr.get_npcs_at_location("town")
        assert len(npcs) == 1
        assert npcs[0].id == "bob"

    def test_register_npc(self, mgr: StateManager):
        new_npc = NPC(id="alice", name="Alice", location="forest")
        mgr.register_npc(new_npc)
        assert mgr.get_npc("alice") is not None
        assert "alice" in mgr.world.relationships


class TestMovement:
    def test_move_player(self, mgr: StateManager):
        mgr.move_player("forest")
        assert mgr.world.current_location == "forest"
        assert mgr.world.player.current_location == "forest"
        assert "forest" in mgr.world.visited_locations

    def test_visited_not_duplicated(self, mgr: StateManager):
        mgr.move_player("forest")
        mgr.move_player("forest")
        assert mgr.world.visited_locations.count("forest") == 1


class TestRelationships:
    def test_adjust(self, mgr: StateManager):
        mgr.world.relationships["bob"] = __import__(
            "models.relationship", fromlist=["Relationship"]
        ).Relationship(npc_id="bob")
        mgr.adjust_relationship("bob", 15, "helped him")
        rel = mgr.get_relationship("bob")
        assert rel.score == 15


class TestQuestFlags:
    def test_set_and_get(self, mgr: StateManager):
        mgr.set_flag("rescued_cat", True)
        assert mgr.get_flag("rescued_cat") is True
        assert mgr.get_flag("nonexistent") is False


class TestFromCampaign:
    def test_starting_items_and_gold(self, tmp_path):
        """Verify that starting_items and starting_gold from campaign YAML are applied."""
        campaign = tmp_path / "test.yaml"
        campaign.write_text(
            """
name: Test Campaign
starting_location: town
player:
  name: Hero
  max_hp: 25
  starting_items:
    - sword
    - potion
  starting_gold: 42
items:
  - id: sword
    name: Sword
    item_type: weapon
    damage: 3
  - id: potion
    name: Potion
    item_type: consumable
    heal_amount: 5
npcs:
  - id: bob
    name: Bob
    location: town
quests:
  - id: main_quest
    name: Main Quest
"""
        )
        w = WorldState.from_campaign(str(campaign))
        assert w.player.name == "Hero"
        assert w.player.max_hp == 25
        assert w.player.current_hp == 25
        assert w.player.gold == 42
        assert "sword" in w.player.inventory
        assert "potion" in w.player.inventory
        assert w.current_location == "town"
        assert "bob" in w.npcs
        assert "bob" in w.relationships
        assert "main_quest" in w.quest_flags
        assert w.quest_flags["main_quest"] is False
