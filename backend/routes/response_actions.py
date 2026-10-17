"""
Response-phase actions on an incident: acknowledge, status, tasks, and
operator-approved alerts. Every action writes an audit row
(IncidentResponseLog). Nothing here sends an alert without an explicit
approval call.

Identity: there is no login yet, so `actor` is typed by the operator and
recorded as given. Treat it as a label, not authenticated identity.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.response import IncidentResponseLog, ResponseTask, ResponseAlert
from backend.routes.incidents import find_incident_by_id
from backend.services.notifications import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["response"])

INCIDENT_STATUSES = {"open", "investigating", "responding", "resolved"}
TASK_STATUSES = {"open", "in_progress", "done"}


class ActorBody(BaseModel):
    actor: str = Field(min_length=1, max_length=120)


class StatusBody(ActorBody):
    status: str
    note: Optional[str] = Field(default=None, max_length=1000)


class TaskCreateBody(ActorBody):
    title: str = Field(min_length=1, max_length=255)
    assignee: str = Field(min_length=1, max_length=120)


class TaskUpdateBody(ActorBody):
    status: str


class AlertDraftBody(ActorBody):
    subject: str = Field(min_length=1, max_length=255)
    body: str = Field(min_length=1, max_length=5000)
    recipients: List[str] = Field(min_length=1, max_length=20)


class AlertDecisionBody(ActorBody):
    reason: Optional[str] = Field(default=None, max_length=500)


def _event_or_404(incident_id: str, db: Session):
    event = find_incident_by_id(incident_id, db)
    if not event:
        raise HTTPException(status_code=404, detail="Incident not found")
    return event


def _log(db: Session, event_id: int, action: str, actor: str, detail: Optional[Dict[str, Any]] = None) -> None:
    db.add(IncidentResponseLog(
        event_id=event_id,
        action=action,
        actor=actor,
        detail=json.dumps(detail) if detail is not None else None,
    ))


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _serialize_state(db: Session, event_id: int) -> Dict[str, Any]:
    logs = (
        db.query(IncidentResponseLog)
        .filter(IncidentResponseLog.event_id == event_id)
        .order_by(IncidentResponseLog.created_at.asc(), IncidentResponseLog.id.asc())
        .all()
    )
    ack = next((row for row in logs if row.action == "acknowledge"), None)
    status_rows = [row for row in logs if row.action == "status_change"]
    current_status = "open"
    if status_rows:
        current_status = json.loads(status_rows[-1].detail or "{}").get("status", "open")

    tasks = (
        db.query(ResponseTask)
        .filter(ResponseTask.event_id == event_id)
        .order_by(ResponseTask.created_at.asc(), ResponseTask.id.asc())
        .all()
    )
    alerts = (
        db.query(ResponseAlert)
        .filter(ResponseAlert.event_id == event_id)
        .order_by(ResponseAlert.created_at.desc(), ResponseAlert.id.desc())
        .all()
    )
    return {
        "acknowledged": ack is not None,
        "acknowledged_by": ack.actor if ack else None,
        "acknowledged_at": _iso(ack.created_at) if ack else None,
        "status": current_status,
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "assignee": t.assignee,
                "status": t.status,
                "created_by": t.created_by,
                "created_at": _iso(t.created_at),
            }
            for t in tasks
        ],
        "alerts": [
            {
                "id": a.id,
                "subject": a.subject,
                "body": a.body,
                "recipients": json.loads(a.recipients or "[]"),
                "status": a.status,
                "created_by": a.created_by,
                "decided_by": a.decided_by,
                "created_at": _iso(a.created_at),
                "delivery_results": json.loads(a.delivery_results) if a.delivery_results else None,
            }
            for a in alerts
        ],
        "log": [
            {
                "action": row.action,
                "actor": row.actor,
                "detail": json.loads(row.detail) if row.detail else None,
                "at": _iso(row.created_at),
            }
            for row in reversed(logs)
        ],
    }


@router.get("/{incident_id}/response")
def get_response_state(incident_id: str, db: Session = Depends(get_db)):
    event = _event_or_404(incident_id, db)
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/acknowledge")
def acknowledge_incident(incident_id: str, body: ActorBody, db: Session = Depends(get_db)):
    event = _event_or_404(incident_id, db)
    existing = (
        db.query(IncidentResponseLog)
        .filter(IncidentResponseLog.event_id == event.id, IncidentResponseLog.action == "acknowledge")
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail=f"Already acknowledged by {existing.actor}")
    _log(db, event.id, "acknowledge", body.actor)
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/status")
def set_incident_status(incident_id: str, body: StatusBody, db: Session = Depends(get_db)):
    event = _event_or_404(incident_id, db)
    if body.status not in INCIDENT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of {sorted(INCIDENT_STATUSES)}")
    _log(db, event.id, "status_change", body.actor, {"status": body.status, "note": body.note})
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/tasks")
def create_task(incident_id: str, body: TaskCreateBody, db: Session = Depends(get_db)):
    event = _event_or_404(incident_id, db)
    task = ResponseTask(
        event_id=event.id,
        title=body.title.strip(),
        assignee=body.assignee.strip(),
        status="open",
        created_by=body.actor,
    )
    db.add(task)
    db.flush()
    _log(db, event.id, "task_created", body.actor, {"task_id": task.id, "title": task.title, "assignee": task.assignee})
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/tasks/{task_id}/status")
def update_task_status(incident_id: str, task_id: int, body: TaskUpdateBody, db: Session = Depends(get_db)):
    event = _event_or_404(incident_id, db)
    if body.status not in TASK_STATUSES:
        raise HTTPException(status_code=400, detail=f"Task status must be one of {sorted(TASK_STATUSES)}")
    task = db.query(ResponseTask).filter(ResponseTask.id == task_id, ResponseTask.event_id == event.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = body.status
    _log(db, event.id, "task_updated", body.actor, {"task_id": task.id, "status": body.status})
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/alerts")
def draft_alert(incident_id: str, body: AlertDraftBody, db: Session = Depends(get_db)):
    """Create an alert draft. Nothing is sent until it is approved."""
    event = _event_or_404(incident_id, db)
    allowed = {r["email"] for r in notification_service.get_alert_email_recipients(db)}
    unknown = [r for r in body.recipients if r not in allowed]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"These recipients are not on the configured email list: {', '.join(unknown)}",
        )
    alert = ResponseAlert(
        event_id=event.id,
        subject=body.subject.strip(),
        body=body.body,
        recipients=json.dumps(sorted(set(body.recipients))),
        status="draft",
        created_by=body.actor,
    )
    db.add(alert)
    db.flush()
    _log(db, event.id, "alert_drafted", body.actor, {"alert_id": alert.id, "recipients": json.loads(alert.recipients)})
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/alerts/{alert_id}/approve")
def approve_alert(incident_id: str, alert_id: int, body: ActorBody, db: Session = Depends(get_db)):
    """Send an approved draft to each recipient and record each result."""
    event = _event_or_404(incident_id, db)
    alert = db.query(ResponseAlert).filter(ResponseAlert.id == alert_id, ResponseAlert.event_id == event.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status != "draft":
        raise HTTPException(status_code=409, detail=f"Alert is already {alert.status}")

    _log(db, event.id, "alert_approved", body.actor, {"alert_id": alert.id})
    results = []
    for recipient in json.loads(alert.recipients):
        res = notification_service.send_alert_email(db, recipient, alert.subject, alert.body)
        results.append({
            "recipient": recipient,
            "success": bool(res.get("success")),
            "detail": res.get("detail"),
        })

    succeeded = sum(1 for r in results if r["success"])
    if succeeded == len(results):
        alert.status = "sent"
    elif succeeded == 0:
        alert.status = "failed"
    else:
        alert.status = "partially_failed"
    alert.decided_by = body.actor
    alert.delivery_results = json.dumps(results)
    _log(db, event.id, "alert_sent", body.actor, {"alert_id": alert.id, "status": alert.status, "delivered": succeeded, "total": len(results)})
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/alerts/{alert_id}/reject")
def reject_alert(incident_id: str, alert_id: int, body: AlertDecisionBody, db: Session = Depends(get_db)):
    event = _event_or_404(incident_id, db)
    alert = db.query(ResponseAlert).filter(ResponseAlert.id == alert_id, ResponseAlert.event_id == event.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status != "draft":
        raise HTTPException(status_code=409, detail=f"Alert is already {alert.status}")
    alert.status = "rejected"
    alert.decided_by = body.actor
    _log(db, event.id, "alert_rejected", body.actor, {"alert_id": alert.id, "reason": body.reason})
    db.commit()
    return _serialize_state(db, event.id)
