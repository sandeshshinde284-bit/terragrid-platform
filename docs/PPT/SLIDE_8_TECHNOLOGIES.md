# Technologies to Be Used in the Solution
## For AI Builder Cup Submission

---

## **Slide 8: Complete Technology Stack**

### **Comprehensive List of All Technologies**

---

## **Programming Languages**

| Language | Version | Purpose | Usage |
|----------|---------|---------|-------|
| **Python** | 3.11+ | Backend development, AI/ML pipelines | FastAPI server, data processing, API integration |
| **JavaScript** | ES2020+ | Frontend development | Vue 3 components, UI logic |
| **TypeScript** | 4.9+ | Type-safe frontend code | Vue 3 components with type safety |
| **SQL** | Standard | Database queries | PostgreSQL queries, complex analytics |

---

## **Backend Framework & Libraries**

| Technology | Version | Purpose |
|------------|---------|---------|
| **FastAPI** | 0.104+ | Web framework for REST API and WebSocket server |
| **Pydantic** | 2.0+ | Data validation and serialization |
| **SQLAlchemy** | 2.0+ | ORM for database interactions |
| **Alembic** | 1.12+ | Database migration tool |
| **aiohttp** | 3.9+ | Async HTTP client for API calls |
| **python-dotenv** | 1.0+ | Environment variable management |

---

## **Frontend Framework & Libraries**

| Technology | Version | Purpose |
|------------|---------|---------|
| **Vue 3** | 3.3+ | Progressive JavaScript framework |
| **Vite** | 5.0+ | Next-gen frontend build tool |
| **Vue Router** | 4.2+ | Client-side routing (navigation between phases) |
| **Pinia** | 2.1+ | State management (incident data, user preferences) |
| **Axios** | 1.6+ | HTTP client for API calls |
| **Leaflet.js** | 1.9+ | Interactive maps (satellite imagery, incidents) |
| **Chart.js** | 4.4+ | Data visualization (forecasts, trends) |
| **Tailwind CSS** | 3.3+ | Utility-first CSS framework |
| **HeadlessUI** | 1.7+ | Unstyled, accessible UI components |

---

## **Google Cloud Platform Services**

| Service | Purpose | Tier |
|---------|---------|------|
| **Cloud Run** | Serverless backend hosting (auto-scaling) | Pay-per-use |
| **Cloud SQL** | PostgreSQL managed database | Standard |
| **Firestore** | NoSQL document database for scalable storage | Spark/Blaze |
| **Cloud Storage** | Object storage for satellite imagery and exports | Standard |
| **Secret Manager** | Secure storage for API keys and credentials | Standard |
| **Pub/Sub** | Event messaging and real-time streaming | Standard |
| **Cloud Logging** | Centralized logging and log analysis | Standard |
| **Cloud Monitoring** | Performance metrics and alerting | Standard |
| **Cloud Scheduler** | Scheduled jobs for periodic data polling | Standard |
| **Cloud VPC** | Virtual private network for security | Standard |

---

## **AI & Machine Learning Services**

| Service | Capability | Purpose |
|---------|-----------|---------|
| **Google Vertex AI** | Embeddings API | Threat analysis, similarity matching, RAG vector storage |
| **Google Gemini 1.5 Flash** | Large Language Model | Playbook generation, impact analysis summaries, RAG response generation |
| **Google Earth Engine** | Satellite imagery processing | Flood detection, fire extent, damage assessment |
| **Google Places API** | Geocoding and location services | Infrastructure location lookup, address validation |
| **RAG Engine** (Custom) | Retrieval Augmented Generation | Query historical incident data + AI analysis for context-aware recommendations |

---

## **RAG (Retrieval Augmented Generation) Architecture**

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Knowledge Base** | Store historical incident data, playbooks, outcomes | Firestore + Cloud Storage |
| **Vector Embeddings** | Convert text to semantic vectors for similarity search | Vertex AI Embeddings |
| **Retrieval** | Find relevant historical incidents for current situation | Semantic search + metadata filtering |
| **Augmentation** | Combine retrieved context with current data | Python custom logic |
| **Generation** | Generate recommendations with full context | Gemini 1.5 Flash |

**How It Works:**
```
Current Disaster Event
    ↓
Convert to embedding (Vertex AI)
    ↓
Search historical incidents (similarity match)
    ↓
Retrieve top 3-5 relevant past incidents
    ↓
Combine with current threat data
    ↓
Feed augmented context to Gemini
    ↓
Generate playbook: "Based on past events + current data, do X"
    ↓
Responder gets context-aware recommendations
```

