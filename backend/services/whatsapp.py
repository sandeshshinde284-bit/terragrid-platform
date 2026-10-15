"""
WhatsApp notification service, via WAHA (WhatsApp HTTP API) - a self-hosted,
free, open-source API that drives a real WhatsApp Web session.

WAHA is not part of this backend's own Dockerfile/Cloud Run deploy: it keeps
a persistent, QR-linked WhatsApp session alive, which needs an always-on
process with persistent storage, not a scale-to-zero container. It runs as
its own service (see docker-compose.yml) and this module just talks to it
over HTTP.

Scope: manual send only (an operator reviews the AI-drafted Agency Alert
text, picks a pre-approved demo recipient, and clicks Send). This does not
auto-dispatch anything - see PREPARE_PHASE_NOTES.md for the separate,
larger "automated" feature (auto-send when a city's risk first crosses a
threshold) this would need to be layered under before going further.
"""
import logging
from typing import Dict, Any, List, Optional

import httpx
from sqlalchemy.orm import Session

from backend.config import settings
from . import alert_recipients

logger = logging.getLogger(__name__)

CHANNEL = "whatsapp"


class WhatsAppService:
    """
    Thin wrapper around WAHA's POST /api/sendText endpoint.

    Deliberately does NOT accept an arbitrary phone number from the
    frontend - only phone numbers on the operator-managed recipient list
    (Settings screen, backed by the alert_recipients table) can be sent to.
    This keeps a WhatsApp "Send" button from becoming an open relay to any
    number a client happens to pass in, while still letting the operator
    add/remove numbers at runtime without a redeploy.
    """

    def __init__(self):
        self.api_url = (settings.WAHA_API_URL or "").rstrip("/")
        self.session = settings.WAHA_SESSION or "default"
        self.api_key = settings.WAHA_API_KEY
        # Recipients live in the DB now (see alert_recipients.py), not here -
        # WAHA_API_URL being set is the only thing fixed at startup.
        self.is_configured = bool(self.api_url)

        if not self.is_configured:
            logger.warning(
                "WhatsAppService not configured (WAHA_API_URL missing) - "
                "WhatsApp sends will be rejected."
            )

    def get_recipients(self, db: Session) -> List[Dict[str, str]]:
        """Operator-managed recipients (Settings screen), for the frontend's recipient picker."""
        return [
            {"label": r.label, "phone_number": r.value}
            for r in alert_recipients.list_recipients(db, CHANNEL)
        ]

    async def send_text(self, db: Session, phone_number: str, text: str) -> Dict[str, Any]:
        """
        Sends a WhatsApp text message via WAHA's POST /api/sendText.

        Args:
            phone_number: Must match one of the recipients currently in the
                alert_recipients table (channel='whatsapp') - rejected
                otherwise (see class docstring).
            text: The message body to send verbatim.

        Returns:
            {"success": bool, "detail": str, "waha_response": dict | None}
            Never raises - callers get a structured result either way, since
            this is a user-initiated action that needs to surface a clear
            error in the UI (WAHA not running, session not linked, no
            recipients configured, etc.) rather than a raw 500.
        """
        if not self.is_configured:
            return {
                "success": False,
                "detail": "WhatsApp sending isn't configured on this backend (WAHA_API_URL missing).",
                "waha_response": None,
            }

        recipient = alert_recipients.find_recipient_by_value(db, CHANNEL, phone_number)
        if not recipient:
            return {
                "success": False,
                "detail": "That phone number isn't on the configured recipient list. Add it in Settings first.",
                "waha_response": None,
            }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        payload = {
            "session": self.session,
            "chatId": f"{recipient.value}@c.us",
            "text": text,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.api_url}/api/sendText",
                    json=payload,
                    headers=headers,
                )

            if response.status_code >= 400:
                logger.warning(f"[FEATURE_HEALTH] feature=waha_whatsapp status=error http_status={response.status_code} body={response.text[:300]}")
                return {
                    "success": False,
                    "detail": f"WAHA rejected the send (HTTP {response.status_code}). Is the '{self.session}' session linked (QR scanned) and in WORKING state?",
                    "waha_response": self._safe_json(response),
                }

            logger.info(f"[FEATURE_HEALTH] feature=waha_whatsapp status=success recipient={recipient.label}")
            return {
                "success": True,
                "detail": f"Sent to {recipient.label}.",
                "waha_response": self._safe_json(response),
            }

        except httpx.ConnectError:
            logger.warning(f"[FEATURE_HEALTH] feature=waha_whatsapp status=unreachable url={self.api_url} reason=connection refused, is the waha container running?")
            return {
                "success": False,
                "detail": f"Couldn't reach WAHA at {self.api_url}. Is the waha container running (docker-compose up waha)?",
                "waha_response": None,
            }
        except httpx.TimeoutException:
            return {
                "success": False,
                "detail": "WAHA didn't respond in time.",
                "waha_response": None,
            }
        except Exception as e:
            logger.exception(f"[FEATURE_HEALTH] feature=waha_whatsapp status=error error={type(e).__name__}: {e}")
            return {
                "success": False,
                "detail": f"Unexpected error: {str(e)}",
                "waha_response": None,
            }

    @staticmethod
    def _safe_json(response: httpx.Response) -> Optional[Dict[str, Any]]:
        try:
            return response.json()
        except Exception:
            return None


_whatsapp_service: Optional[WhatsAppService] = None


def get_whatsapp_service() -> WhatsAppService:
    global _whatsapp_service
    if _whatsapp_service is None:
        _whatsapp_service = WhatsAppService()
    return _whatsapp_service
