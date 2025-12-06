# AI RPG Backend

A modern FastAPI-based backend for an AI-powered roleplaying game with LLM integration.

## Features

- **Python 3.13** - Latest Python with improved performance
- **FastAPI** - Modern async Python web framework
- **OpenAI Integration** - LLM-powered game master and NPCs
- **PostgreSQL** - Persistent data storage
- **Redis** - Caching and session management
- **SQLAlchemy 2.0** - Async ORM
- **Pydantic v2** - Data validation
- **Alembic** - Database migrations
- **Docker** - Containerized deployment

## Architecture

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Core configuration
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   ├── llm/          # LLM integration
│   │   └── cache.py      # Redis cache
│   └── main.py           # FastAPI app
├── alembic/              # Database migrations
├── tests/                # Test suite
└── requirements.txt      # Python dependencies
```

## Quick Start

### 1. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=your-api-key-here
SECRET_KEY=your-secret-key-here
```

### 2. Using Docker (Recommended)

Start all services:

```bash
cd ..
docker-compose up -d
```

The API will be available at `http://localhost:8000`

### 3. Local Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Start PostgreSQL and Redis (or use Docker for just these):

```bash
docker-compose up -d postgres redis
```

Run database migrations:

```bash
alembic upgrade head
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Migrations

Create a new migration:

```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:

```bash
alembic upgrade head
```

Rollback migration:

```bash
alembic downgrade -1
```

## API Endpoints

### Players
- `POST /api/players/` - Create new player
- `GET /api/players/{id}` - Get player details
- `PATCH /api/players/{id}` - Update player
- `DELETE /api/players/{id}` - Delete player

### Game
- `POST /api/game/{player_id}/chat` - Chat with game master
- `GET /api/game/{player_id}/state` - Get game state
- `POST /api/game/{player_id}/location` - Change location

### Quests
- `POST /api/quests/` - Create quest
- `GET /api/quests/player/{player_id}` - Get player quests
- `GET /api/quests/{quest_id}` - Get quest details
- `PATCH /api/quests/{quest_id}` - Update quest

## Testing

Run tests:

```bash
pytest
```

With coverage:

```bash
pytest --cov=app tests/
```

## Development

### Code Quality

Format code:

```bash
ruff format .
```

Lint code:

```bash
ruff check .
```

### Adding New Features

1. Create models in `app/models/`
2. Create schemas in `app/schemas/`
3. Add business logic in `app/services/`
4. Create API routes in `app/api/routes/`
5. Register routes in `app/main.py`
6. Create database migration

## Production Deployment

1. Set `ENVIRONMENT=production` in `.env`
2. Use strong `SECRET_KEY`
3. Configure proper database credentials
4. Set up SSL/TLS
5. Use a reverse proxy (nginx)
6. Enable monitoring and logging

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `SECRET_KEY` - JWT secret key (required)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `DEBUG` - Enable debug mode (development only)

## License

MIT
