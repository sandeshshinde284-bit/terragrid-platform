# RESPONSE Phase — Build Log & Feature Audit

RESPONSE phase was built in an earlier session under a different, more
granular naming scheme (Feature 1-5 + 3A) than the original 13-feature
plan (Core 8 + Selected 5) scoped Sep 27. This file reconciles the two
and tracks what's actually been verified, not just claimed.

Deferred/not-now items have moved to `PHASE_2_ROADMAP.md` (RESPONSE
Phase 2 section) — this file tracks only what's live or in progress.

## Original 13-feature plan vs. verified status

| # | Feature | Status | Evidence |
|---|---|---|---|
| 1 | Real-time Ingestion | ✅ Verified | Live ingestion confirmed against real Postgres, 6 real events |
| 2 | Gemini AI Analysis | 🔶 Credential proven, backend not yet re-verified | `test_gemini_local.py` confirmed the service account + project work (real Gemini JSON response). Not yet confirmed through the actual running backend's `/insights` route with that credential wired into `.env` |
| 3 | Evacuation Zones | ✅ Verified | Real OSRM-routed geometry returned for a live test incident |
| 3 (polling) | Background Polling | ✅ Fixed and verified | Was completely dead due to a two-site `tzlocal`/`Asia-Calcutta` zoneinfo bug — found and fixed this session (`c4bffa7`) |
| 4 | Alert Broadcasting | ✅ Verified | Real WebSocket handshake + payload confirmed |
| 5 | Historical Learning RAG | 🔶 Credential proven, backend not yet re-verified | Same embeddings model (`text-embedding-004`) confirmed live via script. `VectorRAGEngine.get_historical_context()` not yet re-tested against the real Postgres DB with that credential wired in |
| 6 | Interactive Dashboard | ✅ Verified | DB-hydrated, confirmed |
| 7 | Source of Truth (lineage) | ✅ Fixed and verified | Was built but completely unwired (zero call sites anywhere in the ingestion pipeline) — fixed this session (`9c8de47`), confirmed live 4-layer chain for every real event |
| 8 | Resource Optimization | ✅ Built and verified | Was previously just a free-text field in Gemini's dossier JSON, not a standalone computation. Replaced this session (`af2cbab`) with a real deterministic allocation service — no AI dependency, integer allocations proven to sum exactly to the declared resource pool |
| 9 | Impact Score | ✅ Verified | Real risk_score/humanitarian_impact fields confirmed in live incident data |
| 10 | Emergency Route Finding | ✅ Verified | Same OSRM path as #3 |
| 11 | Image+Satellite Cross-Validation | 🔶 Built, not yet live-verified | Built this session (`627e6dd`): real NASA GIBS imagery fetch + Gemini multimodal visual check. Image fetch untestable *from this sandbox* (proxy-blocked — same restriction seen on OSRM/Resend all session, won't affect real deployment). AI verdict half pending the credential being wired into the actual backend |
| 12 | Ask the Map (NL Queries) | ⏸ Skipped for prototype | Moved to `PHASE_2_ROADMAP.md` — deliberate call given submission format, not a gap |
| 13 | Sentinel-1 Flood Detection | 🔶 Built, not yet live-verified | Built this session (`6cda478`): real port of the published UN-SPIDER/DeVries et al. (2020) methodology to the Earth Engine Python API (no official Python port exists anywhere). Needs Earth Engine access confirmed on the same service account (separate permission from plain Vertex AI) before it can run for real |

**Bottom line**: 9 of 13 fully verified live. 4 (#2, #5, #11, #13) have the
AI/EE credential independently proven to work (via a standalone script
run locally), but the actual backend routes haven't been re-tested with
that credential wired into `.env` yet — that's the next concrete step,
not a code gap. 1 (#12) is a deliberate skip, documented in
`PHASE_2_ROADMAP.md`.

## This session's fixes and additions

- **Fixed**: Feature 3/Background Polling, completely dead due to a
  `tzlocal`/zoneinfo bug under `TZ=Asia/Calcutta` (`c4bffa7`)
- **Fixed**: Source of Truth (lineage), built but never wired into the
  ingestion pipeline (`9c8de47`)
- **Added**: Resource Optimization as a real standalone deterministic
  service, replacing the AI-guessed JSON field (`af2cbab`)
- **Added**: Image+Satellite Cross-Validation (`627e6dd`)
- **Added**: Sentinel-1 Flood Detection via Earth Engine (`6cda478`)

## Known, not-yet-fixed data-quality issue (flagged, not actioned)

`backend/services/evacuation_zones.py`'s `_determine_area_type()` has a
hardcoded list of ~8 California cities with crude distance-based
matching, defaulting to `"dense_urban"` (10,000 people/km²) for
anywhere else — including virtually everywhere TerraGrid actually
monitors. Produces unrealistic population estimates outside those 8
cities (66M+ people estimated for a 75km radius around Sacramento in
one test). Flagged to Bhai, not yet actioned pending his decision.

---
*Next concrete step: wire `GOOGLE_APPLICATION_CREDENTIALS` into the
real `.env`, confirm Earth Engine access on the same/another service
account, run the backend locally, and re-test `/insights`,
`/satellite-validation`, and `/flood-detection` against real incidents.*
