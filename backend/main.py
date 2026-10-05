from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import certifi
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from pathlib import Path

# Ensure project root is in sys.path when executed directly as a script
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Force gRPC (used by Google Gemini SDK) to use standard certifi root certificates on Windows
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()

# Import routes (supports both direct script execution and module execution)
try:
    from .routes.disaster_data import router as disaster_router
    from .routes.polling import router as polling_router
    from .routes.zones import router as zones_router
    from .routes.websockets import router as ws_router
    from .routes.incidents import router as incidents_router
except (ImportError, ValueError):
    from backend.routes.disaster_data import router as disaster_router
    from backend.routes.polling import router as polling_router
    from backend.routes.zones import router as zones_router
    from backend.routes.websockets import router as ws_router
    from backend.routes.incidents import router as incidents_router

# Load .env from project root
load_dotenv(root_dir / ".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan manager for startup and shutdown events"""
    try:
        from .services.polling import get_polling_service
        from .services.data_ingestion import DataIngestionService
    except (ImportError, ValueError):
        from backend.services.polling import get_polling_service
        from backend.services.data_ingestion import DataIngestionService
    
    # --- Startup Logic ---
    try:
        polling_service = get_polling_service()
        data_ingestion = DataIngestionService()
        if polling_service.start(data_ingestion):
            print("[OK] Feature 3 (Background Polling) initialized successfully")
        else:
            print("[WARN] Failed to start background polling")
    except Exception as e:
        print(f"[ERROR] Error during startup: {str(e)}")
        
    yield # App runs here
    
    # --- Shutdown Logic ---
    try:
        if polling_service.is_running:
            polling_service.stop()
            print("[OK] Background polling stopped")
    except Exception as e:
        print(f"[ERROR] Error during shutdown: {str(e)}")


app = FastAPI(
    title="TerraGrid API",
    version="1.0.0",
    description="AI-powered disaster intelligence platform",
    lifespan=lifespan
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(disaster_router)
app.include_router(polling_router)
app.include_router(zones_router)
app.include_router(ws_router)
app.include_router(incidents_router)

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "TerraGrid API",
        "version": "1.0.0",
        "environment": os.getenv("ENV","unknown"),
        "database": "connected" if os.getenv("DATABASE_URL") else "not configured",
        "features": {
            "feature_1": "Real-Time Data Ingestion (NASA EONET + GDACS)",
            "feature_2": "Impact Analysis",
            "feature_3": "Background Polling",
            "feature_3a": "Evacuation Zone Mapping"
        }
    }

@app.get("/api/v1/config")
def get_app_config():
    """
    Exposes essential backend configuration flags to the frontend, ensuring
    a Backend-Driven UI pattern (Single Source of Truth).
    """
    return {
        "mock_mode_enabled": os.getenv("USE_MOCK_DATA", "false").lower() == "true",
        "environment": os.getenv("ENV", "development"),
        "mapbox_token": os.getenv("MAPBOX_TOKEN", "")
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "PostgreSQL",
        "cache": "Redis",
        "gcp_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "pubsub_topic": os.getenv("PUBSUB_TOPIC_ID"),
        "timestamp": "2026-09-30T22:15:00Z"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)