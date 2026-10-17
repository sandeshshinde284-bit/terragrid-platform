import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = 'postgresql://terragrid_user:terragrid_pass@localhost:5432/terragrid_db'
    
    # Environment
    ENVIRONMENT: str = 'development'
    ADMIN_TOKEN: str = 'admin-secret-key'
    ALLOWED_ORIGINS: str = 'http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173'
    USE_MOCK_DATA: bool = False

    # Automatic critical-incident emails (risk >= 80) are OFF by default.
    # Alerts are sent only after an operator reviews and approves them.
    AUTO_CRITICAL_EMAIL_ENABLED: bool = False
    
    # AI & GCP
    GCP_PROJECT_ID: str = 'terragrid-platform'
    GCP_REGION: str = 'us-central1'
    GEMINI_API_KEY: str = ''
    GEMINI_MODEL: str = 'gemini-2.5-flash'
    
    # DEPRECATED, no longer read anywhere - notifications.py (both
    # send_critical_alert for RESPONSE phase and send_alert_email for
    # PREPARE phase's Agency Alerts) now sends exclusively via Gmail SMTP
    # (GMAIL_SMTP_* below). Resend's onboarding@resend.dev sender could only
    # deliver to the Resend account's own email (verified against Resend's
    # docs - https://resend.com/docs/knowledge-base/403-error-resend-dev-domain),
    # so it could never reach recipients added at runtime via Settings.
    # RESEND_API_KEY: str = ''
    # RESEND_FROM_EMAIL: str = 'onboarding@resend.dev'
    # RESEND_FROM_NAME: str = 'TerraGrid Alerts'
    # DEPRECATED, no longer read anywhere - RESPONSE phase's critical-alert
    # recipients are now managed at runtime via the Settings screen
    # (CRITICAL_EMAIL_CHANNEL in backend/models/recipient.py's AlertRecipient
    # table) instead of this env var. Re-add any existing recipients through
    # Settings after this change ships; this value is not migrated automatically.
    ALERT_RECIPIENTS: str = 'test@example.com'

    # Gmail SMTP - sends BOTH RESPONSE phase's automatic critical-incident
    # email (send_critical_alert) and PREPARE phase's manual Agency Alerts
    # email (send_alert_email), in notifications.py. Resend's
    # onboarding@resend.dev sender could only deliver to the Resend
    # account's own email, so it could never reach recipients added at
    # runtime via Settings. Gmail SMTP has no such restriction: any address
    # a GMAIL_SMTP_USER account in good standing sends to will go through.
    # GMAIL_SMTP_APP_PASSWORD is a Gmail "App Password" (requires 2-Step
    # Verification on that Google account), NOT the account's real password -
    # never put the real password here.
    GMAIL_SMTP_USER: str = ''
    GMAIL_SMTP_APP_PASSWORD: str = ''
    GMAIL_SMTP_FROM_NAME: str = 'TerraGrid Alerts'

    # DEPRECATED, no longer read anywhere - Agency Alerts recipients are now
    # managed at runtime via the Settings screen (backend/models/recipient.py's
    # AlertRecipient table) instead of this env var. Re-add any existing
    # recipients through Settings after this change ships; this value is
    # not migrated automatically.
    EMAIL_ALERT_RECIPIENTS: str = ''

    # WhatsApp (via WAHA - self-hosted WhatsApp HTTP API, see docker-compose.yml)
    # Kept in the codebase (service, routes, UI) but off by default: WhatsApp's
    # Business Solution Provider terms around unofficial/self-hosted clients
    # like WAHA haven't been confirmed as compliant, so this stays disabled
    # until that's resolved. Flip to True only once that's verified - this is
    # the single switch that controls both the backend send endpoint and
    # whether the frontend shows any WhatsApp UI at all.
    ENABLE_WHATSAPP: bool = False
    # WAHA_API_URL points at the WAHA container: http://waha:3000 when the
    # backend itself runs inside docker-compose, http://localhost:3000 when
    # the backend runs on the host with `docker-compose up waha` alongside it.
    WAHA_API_URL: str = 'http://localhost:3000'
    WAHA_SESSION: str = 'default'
    # Must match the WAHA_API_KEY set on the waha service in docker-compose.yml
    WAHA_API_KEY: str = ''
    # DEPRECATED, no longer read anywhere - see EMAIL_ALERT_RECIPIENTS above,
    # same reason (Settings screen replaces this env var).
    WHATSAPP_RECIPIENTS: str = ''
    
    # External APIs
    OPENWEATHERMAP_API_KEY: str = ''
    OPENWEATHER_API_URL: str = 'https://api.openweathermap.org/data/2.5'
    
    NOAA_API_BASE_URL: str = 'https://api.weather.gov'
    GDACS_API_URL: str = 'https://www.gdacs.org/gdacsapi/api'
    NASA_EONET_URL: str = 'https://eonet.gsfc.nasa.gov/api/v3'
    USGS_EARTHQUAKE_URL: str = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary'
    
    OSRM_API_URL: str = 'https://router.project-osrm.org/route/v1'
    # overpass-api.de is the original/most heavily-used public Overpass
    # instance and is known to return 502/504 under load, independent of
    # anything this app does. OVERPASS_API_URL stays as the primary (kept
    # for backward compat with any existing env config), but each retry in
    # infrastructure.py now rotates to the next mirror in this list instead
    # of hammering the same host 3x - these are independent public servers,
    # so one being overloaded doesn't mean the others are.
    OVERPASS_API_URL: str = 'https://overpass-api.de/api/interpreter'
    OVERPASS_API_MIRRORS: str = 'https://overpass-api.de/api/interpreter,https://overpass.kumi.systems/api/interpreter,https://overpass.openstreetmap.ru/api/interpreter'
    OVERPASS_API_TIMEOUT: int = 12
    OVERPASS_API_RETRIES: int = 3
    
    POLLING_INTERVAL_MINUTES: int = 15
    
    PUBSUB_TOPIC_ID: str = 'terragrid-events'
    USE_PUBSUB: bool = False

    IMD_API_KEY: str = ''
    IMD_API_JWT_TOKEN: str = ''
    IMD_API_ENDPOINT: str = 'https://api.imd.gov.in/v1/'
    
    class Config:
        env_file = '.env'
        extra = 'ignore'

settings = Settings()
