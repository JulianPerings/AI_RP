# 🚀 Quick Start Guide

Get your AI RPG backend up and running in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- (Optional) Python 3.13+ for local development

## Step-by-Step Setup

### 1. Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit the `.env` file and set your keys:

```env
OPENAI_API_KEY=sk-your-actual-openai-key-here
SECRET_KEY=your-random-secret-key-here
```

💡 **Tip**: Generate a secure secret key with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Start the Application

From the project root:

```bash
docker-compose up -d
```

This will start:
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- FastAPI backend (port 8000)

### 3. Verify It's Running

Open your browser to:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

You should see the interactive API documentation!

## 🎮 Try It Out

### Create Your First Character

Using the Swagger UI at http://localhost:8000/docs:

1. Find the `POST /api/players/` endpoint
2. Click "Try it out"
3. Fill in the request body:

```json
{
  "username": "hero123",
  "email": "hero@example.com",
  "password": "securepass123",
  "character_name": "Aragorn",
  "character_class": "Warrior"
}
```

4. Click "Execute"
5. Note the `id` in the response (you'll need this!)

### Chat with the Game Master

1. Find the `POST /api/game/{player_id}/chat` endpoint
2. Enter your player ID from above
3. Try this message:

```json
{
  "message": "I want to explore the nearby forest and look for adventure"
}
```

4. Watch the AI Game Master respond with a dynamic story!

## 📊 View Your Game State

Use `GET /api/game/{player_id}/state` to see:
- Character stats
- Active quests
- Current location
- Available actions

## 🛠️ Useful Commands

### View Logs
```bash
docker-compose logs -f backend
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

### Access Database
```bash
docker-compose exec postgres psql -U postgres -d ai_rpg
```

### Run Tests
```bash
cd backend
pytest
```

## 🐛 Troubleshooting

### "Connection refused" errors
- Make sure Docker is running
- Check if ports 5432, 6379, 8000 are available
- Run `docker-compose ps` to see service status

### "Invalid API key" errors
- Verify your OpenAI API key in `.env`
- Make sure there are no extra spaces
- Check your OpenAI account has credits

### Database errors
- Run `docker-compose down -v` to reset
- Then `docker-compose up -d` to start fresh

## 📚 Next Steps

1. **Explore the API**: Try all endpoints in the Swagger UI
2. **Create Quests**: Use `POST /api/quests/` to add quests
3. **Customize Prompts**: Edit `backend/app/services/llm/prompts.py`
4. **Add Features**: Check out the codebase structure in `backend/`

## 🎯 Example Workflow

```bash
# 1. Create a character
curl -X POST "http://localhost:8000/api/players/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "adventurer",
    "email": "test@example.com",
    "password": "password123",
    "character_name": "Gandalf"
  }'

# 2. Chat with game master (use the ID from step 1)
curl -X POST "http://localhost:8000/api/game/1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What adventures await me?"
  }'

# 3. Check game state
curl "http://localhost:8000/api/game/1/state"
```

## 💡 Tips

- The AI responses are cached in Redis for better performance
- All game data persists in PostgreSQL
- Check logs with `docker-compose logs -f` for debugging
- Use the Makefile for common tasks: `make start`, `make stop`, `make logs`

## 🆘 Need Help?

- Check the [Backend README](./backend/README.md) for detailed docs
- Review the API documentation at `/docs`
- Look at the code examples in `backend/tests/`

Happy adventuring! 🗡️✨
