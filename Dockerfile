# Use official Python runtime
FROM python:3.12-slim

# Set the working directory to the project root (terragrid-platform)
# This is CRITICAL because the code uses absolute imports (e.g. `from backend.routes...`)
WORKDIR /app

# Install system dependencies (purged fake pg_trgm deps)
RUN apt-get update && apt-get install -y gcc

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend folder into /app/backend
COPY backend/ ./backend/

# EXPOSE PORT 8000
EXPOSE 8000

# Command to run the application (running from the root, pointing into the backend package)
CMD ["sh", "-c", "exec uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
