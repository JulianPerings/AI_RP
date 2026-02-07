"""Tests for the dice engine."""

import pytest

from models.character import Character, Stat, Skill
from services.dice import roll_d10, roll, skill_check, attack_roll, initiative_roll


class TestRollD10:
    def test_range(self):
        results = {roll_d10() for _ in range(200)}
        # With 200 rolls we should see most values
        assert min(results) >= 1
        assert max(results) <= 10


class TestRoll:
    def test_basic(self):
        stat = Stat(base=5, modifier=2)
        result = roll(stat, skill_bonus=1)
        assert result.total == result.die_value + 7 + 1
        assert "d10" in result.detail

    def test_no_bonus(self):
        stat = Stat(base=3, modifier=0)
        result = roll(stat)
        assert result.total == result.die_value + 3


class TestSkillCheck:
    def test_easy_check(self):
        # High stat vs low DC — should almost always pass
        c = Character()
        c.stats.strength.base = 10
        c.stats.strength.modifier = 5
        success, result = skill_check(c, "strength", difficulty=1)
        assert success is True
        assert "SUCCESS" in result.detail

    def test_impossible_check(self):
        # Low stat vs very high DC — should almost always fail
        c = Character()
        c.stats.mind.base = 1
        c.stats.mind.modifier = 0
        success, result = skill_check(c, "mind", difficulty=100)
        assert success is False
        assert "FAILURE" in result.detail

    def test_with_skill_bonus(self):
        c = Character(skills=[Skill(name="Lockpicking", level=3, governing_stat="agility")])
        c.stats.agility.base = 5
        _, result = skill_check(c, "agility", difficulty=8, skill_name="Lockpicking")
        assert result.skill_bonus == 3


class TestAttackRoll:
    def test_guaranteed_hit(self):
        stat = Stat(base=10, modifier=10)
        hit, dmg, result = attack_roll(stat, defender_ac=1, weapon_damage=5)
        assert hit is True
        assert dmg >= 1

    def test_guaranteed_miss(self):
        stat = Stat(base=0, modifier=0)
        hit, dmg, result = attack_roll(stat, defender_ac=100, weapon_damage=5)
        assert hit is False
        assert dmg == 0


class TestInitiative:
    def test_returns_roll(self):
        c = Character()
        result = initiative_roll(c)
        assert result.total >= 1
