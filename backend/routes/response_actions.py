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
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.response import IncidentResponseLog, ResponseTask, ResponseAlert, IncidentReport, ResponsePlanDecision, ResponsePlan
from backend.routes.incidents import find_incident_by_id
from backend.services.notifications import notification_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/incidents", tags=["response"])

INCIDENT_STATUSES = {"open", "investigating", "responding", "resolved"}
TASK_STATUSES = {"open", "acknowledged", "in_progress", "blocked", "done"}
PRIORITIES = {"critical", "high", "medium", "low"}  # stored lowercase; the officer picks one per approval


class ActorBody(BaseModel):
    actor: str = Field(min_length=1, max_length=120)

    @field_validator("actor")
    @classmethod
    def _actor_not_blank(cls, value: str) -> str:
        # Typed name, recorded as given; surrounding spaces removed and blank names refused.
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Enter the officer's name")
        return cleaned


class StatusBody(ActorBody):
    status: str
    note: Optional[str] = Field(default=None, max_length=1000)


class TaskCreateBody(ActorBody):
    title: str = Field(min_length=1, max_length=255)
    assignee: str = Field(min_length=1, max_length=120)
    priority: str = Field(default="medium")
    due_at: Optional[datetime] = None


class TaskUpdateBody(ActorBody):
    status: str
    note: Optional[str] = Field(default=None, max_length=500)


class AlertDraftBody(ActorBody):
    task_id: Optional[int] = None
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


