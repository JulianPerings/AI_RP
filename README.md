# AI RPG Application

An AI-powered RPG game with PostgreSQL database backend and OpenAI integration.

## Project Structure

```
app/
├── backend/          # FastAPI backend
│   ├── agents/      # LangGraph AI agents
│   ├── api/         # API routes
│   ├── models/      # SQLAlchemy models
│   ├── schemas/     # Pydantic schemas
│   ├── main.py      # FastAPI app
│   ├── config.py    # Configuration
│   └── database.py  # Database connection
└── frontend/        # (To be implemented)
```

## Quick Start with Docker

1. **Set your OpenAI API key in `.env`:**
```bash
OPENAI_API_KEY=your_actual_key_here
```

2. **Start the application:**
```bash
docker-compose up --build
```

3. **Access the API:**
- API Documentation: http://localhost:8000/docs
- API Base URL: http://localhost:8000

## API Endpoints

### AI Game Master (NEW)
The Game Master is a LangGraph-powered AI agent that creates immersive narrative experiences.

- `POST /game/start-session` - Start a new game session
  ```json
  {"player_id": 1}
  ```
- `POST /game/chat` - Send player action to Game Master
  ```json
  {"message": "I approach the mysterious stranger", "player_id": 1, "session_id": "..."}
  ```
- `GET /game/health` - Check Game Master status

The agent has access to 14 tools to query and modify game state (player stats, inventory, quests, relationships, locations).

### Player Characters
- `POST /player-characters/` - Create player character
- `GET /player-characters/` - List all player characters
- `GET /player-characters/{id}` - Get specific player character
- `PUT /player-characters/{id}` - Update player character
- `DELETE /player-characters/{id}` - Delete player character

### NPCs
- `POST /npcs/` - Create NPC
- `GET /npcs/` - List all NPCs
- `GET /npcs/{id}` - Get specific NPC
- `PUT /npcs/{id}` - Update NPC
- `DELETE /npcs/{id}` - Delete NPC

### Items
- `POST /items/` - Create item
- `GET /items/` - List all items
- `GET /items/{id}` - Get specific item
- `PUT /items/{id}` - Update item
- `DELETE /items/{id}` - Delete item

### Locations
- `POST /locations/` - Create location
- `GET /locations/` - List all locations
- `GET /locations/{id}` - Get specific location
- `PUT /locations/{id}` - Update location
- `DELETE /locations/{id}` - Delete location

### Quests
- `POST /quests/` - Create quest
- `GET /quests/` - List all quests
- `GET /quests/{id}` - Get specific quest
- `PUT /quests/{id}` - Update quest
- `DELETE /quests/{id}` - Delete quest

## Database Schema

- **player_character**: Player data (name, class, level, health, gold, etc.)
- **non_player_character**: NPCs (name, type, health, dialogue, location)
- **item**: Items (name, type, description, value, power, owner/location)
- **location**: Game locations (name, description, type)
- **quest**: Quests (title, description, status, rewards, player)

## Development

### Without Docker

1. Create virtual environment:
```bash
cd app/backend
python -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up PostgreSQL and update `.env` in backend folder

4. Run the application:
```bash
uvicorn main:app --reload
```

## Technologies

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI Agent**: LangGraph, LangChain, OpenAI API (gpt-5-mini)
- **Containerization**: Docker, Docker Compose
