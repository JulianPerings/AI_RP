"""Dice engine — rolls, skill checks, and combat resolution."""

from __future__ import annotations

import random
from dataclasses import dataclass

from models.character import Character, Stat


@dataclass
class RollResult:
    """The result of a single dice roll with modifiers."""

    die_value: int
    modifier: int
    skill_bonus: int
    total: int
    detail: str  # human-readable breakdown


def roll_d10() -> int:
    """Roll a single d10 (1–10)."""
    return random.randint(1, 10)


def roll(
    stat: Stat,
    skill_bonus: int = 0,
    advantage: bool = False,
    disadvantage: bool = False,
) -> RollResult:
    """Roll d10 + stat total + skill bonus.

    With advantage, roll twice and take the higher die.
    With disadvantage, roll twice and take the lower die.
    """
    if advantage and not disadvantage:
        die = max(roll_d10(), roll_d10())
    elif disadvantage and not advantage:
        die = min(roll_d10(), roll_d10())
    else:
        die = roll_d10()

    total = die + stat.total + skill_bonus
    detail = f"d10({die}) + stat({stat.total}) + skill({skill_bonus}) = {total}"
    return RollResult(
        die_value=die,
        modifier=stat.total,
        skill_bonus=skill_bonus,
        total=total,
        detail=detail,
    )


def skill_check(
    character: Character,
    stat_name: str,
    difficulty: int,
    skill_name: str = "",
) -> tuple[bool, RollResult]:
    """Perform a skill check: roll >= difficulty means success."""
    stat = character.stats.get(stat_name)
    bonus = character.get_skill_bonus(skill_name) if skill_name else 0
    result = roll(stat, skill_bonus=bonus)
    success = result.total >= difficulty
    result.detail += f" vs DC {difficulty} → {'SUCCESS' if success else 'FAILURE'}"
    return success, result


def attack_roll(
    attacker_stat: Stat,
    defender_ac: int,
    skill_bonus: int = 0,
    weapon_damage: int = 1,
) -> tuple[bool, int, RollResult]:
    """Resolve an attack: hit check + damage calculation.

    Returns (hit: bool, damage: int, roll_result).
    """
    result = roll(attacker_stat, skill_bonus=skill_bonus)
    hit = result.total >= defender_ac

    damage = 0
    if hit:
        # Damage = weapon base + stat modifier (min 1)
        damage = max(1, weapon_damage + attacker_stat.total)
        # Critical: die == 10 → double damage
        if result.die_value == 10:
            damage *= 2
            result.detail += " [CRITICAL]"

    result.detail += f" vs AC {defender_ac} → {'HIT' if hit else 'MISS'}"
    if hit:
        result.detail += f", {damage} damage"

    return hit, damage, result


def initiative_roll(character: Character) -> RollResult:
    """Roll initiative based on Agility."""
    return roll(character.stats.agility)
