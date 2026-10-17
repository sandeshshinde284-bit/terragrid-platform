"""
Response-phase records: an append-only audit log, response tasks, and
operator-approved alert drafts. Every row names the operator who acted,
as typed on screen. There is no login yet, so these names are
self-declared, not authenticated.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from .base import BaseModel


class IncidentResponseLog(BaseModel):
    """Append-only record of every human action on an incident."""
    __tablename__ = "incident_response_log"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    action = Column(String(40), nullable=False)  # acknowledge, status_change, task_created, task_updated, alert_drafted, alert_approved, alert_rejected, alert_sent
    actor = Column(String(120), nullable=False)
    detail = Column(Text, nullable=True)


class ResponseTask(BaseModel):
    """A task assigned to a named contact during a response."""
    __tablename__ = "response_tasks"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    assignee = Column(String(120), nullable=False)
    status = Column(String(20), nullable=False, default="open")  # open, in_progress, done
    created_by = Column(String(120), nullable=False)


class ResponseAlert(BaseModel):
    """An alert draft. It is sent only after an operator approves it."""
    __tablename__ = "response_alerts"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    recipients = Column(Text, nullable=False)  # JSON list of email addresses
    status = Column(String(20), nullable=False, default="draft")  # draft, sent, partially_failed, failed, rejected
    created_by = Column(String(120), nullable=False)
    decided_by = Column(String(120), nullable=True)
    delivery_results = Column(Text, nullable=True)  # JSON list of {recipient, success, detail}
