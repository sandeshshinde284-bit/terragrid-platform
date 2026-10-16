import os
import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from backend.config import settings
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from . import alert_recipients

logger = logging.getLogger(__name__)

EMAIL_CHANNEL = "email"
# RESPONSE phase's automatic critical-incident alert recipients (sent via
# Gmail SMTP by send_critical_alert, below) - deliberately a SEPARATE
# channel from EMAIL_CHANNEL above (PREPARE phase's manual Agency Alerts
# send), so testing/editing one list from Settings can never accidentally
# change who gets real incident alerts, or vice versa.
CRITICAL_EMAIL_CHANNEL = "critical_email"

class NotificationService:
    """
    Service responsible for dispatching external communications (like emails or SMS)
    to first responders and registered users when severe disasters are detected.

    Both the RESPONSE phase's automatic critical-incident email
    (send_critical_alert) and PREPARE phase's manual Agency Alerts email
    (send_alert_email) go through the same Gmail SMTP account - there is no
    Resend dependency left in this service. They stay on separate
    Settings-managed recipient lists (CRITICAL_EMAIL_CHANNEL vs
    EMAIL_CHANNEL) even though they share one sender.
    """

    def __init__(self):
        # Prevent email spam on every 15-minute polling cycle
        self.sent_alerts = set()

        self.gmail_user = settings.GMAIL_SMTP_USER
        self.gmail_app_password = settings.GMAIL_SMTP_APP_PASSWORD
        self.gmail_from_name = settings.GMAIL_SMTP_FROM_NAME
        self.gmail_configured = bool(self.gmail_user and self.gmail_app_password)
        # is_configured kept as an alias of gmail_configured - send_critical_alert
        # below was written against this name before the Resend removal, and
        # nothing outside this file reads it (verified: only used internally).
        self.is_configured = self.gmail_configured
        if not self.gmail_configured:
            logger.warning("[FEATURE_HEALTH] feature=gmail_smtp status=no_credentials reason=GMAIL_SMTP_USER/GMAIL_SMTP_APP_PASSWORD not configured, all email sending (critical alerts and Agency Alerts) is disabled")
        else:
            logger.info("NotificationService (Gmail SMTP) configured successfully.")

    def send_critical_alert(self, incident: Dict[str, Any], zone_data: Optional[Dict[str, Any]] = None, recipient_emails: List[str] = None, db_session=None):
        """
        Formats and sends an HTML emergency email for a high-risk disaster event.
        
        Args:
            incident: The raw incident data dictionary containing location, type, and impact scores.
            zone_data: Optional evacuation zone population data to include in the email body.
            recipient_emails: A list of target email addresses. Defaults to a test address if none provided.
            db_session: Database session to record alert in alerts table (optional).
            
        Returns:
            bool: True if the email was dispatched successfully via Gmail SMTP, False otherwise.
        """
        if not self.is_configured:
            logger.info("Skipping email alert: Gmail SMTP not configured.")
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
            # Operator-managed recipients (Settings screen, alert_recipients
            # table, CRITICAL_EMAIL_CHANNEL) - takes over from the old
            # ALERT_RECIPIENTS env var, which required a redeploy to change
            # and is no longer read here.
            if db_session:
                try:
                    recipient_emails = [
                        r["email"] for r in self.get_critical_alert_recipients(db_session)
                    ]
                except Exception as recip_e:
                    logger.warning(f"Could not load critical-alert recipients from DB: {str(recip_e)}")
                    recipient_emails = []
            else:
                recipient_emails = []

            if not recipient_emails:
                logger.info("Skipping critical alert email: no critical-alert recipients configured in Settings.")
                return False

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
            logger.info(f"Sending Gmail SMTP critical alert email for incident: {location}")

            max_retries = 3
            import time
            for attempt in range(max_retries):
                try:
                    message = MIMEMultipart("alternative")
                    message["Subject"] = subject
                    message["From"] = f"{self.gmail_from_name} <{self.gmail_user}>"
                    message["To"] = ", ".join(recipient_emails)
                    message.attach(MIMEText(subject, "plain"))
                    message.attach(MIMEText(html_content, "html"))

                    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                        server.login(self.gmail_user, self.gmail_app_password)
                        server.sendmail(self.gmail_user, recipient_emails, message.as_string())

                    logger.info(f"[FEATURE_HEALTH] feature=gmail_smtp status=success location={location} recipients={len(recipient_emails)}")
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
            logger.exception(f"[FEATURE_HEALTH] feature=gmail_smtp status=error attempts={max_retries} location={location}")
            return False

    def get_alert_email_recipients(self, db: Session) -> List[Dict[str, str]]:
        """Operator-managed email recipients (Settings screen), for Agency Alerts' picker."""
        return [
            {"label": r.label, "email": r.value}
            for r in alert_recipients.list_recipients(db, EMAIL_CHANNEL)
        ]

    def get_critical_alert_recipients(self, db: Session) -> List[Dict[str, str]]:
        """
        Operator-managed RESPONSE phase critical-alert recipients (Settings
        screen, CRITICAL_EMAIL_CHANNEL) - used by send_critical_alert above
        and exposed to the frontend so Settings can list/add/remove them.
        """
        return [
            {"label": r.label, "email": r.value}
            for r in alert_recipients.list_recipients(db, CRITICAL_EMAIL_CHANNEL)
        ]

    def send_alert_email(self, db: Session, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """
        Sends a plain alert email to one operator-managed Agency Alerts
        recipient, via Gmail SMTP (same account as send_critical_alert
        above). Unlike send_critical_alert, this carries no incident-specific
        formatting, DB persistence or spam-dedup - those belong to RESPONSE
        phase's automatic incident emails, not this manual, operator-reviewed
        send. Never raises - returns a structured result so the route can
        surface a clear UI error either way.

        Why Gmail SMTP (both here and in send_critical_alert) and not Resend,
        which this service used to use: Resend's onboarding@resend.dev test
        sender can only deliver to the Resend account's own address (see
        GMAIL_SMTP_* comments in config.py) - it couldn't reach recipients
        added at runtime via Settings. Gmail SMTP has no such restriction.

        Args:
            to_email: Must match one of the recipients currently in the
                alert_recipients table (channel='email') - rejected
                otherwise, same allowlist reasoning as WhatsApp.
            subject: Email subject line.
            body: Plain-text message body, exactly as shown on screen.
        """
        if not self.gmail_configured:
            return {
                "success": False,
                "detail": "Email sending isn't configured on this backend (GMAIL_SMTP_USER / GMAIL_SMTP_APP_PASSWORD missing).",
            }

        recipient = alert_recipients.find_recipient_by_value(db, EMAIL_CHANNEL, to_email)
        if not recipient:
            return {
                "success": False,
                "detail": "That email isn't on the configured recipient list. Add it in Settings first.",
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
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.gmail_from_name} <{self.gmail_user}>"
            message["To"] = to_email
            message.attach(MIMEText(body, "plain"))
            message.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
                server.login(self.gmail_user, self.gmail_app_password)
                server.sendmail(self.gmail_user, [to_email], message.as_string())

            logger.info(f"[FEATURE_HEALTH] feature=gmail_smtp status=success recipient={recipient.label}")
            return {
                "success": True,
                "detail": f"Sent to {recipient.label}.",
            }
        except Exception as e:
            logger.exception(f"[FEATURE_HEALTH] feature=gmail_smtp status=error recipient_email={to_email}")
            return {
                "success": False,
                "detail": f"Gmail SMTP error: {str(e)}",
            }

# Global singleton
notification_service = NotificationService()
