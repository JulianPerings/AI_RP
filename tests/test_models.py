"""Tests for Pydantic data models."""

import pytest

from models.character import Character, Stat, Skill, Stats
from models.npc import NPC, NPCMemory
from models.item import Item, ItemType
from models.relationship import Relationship, Disposition, disposition_from_score
from models.action import Action, ActionType


class TestStat:
    def test_total(self):
        s = Stat(base=5, modifier=2)
        assert s.total == 7

    def test_default(self):
        s = Stat()
        assert s.total == 5


class TestCharacter:
    def test_defaults(self):
        c = Character()
        assert c.name == "Adventurer"
        assert c.is_alive()
        assert c.current_hp == 20

    def test_take_damage(self):
        c = Character(current_hp=10)
        dealt = c.take_damage(4)
        assert dealt == 4
        assert c.current_hp == 6

    def test_take_lethal_damage(self):
        c = Character(current_hp=3)
        c.take_damage(10)
        assert c.current_hp == 0
        assert not c.is_alive()

    def test_heal(self):
        c = Character(max_hp=20, current_hp=10)
        healed = c.heal(5)
        assert healed == 5
        assert c.current_hp == 15

    def test_heal_no_overheal(self):
        c = Character(max_hp=20, current_hp=18)
        healed = c.heal(10)
        assert healed == 2
        assert c.current_hp == 20

    def test_gain_xp_no_levelup(self):
        c = Character(xp=0, xp_to_next_level=100)
        assert c.gain_xp(50) is False
        assert c.level == 1

    def test_gain_xp_levelup(self):
        c = Character(xp=0, xp_to_next_level=100, level=1, max_hp=20, current_hp=15)
        assert c.gain_xp(100) is True
        assert c.level == 2
        assert c.max_hp == 25
        assert c.current_hp == 25  # healed to full on levelup

    def test_skill_bonus(self):
        c = Character(skills=[Skill(name="Swordsmanship", level=2)])
        assert c.get_skill_bonus("Swordsmanship") == 2
        assert c.get_skill_bonus("Lockpicking") == 0


class TestRelationship:
    def test_default_neutral(self):
        r = Relationship(npc_id="test")
        assert r.disposition == Disposition.NEUTRAL

    def test_adjust_positive(self):
        r = Relationship(npc_id="test", score=0)
        r.adjust(20, "helped them")
        assert r.score == 20
        assert r.disposition == Disposition.FRIENDLY
        assert "helped them" in r.notes

    def test_adjust_clamps(self):
        r = Relationship(npc_id="test", score=90)
        r.adjust(50)
        assert r.score == 100

    def test_disposition_from_score(self):
        assert disposition_from_score(-80) == Disposition.HOSTILE
        assert disposition_from_score(-30) == Disposition.UNFRIENDLY
        assert disposition_from_score(0) == Disposition.NEUTRAL
        assert disposition_from_score(30) == Disposition.FRIENDLY
        assert disposition_from_score(70) == Disposition.ALLIED


class TestItem:
    def test_weapon(self):
        i = Item(id="sword", name="Sword", item_type=ItemType.WEAPON, damage=5)
        assert i.damage == 5
        assert i.item_type == ItemType.WEAPON


class TestNPC:
    def test_add_memory(self):
        npc = NPC(id="test", name="Test NPC")
        npc.add_memory("Player said hello")
        assert len(npc.recent_memories) == 1
        assert npc.recent_memories[0].summary == "Player said hello"

    def test_context_block(self):
        npc = NPC(id="test", name="Test NPC", personality="Grumpy", location="tavern")
        ctx = npc.get_context_block()
        assert "Test NPC" in ctx
        assert "Grumpy" in ctx
        assert "tavern" in ctx
