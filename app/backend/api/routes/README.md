# Routes Directory

**Purpose**: FastAPI route handlers providing CRUD operations for game entities.

## AI Game Master Routes
- `game.py` - **Game Master AI endpoints** - LangGraph-powered narrative agent
  - `POST /game/start-session` - Begin new game session with intro narrative
  - `POST /game/chat` - Send player action, receive AI-generated narrative response
  - `GET /game/combat/{player_id}` - Get active combat state (teams + HP) for frontend HUD
  - `GET /game/health` - Check Game Master agent status

## Core Entity Routes
- `player_character.py` - Player character endpoints (create, read, update, delete)
- `non_player_character.py` - NPC endpoints with AI dialogue generation
- `item_template.py` - **Item template/blueprint endpoints** - Define item types
- `item_instance.py` - **Item instance endpoints** - Manage actual items in world
- `location.py` - Game location/area endpoints
- `quest.py` - Quest management endpoints

## Relationship System Routes
- `race.py` - Race management endpoints
- `faction.py` - Faction management endpoints
- `race_relationship.py` - Race affinity matrix endpoints (includes `/between/{source}/{target}`)
- `faction_relationship.py` - Faction relationship endpoints (includes `/between/{source}/{target}`)
- `character_relationship.py` - **Unified character relationship endpoints** - Handles ALL character relationships (PC↔NPC, NPC↔NPC)

## Unified Relationship Endpoints
The `/relationships` route provides a simplified API:
- `GET /relationships?source_type=PC&source_id=1` - Get all relationships for a character
- `GET /relationships/character/{type}/{id}` - Get all relationships where character is source OR target
- `GET /relationships/between/{source_type}/{source_id}/{target_type}/{target_id}` - Get specific relationship
- Standard CRUD: `POST /`, `GET /{id}`, `PUT /{id}`, `DELETE /{id}`

## Item System Endpoints
**Templates** (`/item-templates`):
- Standard CRUD operations
- `GET /?category=weapon` - Filter by category

**Instances** (`/item-instances`):
- Standard CRUD operations
- `GET /owner/{owner_type}/{owner_id}` - Get character's inventory
- `GET /location/{location_id}` - Get items on ground at location
- `PATCH /{id}/transfer` - Transfer item ownership (trade, loot, drop)
- `PATCH /{id}/enchant` - Add/update enchantments on specific item

## Pattern
Each module exports a `router` object. The `__init__.py` re-exports them with `*_router` naming for clarity.
All routers are imported in `main.py` and registered with the FastAPI app.

Standard CRUD pattern:
- `POST /` - Create
- `GET /` - List all
- `GET /{id}` - Get by ID
- `PUT /{id}` - Update
- `DELETE /{id}` - Delete
