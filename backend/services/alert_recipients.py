"""
CRUD for Agency Alerts' operator-managed recipient list (Settings screen).

Both channels (email, whatsapp) share one table, keyed by `channel` - see
backend/models/recipient.py for why this replaced the old env-var lists.
Deliberately thin: this is a small, operator-reviewed demo list, not a
general-purpose contacts feature, so no pagination/search is needed.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models.recipient import AlertRecipient


def list_recipients(db: Session, channel: str) -> List[AlertRecipient]:
    return (
        db.query(AlertRecipient)
        .filter(AlertRecipient.channel == channel)
        .order_by(AlertRecipient.id.asc())
        .all()
    )


def find_recipient_by_value(db: Session, channel: str, value: str) -> Optional[AlertRecipient]:
    return (
        db.query(AlertRecipient)
        .filter(AlertRecipient.channel == channel, AlertRecipient.value == value)
        .first()
    )


def add_recipient(db: Session, channel: str, label: str, value: str) -> AlertRecipient:
    recipient = AlertRecipient(channel=channel, label=label.strip(), value=value.strip())
    db.add(recipient)
    db.commit()
    db.refresh(recipient)
    return recipient


def delete_recipient(db: Session, channel: str, recipient_id: int) -> bool:
    recipient = (
        db.query(AlertRecipient)
        .filter(AlertRecipient.id == recipient_id, AlertRecipient.channel == channel)
        .first()
    )
    if not recipient:
        return False
    db.delete(recipient)
    db.commit()
    return True
