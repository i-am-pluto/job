# Greenhouse Memory

Persistent operational memory for Greenhouse-hosted job discovery and application runs.

## Current Rules

- Discover jobs through the public Greenhouse Job Board API before opening a browser.
- Apply only to backend/fullstack roles with score 4 or higher.
- Use `generic-apply` for Greenhouse forms; do not duplicate form-fill logic in the Greenhouse skill.
- Batch successful applications with `scripts/db_batch_insert.py --apps`.
- Log nightly Greenhouse totals with `scripts/db_batch_insert.py --log-run --greenhouse N`.

## CRITICAL: Known Persistent Blockers (updated 2026-05-29)

These companies are permanently blocked or have hard disqualifiers. Check this list BEFORE opening any browser. If a queued job matches, mark it skipped in the run log and move on. Do NOT spend tool calls re-evaluating them.

| Company | Blocker type | Action | Since |
| --- | --- | --- | --- |
| Stripe | Safety restriction — CEO permanently blocked this employer | PERMANENT SKIP — do not attempt, do not open browser, do not score | 2026-05-28 |
| LaunchDarkly | Hard experience minimum 8+ years in JD — profile has ~4 years total | SCORE FAIL (< 4) — remove from queue, never re-queue | 2026-05-29 |
| HackerRank | Career page requires a HackerRank assessment before application submission | SAVE TO PIPELINE — human must complete assessment | 2026-05-28 |
| Razorpay | Career page requires a HackerRank assessment before application submission | SAVE TO PIPELINE — human must complete assessment | 2026-05-28 |
| Samsara | Career page access restricted / requires login before form appears | SAVE TO PIPELINE — human must apply manually | 2026-05-28 |
| Toast | Career page access restricted / requires login before form appears | SAVE TO PIPELINE — human must apply manually | 2026-05-28 |

When processing the queued pipeline jobs, check against this list first:
```
python3 scripts/db.py list  # check duplicates
# then: scan queued jobs vs. known-blocker list above
# skip blockers immediately, log reason, move to next
```

Expected tool calls for known-blocker handling: 1 tool call (list + compare in memory). Zero browser opens needed.

## Scoring Patch: Hard Experience Minimums (added 2026-05-29)

LaunchDarkly escaped the queue with an 8+ year hard minimum in its JD. This means the scoring step at queue-time was too permissive.

Scoring rule addendum: Before queuing any Greenhouse job, extract any explicit years-of-experience minimum from the JD. If the minimum is > 5 years, score the role as < 4 regardless of other signals. Do not queue it.

Profile baseline: ~4 years total experience. Hard minimums > 5 years are not achievable — do not queue, do not attempt.

## Queue Hygiene (added 2026-05-29)

When a queued job is found to have a hard disqualifier (experience minimum, assessment gate, employer restriction):
1. Remove it from `data/pipeline.md` (or mark as BLOCKED with reason).
2. Do NOT leave it in the queue to be re-discovered next run.
3. Add the company to the Known Persistent Blockers table above if the blocker is structural (not a temporary access issue).

The 2026-05-29 failure: 30 tool calls spent re-checking 10 queued jobs that were all blocked. If blockers had been logged and the queue cleaned after the 2026-05-28 run, the 2026-05-29 Greenhouse agent would have correctly reported "0 actionable queued jobs" in < 5 tool calls and stopped.

## Board Registry Notes

- Source of truth: `config/greenhouse_boards.yml`.
- Full board scans are throttled by `data/run-state.json` and run at most once every 7 days.
- On non-scan days, process already queued Greenhouse pipeline jobs only if browser permissions and budget allow.
- Mark 404 boards as `active: false`.
- Update `last_active` when a board returns qualifying jobs.
- Skip stale boards older than 30 days, but do not delete them.
- Known 404 boards (do not re-scan): grammarly, notion, plaid, ramp, rippling, segment.

## Browser Permission Pre-Check

Before starting the Greenhouse apply stage, confirm browser permissions for each queued domain:
- `boards.greenhouse.io` — required for all Greenhouse forms
- Per-company career domains (stripe.com excluded permanently)

If permissions are not confirmed, report "browser permission unconfirmed for [domain]" and skip that job. Do not attempt to grant permissions during the apply stage.

## Durable Learnings

- 2026-05-28: Greenhouse board token 404s: grammarly, notion, plaid, ramp, rippling, segment. Mark inactive in greenhouse_boards.yml.
- 2026-05-28: Stripe safety restriction established — permanently skip, no further evaluation needed.
- 2026-05-28: HackerRank and Razorpay require pre-application assessments — not automatable; save to pipeline for human action.
- 2026-05-29: LaunchDarkly queued with 8+ year hard minimum in JD — scoring step missed this. Scoring rule patched above.
- 2026-05-29: Samsara and Toast both returned restricted access on career page — saved to pipeline, human must apply. These companies recur in queue; mark as SAVE_TO_PIPELINE in any future scoring pass.
- 2026-05-29: 30 tool calls spent re-discovering the same blockers as the 2026-05-28 run. Known-blocker table above prevents this in future runs: check list first, skip in < 5 total tool calls if all queued jobs are blocked.