**Example RAG Output:**
> "Similar flood event in 2023 affected 12K people. We staged 15 clinics in zones B, C, F. Effectiveness: 94%. Recommending same strategy for current event with 2% adjustment for new population density."

---

## **Geospatial & Routing Technologies**

| Technology | Service | Purpose |
|------------|---------|---------|
| **Google Maps API** | Directions API | Route optimization (shortest/fastest/safest path) |
| **Google Maps API** | Distance Matrix API | Calculate travel times between multiple points |
| **Google OR-Tools** | Routing Library | Vehicle routing problem (evacuation route optimization) |
| **Leaflet.js** | Web mapping | Render interactive maps in frontend |
| **GeoJSON** | Data format | Store and transmit geographic features |
| **Turf.js** | Geospatial analysis | Calculate distances, areas, buffers |

---

## **External Data & API Services**

| API Service | Data Type | Authentication | Use Case |
|------------|-----------|-----------------|----------|
| **NASA EONET** | Fire events, active disasters | Public API (no key) | Real-time fire detection (PREDICT) |
| **USGS Earthquake** | Seismic data, magnitude, location | Public API (no key) | Earthquake monitoring (PREDICT) |
| **NOAA Weather** | Historical weather, patterns | API token | Weather trend analysis (PREDICT) |
| **OpenWeatherMap** | 5-day forecasts | API key | City-level forecasts (PREDICT) |
| **OpenStreetMap** | Map tiles, infrastructure | Public tiles | Infrastructure mapping (PREPARE) |
| **Overpass API** | OSM queries | Public API | Building/facility extraction |
| **PowerOutage.us** | Power grid status | Public API (no key) | Cascade power failure modeling (PREDICT) |
| **httpSMS** | SMS sending | API key + phone | Alert broadcast (RESPONSE) |
| **Resend** | Email sending | API key | Email alerts with attachments (RESPONSE) |

---

## **Database Technologies**

| Technology | Type | Purpose | Data Stored |
|-----------|------|---------|-------------|
| **PostgreSQL** (Cloud SQL) | Relational SQL | Transactional data storage | Events, incidents, decisions, lineage, users |
| **Firestore** | NoSQL Document | Scalable document storage | Incident details, playbooks, alerts, recovery tracking |
| **Redis** | In-Memory Cache | Sub-second data retrieval | Latest API data, session cache, real-time metrics |
| **Cloud Storage** | Object Storage | File storage | Satellite imagery, export PDFs, system artifacts |

---

## **Real-Time Communication**

| Technology | Purpose |
|-----------|---------|
| **WebSocket** | Bidirectional real-time communication between backend and frontend |
| **Google Pub/Sub** | Event streaming for internal system communication |
| **Socket.IO** (optional) | Fallback for WebSocket with auto-retry |

---

## **Development & Deployment Tools**

| Tool | Purpose |
|------|---------|
| **Docker** | Containerization (local development, CI/CD) |
| **Docker Compose** | Multi-container orchestration (local environment) |
| **Git** | Version control and collaboration |
| **GitHub** | Repository hosting and CI/CD workflows |
| **GitHub Actions** | Automated testing, linting, deployment |
| **pytest** | Python unit testing framework |
| **Vitest** | Frontend JavaScript testing |
| **ESLint** | JavaScript/TypeScript linting |
| **Prettier** | Code formatting |
| **Pre-commit** | Git hooks for code quality checks |

---

## **Monitoring & Observability**

| Tool | Purpose |
|------|---------|
| **Cloud Logging** | Centralized logging for all services |
| **Cloud Monitoring** | Performance metrics and dashboards |
| **Error Reporting** | Automatic error tracking and alerting |
| **Cloud Trace** | Distributed tracing for performance debugging |
| **Cloud Profiler** | CPU and memory profiling |

---

## **Security & Compliance**

| Technology | Purpose |
|-----------|---------|
| **Google Secret Manager** | Secure credential storage and rotation |
| **Cloud IAM** | Identity and access management |
| **Cloud Armor** | DDoS protection and web application firewall |
| **VPC Service Controls** | Network security perimeter |
| **Cloud Data Loss Prevention** | Sensitive data detection |
| **SSL/TLS** | Encrypted data transmission |

