# Models Directory

**Purpose**: SQLAlchemy ORM models defining database schema for the AI RPG.

## Core Entity Models
- `player_character.py` - PlayerCharacter (name, class, level, health, gold, race, faction, reputation, **current_session_id**)
- `non_player_character.py` - NonPlayerCharacter (name, type, health, behavior_state, base_disposition, race, faction, personality_traits, **following_player_id**)
- `item_template.py` - **ItemTemplate** - Item blueprints (name, category, rarity, weight, properties, requirements)
- `item_instance.py` - **ItemInstance** - Actual items in world (template_id, owner, location, equipped, quantity, durability, enchantments)
- `region.py` - **Region** - World regions containing locations (name, description, races, wealth, climate, political, danger, threats, history)
- `location.py` - Location (name, description, type, **region_id**, **danger_modifier**, **wealth_modifier**, **climate_override**, **population_density**, **accessibility**, **notes**)
- `quest.py` - Quest (title, description, status, rewards, player relationship)

## Relationship System Models
- `race.py` - Race (name, description) - Defines character races (Elf, Dwarf, Human, etc.)
- `faction.py` - Faction (name, description, alignment) - Defines factions/groups
- `race_relationship.py` - RaceRelationship - Race affinity matrix (e.g., Dwarf-Elf tension)
- `faction_relationship.py` - FactionRelationship - Faction dynamics (allied, enemy, neutral)
- `character_relationship.py` - **CharacterRelationship** - Unified relationship system for ALL character interactions (PC↔NPC, NPC↔NPC) using polymorphic character types

## Chat History Models
- `chat_history.py` - **ChatSession** and **ChatMessage** - Persistent conversation storage
  - `ChatSession`: Links sessions to players (session_id, player_id, timestamps)
  - `ChatMessage`: Individual messages (role, content, tool_calls, tool_name)

## Behavior States (NPC)
- `PASSIVE` - Won't initiate combat
- `DEFENSIVE` - Attacks if attacked
- `AGGRESSIVE` - Attacks if relationship < -25
- `HOSTILE` - Attacks on sight
- `PROTECTIVE` - Defends allies/location

## Companion System
NPCs can follow players as companions using `following_player_id`:
- When set, the NPC automatically moves with the player (handled in `move_player` tool)
- Use `set_companion_follow(npc_id, player_id)` to recruit
- Use `dismiss_companion(npc_id)` to have them stay at current location
- Companions appear in session context separately from "NPCs Here"

## Region System
Regions group locations and define shared world characteristics:

**Region Fields:**
- `name`, `description` - Basic identity
- `dominant_race_description` - Who lives here (guides NPC creation)
- `wealth_level` - destitute | poor | modest | prosperous | opulent
- `climate` - temperate | tropical | arid | arctic | mountainous | coastal | swamp | forest
- `terrain_description` - Physical geography
- `political_description` - Who rules, what factions
- `danger_level` - safe | low | moderate | high | deadly
- `threats_description` - Known dangers
- `history_description` - Historical context
- `notable_features` - Landmarks, points of interest

**Usage:**
- Locations link to regions via `region_id`
- Region context guides location/NPC creation for consistency
- GM receives region info in session context

## Location Modifiers
Locations can override or adjust region defaults:

- `danger_modifier` - Add to region danger level (-2 to +2 scale)
- `wealth_modifier` - Add to region wealth level
- `climate_override` - Override region climate (e.g., "underground" for caves)
- `population_density` - sparse | moderate | dense | crowded
- `accessibility` - public | restricted | hidden | secret
- `notes` - GM notes about this specific location

## Item System Design
**Template/Instance Pattern:**
- **ItemTemplate**: Defines WHAT an item is (blueprint) - reusable across many instances
- **ItemInstance**: Actual item in the world (based on template) - unique with owner, location, enchantments, buffs, flaws

**Item Uniqueness (NEW):**
Each ItemInstance can have unique buffs and flaws:
- **buffs**: List of minor advantages (e.g., `["sharp_edge: +2 damage", "lightweight: easier to wield"]`)
- **flaws**: List of minor drawbacks (e.g., `["rusty: -1 durability per use", "chipped: less effective"]`)
- Makes items feel unique even from same template
- LLM interprets these narratively in gameplay

**Properties JSON Examples:**
- Weapon: `{"damage": 10, "damage_type": "slashing", "two_handed": false}`
- Armor: `{"defense": 5, "armor_type": "heavy", "slot": "chest"}`
- Potion: `{"healing": 50, "effect_duration": 10}`

**Modifying Attributes:**
- Template level: Update `properties` in ItemTemplate (affects all future instances)
- Instance level: Update `enchantments`, `buffs`, `flaws` in ItemInstance (affects only that item)

**Polymorphic Ownership:**
- Items can be owned by PCs, NPCs, or NONE (on ground)
- Use `owner_type` (PC/NPC/NONE) + `owner_id`

## Usage
All models inherit from SQLAlchemy `Base` and are auto-imported via `__init__.py`.
Database tables are created automatically on application startup.
