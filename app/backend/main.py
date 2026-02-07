import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# ---- Logging configuration ------------------------------------------------
# DEBUG_MODE=true  → root=DEBUG (verbose: prompts, tool schemas, full payloads)
# DEBUG_MODE=false → root=INFO  (clean: one-line request/response summaries)
_log_level = logging.DEBUG if settings.DEBUG_MODE else logging.INFO
logging.basicConfig(
    level=_log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Silence noisy third-party loggers regardless of debug mode
for _quiet in ("uvicorn.access", "httpx", "httpcore", "openai", "anthropic",
               "langchain", "langsmith", "urllib3"):
    logging.getLogger(_quiet).setLevel(logging.WARNING)

if settings.DEBUG_MODE:
    logger.info("[BOOT] DEBUG_MODE is ON — verbose logging enabled")
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

# ---- Lightweight migrations (add columns to existing tables) ---------------
from sqlalchemy import text as _sa_text, inspect as _sa_inspect

_inspector = _sa_inspect(engine)
_npc_cols = {c["name"] for c in _inspector.get_columns("non_player_character")}
if "voice" not in _npc_cols:
    with engine.begin() as _conn:
        _conn.execute(_sa_text(
            "ALTER TABLE non_player_character ADD COLUMN voice VARCHAR(50)"
        ))
    logger.info("[MIGRATION] Added 'voice' column to non_player_character")


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
