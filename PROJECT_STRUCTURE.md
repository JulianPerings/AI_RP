# 📁 Project Structure

Complete overview of the AI RPG project organization.

## Directory Tree

```
AI_RP/
├── 📄 README.md                    # Main project documentation
├── 📄 QUICKSTART.md                # Quick start guide
├── 📄 ARCHITECTURE.md              # Architecture documentation
├── 📄 PROJECT_STRUCTURE.md         # This file
├── 📄 Makefile                     # Development commands
├── 📄 docker-compose.yml           # Docker orchestration
│
├── 📁 backend/                     # FastAPI Backend
│   ├── 📄 README.md                # Backend documentation
│   ├── 📄 requirements.txt         # Python dependencies
│   ├── 📄 Dockerfile               # Backend container
│   ├── 📄 .env.example             # Environment template
│   ├── 📄 .gitignore               # Git ignore rules
│   ├── 📄 pytest.ini               # Pytest configuration
│   ├── 📄 ruff.toml                # Linting configuration
│   ├── 📄 alembic.ini              # Database migration config
│   │
│   ├── 📁 app/                     # Main application
│   │   ├── 📄 __init__.py
│   │   ├── 📄 main.py              # FastAPI app entry point
│   │   │
│   │   ├── 📁 api/                 # API layer
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📁 routes/          # API endpoints
│   │   │       ├── 📄 __init__.py
│   │   │       ├── 📄 players.py   # Player management
│   │   │       ├── 📄 game.py      # Game interactions
│   │   │       └── 📄 quests.py    # Quest management
│   │   │
│   │   ├── 📁 core/                # Core infrastructure
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 config.py        # Settings & configuration
│   │   │   ├── 📄 logging.py       # Logging setup
│   │   │   └── 📄 security.py      # Auth & security
│   │   │
│   │   ├── 📁 db/                  # Database layer
│   │   │   ├── 📄 __init__.py
│   │   │   └── 📄 base.py          # DB connection & session
│   │   │
│   │   ├── 📁 models/              # SQLAlchemy models
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 player.py        # Player model
│   │   │   ├── 📄 quest.py         # Quest model
│   │   │   ├── 📄 item.py          # Item model
│   │   │   ├── 📄 inventory.py     # Inventory model
│   │   │   └── 📄 event.py         # Game event model
│   │   │
│   │   ├── 📁 schemas/             # Pydantic schemas
│   │   │   ├── 📄 __init__.py
│   │   │   ├── 📄 player.py        # Player DTOs
│   │   │   ├── 📄 quest.py         # Quest DTOs
│   │   │   ├── 📄 item.py          # Item DTOs
│   │   │   └── 📄 game.py          # Game state DTOs
│   │   │
│   │   └── 📁 services/            # Business logic
│   │       ├── 📄 __init__.py
│   │       ├── 📄 cache.py         # Redis cache service
│   │       └── 📁 llm/             # LLM integration
│   │           ├── 📄 __init__.py
│   │           ├── 📄 client.py    # OpenAI client
│   │           ├── 📄 prompts.py   # Prompt templates
│   │           └── 📄 game_master.py # Game master AI
│   │
│   ├── 📁 alembic/                 # Database migrations
│   │   ├── 📄 env.py               # Migration environment
│   │   └── 📄 script.py.mako       # Migration template
│   │
│   ├── 📁 scripts/                 # Utility scripts
│   │   └── 📄 start.sh             # Startup script
│   │
│   └── 📁 tests/                   # Test suite
│       ├── 📄 __init__.py
│       ├── 📄 conftest.py          # Test fixtures
│       └── 📄 test_api.py          # API tests
│
├── 📁 frontend/                    # Frontend (Future)
│   └── (React + TypeScript app)
│
└── 📁 old stuff/                   # Legacy code
    └── (Previous implementation)
```

## File Descriptions

### Root Level

| File | Purpose |
|------|---------|
| `README.md` | Main project overview and documentation |
| `QUICKSTART.md` | Step-by-step setup guide |
| `ARCHITECTURE.md` | System architecture and design |
| `PROJECT_STRUCTURE.md` | This file - project organization |
| `Makefile` | Common development commands |
| `docker-compose.yml` | Multi-container Docker setup |

### Backend Core (`backend/app/`)

#### Main Application
- `main.py` - FastAPI application initialization, middleware, route registration

#### API Layer (`api/routes/`)
- `players.py` - CRUD operations for players/characters
- `game.py` - Game interactions, chat with AI, location changes
- `quests.py` - Quest creation, updates, and retrieval

