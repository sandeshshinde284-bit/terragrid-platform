from sqlalchemy import Column, String, Text, DateTime, Integer
from datetime import datetime
from .base import BaseModel

class GeocodingCache(BaseModel):
    """
    Permanent PostgreSQL cache for AI-generated location names.
    Prevents duplicate LLM API calls across worker processes and restarts.
    """
    __tablename__ = "geocoding_cache"
    
    # MD5 hash of raw_text + coordinates to allow lightning-fast lookups
    location_signature = Column(String(64), unique=True, index=True, nullable=False)
    
    # The clean AI-deduced output (e.g. "Apalachicola, FL, US")
    formatted_location = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<GeocodingCache {self.location_signature}: {self.formatted_location}>"
