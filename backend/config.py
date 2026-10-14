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
    
    # AI & GCP
    GCP_PROJECT_ID: str = 'terragrid-platform'
    GCP_REGION: str = 'us-central1'
    GEMINI_API_KEY: str = ''
    GEMINI_MODEL: str = 'gemini-2.5-flash'
    
    # Notifications
    RESEND_API_KEY: str = ''
    RESEND_FROM_EMAIL: str = 'onboarding@resend.dev'
    RESEND_FROM_NAME: str = 'TerraGrid Alerts'
    ALERT_RECIPIENTS: str = 'test@example.com'
    # Comma-separated "Label:email" pairs for Agency Alerts' manual email
    # send - deliberately separate from ALERT_RECIPIENTS above, which is
    # RESPONSE phase's automatic live-incident email list. Keeping them
    # apart means testing Agency Alerts' demo send can never accidentally
    # email the real incident-response recipient list.
    EMAIL_ALERT_RECIPIENTS: str = ''

    # WhatsApp (via WAHA - self-hosted WhatsApp HTTP API, see docker-compose.yml)
    # WAHA_API_URL points at the WAHA container: http://waha:3000 when the
    # backend itself runs inside docker-compose, http://localhost:3000 when
    # the backend runs on the host with `docker-compose up waha` alongside it.
    WAHA_API_URL: str = 'http://localhost:3000'
    WAHA_SESSION: str = 'default'
    # Must match the WAHA_API_KEY set on the waha service in docker-compose.yml
    WAHA_API_KEY: str = ''
    # Comma-separated "Label:phone_number" pairs, e.g.
    # "Demo Phone 1:919812345678,Demo Phone 2:919812345679" - a fixed,
    # pre-approved demo list (not arbitrary user input) so Agency Alerts can
    # prove the WhatsApp integration works without a real per-audience/
    # per-city contact directory, which doesn't exist yet.
    WHATSAPP_RECIPIENTS: str = ''
    
    # External APIs
    OPENWEATHERMAP_API_KEY: str = ''
    OPENWEATHER_API_URL: str = 'https://api.openweathermap.org/data/2.5'
    
    NOAA_API_BASE_URL: str = 'https://api.weather.gov'
    GDACS_API_URL: str = 'https://www.gdacs.org/gdacsapi/api'
    NASA_EONET_URL: str = 'https://eonet.gsfc.nasa.gov/api/v3'
    USGS_EARTHQUAKE_URL: str = 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary'
    
    OSRM_API_URL: str = 'https://router.project-osrm.org/route/v1'
    OVERPASS_API_URL: str = 'https://overpass-api.de/api/interpreter'
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
