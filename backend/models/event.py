from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from .base import BaseModel

class Event(BaseModel):
    """Natural disaster event (fire, earthquake, flood, etc.)"""
    __tablename__ = "events"
    
    # Basic Info
    event_type = Column(String(50), nullable=False)  # 'fire', 'earthquake', 'flood'
    severity = Column(String(20), nullable=False)  # 'low', 'medium', 'high', 'critical'
    status = Column(String(20), nullable=False)  # 'detected', 'confirmed', 'resolved'
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(255), nullable=True)
    
    # Data
    data = Column(JSONB, nullable=True)  # Raw data from API
    source = Column(String(100), nullable=False)  # 'NASA', 'USGS', 'NOAA'
    
    # Timestamps
    event_timestamp = Column(DateTime, nullable=False)  # When event occurred
    
    # Tracking
    confidence = Column(Float, default=0.0)  # 0.0 - 1.0
    is_verified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Event {self.id}: {self.event_type} at ({self.latitude}, {self.longitude})>"
