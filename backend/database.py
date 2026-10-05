import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

logger = logging.getLogger(__name__)

# Retrieve database URL from environment
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://terragrid_user:terragrid_pass@localhost:5432/terragrid_db"
)

try:
    # Create the SQLAlchemy engine
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,      # Verify connection before usage
        pool_size=10,            # Max number of connections
        max_overflow=20          # Extra connections allowed during spikes
    )
    
    # Create a configured "Session" class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database connection established successfully.")

    # Auto-create tables (like geocoding_cache) if they don't already exist
    from backend.models.base import Base
    import backend.models  # Load all models
    Base.metadata.create_all(bind=engine)

except Exception as e:
    logger.error(f"Failed to connect to database: {e}")
    SessionLocal = None

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to yield a database session.
    Ensures the session is cleanly closed after the request completes.
    """
    if not SessionLocal:
        raise RuntimeError("Database not configured. Check DATABASE_URL.")
        
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

