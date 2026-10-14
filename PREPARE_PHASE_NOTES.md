# PREPARE Phase — Build Log & Deferred Decisions

Running notes for the PREPARE phase build (PR1 → PR7 → PR2 → PR6 → PR4).
Purpose: capture open decisions and ideas raised during the build that we
deliberately deferred, so nothing discussed gets lost between sessions.
Updated as we go; reviewed in full once all 5 PREPARE features ship.

## Build order & status

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| PR1 | 7-Day Forecast Dashboard | ✅ DONE | OpenWeatherMap `/data/2.5/forecast`, mock/live pure (0% cross-contamination) |
| PR7 | Risk Escalation Timeline | ✅ DONE | Reuses PR1's endpoint, no new backend work |
| PR2 | Preparedness Action Generator | ✅ DONE | Gemini via existing DecisionSupportService pattern; mock mode now reflects each city's own severity (routine vs. escalating) instead of one static fixture |
| PR6 | Preparedness Checklist UI | ✅ DONE | Checkboxes (localStorage-persisted), progress bar, deadlines resolved to real dates with urgency, agency ownership filter |
| PR4 | Agency Alert Templates | ✅ DONE | 4 audience-specific templates (Farmers/Hospitals/NGOs/Municipal Corps) per city from one Gemini call; routine-vs-escalating mock branching applied from the start (no repeat of the PR2 bug); master-detail city rail + audience tabs + copy-to-clipboard |
| PR4 ext. | Agency Alert manual send (WhatsApp + Email) | ✅ DONE | Manual-only send of the drafted alert to a pre-approved demo recipient list, via WAHA (WhatsApp) and Resend (email). Separate recipient env vars per channel; `EMAIL_ALERT_RECIPIENTS` deliberately kept independent of the existing `ALERT_RECIPIENTS` used by RESPONSE phase's automatic incident emails. Shared `"Label:value"` recipient parsing extracted into `backend/services/recipients.py`, used by both channels. |
| PR9 | Confidence-Based Alerting | ✅ DONE | `_summarize_forecast_by_day()` now computes `confidence_pct` (the % of a day's ~8 three-hour entries that agree with the day's chosen risk level) and `alert_recommended` (non-GREEN + confidence ≥ 70%) — real agreement-ratio math on data already fetched, not a fabricated score. Surfaced as a badge on Risk Timeline's per-day nodes and on Agency Alerts (plus a low-confidence warning banner there). |
| PR5 | Evacuation Route Pre-Calculation | ✅ DONE | New `GET /api/v1/prepare/evacuation-routes` adapts RESPONSE phase's real OSRM-routed egress corridors (`EvacuationZoneService.get_safe_routes`, already live for Feature 3A) to run proactively per forecasted city — gated on PR9's `alert_recommended` so the real OSRM call only fires once a day is both elevated and well-supported, not for every city or a brief spike. Risk Timeline shows a "Pre-calculate routes" panel only on qualifying cities. |

**PREPARE phase build order complete (PR1 → PR7 → PR2 → PR6 → PR4).** PR4 was later extended with manual WhatsApp/email send, and PR9 (Confidence-Based Alerting) and PR5 (Evacuation Route Pre-Calculation) have since also shipped.

(PR8 deferred earlier for fabrication risk — no verified historical disaster dataset exists to build it on. PR10 — redefined to validate the real 5-day forecast — is next and last in the confirmed build order.)

## Deferred decisions — to revisit once PREPARE phase is complete

### 1. Visual design polish pass
Raised after PR1/PR7 shipped — current UI is functional and verified but has a
"good, not winning" feel (font sizes, block spacing, overall polish didn't get
a dedicated pass yet). Scrollbar/flag/wrap issues were fixed reactively as
found, not as part of a deliberate design pass.

**Recommendation given:** defer a consolidated visual-polish pass to after all
5 PREPARE features ship, rather than interrupting feature velocity now.
**Decision:** not explicitly confirmed by Bhai — implicitly deferred by moving
straight to "next feature."

### 2. AI-generated narrative analysis on the Risk Timeline
Currently the escalation summary sentence ("Delhi escalates to RED by Day 3...")
is rule-based templating, not AI. Raised: should Gemini actually analyze the
5-day pattern (e.g. call out a squall pattern, flag that wind+rain combo is
more dangerous than rain total alone suggests) instead of/alongside the
template sentence?

- Does **not** require a database — single-snapshot analysis, same stateless
  pattern already used in `backend/services/decision_support.py`
  (Vertex AI Gemini call with `use_mock` fallback).
- A **database** only becomes necessary for a related but separate idea:
  trend-over-time analysis ("this forecast got worse since yesterday's check",
  "this is escalating faster than usual") — that needs stored historical
  snapshots to compare against, which nothing currently persists.

**Decision:** deferred until after PREPARE phase completes. Revisit then —
AI-narrative (no DB) is a low-risk upgrade; DB-backed trend analysis is a
larger, separate feature.

### 3. Forecast data persistence
Confirmed (by reading the code): `/api/v1/prepare/forecast` does not write to
the database — every call re-fetches live from OpenWeatherMap (or re-reads
the mock JSON) from scratch, nothing cached or stored.

Not a problem for the hackathon demo scale, but matters if:
- Multiple judges/users hit the dashboard simultaneously (repeated live API
  calls vs. served cache)
- We want historical trend data (see #2 above — this is the same gap)
- OpenWeatherMap is unreachable during judging (live mode has no DB fallback
  to serve from, by design — no silent mock fallback)

**Decision:** deferred, same bucket as #2.

---
*This file is a working log, not a spec — update it inline as new open
questions come up during PR2/PR6/PR4, don't wait until the end.*
