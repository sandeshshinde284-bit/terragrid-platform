"""
Versioned crisis reports. Each successful Gemini report is stored as a new
version in incident_reports. Nothing is overwritten. Offline (fallback)
results are never stored.
"""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.event import Event
from backend.models.response import IncidentReport


def _top_action(dossier: Dict[str, Any]) -> Optional[str]:
    actions = dossier.get("immediate_actions") or []
    return actions[0] if actions else None


def latest_report(db: Session, event_id: int) -> Optional[IncidentReport]:
    return (
        db.query(IncidentReport)
        .filter(IncidentReport.event_id == event_id)
        .order_by(IncidentReport.version.desc())
        .first()
    )


def save_report_version(db: Session, event: Event, dossier: Dict[str, Any]) -> IncidentReport:
    """Store the dossier as the next version and update the incident's summary."""
    current = db.query(func.max(IncidentReport.version)).filter(IncidentReport.event_id == event.id).scalar() or 0
    report = IncidentReport(
        event_id=event.id,
        version=current + 1,
        payload=json.dumps(dossier),
        top_action=_top_action(dossier),
        model_name=settings.GEMINI_MODEL,
    )
    db.add(report)
    db.flush()

    # The list endpoint copies incident.data, so this summary reaches the
    # Incidents screen without another request. The full report stays in incident_reports.
    data = dict(event.data or {})
    data["deep_dossier"] = dossier
    data["response_summary"] = {
        "report_version": report.version,
        "top_action": report.top_action,
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }
    event.data = data
    db.commit()
    db.refresh(report)
    return report


def report_payload(report: IncidentReport) -> Dict[str, Any]:
    return json.loads(report.payload)
