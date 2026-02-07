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
FastAPI, SQLAlchemy, PostgreSQL, LangGraph, LangChain, LangChain-Anthropic

## LLM Providers

All provider logic lives in `agents/llm_factory.py`. A provider is available when its API key is set in `.env`.

| Provider | ID | Backend | Model default |
|----------|----|---------|---------------|
| OpenAI | `openai` | ChatOpenAI | gpt-5-mini |
| xAI (Grok) | `xai` | ChatOpenAI (base_url) | grok-4-1-fast-reasoning |
| Google Gemini | `gemini` | ChatOpenAI (OpenAI-compat) | gemini-2.5-flash-preview-09-2025 |
| Anthropic Claude | `claude` | ChatAnthropic | claude-haiku-4-5-latest |
| Moonshot Kimi | `kimi` | ChatOpenAI (base_url) | kimi-k2.5 |
| Z.AI / ZhipuAI | `zai` | ChatOpenAI (base_url) | glm-4.7-flash |

- Default provider is configured via `DEFAULT_LLM_PROVIDER` in `.env`.
- Requests may override the provider by including `llm_provider` on:
  - `POST /game/start-session`
  - `POST /game/chat`
  - `POST /game/autocomplete`
- `GET /game/providers` returns the list of providers that have a key configured, so the frontend can populate a selector dynamically.

## Logging

By default, the backend reduces log noise by setting these loggers to `WARNING` in `main.py`:
- `uvicorn.access`
- `httpx`
- `httpcore`
