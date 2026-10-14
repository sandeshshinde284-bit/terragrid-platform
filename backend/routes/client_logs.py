"""
Frontend log ingestion.

The browser can't write to a file on its own, so the frontend's structured
logger (frontend/src/utils/logger.ts) POSTs each log line here, and this
route appends it to logs/frontend/frontend.log - a dedicated file handler,
separate from the backend's own logs/backend/backend.log, so the two never
get mixed together in one file.

This endpoint never raises back to the caller except on a malformed
request body: a log that can't be written to disk is itself only logged
(to the backend's own logger), never surfaced as a failure to the user's
browser - logging a problem should never create a second problem.
"""
import logging
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/api/v1/client-logs", tags=["client-logs"])

# Dedicated logger + file handler, kept separate from the root logger
# (propagate=False) so frontend lines land only in logs/frontend/frontend.log
# and never get interleaved into the backend's own log file or console.
_frontend_logger = logging.getLogger("frontend")
_frontend_logger.propagate = False
_frontend_logger.setLevel(logging.INFO)

if not _frontend_logger.handlers:
    root_dir = Path(__file__).resolve().parent.parent.parent
    log_dir = root_dir / "logs" / "frontend"
    log_dir.mkdir(parents=True, exist_ok=True)

    _handler = RotatingFileHandler(
        filename=log_dir / "frontend.log",
        mode="a",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    _handler.setFormatter(
        logging.Formatter(fmt="%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    )
    _frontend_logger.addHandler(_handler)


class ClientLogEntry(BaseModel):
    level: str = Field(description="info | warn | error")
    message: str = Field(description="The formatted log line, same text shown in the browser console")
    url: Optional[str] = Field(default=None, description="The page the log came from")
    client_time: Optional[str] = Field(default=None, description="Client-side ISO timestamp, informational only - the server's own clock is what orders the file")


_LEVEL_MAP = {"info": logging.INFO, "warn": logging.WARNING, "error": logging.ERROR}


@router.post("")
async def ingest_client_log(entry: ClientLogEntry) -> dict:
    level = _LEVEL_MAP.get(entry.level.lower(), logging.INFO)
    location = f" url={entry.url}" if entry.url else ""
    _frontend_logger.log(level, f"{entry.message}{location}")
    return {"status": "logged"}
