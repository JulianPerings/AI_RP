"""Relationship model — tracks player↔NPC disposition and history."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Disposition(str, Enum):
    HOSTILE = "hostile"
    UNFRIENDLY = "unfriendly"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ALLIED = "allied"


# Map disposition to a numeric range for easy threshold checks
DISPOSITION_THRESHOLDS: dict[Disposition, tuple[int, int]] = {
    Disposition.HOSTILE: (-100, -51),
    Disposition.UNFRIENDLY: (-50, -11),
    Disposition.NEUTRAL: (-10, 10),
    Disposition.FRIENDLY: (11, 50),
    Disposition.ALLIED: (51, 100),
}


def disposition_from_score(score: int) -> Disposition:
    """Convert a numeric relationship score to a Disposition label."""
    for disp, (lo, hi) in DISPOSITION_THRESHOLDS.items():
        if lo <= score <= hi:
            return disp
    return Disposition.HOSTILE if score < -100 else Disposition.ALLIED


class Relationship(BaseModel):
    """A relationship between the player and an NPC."""

    npc_id: str
    score: int = Field(default=0, ge=-100, le=100)
    disposition: Disposition = Disposition.NEUTRAL
    notes: list[str] = Field(default_factory=list)  # key events

    def adjust(self, delta: int, note: str = "") -> None:
        """Shift the relationship score and recalculate disposition."""
        self.score = max(-100, min(100, self.score + delta))
        self.disposition = disposition_from_score(self.score)
        if note:
            self.notes.append(note)
