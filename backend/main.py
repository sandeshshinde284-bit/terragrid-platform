from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(title="TerraGrid API", version="1.0.0")

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "service": "TerraGrid API",
        "environment": os.getenv("ENV","unknown"),
        "database": "connected" if os.getenv("DATABASE_URL") else "not configured"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "database": "PostgreSQL",
        "cache": "Redis",
        "gcp_project": os.getenv("GOOGLE_CLOUD_PROJECT")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port= 8000)