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
| 10 | AI priority vs officer priority | Kept separate. Gemini's `IMMEDIATE / HIGH / STAGED` is stored as received and never overwritten. The officer's `high / medium / low` controls task ordering. Suggested default when the officer has not chosen: `IMMEDIATE → high`, `HIGH → high`, `STAGED → medium`. This is a default, not an equivalence between the scales. |
| 11 | Report version | Every decision and task records its report version. Decisions cannot be applied to a superseded report (already enforced by the decide endpoint, which returns 409). Tasks from earlier versions stay open and editable. |
| 12 | Create Response Plan | Opens the recommendation selection only. The UI must not describe anything as saved until a decision is persisted. |
| 13 | Idempotent approval | One transaction saves the decision, creates the task and writes the audit entry. A duplicate decision for the same report and action is refused. Verified: the decide endpoint already does all three in one commit and refuses duplicates. Still to add: a concurrent duplicate that slips past the check must return 409, not 500 (handle the unique-constraint error). |
| 14 | Task progress history | Recorded as `incident_response_log` events, not as a single latest note. Verified: status changes are already logged with their note. No `progress_note` column is added; if the latest note is needed on screen, it is read from the log. |
| 15 | Progress calculation | Task completion = done tasks ÷ approved tasks, counting tasks from all report versions. Review progress = decided recommendations ÷ recommendations in the latest report. The two are shown separately. |
| 16 | Three separate statuses | Incident status (existing: open, investigating, responding, resolved). Plan review status (Pending, Partially Reviewed, Fully Reviewed). Task execution status (open, acknowledged, in progress, blocked, done). Plan Summary never sets the incident to resolved. |
| 17 | Source of recommendations | The Response Plan is built only from the saved Gemini report. It never triggers a new Gemini call. |

## Data the screens may show

- Recommendation text, AI priority and AI category: from the saved crisis report (`incident_reports.payload`).
- Officer decision, officer priority, assignee, due date, reason: from `response_plan_decisions` and `response_tasks`.
- Progress notes and status history: `incident_response_log` (existing), read back per task.
- Nothing else. Mockup values such as team names, timeframes and population figures are illustrative and must not appear on the live screen.

## Changes from the review

- `response_tasks.progress_note` is dropped. Progress history comes from `incident_response_log`.
- Step 4 must handle the concurrent duplicate-decision case (409, not 500).
- Step 7 (activity log) is no longer optional: approve, reject and task updates are already logged, so it is verification only.

## Step 1: done

- Added `ai_priority`, `ai_category` and `officer_priority` to `response_plan_decisions`.
- Migration `005_decision_snapshot` adds them. It is written to work with the startup `create_all` path, which builds these tables outside the migrations. Tested: upgrade, downgrade and upgrade again on the local database.
- The decide endpoint copies the AI values from the saved report by index. The client cannot set them.
- `officer_priority` is set only for approvals.
- `decided_at` was not added. `created_at` already records when the decision was saved, so a second timestamp would duplicate it.
- Not yet tested: a real approval through the endpoint. That needs a saved Gemini report, and none exists in this environment.

## Step 2: done

`GET /response/plan` now returns:
- `actions`: the latest report's recommendations. Each has its AI priority and category (the decision's snapshot if one exists, otherwise the saved report), `officer_priority`, `decision`, `decided_by`, `decided_at`, and the linked `task`.
- `tasks`: every task for the incident, from all report versions. Each has `report_version`, which is null for tasks created directly.
- `review`: counts for the latest report: total, approved, rejected, pending.
- `task_summary`: counts for tasks approved from any report version: approved, done, and by status.

Existing fields are unchanged, so `ResponsePlanPanel` keeps working.

Tested:
- Inside a transaction rolled back afterwards: two report versions with decisions. Results: the latest version is shown, decisions from the older version are not applied to it, the older version's approved task still appears with its version, and the counts are correct.
- Over HTTP on a real event with no saved report: the endpoint returns the empty state.
- Not tested: a real Gemini report, because none exists in this environment.

## Step 3: done

In `ResponsePlanPanel.vue`:
- The panel opens on an overview: counts (total, approved, rejected, pending) and one button that matches the plan state. No report: no button, only the message. Nothing decided: "Create Response Plan". Decisions made but none approved: "Continue Response Plan". Any approved: "Manage Response Plan".
- Create opens the selection: checkboxes, Select all, Clear selection, a count, and each action's AI priority and category (or "not in report"). All actions start selected.
- Continue opens review for the selected actions plus any already decided. Resuming a plan reviews the pending actions.
- Selection is screen state only. The screen says it is not saved, and a refresh clears it.
- The existing approve and reject controls are unchanged.

Tested in the browser with mocked plan responses (test data only, not saved): no report, fresh report, and one approved. All checks pass. Not yet checked by eye at tablet width.

## Next

- Step 4: Review & Approve Actions. Refine decisions, add the duplicate-decision 409 handling, and show the report version per decision.
