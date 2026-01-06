# AI RPG Application

An AI-powered RPG game with React frontend, FastAPI backend, and OpenAI Game Master.

## Project Structure

```
app/
├── backend/         # FastAPI backend
│   ├── agents/      # LangGraph AI agents & tools
│   ├── api/         # API routes
│   ├── models/      # SQLAlchemy models
│   ├── schemas/     # Pydantic schemas
│   ├── main.py      # FastAPI app
│   ├── config.py    # Configuration
│   └── database.py  # Database connection
└── frontend/        # React + Vite UI
    ├── src/
    │   ├── views/   # PlayerList, CreatePlayer, Chat
    │   ├── api/     # API client
    │   └── App.jsx
    └── vite.config.js
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

3. **Access the application:**
- **Frontend UI**: http://localhost:5173
- **SWAGGER API endpoints**: http://localhost:8000/docs
- **API Base**: http://localhost:8000

## Features

### Frontend UI
- **Player List** - View all characters with stats (health, gold, XP, level)
- **Create Character** - Form with name, class, race, location, backstory, starting gold/health
- **Chat Interface** - Real-time conversation with AI Game Master
  - Loading indicator while GM responds
  - Tool calls displayed for transparency
  - Stats refresh after each response

### AI Game Master
LangGraph-powered agent that creates immersive narratives using 20+ tools:
- Query/modify player stats, inventory, quests, relationships
- Create items with unique buffs/flaws
- Spawn NPCs and manage locations
- Parse character backstories to auto-create items/NPCs on session start
- Long-term memory system for continuity across sessions

### Session Management
- Persistent chat history per session
- Previous session summary

## API Endpoints

### Game Master
- `POST /game/start-session` - Start session (uses existing session_id if available)
- `POST /game/chat` - Send player action, receive narrative response
- `GET /game/history/{session_id}` - Get chat history
- `POST /game/memory/summarize/{session_id}` - Generate session summary
- `GET /game/memory/search/{player_id}?query=...` - Search past memories

### Player Characters
- `POST /player-characters/` - Create player character
- `GET /player-characters/` - List all player characters
- `GET /player-characters/{id}` - Get specific player character
- `PUT /player-characters/{id}` - Update player character
- `DELETE /player-characters/{id}` - Delete player character

### Other Resources
Standard CRUD endpoints for: NPCs, Items, Locations, Quests, Races, Factions

## Database Schema

### Core Models
- **player_character**: Name, class, level, health, gold, current_session_id
- **non_player_character**: Name, type, health, behavior_state, personality_traits
- **item_template**: Item blueprints (name, category, rarity, properties)
- **item_instance**: Actual items with owner, location, buffs, flaws, enchantments
- **location**: Name, description, type
- **quest**: Title, description, status, rewards
- **chat_session**: Session_id, player_id, summary, keywords (for memory)
- **chat_message**: Role, content, tool_calls, timestamps

### Relationships
- **character_relationship**: Unified PC↔NPC, NPC↔NPC relationships with canonical ordering
- **race_relationship**: Race affinity matrix
- **faction_relationship**: Faction dynamics

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

- **Frontend**: React 18, React Router, Vite
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **AI Agent**: LangGraph, LangChain, OpenAI API (gpt-5-mini)
- **Containerization**: Docker, Docker Compose

## Recent Updates

### Bug Fixes
- Fixed tool calls accumulation (unique thread per invocation)
- Fixed session start prompt appearing in chat history
- Fixed double session creation (player creation + start-session)
- Fixed React StrictMode double-initialization

### New Features
- **Region & Location System** - Locations link to regions with modifiers (danger, wealth, climate)
- **Improved Storytelling** - No inventory dumps, no explicit options, concise prose
- **Duplicate Prevention** - GM checks existing locations/NPCs before creating
- **NPC Movement** - Escorts move with player, companions auto-follow
- Item uniqueness system with buffs/flaws
- Backstory parsing to auto-spawn items/NPCs
- Long-term memory system for session continuity
