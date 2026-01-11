# Agents Directory

**Purpose**: LangGraph-based AI agents that power the immersive RPG experience.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Game Master Agent                  │
│  (LangGraph + gpt-5-mini + reasoning_effort=low)   │
├─────────────────────────────────────────────────────┤
│  Tools: 44 database operations                       │
│  Memory: Rolling sessions + Auto-summarization       │
│  State: Player context, location, messages, summaries│
└─────────────────────────────────────────────────────┘
```

## Files

- `game_master.py` - **GameMasterAgent** - Main LangGraph agent with narrative generation and reasoning
- `tools.py` - Database tools the agent can invoke (44 tools)
- `state.py` - **GameState** TypedDict for agent state management
- `story_manager.py` - **StoryManager** - Simplified story storage in PlayerCharacter.story_messages
- `prompts.py` - **Centralized LLM prompts** - All prompts separated from code logic
- `context_builder.py` - **Session context builder** - Builds rich context with inventory, NPCs, items, quests
- `autocomplete.py` - **Autocomplete handler** - Context-aware action suggestions for player input

**Deprecated:**
- `chat_history_manager.py` - Old session-based persistence (replaced by StoryManager)
- `memory_manager.py` - Old memory system (to be refactored)

## Prompts Module

All LLM prompts are centralized in `prompts.py` for easy management:

| Prompt | Purpose |
|--------|--------|
| `GAME_MASTER_SYSTEM_PROMPT` | Core GM persona, tools guide, and style instructions |
| `SESSION_START_PROMPT` | Backstory parsing and session initialization |
| `ARCHIVE_SUMMARY_PROMPT` | Summarizing messages for rolling archives |
| `MEMORY_SUMMARY_PROMPT` | Detailed session summaries for long-term memory |
| `AUTOCOMPLETE_PROMPT` | Polish player input into narrative prose |

**Helper functions:**
- `format_session_start(player_id)` - Format session start with player ID
- `format_archive_summary(messages_text)` - Format archive summary prompt
- `format_memory_summary(conversation)` - Format memory summary prompt

**Benefits:**
- Review/modify prompts without touching code logic
- Version control prompt changes separately
- Test different prompt variations easily
- Share prompts across multiple agents

## Game Master Agent

The `GameMasterAgent` is a stateful LangGraph agent that:
- Narrates scenes and events with atmospheric detail
- Controls NPCs based on personality and relationships
- Manages game state (health, gold, inventory, quests)
- Creates drama through challenges and moral dilemmas

### Storytelling Guidelines
The GM follows strict narrative rules:
- **No inventory dumps** - Don't list items unless player asks
- **No explicit options** - End with atmosphere/NPC action, not "What do you do? A/B/C"
- **Move NPCs** - When escorting player, use `move_npc` to move the NPC too
- **Trust the player** - They know their situation; don't summarize
- **Avoid duplicates** - Check existing locations/NPCs/items before creating new ones
- **Concise prose** - Aim for paragraphs, not essays

### Tools Available (44 total)

**Query Tools:**
| Tool | Description |
|------|-------------|
| `get_player_info` | Get player stats, location |
| `get_location_info` | Get location details |
| `get_npc_info` | Get NPC details, personality, faction |
| `get_npcs_at_location` | List all NPCs at a location |
| `get_relationship` | Query relationship between any two characters |
| `get_player_quests` | List player's quests |
| `list_item_templates` | Search/list item templates by name or category |

**Inventory Query Tools (IMPORTANT):**
| Tool | Description |
|------|-------------|
| `get_items_at_location` | List items on ground (returns **instance_id**) |
| `get_player_inventory` | List player's items (returns **instance_id**) |
| `get_npc_inventory` | List NPC's items (returns **instance_id**) |

**Context-first (reduce tool calls):**
- The GM receives session context that already includes player stats, local NPCs/items, combat state, and inventory with `instance_id` for each stack.
- Prefer using IDs from context; use query tools as fallback when details are missing.

**Long-Term Memory Tools:**
| Tool | Description |
|------|-------------|
| `search_memories` | Search past session summaries by keyword |
| `recall_session_details` | Get full details of a past session |

**Combat Tools:**
| Tool | Description |
|------|-------------|
| `initiate_combat` | Start combat (PC implied by player_id; provide ally/enemy NPC id lists) |
| `get_active_combat` | Check if player is in active combat |
| `add_combatant` | Add NPC/PC to an active combat |
| `remove_combatant` | Remove combatant (fled, captured, etc.) |
| `update_combat_hp` | Update HP in combat tracker (syncs with actual character) |
| `end_combat` | End combat with outcome and narrative summary |

**Starting Combat Params (IMPORTANT):**
- `initiate_combat(player_id, description, player_team_ids=None, enemy_team_ids=[...])`
- `player_team_ids`: optional ally NPC ids. The player's PC is automatically included via `player_id`.
- `enemy_team_ids`: required enemy NPC ids.

**Cinematic Combat Summaries:**
- The `summary` passed to `end_combat` replaces the individual combat messages in the story log.
- Write it as a tight, in-world story beat that flows naturally with the surrounding narrative.
- Prefer **4-8 sentences** (roughly 70-140 words) and avoid rewriting the full exchange blow-by-blow.
- Avoid meta headers (e.g. "COMBAT SUMMARY") and avoid bullet-point recaps.
- End with a small forward hook (immediate aftermath / what the world does next).

**Combat Tool Params (IMPORTANT):**
- `player_id` refers to the *owner player* whose combat session is being tracked/modified.
  Combat sessions are keyed per-player, so all combat tools take `player_id`.
- `char_type` + `char_id` identify the *combatant* inside that combat:
  - `char_type="PC"` → `char_id` is a `PlayerCharacter.id`
  - `char_type="NPC"` → `char_id` is a `NonPlayerCharacter.id`
- `team` is the side to join: `"player"` (allies) or `"enemy"`.

**Item Transfer (uses instance_id):**
| Tool | Description |
|------|-------------|
| `pickup_item` | Player picks up item from ground |
| `drop_item` | Player drops item at location |
| `transfer_item` | Move item between any owners |
| `consume_item_instance` | Decrement quantity for consumables/ammo; deletes stack at 0 |

**Consumables & Ammo (IMPORTANT):**
- When narration uses ammo/consumables (arrows, potions, bandages, etc.), first call `get_player_inventory` to find the correct `instance_id`, then call `consume_item_instance(instance_id, amount)`.

**Item Creation (creates NEW items with optional buffs/flaws):**
| Tool | Description |
|------|-------------|
| `create_item_for_player` | ⚠️ Spawn new item for player with unique buffs/flaws |
| `create_item_for_npc` | ⚠️ Spawn new item for NPC with unique buffs/flaws |
| `spawn_item_at_location` | ⚠️ Spawn new item on ground with unique buffs/flaws |

All item creation tools now accept optional `buffs` and `flaws` parameters to make items unique.

**Player Management:**
| Tool | Description |
|------|-------------|
| `update_player_health` | Apply damage or healing |
| `update_player_gold` | Add/remove gold |
| `update_player_experience` | Add XP, auto level-up |
| `move_player` | Change player location (companions auto-move) |

**NPC Management:**
| Tool | Description |
|------|-------------|
| `move_npc` | Move NPC to new location |
| `update_npc_health` | Damage or heal NPC |
| `update_npc_behavior` | Change behavior state |
| `update_npc_disposition` | Adjust NPC attitude |
| `create_npc` | Spawn new NPC in world |

**Companion Management:**
| Tool | Description |
|------|-------------|
| `set_companion_follow` | Make NPC follow player (auto-moves with player) |
| `dismiss_companion` | Stop NPC from following (stays at current location) |
| `get_player_companions` | List NPCs following a player |

**Relationship & Quest:**
| Tool | Description |
|------|-------------|
| `update_relationship` | Modify relationship value |
| `create_quest` | Create new quest |
| `update_quest_status` | Complete/abandon quest |

**World Building:**
| Tool | Description |
|------|-------------|
| `list_locations` | List/search locations (check before creating!) |
| `create_location` | Create new area with region_id, modifiers |
| `create_item_template` | Define new item type |

**Region Management:**
| Tool | Description |
|------|-------------|
| `get_region_info` | Get region details (races, wealth, climate, danger) |
| `list_regions` | List all world regions |
| `create_region` | Create new region with characteristics |
| `update_region` | Update region properties |
| `assign_location_to_region` | Link location to a region |

**Race Management:**
| Tool | Description |
|------|-------------|
| `list_races` | List all available races |
| `get_race_relationships` | Get racial relationship modifiers |
| `create_race` | Create new race (e.g., Orcs, Goblins) |
| `update_race_relationship` | Set hostility/alliance between races |

## Item System - IMPORTANT

**Instance vs Template:**
- **template_id**: Blueprint for an item type (e.g., "Iron Sword")
- **instance_id**: A specific item in the world (the sword in player's bag)

**Correct Flow for Picking Up Items:**
```
1. get_items_at_location(location_id) → returns [{instance_id: 5, name: "Sword", ...}]
2. pickup_item(player_id, item_instance_id=5) → moves item to player
```

**Correct Flow for Giving Items:**
```
1. get_player_inventory(player_id) → returns [{instance_id: 5, name: "Sword", ...}]
2. transfer_item(item_instance_id=5, new_owner_type="NPC", new_owner_id=3)
```

**Template Search (IMPORTANT):**
Always search for existing templates before creating new ones:
```python
list_item_templates(search="sword")  # Find sword templates
list_item_templates(category="weapon")  # List all weapons
```

**Seeded Templates:**
- Iron Sword, Healing Potion, Bread, Torch, Traveler's Cape

**When to Create Items:**
- Quest rewards → `create_item_for_player`
- NPC shop inventory setup → `create_item_for_npc`
- Loot spawn → `spawn_item_at_location`

## Usage

```python
from agents import create_game_master

