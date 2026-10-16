from backend.config import settings
import logging
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

logger = logging.getLogger(__name__)

# Retrieve database URL from environment
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,      # Verify connection before usage
    pool_size=10,            # Max number of connections
    max_overflow=20          # Extra connections allowed during spikes
)

# Create a configured "Session" class (safe to create even before DB is confirmed reachable)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _init_db(max_retries: int = 5, base_delay: float = 2.0) -> bool:
    """
    Attempt to connect and create tables, retrying with backoff.
    Returns True on success, False if all attempts failed.
    """
    from backend.models.base import Base
    import backend.models  # Load all models

    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database connection established successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))  # 2s, 4s, 8s, 16s...
                time.sleep(delay)
    return False


_db_ready = _init_db()
_db_ready = False  # Lazy: get_db() attempts connection on first request,
                     # so a slow/cold Cloud SQL connection never blocks the
                     # app from binding its port and passing Cloud Run's
                     # startup health probe.



def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to yield a database session.
    Ensures the session is cleanly closed after the request completes.
    Retries initialization once per request if startup init failed,
    so a transient cold-start failure doesn't break this instance forever.
    """
    global _db_ready
    if not _db_ready:
        _db_ready = _init_db(max_retries=1, base_delay=0)
        if not _db_ready:
            raise RuntimeError("Database not configured. Check DATABASE_URL.")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

