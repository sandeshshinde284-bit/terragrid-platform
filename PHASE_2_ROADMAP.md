# Phase 2 Roadmap — Deferred & Not-Now Items

Consolidated backlog of everything deliberately NOT being built for the
Oct 18 prototype / Oct 25 submission, organized by disaster-management
lifecycle stage (PREPARE, RESPONSE, PREDICT, RECOVER). This is a
reorganization, not new scope — every item here was already decided
against building now; this file just gives each a single, findable home
instead of being buried inline in per-phase build logs.

PREDICT and RECOVER are not phases TerraGrid has built any part of yet
(only PREPARE and RESPONSE exist in code). Their sections below are
placeholders for exactly that reason — nothing is listed under them
because nothing has been proposed and deferred there yet, not because
content was omitted.

---

## PREPARE Phase 2

### PR3 — Resource Pre-Positioning Map (Asset Tracking) — 🧊 ICEBOXED
Would show real-time ambulances/rescue boats/water trucks on a map.
Iceboxed, not deferred-for-later: there's no sovereign municipal
database integration giving TerraGrid live GPS coordinates for real
emergency assets, and building it anyway would mean plotting invented
GPS dots on the map — a direct violation of the project's Zero-Mock-Data
rule. Unlike PR8 below (blocked on a historical dataset that might
someday exist), PR3 is blocked on data access TerraGrid will likely
never have; revisit only if a real asset-tracking data source becomes
available.

### PR8 — ⏸ DEFERRED
Deferred: no verified historical dataset exists to build this against.
(This is the full extent of what was documented for PR8 at the time it
was deferred — no fuller spec exists in the project's history, so none
is invented here. If PR8's original intent needs to be recovered, that
has to come from Bhai, not reconstructed.)

### Visual design polish pass
Raised after PR1/PR7 shipped — the UI is functional and verified but has
a "good, not winning" feel (font sizes, block spacing, overall polish
didn't get a dedicated pass). Scrollbar/flag/wrap issues were fixed
reactively as found, not as part of a deliberate design pass.
**Decision:** deferred to after the prototype ships.

### AI-generated narrative analysis on the Risk Timeline
Currently the escalation summary sentence ("Delhi escalates to RED by
Day 3...") is rule-based templating, not AI. Open question: should
Gemini actually analyze the 5-day pattern (e.g. call out a squall
pattern, flag that wind+rain combo is more dangerous than rain total
alone suggests) instead of/alongside the template sentence?
- Does **not** require a database — single-snapshot analysis, same
  stateless pattern already used in `backend/services/decision_support.py`.
- A **database** only becomes necessary for a related but separate idea:
  trend-over-time analysis ("this forecast got worse since yesterday's
  check") — needs stored historical snapshots, which nothing currently
  persists.
**Decision:** deferred. AI-narrative (no DB) is a low-risk upgrade;
DB-backed trend analysis is a larger, separate feature.

### Forecast data persistence
Confirmed by reading the code: `/api/v1/prepare/forecast` does not write
to the database — every call re-fetches live from OpenWeatherMap (or
re-reads the mock JSON) from scratch, nothing cached or stored. Not a
problem at hackathon demo scale, but matters if: multiple judges hit the
dashboard simultaneously (repeated live API calls vs. a served cache),
historical trend data is wanted later (same gap as above), or
OpenWeatherMap is unreachable during judging (no DB fallback to serve
from, by design — no silent mock fallback).
**Decision:** deferred, same bucket as the narrative-analysis item above.

---

## RESPONSE Phase 2

### Feature 12 — Ask the Map (Natural Language Queries) — ⏸ SKIPPED FOR PROTOTYPE
Gemini function-calling to translate natural language into the existing
`/api/v1/incidents` filters (status/severity/event_type — already live).
Deliberately not built for Oct 18: the submission is judged from a
walkthrough/recording rather than live judge interaction, so an
unused NL search box has low demo value relative to its cost. Backend
work would be small (~1-2 hrs) once Gemini credentials are confirmed
live — revisit if selected for a later round where live interaction
matters.

---

## PREDICT Phase 2

*(placeholder — no PREDICT-phase work has been scoped or deferred yet)*

---

## RECOVER Phase 2

*(placeholder — no RECOVER-phase work has been scoped or deferred yet)*

---
*This file is a living backlog — add to the matching phase section as
new "not now" decisions get made, rather than letting them sit inline
in a build log.*