#### Core Infrastructure (`core/`)
- `config.py` - Environment-based settings using Pydantic
- `logging.py` - Structured logging with Loguru
- `security.py` - JWT tokens, password hashing, authentication

#### Database (`db/` & `models/`)
- `base.py` - SQLAlchemy engine, session management
- `player.py` - Player/character data model
- `quest.py` - Quest tracking and progress
- `item.py` - Item templates and properties
- `inventory.py` - Player inventory management
- `event.py` - Game event logging

#### Schemas (`schemas/`)
Pydantic models for request/response validation:
- `player.py` - PlayerCreate, PlayerResponse, PlayerUpdate
- `quest.py` - QuestCreate, QuestResponse, QuestUpdate
- `item.py` - ItemCreate, ItemResponse
- `game.py` - ChatRequest, ChatResponse, GameStateResponse

#### Services (`services/`)
- `cache.py` - Redis integration for caching and sessions
- `llm/client.py` - OpenAI API client with retry logic
- `llm/prompts.py` - Prompt templates for different scenarios
- `llm/game_master.py` - AI game master service

### Configuration Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python package dependencies |
| `.env.example` | Environment variable template |
| `Dockerfile` | Backend container definition |
| `alembic.ini` | Database migration configuration |
| `pytest.ini` | Test framework settings |
| `ruff.toml` | Code linting and formatting rules |

### Tests (`tests/`)
- `conftest.py` - Pytest fixtures and test database setup
- `test_api.py` - API endpoint tests

## Key Components

### 1. API Endpoints

```
/api/players/
├── POST   /              Create player
├── GET    /{id}          Get player
├── PATCH  /{id}          Update player
└── DELETE /{id}          Delete player

/api/game/
├── POST   /{id}/chat     Chat with game master
├── GET    /{id}/state    Get game state
└── POST   /{id}/location Change location

/api/quests/
├── POST   /              Create quest
├── GET    /player/{id}   Get player quests
├── GET    /{id}          Get quest
└── PATCH  /{id}          Update quest
```

### 2. Database Models

```python
Player          # User accounts and characters
Quest           # Quest tracking
Item            # Item templates
Inventory       # Player items
GameEvent       # Event logging
```

### 3. LLM Integration

```python
LLMClient           # OpenAI API wrapper
GameMasterService   # AI game master
Prompts             # Template library
```

### 4. Infrastructure

```python
Settings        # Configuration management
Logger          # Structured logging
CacheService    # Redis integration
Security        # Auth & encryption
```

## Data Flow

```
Request → API Route → Service Layer → Database/LLM → Response
                    ↓
                  Cache
```

## Development Workflow

1. **Local Development**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Docker Development**
   ```bash
   docker-compose up -d
   ```

3. **Testing**
   ```bash
   cd backend
   pytest
   ```

4. **Database Migrations**
   ```bash
   alembic revision --autogenerate -m "message"
   alembic upgrade head
   ```

## Environment Variables

Required in `.env`:
```env
# OpenAI
OPENAI_API_KEY=sk-...

# Security
SECRET_KEY=...

# Database
DATABASE_URL=postgresql+asyncpg://...

# Redis
REDIS_URL=redis://...
```

## Dependencies

### Core
- FastAPI - Web framework
- Uvicorn - ASGI server
- SQLAlchemy - ORM
- Pydantic - Validation

### LLM
- OpenAI - GPT integration
- LangChain - LLM framework
- Instructor - Structured outputs

### Infrastructure
- PostgreSQL - Database
- Redis - Cache
- Alembic - Migrations

### Development
- Pytest - Testing
- Ruff - Linting
- Docker - Containerization

## Port Allocation

| Service | Port | Purpose |
|---------|------|---------|
| Backend | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache & sessions |

## Future Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   ├── pages/          # Page components
│   ├── hooks/          # Custom hooks
│   ├── services/       # API clients
│   └── stores/         # State management
├── public/             # Static assets
└── package.json        # Dependencies
```

## Notes

- All Python code follows PEP 8 style
- Type hints used throughout
- Async/await for I/O operations
- Comprehensive error handling
- Structured logging
- Test coverage target: >80%

## Quick Reference

### Start Development
```bash
make start          # Start all services
make logs           # View logs
make test           # Run tests
```

### Database
```bash
make migrate        # Run migrations
make migrate-create # Create new migration
make db-shell       # Access database
```

### Cleanup
```bash
make stop           # Stop services
make clean          # Remove containers & volumes
```

---

**Last Updated**: 2024-12-06
**Version**: 0.1.0
