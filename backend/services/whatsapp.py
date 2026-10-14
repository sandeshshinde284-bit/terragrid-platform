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

from backend.config import settings

logger = logging.getLogger(__name__)


class WhatsAppRecipient:
    def __init__(self, label: str, phone_number: str):
        self.label = label
        self.phone_number = phone_number

    def to_dict(self) -> Dict[str, str]:
        return {"label": self.label, "phone_number": self.phone_number}


class WhatsAppService:
    """
    Thin wrapper around WAHA's POST /api/sendText endpoint.

    Deliberately does NOT accept an arbitrary phone number from the
    frontend - only phone numbers pre-approved via the WHATSAPP_RECIPIENTS
    env var (get_recipients()) can be sent to. This keeps a WhatsApp "Send"
    button from becoming an open relay to any number a client happens to
    pass in.
    """

    def __init__(self):
        self.api_url = (settings.WAHA_API_URL or "").rstrip("/")
        self.session = settings.WAHA_SESSION or "default"
        self.api_key = settings.WAHA_API_KEY
        self.recipients = self._parse_recipients(settings.WHATSAPP_RECIPIENTS)
        self.is_configured = bool(self.api_url) and len(self.recipients) > 0

        if not self.is_configured:
            logger.warning(
                "WhatsAppService not fully configured (WAHA_API_URL or "
                "WHATSAPP_RECIPIENTS missing) - WhatsApp sends will be rejected."
            )

    @staticmethod
    def _parse_recipients(raw: str) -> List[WhatsAppRecipient]:
        """
        Parses "Label:phone_number,Label2:phone_number2" into a list of
        WhatsAppRecipient. Silently skips malformed entries rather than
        crashing service startup over a typo in .env.
        """
        recipients: List[WhatsAppRecipient] = []
        if not raw:
            return recipients

        for entry in raw.split(","):
            entry = entry.strip()
            if not entry or ":" not in entry:
                continue
            label, phone_number = entry.split(":", 1)
            label = label.strip()
            phone_number = phone_number.strip()
            if label and phone_number:
                recipients.append(WhatsAppRecipient(label, phone_number))

        return recipients

    def get_recipients(self) -> List[Dict[str, str]]:
        """Pre-approved demo recipients, for the frontend's recipient picker."""
        return [r.to_dict() for r in self.recipients]

    def _find_recipient(self, phone_number: str) -> Optional[WhatsAppRecipient]:
        return next((r for r in self.recipients if r.phone_number == phone_number), None)

    async def send_text(self, phone_number: str, text: str) -> Dict[str, Any]:
        """
        Sends a WhatsApp text message via WAHA's POST /api/sendText.

        Args:
            phone_number: Must match one of the pre-approved WHATSAPP_RECIPIENTS
                entries - rejected otherwise (see class docstring).
            text: The message body to send verbatim.

        Returns:
            {"success": bool, "detail": str, "waha_response": dict | None}
            Never raises - callers get a structured result either way, since
            this is a user-initiated action that needs to surface a clear
            error in the UI (WAHA not running, session not linked, etc.)
            rather than a raw 500.
        """
        if not self.is_configured:
            return {
                "success": False,
                "detail": "WhatsApp sending isn't configured on this backend (WAHA_API_URL / WHATSAPP_RECIPIENTS missing).",
                "waha_response": None,
            }

        recipient = self._find_recipient(phone_number)
        if not recipient:
            return {
                "success": False,
                "detail": "That phone number isn't one of the pre-approved demo recipients.",
                "waha_response": None,
            }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key

        payload = {
            "session": self.session,
            "chatId": f"{recipient.phone_number}@c.us",
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
                logger.warning(f"WAHA sendText failed ({response.status_code}): {response.text[:300]}")
                return {
                    "success": False,
                    "detail": f"WAHA rejected the send (HTTP {response.status_code}). Is the '{self.session}' session linked (QR scanned) and in WORKING state?",
                    "waha_response": self._safe_json(response),
                }

            logger.info(f"WhatsApp message sent to {recipient.label} ({recipient.phone_number}) via WAHA.")
            return {
                "success": True,
                "detail": f"Sent to {recipient.label}.",
                "waha_response": self._safe_json(response),
            }

        except httpx.ConnectError:
            logger.warning(f"Could not reach WAHA at {self.api_url} - is the waha container running?")
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
            logger.exception(f"Unexpected error sending WhatsApp message: {str(e)}")
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
