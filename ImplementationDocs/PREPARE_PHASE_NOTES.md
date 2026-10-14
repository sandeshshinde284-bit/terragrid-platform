# PREPARE Phase — Build Log

Running notes for the PREPARE phase build. Deferred/iceboxed items and
future-improvement ideas have moved to `PHASE_2_ROADMAP.md` (PREPARE
Phase 2 section) — this file now tracks only what's actually live.

## Build order & status (all live/built items)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| PR1 | 7-Day Forecast Dashboard | ✅ DONE | OpenWeatherMap `/data/2.5/forecast`, mock/live pure (0% cross-contamination) |
| PR7 | Risk Escalation Timeline | ✅ DONE | Reuses PR1's endpoint, no new backend work |
| PR2 | Preparedness Action Generator | ✅ DONE | Gemini via existing DecisionSupportService pattern; mock mode reflects each city's own severity (routine vs. escalating) instead of one static fixture |
| PR6 | Preparedness Checklist UI | ✅ DONE | Checkboxes (localStorage-persisted), progress bar, deadlines resolved to real dates with urgency, agency ownership filter |
| PR4 | Agency Alert Templates | ✅ DONE | 4 audience-specific templates (Farmers/Hospitals/NGOs/Municipal Corps) per city from one Gemini call; master-detail city rail + audience tabs + copy-to-clipboard |
| PR4 ext. | Agency Alert manual send (WhatsApp + Email) | ✅ DONE | Manual-only send of the drafted alert to a pre-approved demo recipient list, via WAHA (WhatsApp) and Resend (email). Shared `"Label:value"` recipient parsing in `backend/services/recipients.py`. |
| PR9 | Confidence-Based Alerting | ✅ DONE | `_summarize_forecast_by_day()` computes `confidence_pct` (% of a day's ~8 three-hour entries agreeing with the day's chosen risk level) and `alert_recommended` (non-GREEN + confidence ≥ 70%) — real agreement-ratio math, not a fabricated score. Surfaced on Risk Timeline and Agency Alerts. |
| PR5 | Evacuation Route Pre-Calculation | ✅ DONE | New `GET /api/v1/prepare/evacuation-routes` adapts RESPONSE phase's real OSRM-routed egress corridors to run proactively per forecasted city — gated on PR9's `alert_recommended`. |
| PR10 | Source of Truth / Preparedness Validation | ✅ DONE | New `GET /api/v1/prepare/source-of-truth` audits the forecast data itself across three checks: freshness (cache age vs. TTL), completeness (every monitored city returned?), sufficiency (full day's readings vs. a thin first/last-day slice). Rolls up to `overall: verified \| degraded`. |

**All 10 original PREPARE PR items resolved**: 8 built directly above, PR4 extended with manual send, 2 moved to `PHASE_2_ROADMAP.md` (PR8 deferred, PR3 iceboxed — see that file for why).

---
*This file is a working log, not a spec. For anything NOT being built
right now, see `PHASE_2_ROADMAP.md` instead of documenting it here.*
