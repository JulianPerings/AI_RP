"""Logging service — configurable debug logging for agent LLM calls."""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from app.config import PROJECT_ROOT

LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure and return the root game logger.

    When ``debug`` is True (or the ``AI_RPG_DEBUG`` env var is set),
    all agent ↔ LLM traffic is logged at DEBUG level to both the
    console and a timestamped log file in ``logs/``.

    In normal mode only WARNING+ goes to the console (no file).
    """
    logger = logging.getLogger("ai_rpg")
    logger.handlers.clear()
    logger.propagate = False

    debug = debug or os.getenv("AI_RPG_DEBUG", "").lower() in ("1", "true", "yes")
    level = logging.DEBUG if debug else logging.WARNING

    logger.setLevel(level)

    # --- Console handler -----------------------------------------------------
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    if debug:
        console_fmt = logging.Formatter(
            "[%(asctime)s] %(name)s.%(funcName)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S",
        )
    else:
        console_fmt = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # --- File handler (debug only) -------------------------------------------
    if debug:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            LOGS_DIR / f"session_{ts}.log", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "[%(asctime)s] %(name)s.%(funcName)s | %(levelname)s | %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
        logger.debug("Debug logging enabled — log file: logs/session_%s.log", ts)

    return logger


def get_logger(name: str = "") -> logging.Logger:
    """Return a child logger under the ``ai_rpg`` namespace."""
    base = logging.getLogger("ai_rpg")
    if name:
        return base.getChild(name)
    return base
