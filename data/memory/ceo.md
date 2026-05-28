# Job CEO Memory

This is persistent operational memory for the job-search CEO agent. Keep it focused on durable run learnings, not profile facts. Profile facts belong in `profile.md`; resume facts belong in `resumes/*.md`.

## Current Priorities

- Preserve quality threshold: apply only to score 4 or 5 roles.
- Keep platform agents focused on backend/fullstack roles in India or India-compatible remote roles.
- Prefer cached resumes unless a concrete JD justifies tuning.
- Batch DB writes through helper scripts only.
- Schedule or re-trigger nightly runs AFTER 7pm IST to avoid session-limit blocks on all three platforms.
- Control token/session usage with sequential APPLY agents only. Never launch Naukri, Instahyre, and LinkedIn apply agents in parallel.
- Prioritize Naukri first, then Instahyre, then LinkedIn only as a bounded 3-5 Easy Apply fallback if budget remains.
- Nightly status checks are Gmail-only and incremental from `data/run-state.json`; portal status checks are manual/weekly only.
- Greenhouse full board scans run at most once every 7 days using `data/run-state.json`; non-scan days can process queued pipeline jobs only.
- Greenhouse: requires browser domain permission grants before autonomous apply is possible. Pre-check permission status before scheduling Greenhouse apply stage.

## Platform Health

| Platform | Recent signal | Applied this run | Blocker | Next adjustment |
| --- | --- | --- | --- | --- |
| Instahyre | 2 resume views (Centricity WealthTech May 25, Sprinklr Jan 8). 25 total apps in DB. Queue exhausted today. | 0 (queue exhausted) | All 25 applied earlier same day; 0 undecided cards remaining | Skip Instahyre if today's count >= 15. Resume next day. |
| Naukri | 0 recruiter responses. High activity level (4 NVites, mostly mismatches). 6 total apps in DB (1 this run: IDESLABS). | 1 | Naukri NopeRi API needs NAUKRI_USERNAME/NAUKRI_PASSWORD in .env. Questionnaire 406 blocks (Synaptein, Hour Consulting, NeoSOFT). Large Accenture/big-co external redirect flood — low value. | Set NAUKRI_USERNAME and NAUKRI_PASSWORD in .env before next run. Quota cap 15. |
| LinkedIn | 87 applied total (external tracking). 0 recruiter replies. 0 interview advances. Top Applicant signal for Peak XV. | 0 (all external-apply) | All scanned keyword results were large-company external-apply dominated. Synthetic click failure on Easy Apply modal. | Use coordinate-click for Easy Apply modal (not JS click). Only pursue Easy Apply; external paths require explicit budget. Cap 3-5 applications. |
| Greenhouse | 25 boards scanned (19 active, 6 404: grammarly, notion, plaid, ramp, rippling, segment). 10 high-score jobs found and queued. | 0 | Browser permissions blocked for boards.greenhouse.io and all company career domains. | Human must grant browser permission for boards.greenhouse.io and Stripe/HackerRank/Razorpay/LaunchDarkly/Toast/Samsara career domains. Then Greenhouse can use generic-apply. |

## Agent Budgets

