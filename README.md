# AI RPG - AI-Powered Roleplaying Game

An immersive AI-driven roleplaying game with LLM-powered game master, dynamic quests, and intelligent NPCs.

## 🎮 Features

- **AI Game Master** - Dynamic storytelling powered by OpenAI GPT models
- **Intelligent NPCs** - Characters with unique personalities and dialogue
- **Dynamic Quests** - AI-generated quests tailored to your character
- **Persistent World** - Track items, inventory, events, and progress
- **Real-time Chat** - Interactive conversations with the game world
- **Character Progression** - Level up, gain experience, and grow stronger

## 🏗️ Architecture

### Backend (FastAPI + Python)
- Python 3.13 with modern async FastAPI
- OpenAI GPT integration for AI features
- PostgreSQL for persistent storage
- Redis for caching and sessions
- SQLAlchemy 2.0 async ORM
- Comprehensive API with automatic docs

### Frontend (Coming Soon)
- React 18+ with TypeScript
- Real-time WebSocket communication
- Beautiful UI with TailwindCSS & shadcn/ui
- Responsive design for all devices

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI_RP
   ```

2. **Configure environment**
   ```bash
   cd backend
   cp .env.example .env
   ```
   
   Edit `.env` and add your OpenAI API key:
   ```env
   OPENAI_API_KEY=your-api-key-here
   SECRET_KEY=your-secret-key-change-in-production
   ```

3. **Start the application**
   ```bash
   cd ..
   docker-compose up -d
   ```

4. **Access the API**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📚 Documentation

- [Backend Documentation](./backend/README.md)
- API Documentation: Available at `/docs` when running

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **OpenAI API** - LLM integration
- **PostgreSQL** - Primary database
- **Redis** - Caching & sessions
- **SQLAlchemy** - ORM
- **Pydantic** - Data validation
- **Alembic** - Database migrations
- **Docker** - Containerization

### Planned Frontend
- **React** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **shadcn/ui** - Component library
- **React Query** - Server state
- **Zustand** - Client state

## 🎯 Roadmap

### Phase 1: Backend Foundation ✅
- [x] FastAPI application structure
- [x] Database models (Player, Quest, Item, Inventory, Events)
- [x] LLM integration with OpenAI
- [x] Core API endpoints
- [x] Docker setup

### Phase 2: Core Gameplay (In Progress)
- [ ] Combat system
- [ ] Item and inventory management
- [ ] Quest generation and tracking
- [ ] Event system
- [ ] Character progression

### Phase 3: Frontend
- [ ] React application setup
- [ ] Character creation UI
- [ ] Chat interface
- [ ] Inventory and quest UI
- [ ] Real-time updates via WebSockets

### Phase 4: Advanced Features
- [ ] Multiplayer interactions
- [ ] World map and locations
- [ ] Advanced AI behaviors
- [ ] Voice integration
- [ ] Mobile app

## 🧪 Development

### Running Tests
```bash
cd backend
pytest
```

### Database Migrations
```bash
cd backend
alembic revision --autogenerate -m "Description"
alembic upgrade head
```

### Code Quality
```bash
cd backend
ruff format .
ruff check .
```

## 📝 API Examples

### Create a Player
```bash
curl -X POST "http://localhost:8000/api/players/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "hero123",
    "email": "hero@example.com",
    "password": "securepass123",
    "character_name": "Aragorn",
    "character_class": "Warrior"
  }'
```

### Chat with Game Master
```bash
curl -X POST "http://localhost:8000/api/game/1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to explore the nearby forest"
  }'
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- OpenAI for GPT models
- FastAPI community
- All contributors and testers
