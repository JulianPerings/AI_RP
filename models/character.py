"""Player character model — stats, skills, inventory, and HP."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Stat(BaseModel):
    """A single character stat with a base value and optional modifier."""

    base: int = 5
    modifier: int = 0

    @property
    def total(self) -> int:
        return self.base + self.modifier


class Stats(BaseModel):
    """The four core stats."""

    strength: Stat = Field(default_factory=Stat)
    agility: Stat = Field(default_factory=Stat)
    mind: Stat = Field(default_factory=Stat)
    charisma: Stat = Field(default_factory=Stat)

    def get(self, name: str) -> Stat:
        """Retrieve a stat by name (case-insensitive)."""
        return getattr(self, name.lower())


class Skill(BaseModel):
    """A learned skill that grants a bonus to relevant checks."""

    name: str
    description: str = ""
    level: int = Field(default=1, ge=1, le=3)  # +1 / +2 / +3
    governing_stat: str = "strength"  # which stat this skill keys off


class Character(BaseModel):
    """The player character."""

    name: str = "Adventurer"
    title: str = ""
    backstory: str = ""

    # Combat
    max_hp: int = 20
    current_hp: int = 20
    armor_class: int = 5

    # Stats & skills
    stats: Stats = Field(default_factory=Stats)
    skills: list[Skill] = Field(default_factory=list)

    # Inventory (list of item IDs)
    inventory: list[str] = Field(default_factory=list)
    gold: int = 0

    # Location
    current_location: str = ""

    # XP / levelling (simple)
    level: int = 1
    xp: int = 0
    xp_to_next_level: int = 100

    def is_alive(self) -> bool:
        return self.current_hp > 0

    def take_damage(self, amount: int) -> int:
        """Apply damage (after AC reduction). Returns actual damage dealt."""
        effective = max(0, amount)
        self.current_hp = max(0, self.current_hp - effective)
        return effective

    def heal(self, amount: int) -> int:
        """Heal HP up to max. Returns actual amount healed."""
        before = self.current_hp
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        return self.current_hp - before

    def gain_xp(self, amount: int) -> bool:
        """Add XP. Returns True if the character leveled up."""
        self.xp += amount
        if self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level += 1
            self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
            self.max_hp += 5
            self.current_hp = self.max_hp
            return True
        return False

    def get_skill_bonus(self, skill_name: str) -> int:
        """Return the bonus for a named skill, or 0 if not learned."""
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill.level
        return 0
