# Services

Core service layer that agents and the game loop depend on. These are **not** LLM agents — they are deterministic (or LLM-assisted) utilities.

## Files

| File                | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `llm_service.py`    | Unified LLM interface (OpenAI/xAI/Gemini) via LiteLLM           |
| `dice.py`           | d10 dice engine — rolls, skill checks, attack resolution         |
| `state_manager.py`  | CRUD helpers for WorldState (inventory, NPCs, relationships)     |
| `save_manager.py`   | Persist/load game state to JSON files in `data/saves/`           |
| `memory_manager.py` | NPC memory summarisation — compresses old interactions via LLM   |
| `logger.py`         | Debug logging — agent ↔ LLM traffic to console and `logs/`      |

## Dice System

- Base die: **d10** (1–10)
- Checks: `d10 + stat_total + skill_bonus` vs. difficulty class (DC)
- Attacks: same roll vs. defender AC; damage = weapon_base + stat_total (min 1)
- Critical hit: die roll of 10 → double damage
- Advantage/disadvantage: roll twice, take higher/lower

## Debug Logging

The `logger.py` module provides structured logging under the `ai_rpg` namespace. Enable debug mode to see all agent ↔ LLM traffic:

- **CLI flag**: `python -m app.main --debug`
- **Env var**: `AI_RPG_DEBUG=1`
- **In-game**: type `debug` to toggle on/off at runtime

When active, logs go to both stderr and a timestamped file in `logs/`. Logged info includes:
- Every LLM request (provider, model, messages, temperature)
- Every LLM response (full content)
- Agent prompt loading and chat calls

## Memory Summarisation Flow

1. NPC interaction recorded as a `NPCMemory` entry (summary + optional raw exchange)
2. When `recent_memories` exceeds the threshold (default 8), the `MemoryManager` calls the LLM to compress older entries into `memory_summary`
3. Only the most recent entries are kept verbatim; everything else lives in the compressed summary