| Agent | Budget | Stop rule |
| --- | --- | --- |
| CEO preflight | 6 tool calls / 8k tokens max | Return remaining quotas and dup list only. |
| Status/Gmail | 6 tool calls / 5k tokens max | Incremental Gmail only; no portal status checks. |
| Resume strategy | 3 tool calls / 4k tokens max | Reuse cached PDFs unless a concrete JD requires tuning. |
| Naukri apply | 45 tool calls / 25k tokens max | Stop at 15 applied or budget limit. Flush every 3-4 apps. |
| Instahyre apply | 35 tool calls / 18k tokens max | Skip if remaining quota is 0; otherwise stop at 15 or budget limit. |
| LinkedIn apply | 12 tool calls / 8k tokens max | Fallback only; Easy Apply only; cap 3-5. |
| Greenhouse apply | 20 tool calls / 12k tokens max | Only if browser permission confirmed. Use generic-apply per job. Cap 10. |
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
- 2026-05-28 (run 4 — final log): Naukri 1 applied (IDESLABS BackEnd Developer, Bengaluru, score 4). Instahyre exhausted (25 apps today). LinkedIn 0 applied — all scanned jobs were external-apply dominated; 14 saved to pipeline. Greenhouse 0 applied — browser domain permissions blocked all 10 queued high-score jobs (Stripe x4, LaunchDarkly, Samsara, Toast, HackerRank x2, Razorpay). Naukri NopeRi adapter needs .env credentials to function reliably. Total DB: 31 applications (25 instahyre, 6 naukri).
- 2026-05-28: Naukri questionnaire 406 block pattern: Synaptein, Hour Consulting, NeoSOFT all triggered questionnaire blocks. These appear when Naukri's job form includes employer-specific screening questions that NopeRi cannot submit. Skip these with a note; do not retry.
- 2026-05-28: Greenhouse board token 404s: grammarly, notion, plaid, ramp, rippling, segment. Remove or mark inactive in greenhouse_boards.yml on next maintenance pass.
- 2026-05-28: LinkedIn "Top Applicant" signal on Peak XV Senior Full-Stack Engineer (job ID 4419048709) — investigate and prioritize if Easy Apply is available.
- 2026-05-28: Narendra K. (Honeywell, LinkedIn) sent outreach Wed 7:25 AM — no response yet. Human should decide whether to reply.

## Action Items Backlog (requires human)

- Goldman Sachs: incomplete application "Software Engineering - Data, Lakehouse and AI Data Platform Engineer" — decide to complete or abandon.
- EPAM India: "Confirm your application" email — click required, agent cannot action.
- Amazon recruiter Jiani Ji: reply pending after resume sent May 13 — consider follow-up.
- Amazon recruiter Manikanta Bellapu: reply pending after resume sent May 13 — consider follow-up.
- Singapore recruiter Adam Modelski (Legacy Resourcing): reply pending after resume sent May 20 — consider follow-up.
- LinkedIn Narendra K. (Honeywell) outreach: sent Wed 7:25 AM — decide whether to reply.
- Greenhouse browser permissions: grant permissions for boards.greenhouse.io, stripe.com, hackerrank.com, razorpay.com, launchdarkly.com, toast.com, samsara.com to enable autonomous apply next run.
- Peak XV Senior Full-Stack Engineer (LinkedIn job 4419048709): Top Applicant signal — check if Easy Apply is still open and prioritize.

## Status Updates Needed in DB

- EPAM India — Sr Java Software Developer — Rejected (gmail: "Unfortunately...")
- foodpanda — Backend Software Engineer II — Rejected (gmail: "after careful consideration...")

## Next Run Checklist

- [ ] Set NAUKRI_USERNAME and NAUKRI_PASSWORD in .env before run — NopeRi adapter is blocked without credentials.
- [ ] Grant browser permissions for boards.greenhouse.io and Stripe/HackerRank/Razorpay/LaunchDarkly/Toast/Samsara career domains before run — 10 high-score Greenhouse jobs queued in pipeline.
- [ ] Update EPAM India and foodpanda statuses to Rejected in DB (carry-over from prior runs).
- [ ] Run AFTER 7pm IST — session limits reset at 7pm IST on all platforms.
- [ ] Run order: Naukri first through NopeRi only (quota 15), Instahyre second (only if today count < 15, otherwise skip), LinkedIn third (Easy Apply only, cap 3-5), Greenhouse fourth (weekly board scan only if due; otherwise queued jobs only if permissions confirmed).
- [ ] Refresh dup list from DB before each platform: `python3 scripts/db.py list`.
- [ ] Do NOT use `--naukri` flag in db_batch_insert.py — it does not exist.
- [ ] Remove or mark inactive Greenhouse boards: grammarly, notion, plaid, ramp, rippling, segment (all returned 404 this run).
- [ ] Pipeline has 10 Greenhouse jobs and 14 LinkedIn jobs ready — prioritize Greenhouse queued jobs on non-scan days; LinkedIn external jobs require explicit budget.
- [ ] Flush Naukri apps with `scripts/db_batch_insert.py --apps` after every 3-4 successful applications.
- [ ] LinkedIn: use coordinate-click (not JS click) for Easy Apply modal. Budget ~6-8 tool calls per Easy Apply job.
