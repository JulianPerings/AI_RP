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

## LLM Provider

The backend can route LLM calls to either OpenAI or xAI (Grok) via OpenAI-compatible API.

- Default provider is configured via `DEFAULT_LLM_PROVIDER`.
- Requests may override provider by including `llm_provider` (`openai` or `xai`) on:
  - `POST /game/start-session`
  - `POST /game/chat`
  - `POST /game/autocomplete`

When using `llm_provider="xai"`, `XAI_API_KEY` must be set.

The following providers are recognized as placeholders but are not implemented yet:
- `gemini`
- `kimi`
- `claude`

## Logging

By default, the backend reduces log noise by setting these loggers to `WARNING` in `main.py`:
- `uvicorn.access`
- `httpx`
- `httpcore`