def _to_utc_naive(dt: Optional[datetime]) -> Optional[datetime]:
    """Store deadlines as naive UTC, like the rest of the tables."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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

    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    tasks = sorted(
        db.query(ResponseTask).filter(ResponseTask.event_id == event_id).all(),
        key=lambda t: (priority_rank.get(t.priority, 1), t.due_at or datetime.max, t.id),
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
                "priority": t.priority,
                "due_at": _iso(t.due_at),
                "note": t.note,
                "created_by": t.created_by,
                "created_at": _iso(t.created_at),
            }
            for t in tasks
        ],
        "alerts": [
            {
                "id": a.id,
                "task_id": a.task_id,
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
    priority = body.priority.strip().lower()
    if priority not in PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Priority must be one of {sorted(PRIORITIES)}")
    task = ResponseTask(
        event_id=event.id,
        title=body.title.strip(),
        assignee=body.assignee.strip(),
        status="open",
        priority=priority,
        due_at=_to_utc_naive(body.due_at),
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
    if body.status == "blocked" and not (body.note and body.note.strip()):
        raise HTTPException(status_code=400, detail="Say why the task is blocked")
    task.status = body.status
    task.note = body.note.strip() if body.note and body.note.strip() else None
    _log(db, event.id, "task_updated", body.actor, {"task_id": task.id, "status": body.status, "note": task.note})
    db.commit()
    return _serialize_state(db, event.id)


@router.post("/{incident_id}/response/alerts")
def draft_alert(incident_id: str, body: AlertDraftBody, db: Session = Depends(get_db)):
    """Create an alert draft. Nothing is sent until it is approved."""
    event = _event_or_404(incident_id, db)
    if body.task_id is not None:
        task = db.query(ResponseTask).filter(ResponseTask.id == body.task_id, ResponseTask.event_id == event.id).first()
        if not task:
            raise HTTPException(status_code=400, detail="That task does not belong to this incident")
    allowed = {r["email"] for r in notification_service.get_alert_email_recipients(db)}
    unknown = [r for r in body.recipients if r not in allowed]
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"These recipients are not on the configured email list: {', '.join(unknown)}",
        )
    alert = ResponseAlert(
        event_id=event.id,
        task_id=body.task_id,
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


# ---------------------------------------------------------------------------
# Response plan: operator decisions on the latest crisis report's
# recommendations. Approving creates a ResponseTask that remembers which
# report version and action it came from. Reports are never edited here.
# ---------------------------------------------------------------------------

class PlanDetailsBody(ActorBody):
    name: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)


def _plan_details_out(row: Optional[ResponsePlan]) -> Optional[Dict[str, Any]]:
    if row is None:
        return None
    return {
        "name": row.name,
        "description": row.description,
        "created_by": row.created_by,
        "created_at": row.created_at.isoformat() + "Z",
        "updated_by": row.updated_by,
        "updated_at": row.updated_at.isoformat() + "Z",
    }


class PlanDecisionBody(ActorBody):
    report_id: int
    action_index: int = Field(ge=0)
    decision: str  # approve | reject
    assignee: Optional[str] = Field(default=None, max_length=120)
    priority: Optional[str] = Field(default=None, max_length=10)  # required to approve; ignored on reject
    due_at: Optional[datetime] = None
    reason: Optional[str] = Field(default=None, max_length=500)


def _task_out(task: ResponseTask, report_version: Optional[int]) -> Dict[str, Any]:
    return {
        "id": task.id,
        "title": task.title,
        "assignee": task.assignee,
        "status": task.status,
        "priority": task.priority,
        "due_at": task.due_at.isoformat() + "Z" if task.due_at else None,
        "note": task.note,
        "created_by": task.created_by,
        "created_at": task.created_at.isoformat() + "Z",
        # The report version the task came from. None for tasks created directly, not from a recommendation.
        "report_version": report_version,
    }


@router.get("/{incident_id}/response/plan")
def get_response_plan(incident_id: str, db: Session = Depends(get_db)):
    """
    Plan state for the Response tab.
    - actions: the latest report's recommendations, each with its AI values and its decision so far.
    - tasks: every task for the incident, from all report versions, each with the version it came from.
    - review: counts for the latest report's recommendations.
    - task_summary: progress for tasks approved from any report version.
    """
    from backend.services.report_versions import latest_report, report_payload
    event = _event_or_404(incident_id, db)
    report = latest_report(db, event.id)

    # Every decision for this incident, paired with the version of the report it belongs to.
    all_decisions = (
        db.query(ResponsePlanDecision, IncidentReport.version)
        .join(IncidentReport, IncidentReport.id == ResponsePlanDecision.report_id)
        .filter(ResponsePlanDecision.event_id == event.id)
        .all()
    )
    version_by_task = {d.task_id: version for d, version in all_decisions if d.task_id is not None}
    approved_task_ids = {d.task_id for d, _ in all_decisions if d.decision == "approved" and d.task_id is not None}

    tasks = (
        db.query(ResponseTask)
        .filter(ResponseTask.event_id == event.id)
        .order_by(ResponseTask.created_at.asc(), ResponseTask.id.asc())
        .all()
    )
    tasks_by_id = {t.id: t for t in tasks}
    tasks_out = [_task_out(t, version_by_task.get(t.id)) for t in tasks]

    by_status = {status: 0 for status in sorted(TASK_STATUSES)}
    approved_tasks = [tasks_by_id[tid] for tid in approved_task_ids if tid in tasks_by_id]
    for t in approved_tasks:
        by_status[t.status] = by_status.get(t.status, 0) + 1
    task_summary = {
        "approved": len(approved_tasks),
        "done": by_status.get("done", 0),
        "by_status": by_status,
    }

    activity_rows = (
        db.query(IncidentResponseLog)
        .filter(IncidentResponseLog.event_id == event.id,
                IncidentResponseLog.action.in_(["plan_approved", "plan_rejected", "task_updated", "plan_details_saved"]))
        .order_by(IncidentResponseLog.created_at.desc(), IncidentResponseLog.id.desc())
        .limit(30).all()
    )
    activity = [{"action": row.action, "actor": row.actor,
                 "at": _iso(row.created_at),
                 "detail": json.loads(row.detail) if row.detail else {}}
                for row in activity_rows]
    # The current report is always the latest. Older approved tasks remain visible.
    previous_report_tasks = sum(1 for t in tasks_out if t["report_version"] is not None
                                and report is not None and t["report_version"] < report.version)

    plan_row = db.query(ResponsePlan).filter(ResponsePlan.event_id == event.id).first()
    plan_details = _plan_details_out(plan_row)

    if not report:
        return {
            "plan": plan_details,
            "report": None,
            "actions": [],
            "review": {"total": 0, "approved": 0, "rejected": 0, "pending": 0},
            "tasks": tasks_out,
            "task_summary": task_summary,
            "activity": activity,
            "previous_report_tasks": previous_report_tasks,
            "message": "Generate a crisis report first. Its recommendations appear here.",
        }

    decisions = {d.action_index: d for d, _ in all_decisions if d.report_id == report.id}
    dossier = report_payload(report)
    priorities = dossier.get("immediate_action_priority") or []
    categories = dossier.get("immediate_action_category") or []

    actions = []
    for i, text in enumerate(dossier.get("immediate_actions") or []):
        d = decisions.get(i)
        # Reports saved before these fields existed have no value; None means "not in report".
        payload_priority = priorities[i] if i < len(priorities) else None
        payload_category = categories[i] if i < len(categories) else None
        task = tasks_by_id.get(d.task_id) if d and d.task_id else None
        actions.append({
            "index": i,
            "text": text,
            "priority": (d.ai_priority or payload_priority) if d else payload_priority,
            "category": (d.ai_category or payload_category) if d else payload_category,
            "officer_priority": d.officer_priority if d else None,
            "decision": d.decision if d else None,
            "decided_by": d.decided_by if d else None,
            "decided_at": d.created_at.isoformat() + "Z" if d else None,
            "task_id": d.task_id if d else None,
            "task": _task_out(task, version_by_task.get(task.id)) if task else None,
            "reason": d.reason if d else None,
        })

    approved = sum(1 for a in actions if a["decision"] == "approved")
    rejected = sum(1 for a in actions if a["decision"] == "rejected")
    return {
        "plan": plan_details,
        "report": {
            "id": report.id,
            "version": report.version,
            "generated_at": report.created_at.isoformat() + "Z",
            "model": report.model_name,
            "is_ai_generated": True,
        },
        "actions": actions,
        "review": {
            "total": len(actions),
            "approved": approved,
            "rejected": rejected,
            "pending": len(actions) - approved - rejected,
        },
        "tasks": tasks_out,
        "task_summary": task_summary,
            "activity": activity,
            "previous_report_tasks": previous_report_tasks,
        "note": "AI recommendations. Each needs an officer's approval before it becomes a task.",
    }


@router.post("/{incident_id}/response/plan/details")
def save_plan_details(incident_id: str, body: PlanDetailsBody, db: Session = Depends(get_db)):
    """Save the plan's name and description. The first save records who created the plan."""
    event = _event_or_404(incident_id, db)
    name = body.name.strip() if body.name and body.name.strip() else None
    description = body.description.strip() if body.description and body.description.strip() else None
    row = db.query(ResponsePlan).filter(ResponsePlan.event_id == event.id).first()
    if row is None:
        row = ResponsePlan(event_id=event.id, name=name, description=description,
                           created_by=body.actor, updated_by=body.actor)
        db.add(row)
    else:
        row.name = name
        row.description = description
        row.updated_by = body.actor
    _log(db, event.id, "plan_details_saved", body.actor, {"name": name})
    db.commit()
    db.refresh(row)
    return _plan_details_out(row)


