from sqlalchemy import Column, String
from .base import BaseModel


class AlertRecipient(BaseModel):
    """
    Operator-managed Agency Alerts recipient (manual WhatsApp/email send,
    see routes/prepare.py's /alerts/send and /alerts/send-email).

    Replaces the old WHATSAPP_RECIPIENTS / EMAIL_ALERT_RECIPIENTS env vars -
    those required a Cloud Run redeploy to change; this table is editable
    from the Settings screen at runtime, no redeploy needed. Still a fixed,
    reviewed allowlist (not open relay to arbitrary input) - see
    WhatsAppService's and NotificationService's docstrings for why that
    constraint stays even though it's now DB-backed.
    """
    __tablename__ = "alert_recipients"

    channel = Column(String(20), nullable=False)  # 'email' | 'whatsapp'
    label = Column(String(100), nullable=False)
    value = Column(String(255), nullable=False)  # email address or E.164-ish phone number

    def __repr__(self):
        return f"<AlertRecipient {self.id}: {self.channel} {self.label}={self.value}>"
