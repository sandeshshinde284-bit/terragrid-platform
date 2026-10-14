# Brief About the Idea: TerraGrid
## **For AI Builder Cup Submission**

---

## **[FOR PDF/SLIDE] — Use This in Submission**

### **The Problem (1 Paragraph)**

Natural disasters in APAC kill thousands yearly. The core issue isn't detection—satellites handle that. **The issue is speed and coordination.** Disaster response today is siloed: meteorologists forecast, planners allocate resources days later, responders in the field lack real-time intel, and lessons learned never feed back to prevention. **Decision-to-action takes hours. By then, preventable lives are lost.**

### **The Solution (2 Paragraphs)**

**TerraGrid is an AI-powered disaster intelligence platform that unifies response across four phases:**

1. **PREDICT** — 7-day forecast + infrastructure vulnerability identification
2. **PREPARE** — AI impact analysis ("X buildings exposed, Y population at risk") + resource pre-positioning
3. **RESPONSE** — Live incident dashboard + dynamic evacuation routing + multi-channel alerts
4. **RECOVER** — Before/after damage assessment + lessons learned

Unlike point solutions (fire detection, earthquake dashboards), TerraGrid connects all four phases. Every decision is tracked—why it was made, what data informed it, whether it worked post-event. Responders don't just see data; they get AI recommendations: *"Route evac via Highway 3 (not Highway 1—flooded). This saves 15 min/person."*

---

## **[FOR SPEAKING ONLY] — Don't Put in PDF, Use When Speaking Verbally**

### **Why It Wins (1 Paragraph)**

**Other teams:** "We detected the disaster."  
**TerraGrid:** "We detected it, measured who/what's exposed, optimized response in real-time, and learned to predict it better next time."

Built on Google Cloud (Vertex AI, Earth Engine, OR-Tools), TerraGrid integrates 7+ APIs (NASA EONET, USGS, NOAA, weather, infrastructure, power grids) into a single workflow. Four phases. One platform. Full decision lineage. Lives saved.

### **30-Second Pitch (For Elevator)**

> "TerraGrid connects disaster detection, analysis, planning, and response into one AI-powered platform. While competitors show you disasters happened, we show you what's exposed, optimize your response in real-time, and learn to predict it better next time. Built on Google Cloud. Four phases. Lives saved."

### **Key Stats for Judges**

- **Problem Scale:** 1000s killed/year in APAC; decision-to-action delays are the #1 preventable loss factor
- **Solution Scope:** 4 integrated phases (vs. typical single-phase tools)
- **AI Integration:** Threat analysis + impact analysis + route optimization + decision lineage (not just a dashboard)
- **Tech Stack:** FastAPI + Vue 3 + Vertex AI + Earth Engine + OR-Tools (production-ready)
- **Data Coverage:** 7 APIs integrated; real-time updates via WebSocket
- **Unique Angle:** Every action links to data + outcomes; teams learn from every disaster

---

**Total word count: ~300 words — brief, punchy, clear. That's what "brief" means.**
