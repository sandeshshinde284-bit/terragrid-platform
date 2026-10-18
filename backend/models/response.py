"""
Response-phase records: an append-only audit log, response tasks, and
operator-approved alert drafts. Every row names the operator who acted,
as typed on screen. There is no login yet, so these names are
self-declared, not authenticated.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, UniqueConstraint
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
    status = Column(String(20), nullable=False, default="open")  # open, acknowledged, in_progress, blocked, done
    priority = Column(String(10), nullable=False, default="medium")  # critical, high, medium, low (lowercase)
    due_at = Column(DateTime, nullable=True)  # UTC, naive
    note = Column(Text, nullable=True)  # e.g. why a task is blocked
    created_by = Column(String(120), nullable=False)


class ResponseAlert(BaseModel):
    """An alert draft. It is sent only after an operator approves it."""
    __tablename__ = "response_alerts"

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("response_tasks.id"), nullable=True)  # the task this alert concerns, if any
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    recipients = Column(Text, nullable=False)  # JSON list of email addresses
    status = Column(String(20), nullable=False, default="draft")  # draft, sent, partially_failed, failed, rejected
    created_by = Column(String(120), nullable=False)
    decided_by = Column(String(120), nullable=True)
    delivery_results = Column(Text, nullable=True)  # JSON list of {recipient, success, detail}


class IncidentReport(BaseModel):
    """
    A saved, versioned Gemini crisis report. Each Generate or Update creates
    a new version; nothing is overwritten. Fallback (offline) results are not
    stored, so an outage cannot replace a real report.
    """
    __tablename__ = "incident_reports"
    __table_args__ = (UniqueConstraint("event_id", "version", name="uq_incident_report_version"),)

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    payload = Column(Text, nullable=False)  # JSON: the full dossier as returned by Gemini
    top_action = Column(Text, nullable=True)  # first recommendation, for quick display
    model_name = Column(String(80), nullable=False)  # the configured Gemini model


class ResponsePlanDecision(BaseModel):
    """
    An operator's decision on one recommendation from one report version.
    Approving creates a ResponseTask; the decision keeps the link to the
    report and action it came from. Decisions are final.
    """
    __tablename__ = "response_plan_decisions"
    __table_args__ = (UniqueConstraint("report_id", "action_index", name="uq_plan_decision_action"),)

    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    report_id = Column(Integer, ForeignKey("incident_reports.id"), nullable=False, index=True)
    action_index = Column(Integer, nullable=False)
    action_text = Column(Text, nullable=False)  # snapshot of the recommendation as it was reviewed
    decision = Column(String(10), nullable=False)  # approved, rejected
    task_id = Column(Integer, ForeignKey("response_tasks.id"), nullable=True)
    decided_by = Column(String(120), nullable=False)
    reason = Column(Text, nullable=True)
    # Snapshot at decision time. ai_* come from the saved report (null for reports saved before
    # these fields existed); officer_priority is set only for approvals. The decision time is created_at.
    ai_priority = Column(String(12), nullable=True)  # IMMEDIATE, HIGH, STAGED
    ai_category = Column(String(40), nullable=True)
    officer_priority = Column(String(10), nullable=True)  # critical, high, medium, low (lowercase)
