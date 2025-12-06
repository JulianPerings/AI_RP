# 🏗️ Architecture Documentation

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│                    (Future: React + TS)                      │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Chat   │  │ Inventory│  │  Quests  │  │Character │   │
│  │    UI    │  │    UI    │  │    UI    │  │   Stats  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                    HTTP/WebSocket
                            │
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  API Routes                           │  │
│  │  /players  /game  /quests  /items  /inventory        │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Business Logic Layer                     │  │
│  │                                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Game Master │  │   Cache     │  │   Events    │  │  │
│  │  │   Service   │  │  Service    │  │   System    │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Data Access Layer                        │  │
│  │         SQLAlchemy Models & Schemas                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
           │                    │                    │
           │                    │                    │
    ┌──────▼──────┐      ┌─────▼─────┐      ┌──────▼──────┐
    │  PostgreSQL │      │   Redis   │      │  OpenAI API │
    │  (Database) │      │  (Cache)  │      │    (LLM)    │
    └─────────────┘      └───────────┘      └─────────────┘
```

## Component Breakdown

### 1. API Layer (`app/api/`)

**Routes:**
- `players.py` - Player/character management
- `game.py` - Game interactions and chat
- `quests.py` - Quest management
- Future: `items.py`, `inventory.py`, `combat.py`

**Responsibilities:**
- Request validation
- Response formatting
- Error handling
- Route registration

### 2. Business Logic Layer (`app/services/`)

#### Game Master Service (`llm/game_master.py`)
```python
GameMasterService
├── generate_response()      # Main game narrative
├── generate_npc_dialogue()  # NPC conversations
├── generate_quest()         # Dynamic quest creation
└── describe_location()      # World descriptions
```

#### LLM Client (`llm/client.py`)
- OpenAI API integration
- Retry logic with exponential backoff
- Token usage tracking
- Error handling

#### Cache Service (`cache.py`)
- Redis connection management
- Session storage
- LLM response caching
- Rate limiting data

### 3. Data Layer

#### Models (`app/models/`)
```
Player
├── id, username, email
├── character_name, character_class
├── level, experience
├── health, mana
├── current_location
├── game_state (JSON)
└── relationships: inventory, quests, events

Quest
├── id, player_id
├── title, description, quest_type
├── status, progress
├── objectives (JSON)
└── rewards (JSON)

Item
├── id, name, description
├── item_type, rarity
├── value, weight
├── stats (JSON)
└── effects (JSON)

Inventory
├── player_id, item_id
├── quantity
└── equipped

GameEvent
├── player_id
├── event_type, event_name
├── event_data (JSON)
└── created_at
```

#### Schemas (`app/schemas/`)
- Pydantic models for validation
- Request/response DTOs
- Type safety

### 4. Core Infrastructure (`app/core/`)

- `config.py` - Environment-based configuration
- `logging.py` - Structured logging with Loguru
- `security.py` - JWT tokens, password hashing

## Data Flow Examples

### Chat Interaction Flow

```
User Message
    │
    ▼
API Endpoint (/game/{id}/chat)
    │
    ├─► Validate Request (Pydantic)
    │
    ├─► Get Player from DB
    │
    ├─► Get Active Quests
    │
    ├─► Check Cache for similar response
    │   └─► Cache Miss
    │
    ├─► Call Game Master Service
    │   │
    │   ├─► Build Context (player, location, quests)
    │   │
    │   ├─► Format Prompt
    │   │
    │   └─► Call OpenAI API
    │       └─► Return AI Response
    │
    ├─► Cache Response (Redis)
    │
    ├─► Log Event (GameEvent)
    │
    └─► Return Response to User
```

### Quest Creation Flow

```
Create Quest Request
    │
    ▼
API Endpoint (/quests/)
    │
    ├─► Validate Quest Data
    │
    ├─► Verify Player Exists
    │
    ├─► Create Quest Record (PostgreSQL)
    │
    ├─► Log Event (QUEST_STARTED)
    │
    ├─► Update Player State
    │
    └─► Return Quest Details
