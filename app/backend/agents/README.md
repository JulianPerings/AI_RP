# Agents Directory

**Purpose**: LangGraph-based AI agents that power the immersive RPG experience.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Game Master Agent                  │
│  (LangGraph + gpt-5-mini + reasoning_effort=medium) │
├─────────────────────────────────────────────────────┤
│  Tools: 30 database operations                       │
│  Memory: Database-backed chat history                │
│  State: Player context, location, messages           │
└─────────────────────────────────────────────────────┘
```

## Files

- `game_master.py` - **GameMasterAgent** - Main LangGraph agent with narrative generation and reasoning
- `tools.py` - Database tools the agent can invoke (30 tools)
- `state.py` - **GameState** TypedDict for agent state management
- `chat_history_manager.py` - Database-backed conversation persistence

## Game Master Agent

The `GameMasterAgent` is a stateful LangGraph agent that:
- Narrates scenes and events with atmospheric detail
- Controls NPCs based on personality and relationships
- Manages game state (health, gold, inventory, quests)
- Creates drama through challenges and moral dilemmas

### Tools Available (30 total)

**Query Tools:**
| Tool | Description |
|------|-------------|
| `get_player_info` | Get player stats, location |
| `get_location_info` | Get location details |
| `get_npc_info` | Get NPC details, personality, faction |
| `get_npcs_at_location` | List all NPCs at a location |
| `get_relationship` | Query relationship between any two characters |
| `get_player_quests` | List player's quests |
| `list_all_locations` | Get all world locations |
| `list_item_templates` | Get available item types |

**Inventory Query Tools (IMPORTANT):**
| Tool | Description |
|------|-------------|
| `get_items_at_location` | List items on ground (returns **instance_id**) |
| `get_player_inventory` | List player's items (returns **instance_id**) |
| `get_npc_inventory` | List NPC's items (returns **instance_id**) |

**Item Transfer (uses instance_id):**
| Tool | Description |
|------|-------------|
| `pickup_item` | Player picks up item from ground |
| `drop_item` | Player drops item at location |
| `transfer_item` | Move item between any owners |

**Item Creation (creates NEW items):**
| Tool | Description |
|------|-------------|
| `create_item_for_player` | ⚠️ Spawn new item for player (use for rewards) |
| `create_item_for_npc` | ⚠️ Spawn new item for NPC (use for setup) |
| `spawn_item_at_location` | ⚠️ Spawn new item on ground |

**Player Management:**
| Tool | Description |
|------|-------------|
| `update_player_health` | Apply damage or healing |
| `update_player_gold` | Add/remove gold |
| `update_player_experience` | Add XP, auto level-up |
| `move_player` | Change player location |

**NPC Management:**
| Tool | Description |
|------|-------------|
| `move_npc` | Move NPC to new location |
| `update_npc_health` | Damage or heal NPC |
| `update_npc_behavior` | Change behavior state |
| `update_npc_disposition` | Adjust NPC attitude |
| `create_npc` | Spawn new NPC in world |

**Relationship & Quest:**
| Tool | Description |
|------|-------------|
| `update_relationship` | Modify relationship value |
| `create_quest` | Create new quest |
| `update_quest_status` | Complete/abandon quest |

**World Building:**
| Tool | Description |
|------|-------------|
| `create_location` | Create new area |
| `create_item_template` | Define new item type |

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
- `POST /game/start-session` - Begin new game session with intro narrative
- `POST /game/chat` - Send player action, receive narrative response
- `GET /game/health` - Check agent status

## Configuration

The agent uses settings from `config.py`:
- `OPENAI_API_KEY` - Required for LLM calls
- `OPENAI_MODEL` - Model to use (default: gpt-5-mini)

## Session Memory

LangGraph's `MemorySaver` maintains conversation history per session.
Each `session_id` preserves:
- Message history
- Tool call results
- Narrative continuity

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
