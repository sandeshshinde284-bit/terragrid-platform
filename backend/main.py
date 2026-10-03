from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Import routes
from .routes.disaster_data import router as disaster_router
from .routes.polling import router as polling_router
from .routes.zones import router as zones_router
from .routes.websockets import router as ws_router

load_dotenv()

app = FastAPI(
    title="TerraGrid API",
    version="1.0.0",
    description="AI-powered disaster intelligence platform"
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


# Startup event to initialize Feature 3 polling
@app.on_event("startup")
async def startup_event():
    """Initialize background polling service on startup"""
    from .services.polling import get_polling_service
    from .services.data_ingestion import DataIngestionService
    
    try:
        polling_service = get_polling_service()
        data_ingestion = DataIngestionService()
        
        if polling_service.start(data_ingestion):
            print("[OK] Feature 3 (Background Polling) initialized successfully")
        else:
            print("[WARN] Failed to start background polling")
    except Exception as e:
        print(f"[ERROR] Error during startup: {str(e)}")


# Shutdown event to cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    from .services.polling import get_polling_service
    
    try:
        polling_service = get_polling_service()
        if polling_service.is_running:
            polling_service.stop()
            print("[OK] Background polling stopped")
    except Exception as e:
        print(f"[ERROR] Error during shutdown: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)