---

## **Technology Stack by Layer**

### **Data Ingestion Layer**
```
External APIs (7+ sources)
    ↓
Python + aiohttp (async API calls)
    ↓
Redis Cache (latest data)
    ↓
Cloud SQL / Firestore (persistent storage)
```

### **Processing Layer**
```
FastAPI (REST + WebSocket endpoints)
    ↓
Vertex AI (threat analysis, embeddings)
    ↓
Gemini 1.5 Flash (playbook generation)
    ↓
OR-Tools (route optimization)
    ↓
Custom Python logic (decision lineage, impact analysis)
```

### **Frontend Layer**
```
Vue 3 + TypeScript (components)
    ↓
Vite (build tool)
    ↓
Pinia (state management)
    ↓
Axios (API calls)
    ↓
Leaflet + Chart.js (data visualization)
    ↓
Tailwind CSS (styling)
```

### **Infrastructure Layer**
```
Google Cloud Run (serverless backend)
    ↓
Cloud SQL (PostgreSQL database)
    ↓
Firestore (document store)
    ↓
Cloud Storage (imagery, exports)
    ↓
Cloud Logging + Monitoring (observability)
    ↓
Secret Manager (secure credentials)
```

---

## **Why Google Cloud Native?**

| Capability | Google Cloud Service | Benefit |
|-----------|----------------------|---------|
| **Satellite Processing** | Earth Engine | No need to build custom geospatial pipeline |
| **AI/ML** | Vertex AI + Gemini | Pre-trained models, no ML expertise needed |
| **Routing Optimization** | OR-Tools | Industry-standard vehicle routing solver |
| **Real-Time Streaming** | Pub/Sub | Handles 1000s of concurrent messages |
| **Scalability** | Cloud Run | Auto-scales 0 → 10K users in seconds |
| **Database** | Cloud SQL + Firestore | SQL consistency + NoSQL scalability |
| **Security** | Secret Manager + IAM | Enterprise-grade credential management |
| **Free Tier** | $300 for 90 days | MVP cost: zero (within free tier) |

---

## **Total Technology Count**

| Category | Count |
|----------|-------|
| Programming Languages | 4 |
| Backend Frameworks | 6 |
| Frontend Frameworks | 9 |
| Google Cloud Services | 10 |
| AI/ML Services | 4 |
| Geospatial Technologies | 6 |
| External APIs | 9 |
| Databases | 4 |
| Real-Time Tech | 3 |
| DevOps Tools | 10 |
| Monitoring Tools | 5 |
| Security Tools | 6 |
| **TOTAL** | **76+ Technologies** |

---

## **Open Source vs. Commercial**

| Category | Count | Cost |
|----------|-------|------|
| **Open Source** | 45 | Free |
| **Google Cloud (Free Tier)** | 10 | $0 (within $300 credits) |
| **Commercial APIs** (Optional) | 3 | Pay-per-use (httpSMS, Resend, Maps) |
| **Proprietary Google Services** | 18 | Covered by free tier |
| **TOTAL** | 76 | Hackathon: $0 |

---

## **Tech Stack Highlights**

✅ **Modern & Future-Proof**
- Vue 3 (latest), FastAPI (modern async), Python 3.11+
- No legacy dependencies or deprecated libraries

✅ **Scalable**
- Serverless (Cloud Run), auto-scaling database (Firestore), async backend
- Handles disaster-scale traffic surges

✅ **AI-Powered**
- Vertex AI + Gemini for intelligent recommendations
- OR-Tools for complex optimization problems

✅ **Real-Time**
- WebSocket for sub-30-second data updates
- Pub/Sub for event-driven architecture

✅ **Production-Ready**
- Enterprise-grade security (SSL, IAM, Secret Manager)
- Comprehensive monitoring (Cloud Logging, Cloud Monitoring)
- Disaster recovery (Cloud SQL backups, failover)

✅ **Cost-Effective**
- Open source where possible (Python, Vue, PostgreSQL)
- Google Cloud free tier ($300) covers MVP
- Pay-per-use for production (scales cost with usage)

---

## **Deployment Pipeline**

```
GitHub Repo
    ↓
GitHub Actions (lint, test, build)
    ↓
Docker build (containerize)
    ↓
Push to Artifact Registry
    ↓
Deploy to Cloud Run
    ↓
Health checks + monitoring
    ↓
Production live
```

---

**End of Slide 8**
