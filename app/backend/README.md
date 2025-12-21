# Backend Directory

**Purpose**: FastAPI backend server for AI RPG game with PostgreSQL database.

## Key Files
- `main.py` - FastAPI application entry point, router registration
- `database.py` - SQLAlchemy database connection and session management
- `config.py` - Environment configuration and settings
- `seed.py` - Database seed script with initial game data
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## Subdirectories
- `api/` - API route handlers
- `models/` - SQLAlchemy ORM models (database tables)
- `schemas/` - Pydantic schemas for request/response validation
- `agents/` - LangGraph AI Game Master agent

## Database Seeding

The seed script populates the database with starter content:
- **2 Locations**: The Rusty Tankard (tavern), Whispering Woods (wilderness)
- **3 Races**: Human, Elf, Dwarf (with relationship modifiers)
- **1 Faction**: Merchants Guild
- **1 NPC**: Greta Ironbrew (dwarven innkeeper)

### Auto-seed on startup
Set `SEED_DATABASE=true` in environment (default in docker-compose).

### Manual seed
```bash
docker-compose exec backend python seed.py
```

## Tech Stack
FastAPI, SQLAlchemy, PostgreSQL, OpenAI API, LangGraph, LangChain
