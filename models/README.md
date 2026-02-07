# Models

Pydantic v2 data models that define all game entities. These are the **source of truth** for game state — agents read from and propose changes to these models, but never bypass them.

## Files

| File               | Description                                                        |
|--------------------|--------------------------------------------------------------------|
| `character.py`     | Player character — stats (STR/AGI/MND/CHA), skills, HP, inventory |
| `npc.py`           | NPC — personality, memory (recent + summary), basic stats          |
| `item.py`          | Items — weapons, armor, consumables, quest items                   |
| `relationship.py`  | Player↔NPC relationship tracking with disposition levels           |
| `world_state.py`   | Top-level state container; built from campaign YAML                |
| `action.py`        | Structured action/result objects passed between agents & services  |
| `campaign.py`      | Campaign YAML schema — used for validation and generation          |

## Stat System

Four core stats, each with a base value and modifier:

- **Strength** — melee damage, physical feats, carrying
- **Agility** — dodge, ranged attacks, stealth, initiative
- **Mind** — magic, lore, perception, puzzles
- **Charisma** — persuasion, intimidation, NPC disposition

Skills grant +1/+2/+3 bonuses to relevant checks. Checks use `d10 + stat_modifier + skill_bonus` vs. a difficulty threshold.

## Relationships

Numeric score from –100 to +100 mapped to dispositions:

| Range       | Disposition |
|-------------|-------------|
| –100 to –51 | Hostile     |
| –50 to –11  | Unfriendly  |
| –10 to +10  | Neutral     |
| +11 to +50  | Friendly    |
| +51 to +100 | Allied      |
