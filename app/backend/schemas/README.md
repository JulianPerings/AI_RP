# Schemas Directory

**Purpose**: Pydantic schemas for request validation and response serialization.

## Schema Pattern
Each module defines two schemas per entity:
- `*Create` - Input validation for POST/PUT requests
- `*Response` - Output serialization with `from_attributes=True`

## Core Entity Schemas
- `player_character.py` - PlayerCharacterCreate, PlayerCharacterResponse
- `non_player_character.py` - NonPlayerCharacterCreate, NonPlayerCharacterResponse
- `item_template.py` - **ItemTemplateCreate, ItemTemplateResponse** - Item blueprint schemas
- `item_instance.py` - **ItemInstanceCreate, ItemInstanceResponse** - Item instance schemas
- `location.py` - LocationCreate, LocationResponse
- `quest.py` - QuestCreate, QuestResponse

## Relationship System Schemas
- `race.py` - RaceCreate, RaceResponse
- `faction.py` - FactionCreate, FactionResponse
- `race_relationship.py` - RaceRelationshipCreate, RaceRelationshipResponse
- `faction_relationship.py` - FactionRelationshipCreate, FactionRelationshipResponse
- `character_relationship.py` - **CharacterRelationshipCreate, CharacterRelationshipResponse** - Unified schema for all character relationships with polymorphic type support

## Validation
- Relationship values constrained to -100 to +100 range
- Enums for behavior states, faction types, relationship types
- JSON fields for reputation and personality traits

## Usage
Schemas ensure type safety and automatic API documentation in FastAPI.