@router.post("/{incident_id}/response/plan/decide")
def decide_plan_action(incident_id: str, body: PlanDecisionBody, db: Session = Depends(get_db)):
    from backend.services.report_versions import latest_report, report_payload
    event = _event_or_404(incident_id, db)
    if body.decision not in {"approve", "reject"}:
        raise HTTPException(status_code=400, detail="decision must be approve or reject")
    # Priority is required only for approval. Reject records no priority.
    priority = (body.priority or "").strip().lower() or None
    if body.decision == "approve" and priority not in PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Choose a priority: {sorted(PRIORITIES)}")

    report = db.query(IncidentReport).filter(IncidentReport.id == body.report_id, IncidentReport.event_id == event.id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    latest = latest_report(db, event.id)
    if latest is None or latest.id != report.id:
        raise HTTPException(status_code=409, detail="This report has been superseded. Review the latest report's recommendations.")

    payload = report_payload(report)
    actions = payload.get("immediate_actions") or []
    if body.action_index >= len(actions):
        raise HTTPException(status_code=400, detail="No recommendation at that index")
    text = actions[body.action_index]
    # AI values are copied from the saved report, never from the client.
    priorities = payload.get("immediate_action_priority") or []
    categories = payload.get("immediate_action_category") or []
    ai_priority = priorities[body.action_index] if body.action_index < len(priorities) else None
    ai_category = categories[body.action_index] if body.action_index < len(categories) else None

    if db.query(ResponsePlanDecision).filter(
        ResponsePlanDecision.report_id == report.id, ResponsePlanDecision.action_index == body.action_index
    ).first():
        raise HTTPException(status_code=409, detail="This recommendation already has a decision")

    task_id = None
    if body.decision == "approve":
        if not body.assignee:
            raise HTTPException(status_code=400, detail="An assignee is required to approve")
        task = ResponseTask(
            event_id=event.id,
            title=text[:250] + ("…" if len(text) > 250 else ""),
            assignee=body.assignee,
            status="open",
            priority=priority,
            due_at=_to_utc_naive(body.due_at),
            note=f"From AI report v{report.version}, recommendation {body.action_index + 1}. Full text: {text}",
            created_by=body.actor,
        )
        db.add(task)
        db.flush()
        task_id = task.id

    db.add(ResponsePlanDecision(
        event_id=event.id,
        report_id=report.id,
        action_index=body.action_index,
        action_text=text,
        decision="approved" if body.decision == "approve" else "rejected",
        task_id=task_id,
        decided_by=body.actor,
        reason=body.reason,
        ai_priority=ai_priority,
        ai_category=ai_category,
        officer_priority=priority if body.decision == "approve" else None,
    ))
    _log(db, event.id, "plan_" + ("approved" if body.decision == "approve" else "rejected"), body.actor, {
        "report_version": report.version,
        "action_index": body.action_index,
        "task_id": task_id,
    })
    db.commit()
    return _serialize_state(db, event.id)
