# Response tab: Step 0 decisions

Status: decided. These are the recommended defaults from the planning notes, confirmed by "complete step 0".
Change this file if a decision changes; the code follows it.

## Decisions

| # | Question | Decision |
|---|----------|----------|
| 1 | Officer priority scale | `high / medium / low` (existing task values). Gemini's `IMMEDIATE / HIGH / STAGED` is shown as the AI suggestion next to it. The officer's choice is stored separately and can differ from the AI suggestion. |
| 2 | Assignee | Free text, max 120 characters (existing `assignee` field). No fixed team list. |
| 3 | "Key Details" column (timeframes, population notes) | Removed. Only AI priority and AI category are shown until grounded fields exist. |
| 4 | Plan name | Derived from incident data: "<event type> · <location> · Response Plan". No AI-written name or description. |
| 5 | Separate `response_plans` table | Not created. A plan is the recommendations of one report version plus their decisions. |
| 6 | Draft selection (Step 3) | Kept in local screen state until the officer continues. The screen must not say it is saved. |
| 7 | Created by / Created on | Shown only after a decision exists, from that decision's officer and timestamp. |
| 8 | Activity log and export | Activity log only if the decide endpoint already writes to `incident_response_log` (checked in Step 7). Export deferred. |
| 9 | Tasks from earlier report versions | Kept and shown in Active Tasks. A new report does not remove them. |

## Data the screens may show

- Recommendation text, AI priority and AI category: from the saved crisis report (`incident_reports.payload`).
- Officer decision, officer priority, assignee, due date, reason: from `response_plan_decisions` and `response_tasks`.
- Progress notes: `response_tasks` (new `progress_note` field, Step 5).
- Nothing else. Mockup values such as team names, timeframes and population figures are illustrative and must not appear on the live screen.

## Next

- Step 1: add `ai_priority`, `ai_category`, `officer_priority` and `decided_at` to `response_plan_decisions` (Alembic migration).
