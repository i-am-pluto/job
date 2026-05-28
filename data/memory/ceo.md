# Job CEO Memory

This is persistent operational memory for the job-search CEO agent. Keep it focused on durable run learnings, not profile facts. Profile facts belong in `profile.md`; resume facts belong in `resumes/*.md`.

## Current Priorities

- Preserve quality threshold: apply only to score 4 or 5 roles.
- Keep platform agents focused on backend/fullstack roles in India or India-compatible remote roles.
- Prefer cached resumes unless a concrete JD justifies tuning.
- Batch DB writes through helper scripts only.
- Schedule or re-trigger nightly runs AFTER 7pm IST to avoid session-limit blocks on all three platforms.
- Control token/session usage with sequential APPLY agents only. Never launch Naukri, Instahyre, and LinkedIn apply agents in parallel.
- Prioritize Naukri first, then Instahyre, then LinkedIn only as a bounded fallback if budget remains.

## Platform Health

| Platform | Recent signal | Applied this run | Blocker | Next adjustment |
| --- | --- | --- | --- | --- |
| Instahyre | 2 resume views (Centricity, Sprinklr). 24 apps submitted in run 2 (pre-limit). | 24 | Prior run overshot Instahyre cap | Remaining quota should be 0 unless new run date/day requires otherwise. Skip if today's count is already 15+. |
| Naukri | 0 recruiter responses. 7 profile views. 9 prior apps all "Application sent". 1 app in DB (Trade Brains). | 0 | Session limit hit before apply stage in run 2 | Top priority. Quota cap: 15. Do NOT use `--naukri` flag in db_batch_insert.py. Do not run profile boost. |
| LinkedIn | No recruiter replies. 3 stale threads (Amazon x2, Singapore x1). 20+ apply confirmation emails seen. | 0 | Cloudflare 522 + session limit in run 2 | Fallback only after Naukri + Instahyre. Cap 5-10 if budget remains; avoid complex external flows. |

## Agent Budgets

| Agent | Budget | Stop rule |
| --- | --- | --- |
| CEO preflight | 6 tool calls / 8k tokens max | Return remaining quotas and dup list only. |
| Status/Gmail | 10 tool calls / 8k tokens max | Clear status updates only; no broad mailbox analysis. |
| Resume strategy | 3 tool calls / 4k tokens max | Reuse cached PDFs unless a concrete JD requires tuning. |
| Naukri apply | 45 tool calls / 25k tokens max | Stop at 15 applied or budget limit. Flush every 3-4 apps. |
| Instahyre apply | 35 tool calls / 18k tokens max | Skip if remaining quota is 0; otherwise stop at 15 or budget limit. |
| LinkedIn apply | 25 tool calls / 15k tokens max | Fallback only; stop on first complex external flow. |
| Final log | 4 tool calls / 4k tokens max | Compact summary only; do not invoke long CEO log mode after failure. |

If any stage reports `You've hit your session limit`, stop the run immediately after flushing already-applied jobs. Do not retry, do not spawn more agents, and do not run CEO log mode.

## Run Learnings

- 2026-05-28: Plugin memory initialized. Next run should replace placeholder platform health with measured outcomes.
- 2026-05-28 (run 2): ALL THREE platforms blocked by session limit before apply stage. Run was scheduled too early. Must run after 7pm IST. STATUS phase succeeded fully.
- 2026-05-28: `db_batch_insert.py --log-run` does NOT support `--naukri` flag. Log Naukri applied count in `--summary` text only.
- 2026-05-28: LinkedIn first-attempt failure pattern: Cloudflare 522 timeout before session-limit hit. Retry works but session was already expired. Run timing is the root fix.
- 2026-05-28: Gmail scan found clear rejections for EPAM India (Sr Java SDE) and foodpanda (Backend SDE II). Both need DB status updates if those applications are tracked.
- 2026-05-28: Goldman Sachs has an incomplete application in-flight. Human must decide whether to complete it.
- 2026-05-28: EPAM sent a "Confirm your application" email — this requires a human email click; agent cannot action it.
- 2026-05-28: Resume strategy: all three archetypes (general-backend/base.pdf, distributed-data/backend-systems.pdf, ai-backend/ai-backend.pdf) were REUSE. 0 tuning needed this run.
- 2026-05-28: Instahyre resume views: Centricity WealthTech (May 25) and Sprinklr (Jan 8) — activity exists but no active recruiter outreach.
- 2026-05-28 (run 3 — session reset): Session limit confirmed cleared. Previous run applied 24 Instahyre jobs successfully before the limit hit (all logged in DB). Fixed workflow assumption: quotas are remaining caps, not automatic 15/15/15 launches. Resume REUSE decisions carry over — no tuning needed. Dup list now has 26 total entries; all 24 new Instahyre apps are in DB. Carry-over STATUS/ACTION items from run 2 still pending (EPAM/foodpanda rejections, Goldman Sachs incomplete app).
- 2026-05-28: Quota burn root cause was parallel APPLY agent fan-out plus long CEO/profile/log calls. Future runs must use a sequential controller with per-agent budgets: Naukri first, Instahyre second if remaining quota exists, LinkedIn fallback only.

## Action Items Backlog (requires human)

- Goldman Sachs: incomplete application "Software Engineering - Data, Lakehouse and AI Data Platform Engineer" — decide to complete or abandon.
- EPAM India: "Confirm your application" email — click required, agent cannot action.
- Amazon recruiter Jiani Ji: 15 days no reply after resume sent May 13 — consider follow-up.
- Amazon recruiter Manikanta Bellapu: 15 days no reply after resume sent May 13 — consider follow-up.
- Singapore recruiter Adam Modelski (Legacy Resourcing): 8 days no reply after resume sent May 20 — consider follow-up.

## Status Updates Needed in DB

- EPAM India — Sr Java Software Developer — Rejected (gmail subject: "Unfortunately...")
- foodpanda — Backend Software Engineer II — Rejected (gmail subject: "after careful consideration...")

## Next Run Checklist

- [x] Session limit confirmed reset — this is the active run session.
- [x] Resume decisions confirmed REUSE: general-backend→output/base.pdf, distributed-data→output/backend-systems.pdf, ai-backend→output/ai-backend.pdf.
- [x] Dup list refreshed from DB: 26 entries (see DB list).
- Update EPAM India and foodpanda statuses to Rejected in DB (STATUS/ACTION stage carry-over).
- Remaining quota is computed from DB/run state before each platform. Do not assume Instahyre 15 / Naukri 15 / LinkedIn 15 are all active.
- Run Naukri APPLY first. Run Instahyre only if today's remaining Instahyre quota is positive. Run LinkedIn only if budget remains.
- Flush applications with `scripts/db_batch_insert.py --apps`.
- Append only durable lessons to memory files.
- Do NOT use `--naukri` flag in db_batch_insert.py — it does not exist.
- Run AFTER 7pm IST for future sessions (session limits reset at 7pm IST on all three platforms).
