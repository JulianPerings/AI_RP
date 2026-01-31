import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
from database import Base, engine
from api.routes import (
    player_character_router,
    non_player_character_router,
    item_template_router,
    item_instance_router,
    region_router,
    location_router,
    quest_router,
    race_router,
    faction_router,
    race_relationship_router,
    faction_relationship_router,
    character_relationship_router,
    game_router
)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run startup tasks."""
    # Auto-seed if SEED_DATABASE=true
    if os.getenv("SEED_DATABASE", "false").lower() == "true":
        from seed import seed_database
        seed_database()
    yield

app = FastAPI(
    title="AI RPG API",
    description="Backend API for AI-powered RPG game",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(player_character_router)
app.include_router(non_player_character_router)
app.include_router(item_template_router)
app.include_router(item_instance_router)
app.include_router(region_router)
app.include_router(location_router)
app.include_router(quest_router)
app.include_router(race_router)
app.include_router(faction_router)
app.include_router(race_relationship_router)
app.include_router(faction_relationship_router)
app.include_router(character_relationship_router)
app.include_router(game_router)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to AI RPG API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
