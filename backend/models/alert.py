from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Text
from .base import BaseModel

class Alert(BaseModel):
    """Emergency alert to be sent to users"""
    __tablename__ = "alerts"
    
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=True)
    
    # Alert info
    alert_type = Column(String(50), nullable=False)  # 'evacuation', 'shelter', 'resource'
    status = Column(String(20), nullable=False)  # 'pending', 'sent', 'delivered', 'failed'
    
    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)
    
    # Delivery
    channels = Column(String(255), nullable=True)  # 'sms,email,push'
    
    # Status tracking
    is_critical = Column(Boolean, default=False)
    retry_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Alert {self.id}: {self.alert_type} for event {self.event_id}>"
