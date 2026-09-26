from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from .base import BaseModel

class Analysis(BaseModel):
    """AI analysis of event threats and impacts"""
    __tablename__ = "analyses"
    
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    
    # Analysis type
    analysis_type = Column(String(50), nullable=False)  # 'threat', 'cascade', 'evacuation'
    
    # Results
    summary = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    
    # Detailed data
    data = Column(JSONB, nullable=True)
    
    # Model used
    model = Column(String(50), nullable=False)  # 'gemini-1.5-flash', etc.
    
    def __repr__(self):
        return f"<Analysis {self.id}: {self.analysis_type} for event {self.event_id}>"
