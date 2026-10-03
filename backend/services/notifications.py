import os
import logging
from typing import Dict, Any, List, Optional
import resend

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service responsible for dispatching external communications (like emails or SMS) 
    to first responders and registered users when severe disasters are detected.
    """
    
    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
        self.from_name = os.getenv("RESEND_FROM_NAME", "TerraGrid Alerts")
        
        # Prevent email spam on every 15-minute polling cycle
        self.sent_alerts = set()
        
        if self.api_key and self.api_key != "re_your_api_key_from_resend_dashboard":
            resend.api_key = self.api_key
            self.is_configured = True
            logger.info("NotificationService (Resend) configured successfully.")
        else:
            self.is_configured = False
            logger.warning("RESEND_API_KEY is not configured or is using the default template. Email alerts are disabled.")

    def send_critical_alert(self, incident: Dict[str, Any], zone_data: Optional[Dict[str, Any]] = None, recipient_emails: List[str] = None):
        """
        Formats and sends an HTML emergency email for a high-risk disaster event.
        
        Args:
            incident: The raw incident data dictionary containing location, type, and impact scores.
            zone_data: Optional evacuation zone population data to include in the email body.
            recipient_emails: A list of target email addresses. Defaults to a test address if none provided.
            
        Returns:
            bool: True if the email was dispatched successfully to Resend, False otherwise.
        """
        if not self.is_configured:
            logger.info("Skipping email alert: Resend not configured.")
            return False
            
        location = incident.get("location_name", "Unknown Location")
        threat_score = incident.get("impact", {}).get("risk_score", 0)
        
        # SPAM PREVENTION: Only send one email per incident location/threat combo
        alert_signature = f"{location}_{threat_score}"
        if alert_signature in self.sent_alerts:
            logger.debug(f"Email already sent for {alert_signature}. Skipping to prevent spam.")
            return False

        if not recipient_emails:
            # Pull default recipients from .env, fallback to test email if missing
            env_recipients = os.getenv("ALERT_RECIPIENTS", "test@example.com")
            recipient_emails = [email.strip() for email in env_recipients.split(",") if email.strip()]
            
        incident_type = str(incident.get("event_type", "disaster")).upper()
        
        subject = f"🔴 CRITICAL ALERT: {incident_type} detected near {location} (Threat: {threat_score}/100)"
        
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
                    logger.info(f"Email sent successfully! ID: {response.get('id')}")
                    self.sent_alerts.add(alert_signature)
                    return True
                except Exception as attempt_e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Email send attempt {attempt + 1} failed, retrying in 2 seconds: {str(attempt_e)}")
                        time.sleep(2)
                    else:
                        raise  # Re-raise to be caught by the outer block

        except Exception as e:
            logger.exception(f"Failed to send Resend email after {max_retries} attempts.")
            return False

# Global singleton
notification_service = NotificationService()
