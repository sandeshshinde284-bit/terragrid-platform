# Open Items / Decisions Log

Running list of things flagged but deliberately NOT fixed yet, so nothing
gets lost under deadline pressure. Prototype deadline: Oct 18, 2026.
Submission deadline: Oct 25, 2026.

## Zero-mock-data discipline
Every item below was found or decided by checking actual code, not assumed.
When picking one up, verify it's still accurate (code may have moved).

---

## 1. "Needs attention first" priority strip — not geolocation-based

**Where:** `frontend/src/views/prepare/ForecastDashboard.vue`, `priorityIncidents`
computed property.

**What it actually does today:** scans ALL monitored cities worldwide,
picks the top 3 whose worst day has crossed out of GREEN, ranked by
severity — **regardless of which country the viewer is in or which country
tab is open.** There is no geolocation, no IP lookup, no concept of "where
the user is" anywhere in the app.

**Decision needed:** how should this scope?
- (a) Keep as global top-3 (current behavior) — zero work.
- (b) Scope to whichever country tab is already selected on this screen —
  cheap, reuses the existing `selectedCountry` filter, no new permissions.
- (c) Real geolocation/IP detection of the viewer's actual location —
  more work, needs a fallback for denied permission or a location outside
  the monitored-cities list.

**Status:** deferred by user (Oct 17) — "skip for now but let's create a
document so we don't forget anything." Not implemented. Revisit before
submission.

---

## 2. Infrastructure/geospatial linkage (Respond phase)

**Where:** `InfrastructureService` (`backend/services/infrastructure.py`) —
queries OpenStreetMap/Overpass for real hospitals, fire stations, schools,
power grids, bridges near a lat/lon, specifically to stop the AI from
hallucinating nearby infrastructure.

**Current state:** wired into RESPOND's incident routes
(`backend/routes/incidents.py`) only. Not connected to Prepare at all.

**Status:** deferred, explicitly flagged to user as a Respond-phase item.
Not started.

---

## 3. `IncidentDetail.vue` — evidence tabs are 100% mock data

**Where:** `frontend/src/views/IncidentDetail.vue`. The `detail` computed
property does `JSON.parse(JSON.stringify(mockDetails))` from
`@/data/mock_incident_evidence.json` unconditionally on every render,
overlaying only `lastUpdated`/`lastVerified` timestamps. Source/AI/evidence/
audit-trail tabs show identical fabricated content no matter which incident
you open.

**Severity:** significant, pre-existing zero-mock-data violation. Found
during the external-review fact-check pass (not something the review itself
caught).

**Status:** RESOLVED on `feature/unified-incident-id` (Oct 17). The mock file
was deleted. Overview now shows only real values, "—" when a value is missing.
Also removed the same invented defaults from Dashboard, Incidents, Alerts,
Map, Analysis, IncidentCard and the websocket feed (150 km², 50,000 people,
5.2 km²/h, 31.2 km² forecast, threat score 50, wind speed and 28.4°C/78%
sensor readings). Runtime-unverified: needs a live-DB check.

---

## 4. Prepare ↔ Respond phase linkage (the core USP problem)

**Background:** the product's pitched 4-phase lifecycle is
Predict → Prepare → Response → Recover. Prepare and Respond are currently
disconnected systems:
- **Prepare** = `OpenWeatherService` forecast, in-memory cache only, never
  persisted to the DB.
- **Respond** = persisted SQLAlchemy `Event` model, populated by a separate
  NASA/USGS/NOAA detection pipeline.
- Zero code-level links between them in either direction (confirmed via
  grep — only false-positive matches on the word "prepare"/"preparedness"
  inside unrelated Respond-phase recommended-action text).
- One existing positive link: `/prepare/evacuation-routes` already reuses
  Respond's real `EvacuationZoneService.get_safe_routes`.

**Agreed plan (user's own, Oct 17):**
1. Fix any remaining Prepare issues individually (1–2 hr budget). **DONE** —
   PR #14 (priority strip + Evidence-to-Action chain, merged) and PR #15
   (i18n sweep + second jargon-phrase fix, open, not yet merged).
2. Fully recheck/audit the complete Respond phase — routes, services, all
   Respond `.vue` views (Dashboard, IncidentsScreen, IncidentDetail,
   MapFullScreen, AnalysisScreen, AlertsScreen) for mock data, jargon,
   hardcoded/un-localized text, and general correctness. **Known lead:**
   item #3 above. **NOT STARTED.**
3. Only after Stage 2's findings are confirmed with the user — decide how
   to actually link Prepare and Respond. Three options were discussed but
   none chosen yet: (i) navigational link only, (ii) a real predictive
   hand-off from Prepare into the Respond `Event` DB, (iii) defer past the
   deadline. **NOT DECIDED.**

**Status:** Stage 1 done, Stage 2 next, Stage 3 blocked on Stage 2.

---

## 5. Two events at identical coordinates can merge into one row (found Oct 17)

**Where:** `backend/services/data_ingestion.py`, `_store_event_sync`. It
deduplicates by `(round(lat,4), round(lon,4), event_type)`. Two real events of
the same type at the same rounded location become one database row.

**Effect:** a second flood at the exact same spot won't appear as its own
incident. Rare in practice, but it can happen (e.g. repeated alerts for one
river station).

**Status:** noted, not changed. Needs a product decision on what counts as
"the same event" (source ID vs. location).

## 6. Unified incident ID + shared selection (done on `feature/unified-incident-id`)

- Ingest response now stamps `event_<db id>` onto each event
  (`data_ingestion.py`, after `_store_event_sync`), matching `GET /incidents`.
- Dashboard prefers `event.id` over source-specific IDs, and no longer uses
  `Date.now()` in the fallback ID.
- Incidents screen uses the shared `appStore.selectedIncident`, highlights the
  same row the Dashboard/map picked, and scrolls it into view.
- Not runtime-tested against a live database yet; only compiled and built.


## 7. Stage 2 Respond audit - status (Oct 17)

- Point 2 (report flow): teaser now goes straight to the incident's overview;
  report shows top 3 resources first. Still open: whether the AI plan and
  dossier content is actually useful for an official (needs a domain check).
- Point 3 (dashboard vs incidents): dashboard list shows top 5 by risk; the
  Incidents page is the full table. Shared ID and selection in PR #16.
- Point 4 (map highlight): full-screen map marker click now selects the
  incident and shows an "Open incident" card.
- Landing: `/` already loads the Response dashboard.
- Fallback AI plan/dossier (`backend/data/fallbacks/*.json`) is one generic
  "offline" message for every incident. Honest, but identical. Left as-is.
- Demo mode (`initMockData` in the store) only runs when the user turns on
  mock mode and the live fetch fails. Left as-is, deliberate.
- Current status / Last operational update text in Overview is still
  hardcoded English. Not a mock-data issue; left for a localisation pass.