gm = create_game_master()

# Start a new session
intro = gm.start_session(player_id=1, session_id="unique-session-id")

# Chat with the Game Master
response = gm.chat(
    message="I approach the mysterious stranger",
    player_id=1,
    session_id="unique-session-id",
    session_context={"player_name": "Aldric", "location_id": 1}
)
```

## API Endpoints

The agent is exposed via `/game` routes:
- `POST /game/start-session` - Begin new game session with intro narrative (parses backstory to spawn items/NPCs)
- `POST /game/chat` - Send player action with optional tags, receive narrative response
- `GET /game/story/{player_id}` - Get story messages for a player
- `DELETE /game/story/{player_id}` - Clear story (reset)
- `GET /game/health` - Check agent status
- `POST /game/roll-dice` - Roll d20 with optional luck reroll

### Start Session Enhancement (NEW)
The `/game/start-session` endpoint now intelligently parses the player's `description` field:
- **Items mentioned** → Spawned with unique buffs/flaws reflecting their history
- **NPCs mentioned** → Created and placed at appropriate locations
- **Relationships** → Established automatically

Example: If player description says "carries his father's sword", the LLM will:
1. Create the sword with buffs like `["heirloom: +1 morale", "well-balanced"]`
2. Give it to the player
3. Mention it in the intro narrative

**Long-Term Memory Endpoints:**
- `POST /game/memory/summarize/{session_id}` - Generate summary for a session
- `GET /game/memory/search/{player_id}?query=bob` - Search memories by keyword
- `GET /game/memory/all/{player_id}` - Get all player memories
- `GET /game/memory/session/{session_id}` - Get full session details

## Story Architecture (Simplified)

Stories are stored directly in `PlayerCharacter.story_messages` as a JSON array.

### Message Format
```json
{
  "role": "gm" | "player",
  "content": "The message text...",
  "tags": ["dice:15", "critical", "combat"],
  "timestamp": "2024-01-15T10:30:00"
}
```

### Tags
Messages can be tagged for filtering and special handling:
- `dice:N` - Player rolled N on d20
- `critical` - Natural 20
- `fumble` - Natural 1
- `combat` - Combat-related message
- `session_start` - Session intro message

### Context Building
Each LLM call includes:
1. **System prompt** - Core GM instructions (~800 tokens)
2. **Rich session context** - Built by `context_builder.py`:
   - Player stats (name, class, level, health, gold, luck)
   - Current location details
   - **Full inventory** with equipped status
   - **NPCs at location** with behavior/health
   - **Items on ground** with instance_ids for pickup
   - **Active quests** with completion status
3. **Recent messages** - Last 20 messages from story_messages

### Combat Compression (Future)
When combat ends, all combat-tagged messages can be compressed into a single summary:
```python
story_manager.compress_tagged_messages(player_id, "combat:123", summary_text)
```

## Configuration

Settings in `config.py`:

**LLM Settings** (gpt-5-mini: 400k context, 128k max output, reasoning support):
| Setting | Default | Description |
|---------|---------|-------------|
| `OPENAI_API_KEY` | - | Required for LLM calls |
| `OPENAI_MODEL` | gpt-5-mini | Model to use |
| `LLM_TEMPERATURE` | 0.8 | Creativity (0.0-2.0), higher = more creative |
| `LLM_MAX_TOKENS` | 8192 | Max response tokens (model supports up to 128k) |
| `LLM_REASONING_EFFORT` | low | Reasoning depth: "low", "medium", "high" |
| `SUMMARY_LLM_TEMPERATURE` | 0.3 | Lower temp for consistent summaries |
| `SUMMARY_LLM_MAX_TOKENS` | 500 | Summary responses are short |

**Session Management:**
| Setting | Default | Description |
|---------|---------|-------------|
| `MIN_MESSAGES_IN_SESSION` | 15 | Messages to keep in active session after archiving |
| `MAX_MESSAGES_BEFORE_ARCHIVE` | 30 | Trigger archiving at this count |
| `SUMMARIES_IN_CONTEXT` | 5 | Previous summaries to include in context |

**Environment Override:** All settings can be overridden via `.env` file or environment variables.

---

## Example Gameplay Scenarios

### Scenario 1: Combat Encounter
**Player says:** "I attack the goblin with my sword"

**Agent should:**
1. `get_player_info(player_id)` → Check player stats, equipped weapon
2. `get_npc_info(goblin_id)` → Check goblin health, behavior
3. `get_relationship("PC", player_id, "NPC", goblin_id)` → Check hostility
4. `update_npc_health(goblin_id, -15)` → Apply damage
5. `update_npc_behavior(goblin_id, "hostile")` → Goblin becomes hostile
6. `update_player_health(player_id, -5)` → Goblin counterattacks
7. `update_relationship("PC", player_id, "NPC", goblin_id, -20)` → Relationship worsens
8. Narrate the combat cinematically

---

### Scenario 2: NPC Follows Player
**Player says:** "I ask the merchant to follow me to the forest"

**Agent should:**
1. `get_npc_info(merchant_id)` → Check merchant personality/disposition
2. `get_relationship("PC", player_id, "NPC", merchant_id)` → Check trust level
3. If relationship > 25: `move_npc(merchant_id, forest_location_id)` → NPC follows
4. `update_npc_disposition(merchant_id, +5)` → Merchant appreciates being asked
5. Narrate the merchant agreeing (or refusing if relationship too low)

---

### Scenario 3: Trading Items
**Player says:** "I want to buy the enchanted dagger from the blacksmith"

**Agent should:**
1. `get_player_info(player_id)` → Check player gold
2. `get_npc_info(blacksmith_id)` → Get blacksmith info
3. `list_item_templates(category="weapon")` → Find dagger template
4. `update_player_gold(player_id, -50)` → Deduct gold
5. `give_item_to_player(player_id, dagger_template_id)` → Add to inventory
6. `update_relationship("PC", player_id, "NPC", blacksmith_id, +5)` → Good customer
7. Narrate the transaction

---

### Scenario 4: Quest Completion
**Player says:** "I deliver the artifact to the wizard"

**Agent should:**
1. `get_player_quests(player_id)` → Find the delivery quest
2. `get_player_info(player_id)` → Check player has artifact
3. `transfer_item(artifact_instance_id, "NPC", wizard_id)` → Give to wizard
4. `update_quest_status(quest_id, is_completed=True)` → Mark complete
5. `update_player_gold(player_id, +100)` → Quest reward
6. `update_player_experience(player_id, +50)` → XP reward
7. `update_relationship("PC", player_id, "NPC", wizard_id, +15)` → Wizard grateful
8. Narrate the completion and rewards

---

### Scenario 5: Dynamic World Building
**Player says:** "I explore the dark cave I discovered"

**Agent should:**
1. `list_all_locations()` → Check if cave exists
2. If not: `create_location("Dark Cave", "A damp cave with echoing drips...", "dungeon")`
3. `move_player(player_id, new_cave_id)` → Move player there
4. `create_npc("Cave Spider", "monster", cave_id, behavior_state="aggressive")` → Spawn enemy
5. `spawn_item_at_location(treasure_template_id, cave_id)` → Add loot
6. Narrate the discovery and what the player sees

---

### Scenario 6: NPC Behavior Changes
**Player says:** "I threaten the guard and demand he lets me pass"

**Agent should:**
1. `get_npc_info(guard_id)` → Check guard behavior, disposition
2. `get_relationship("PC", player_id, "NPC", guard_id)` → Current relationship
3. `update_npc_behavior(guard_id, "defensive")` → Guard becomes wary
4. `update_npc_disposition(guard_id, -15)` → Guard dislikes being threatened
5. `update_relationship("PC", player_id, "NPC", guard_id, -25)` → Relationship damaged
6. Narrate guard's reaction based on his personality traits

---

### Scenario 7: Looting a Defeated Enemy
**Player says:** "I search the bandit's body for loot"

**Agent should:**
1. `get_npc_info(bandit_id)` → Confirm bandit is dead (health = 0)
2. `get_location_info(location_id)` → Get current location
3. Query bandit's inventory (items with owner_type=NPC, owner_id=bandit_id)
4. `transfer_item(item_id, "PC", player_id)` → Transfer each item to player
5. `update_player_experience(player_id, +10)` → XP for victory
6. Narrate what the player finds

---

### Scenario 8: Reputation-Based NPC Reactions
**Player says:** "I enter the tavern"

**Agent should:**
1. `move_player(player_id, tavern_id)` → Move to tavern
2. `get_npcs_at_location(tavern_id)` → Get all NPCs present
3. For each NPC: `get_relationship("PC", player_id, "NPC", npc_id)`
4. NPCs with high relationship greet warmly
5. NPCs with low relationship act cold or hostile
6. `update_npc_behavior()` accordingly for hostile NPCs
7. Narrate the scene with appropriate NPC reactions
