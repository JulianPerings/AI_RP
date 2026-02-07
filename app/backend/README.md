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
Each provider exposes multiple selectable models via `MODEL_REGISTRY`.

| Provider | ID | Backend | Default model | Thinking |
|----------|----|---------|---------------|----------|
| OpenAI | `openai` | ChatOpenAI | gpt-5-mini | `reasoning_effort` |
| xAI (Grok) | `xai` | ChatOpenAI (base_url) | grok-4-1-fast-reasoning | — |
| Google Gemini | `gemini` | ChatOpenAI (OpenAI-compat) | gemini-2.5-flash-preview-09-2025 | `reasoning_effort` |
| Anthropic Claude | `claude` | ChatAnthropic | claude-haiku-4-5-latest | `extended_thinking` |
| Moonshot Kimi | `kimi` | ChatOpenAI (base_url) | kimi-k2.5 | — |
| Z.AI / ZhipuAI | `zai` | ChatOpenAI (base_url) | glm-4.7-flash | — |

- Default provider is configured via `DEFAULT_LLM_PROVIDER` in `.env`.
- Requests may override provider, model, and thinking mode by including `llm_provider`, `model`, and `thinking` on:
  - `POST /game/start-session`
  - `POST /game/chat`
  - `POST /game/autocomplete`
- `GET /game/providers` returns providers with their models and thinking capability, so the frontend settings modal can be populated dynamically.
- The frontend stores the selection in `localStorage` (`llm_provider`, `llm_model`, `llm_thinking`) and a gear icon on the home screen opens the settings.

## Logging

Controlled by `DEBUG_MODE` in `.env`:

- **`DEBUG_MODE=false`** (default) — Clean INFO output: one-line summaries per request
  ```
  [LLM] openai/gpt-5-mini thinking=False
  [CHAT] Player 2 | provider=openai model=gpt-5-mini | History: 20 msgs
  [RESPONSE] 3 tool calls | Response length: 463
  ```
- **`DEBUG_MODE=true`** — Verbose DEBUG output: full prompts, tool schemas, tool call args/results, LLM kwargs

Third-party loggers (`uvicorn.access`, `httpx`, `httpcore`, `openai`, `anthropic`, `langchain`, `langsmith`) are silenced to `WARNING` regardless of debug mode.

## Text-to-Speech (TTS)

Gemini-powered TTS with a director LLM that transforms GM narrative into multi-speaker audio.
Requires `GEMINI_API_KEY`. See `agents/README.md` for the full pipeline architecture.

| Setting | Default | Description |
|---------|---------|-------------|
| `TTS_MODEL` | `gemini-2.5-flash-preview-tts` | Gemini TTS model |
| `TTS_DIRECTOR_MODEL` | `gemini-2.5-flash-lite` | LLM for text → TTS script transformation |
| `TTS_NARRATOR_VOICE` | `Charon` | Narrator voice (male, informative) |
| `TTS_CHARACTER_VOICE_FEMALE` | `Aoede` | Default female NPC voice |
| `TTS_CHARACTER_VOICE_MALE` | `Puck` | Default male NPC voice |

API: `POST /game/tts` with `{"text": "..."}` → returns `audio/wav`.
Frontend toggle in settings modal (only visible when Gemini key is configured).
