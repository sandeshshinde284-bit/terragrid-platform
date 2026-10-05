# TerraGrid Platform

Disaster Intelligence & Response Platform - Google Cloud APAC Hackathon 2026

## Overview

TerraGrid is an AI-powered platform that detects natural disasters (fires, earthquakes, floods) and provides real-time evacuation guidance, resource optimization, and emergency alerts to save lives.

## Features

- 🔥 Real-time fire detection via satellite data (NASA EONET)
- 🌍 Earthquake monitoring (USGS)
- 💨 Weather analysis (NOAA)
- 🗺️ Evacuation route optimization (Google Maps + OR-Tools)
- 📍 Infrastructure mapping (OpenStreetMap)
- ⚡ Power outage cascade modeling (PowerOutage.us)
- 📱 Multi-channel alerts (SMS via httpSMS, Email via Resend)
- 🤖 AI threat analysis (Google Gemini)






## Quick Start (Local Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- GCP Account (free trial - $300 credits)

### Installation

```bash
# Clone repo
git clone https://github.com/YOUR_USERNAME/terragrid-platform.git
cd terragrid-platform

# Setup Python
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup Node
cd frontend
npm install
cd ..

# Start Docker services
docker-compose up -d

# Copy env template and add YOUR OWN API keys
cp .env.example .env
# Edit .env with your own API keys (see API Keys section below)

# Run backend
python main.py

# Run frontend (in another terminal)
cd frontend
npm run dev
```

Visit `http://localhost:5173` for the UI.

## Architecture

- **Backend:** FastAPI (Python)
- **Frontend:** Vue 3 + Vite
- **Database:** PostgreSQL
- **Cache:** Redis
- **Cloud:** Google Cloud (Cloud Run, Cloud SQL, Pub/Sub, Secret Manager)
- **AI:** Google Gemini 1.5 Flash

## API Keys Required (Bring Your Own)

### Free APIs (No Key Needed):
- **NASA EONET** — Fire detection (free, public)
- **USGS Earthquake** — Seismic data (free, public)
- **Overpass/OpenStreetMap** — Infrastructure mapping (free, public)
- **PowerOutage.us** — Power outage data (free, public)

### Free Tokens/Accounts (Get Your Own):
- **NOAA Weather** — Free token (email request at ncdc.noaa.gov)
- **Google Cloud** — $300 free credits (valid 90 days)
- **httpSMS** — Free tier: 200 SMS/month (uses your phone)
- **Resend** — Free tier: 3,000 emails/month (permanent)

### Cost Breakdown: