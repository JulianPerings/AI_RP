"""Save manager — persist and load game state to/from JSON files."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.config import SAVES_DIR
from models.world_state import WorldState


class SaveManager:
    """Handles saving and loading WorldState to disk as JSON."""

    def __init__(self, save_dir: Path | None = None) -> None:
        self.save_dir = save_dir or SAVES_DIR
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _save_path(self, slot: str = "autosave") -> Path:
        return self.save_dir / f"{slot}.json"

    def save(self, world: WorldState, slot: str = "autosave") -> Path:
        """Serialize world state to a JSON file. Returns the file path."""
        path = self._save_path(slot)
        data = world.model_dump(mode="json")
        data["_saved_at"] = datetime.now().isoformat()
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path

    def load(self, slot: str = "autosave") -> WorldState | None:
        """Load world state from a save slot. Returns None if not found."""
        path = self._save_path(slot)
        if not path.exists():
            return None
        with open(path, "r") as f:
            data = json.load(f)
        data.pop("_saved_at", None)
        return WorldState.model_validate(data)

    def load_latest(self) -> WorldState | None:
        """Load the most recently modified save file."""
        saves = list(self.save_dir.glob("*.json"))
        if not saves:
            return None
        latest = max(saves, key=lambda p: p.stat().st_mtime)
        with open(latest, "r") as f:
            data = json.load(f)
        data.pop("_saved_at", None)
        return WorldState.model_validate(data)

    def list_saves(self) -> list[str]:
        """Return names of all available save slots."""
        return [p.stem for p in sorted(self.save_dir.glob("*.json"))]

    def delete(self, slot: str) -> bool:
        """Delete a save file. Returns True if it existed."""
        path = self._save_path(slot)
        if path.exists():
            path.unlink()
            return True
        return False
