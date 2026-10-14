import os
import html
import logging
from backend.config import settings
from typing import Dict, Any, List, Optional
import resend

from .recipients import parse_labeled_recipients

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service responsible for dispatching external communications (like emails or SMS)
    to first responders and registered users when severe disasters are detected.
    """

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.RESEND_FROM_EMAIL
        self.from_name = settings.RESEND_FROM_NAME

        # Prevent email spam on every 15-minute polling cycle
        self.sent_alerts = set()

        # PREPARE phase's Agency Alerts manual email send - a fixed,
        # pre-approved demo recipient list, same reasoning as
        # WhatsAppService's WHATSAPP_RECIPIENTS (see whatsapp.py).
        self.alert_email_recipients = parse_labeled_recipients(settings.EMAIL_ALERT_RECIPIENTS)

        if self.api_key and self.api_key != "re_your_api_key_from_resend_dashboard":
            resend.api_key = self.api_key
            self.is_configured = True
            logger.info("NotificationService (Resend) configured successfully.")
        else:
            self.is_configured = False
            logger.warning("[FEATURE_HEALTH] feature=resend_email status=no_api_key reason=RESEND_API_KEY not configured or still the default placeholder, email alerts are disabled")

    def send_critical_alert(self, incident: Dict[str, Any], zone_data: Optional[Dict[str, Any]] = None, recipient_emails: List[str] = None, db_session=None):
        """
        Formats and sends an HTML emergency email for a high-risk disaster event.
        
        Args:
            incident: The raw incident data dictionary containing location, type, and impact scores.
            zone_data: Optional evacuation zone population data to include in the email body.
            recipient_emails: A list of target email addresses. Defaults to a test address if none provided.
            db_session: Database session to record alert in alerts table (optional).
            
        Returns:
            bool: True if the email was dispatched successfully to Resend, False otherwise.
        """
        if not self.is_configured:
            logger.info("Skipping email alert: Resend not configured.")
            return False
            
        location = incident.get("location_name", "Unknown Location")
        threat_score = incident.get("impact", {}).get("risk_score", 0)
        
        # Check database for existing alert (more reliable than in-memory)
        if db_session:
            try:
                from ..models.alert import Alert
                from ..models.event import Event
                
                # Find event by coordinates and type
                existing_alert = db_session.query(Alert).join(Event).filter(
                    Event.latitude == incident.get("latitude"),
                    Event.longitude == incident.get("longitude"),
                    Event.event_type == incident.get("event_type"),
                    Alert.status == "sent"
                ).first()
                
                if existing_alert:
                    logger.debug(f"Alert already sent for this incident. Skipping to prevent spam.")
                    return False
            except Exception as check_e:
                logger.warning(f"Could not check database for existing alert: {str(check_e)}")
        
        # Fallback to in-memory prevention if DB not available
        alert_signature = f"{location}_{threat_score}"
        if alert_signature in self.sent_alerts:
            logger.debug(f"Email already sent for {alert_signature}. Skipping to prevent spam.")
            return False

        if not recipient_emails:
            # Pull default recipients from .env, fallback to test email if missing
            env_recipients = settings.ALERT_RECIPIENTS
            recipient_emails = [email.strip() for email in env_recipients.split(",") if email.strip()]
            
        incident_type = str(incident.get("event_type", "disaster")).upper()
        
        subject = f"CRITICAL ALERT: {incident_type} detected near {location} (Threat: {threat_score}/100)"
        
        # Build HTML Body
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #ef4444; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0; font-size: 24px;">TERRAGRID EMERGENCY ALERT </h1>
            </div>
            <div style="padding: 20px; background-color: #ffffff; color: #374151;">
                <h2 style="color: #111827; border-bottom: 2px solid #ef4444; padding-bottom: 8px;">Incident Summary</h2>
                <ul style="list-style-type: none; padding: 0; font-size: 16px;">
                    <li style="margin-bottom: 10px;"><strong>Type:</strong> {incident_type}</li>
                    <li style="margin-bottom: 10px;"><strong>Location:</strong> {location}</li>
                    <li style="margin-bottom: 10px;"><strong>Threat Score:</strong> <span style="color: #ef4444; font-weight: bold;">{threat_score}/100</span></li>
                    <li style="margin-bottom: 10px;"><strong>Coordinates:</strong> {incident.get("latitude")}, {incident.get("longitude")}</li>
                </ul>
        """
        
        if zone_data:
             html_content += f"""
                <h2 style="color: #111827; border-bottom: 2px solid #ef4444; padding-bottom: 8px; margin-top: 20px;">Evacuation Zones</h2>
                <p><strong>Immediate Action Required:</strong> Approximately {zone_data.get('total_population_affected', 0):,} people are in the calculated impact zones.</p>
             """
             
        html_content += """
                <div style="margin-top: 30px; padding: 15px; background-color: #f3f4f6; border-radius: 6px; font-size: 14px; text-align: center;">
                    <p style="margin: 0;">Access the TerraGrid Command Center immediately for real-time tracking and safe routing.</p>
                </div>
            </div>
        </div>
        """

        try:
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": recipient_emails,
                "subject": subject,
                "html": html_content,
            }
            
            logger.info(f"Sending Resend email alert for incident: {location}")
            
            max_retries = 3
            import time
            for attempt in range(max_retries):
                try:
                    response = resend.Emails.send(params)
                    resend_email_id = response.get('id', 'unknown')
                    logger.info(f"[FEATURE_HEALTH] feature=resend_email status=success resend_id={resend_email_id} location={location}")
                    self.sent_alerts.add(alert_signature)
                    
                    # Record alert in database
                    if db_session:
                        try:
                            from ..models.alert import Alert
                            from ..models.event import Event
                            from datetime import datetime
                            
                            # Find the event record
                            event = db_session.query(Event).filter(
                                Event.latitude == incident.get("latitude"),
                                Event.longitude == incident.get("longitude"),
                                Event.event_type == incident.get("event_type")
                            ).first()
                            
                            if event:
                                # Create alert record
                                alert_record = Alert(
                                    event_id=event.id,
                                    alert_type="critical_threat",
                                    status="sent",
                                    title=subject,
                                    message=html_content[:1000],  # Store first 1000 chars
                                    channels="email",
                                    is_critical=True,
                                    retry_count=attempt
                                )
                                db_session.add(alert_record)
                                db_session.commit()
                                logger.info(f"Alert record persisted to database for event {event.id}")
                        except Exception as db_e:
                            logger.warning(f"Could not persist alert to database: {str(db_e)}")
                            # Don't fail the email sending if database fails
                    
                    return True
                except Exception as attempt_e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Email send attempt {attempt + 1} failed, retrying in 2 seconds: {str(attempt_e)}")
                        time.sleep(2)
                    else:
                        raise  # Re-raise to be caught by the outer block

        except Exception as e:
            logger.exception(f"[FEATURE_HEALTH] feature=resend_email status=error attempts={max_retries} location={location}")
            return False

    def get_alert_email_recipients(self) -> List[Dict[str, str]]:
        """Pre-approved demo email recipients, for Agency Alerts' picker."""
        return [{"label": r.label, "email": r.value} for r in self.alert_email_recipients]

    def _find_alert_email_recipient(self, email: str) -> Optional[Any]:
        return next((r for r in self.alert_email_recipients if r.value == email), None)

    def send_alert_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Sends a plain alert email to one pre-approved Agency Alerts demo
        recipient. Unlike send_critical_alert above, this carries no
        incident-specific formatting, DB persistence or spam-dedup - those
        belong to RESPONSE phase's automatic incident emails, not this
        manual, operator-reviewed send. Never raises - returns a structured
        result so the route can surface a clear UI error either way.

        Args:
            to_email: Must match one of the EMAIL_ALERT_RECIPIENTS entries -
                rejected otherwise, same allowlist reasoning as WhatsApp.
            subject: Email subject line.
            body: Plain-text message body, exactly as shown on screen.
        """
        if not self.is_configured:
            return {
                "success": False,
                "detail": "Email sending isn't configured on this backend (RESEND_API_KEY missing).",
            }

        recipient = self._find_alert_email_recipient(to_email)
        if not recipient:
            return {
                "success": False,
                "detail": "That email isn't one of the pre-approved demo recipients.",
            }

        safe_body = html.escape(body).replace("\n", "<br>")
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #2563eb; color: white; padding: 20px;">
                <h1 style="margin: 0; font-size: 20px;">TerraGrid Agency Alert</h1>
            </div>
            <div style="padding: 20px; background-color: #ffffff; color: #374151; font-size: 15px; line-height: 1.5;">
                {safe_body}
            </div>
        </div>
        """

        try:
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            logger.info(f"Agency Alert email sent to {recipient.label} ({to_email}) via Resend.")
            return {
                "success": True,
                "detail": f"Sent to {recipient.label}.",
                "resend_id": response.get("id") if isinstance(response, dict) else None,
            }
        except Exception as e:
            logger.exception(f"Failed to send Agency Alert email to {to_email}.")
            return {
                "success": False,
                "detail": f"Resend error: {str(e)}",
            }

# Global singleton
notification_service = NotificationService()