```

## Technology Stack Details

### Backend Framework
- **FastAPI** - Async Python web framework
  - Automatic OpenAPI docs
  - Type hints & validation
  - WebSocket support
  - Dependency injection

### Database
- **PostgreSQL** - Primary data store
  - ACID compliance
  - JSON support for flexible data
  - Full-text search capabilities
  
- **SQLAlchemy 2.0** - Async ORM
  - Type-safe queries
  - Relationship management
  - Migration support via Alembic

### Caching & Queue
- **Redis** - In-memory data store
  - Session management
  - LLM response caching
  - Rate limiting
  - Future: Pub/Sub for events

### LLM Integration
- **OpenAI API** - GPT models
  - GPT-4 for complex narratives
  - GPT-3.5 for quick responses
  - Function calling for structured data
  
- **LangChain** - LLM framework (planned)
  - Prompt templates
  - Memory management
  - Agent capabilities

### Security
- **JWT** - Token-based auth
- **bcrypt** - Password hashing
- **CORS** - Cross-origin protection
- **Rate Limiting** - API protection

## Deployment Architecture

### Docker Compose (Development)
```
┌─────────────┐
│   Backend   │ :8000
│  (FastAPI)  │
└─────────────┘
       │
       ├─────► PostgreSQL :5432
       │
       ├─────► Redis :6379
       │
       └─────► OpenAI API (external)
```

### Production (Future)
```
Internet
    │
    ▼
┌─────────────┐
│   Nginx     │ :80, :443
│ (Reverse    │
│   Proxy)    │
└─────────────┘
    │
    ├─► Backend (Multiple instances)
    │   └─► Load Balanced
    │
    ├─► PostgreSQL (Primary + Replica)
    │
    ├─► Redis (Cluster)
    │
    └─► Monitoring (Prometheus + Grafana)
```

## Scaling Considerations

### Horizontal Scaling
- Multiple FastAPI instances behind load balancer
- Stateless design (sessions in Redis)
- Database connection pooling

### Caching Strategy
```
Cache Layers:
1. Redis - Session data (TTL: 1 hour)
2. Redis - LLM responses (TTL: 24 hours)
3. Redis - Quest templates (TTL: 1 week)
4. PostgreSQL - Permanent data
```

### Performance Optimization
- Async I/O throughout
- Database query optimization
- LLM response caching
- Connection pooling
- Background tasks with Celery (future)

## Security Architecture

### Authentication Flow
```
1. User Login
   └─► Validate credentials
       └─► Generate JWT token
           └─► Return token

2. Authenticated Request
   └─► Extract JWT from header
       └─► Validate token
           └─► Extract user info
               └─► Process request
```

### Data Protection
- Passwords: bcrypt hashed
- API Keys: Environment variables
- Secrets: Never in code/git
- Database: Encrypted connections
- HTTPS: Required in production

## Future Enhancements

### Phase 1 (Current)
- ✅ Core API structure
- ✅ Database models
- ✅ LLM integration
- ✅ Basic game mechanics

### Phase 2
- [ ] Combat system
- [ ] Item crafting
- [ ] Advanced quest system
- [ ] WebSocket real-time updates

### Phase 3
- [ ] Multiplayer features
- [ ] World map system
- [ ] Advanced AI behaviors
- [ ] Voice integration

### Phase 4
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Mod support
- [ ] Community features

## Monitoring & Observability

### Logging
- Structured logs (Loguru)
- Request/response logging
- Error tracking
- Performance metrics

### Future Monitoring
- Prometheus metrics
- Grafana dashboards
- Sentry error tracking
- LangSmith LLM tracing

## Development Workflow

```
1. Feature Branch
   └─► Write Code
       └─► Write Tests
           └─► Run Tests Locally
               └─► Commit & Push
                   └─► CI/CD Pipeline
                       ├─► Run Tests
                       ├─► Lint Code
                       ├─► Build Docker
                       └─► Deploy (if main)
```

## API Design Principles

1. **RESTful** - Standard HTTP methods
2. **Versioned** - `/api/v1/` prefix (future)
3. **Documented** - Auto-generated OpenAPI
4. **Validated** - Pydantic schemas
5. **Consistent** - Standard response formats
6. **Secure** - Authentication required
7. **Performant** - Async throughout

## Database Schema Design

### Normalization
- 3NF for core entities
- JSON for flexible/dynamic data
- Indexes on foreign keys
- Composite indexes for queries

### Relationships
```
Player 1──────* Inventory *──────1 Item
   │
   ├──────* Quest
   │
   └──────* GameEvent
```

## Error Handling Strategy

```python
HTTP Status Codes:
200 - Success
201 - Created
204 - No Content
400 - Bad Request (validation)
401 - Unauthorized
404 - Not Found
500 - Server Error

Error Response Format:
{
  "detail": "Error message",
  "error_code": "SPECIFIC_ERROR",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

This architecture provides a solid foundation for a scalable, maintainable AI RPG system with room for future enhancements.
