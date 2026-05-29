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
| Instahyre | Queue exhausted 2026-05-29 (second consecutive day after 25-app run 2026-05-28). 25 total apps in DB. | 0 (queue exhausted — expected, not a bug) | Matching feed empty — refreshes daily. Used only 12 tool calls; agent stopped correctly. | Queue expected to refresh by next run. Check matching=true&status=0 first; if empty, skip stage entirely in < 5 tool calls. |
| Naukri | 3 new apps 2026-05-29 (TCS, Persistent, Nustar). Sandhata was dupe. 50 total Naukri apps in DB. | 3 (4 attempted, 1 dupe skipped) | Keyword "Java developer" surfacing walk-in events and LAMP roles. Quota of 15 not met. | Switch to quality keywords: "Java backend", "Spring Boot", "backend engineer", "platform engineer". Re-read dup list right before building submission batch. |
| LinkedIn | 0 applied 2026-05-29. 47 tool calls consumed on 1 stuck job (G-P Greenhouse-inside-LinkedIn trap). | 0 (budget exhausted on 1 job) | Greenhouse-inside-LinkedIn modal trap. Pre-scoring rule not followed. Keyword "Java backend" returned 400+ results with ~1% Easy Apply rate. | Score ALL cards before opening any. Detect and immediately skip Greenhouse-inside-LinkedIn jobs. Switch to narrower keywords. |
| Greenhouse | 0 applied 2026-05-29 (0 applied across all runs). 10 queued jobs all blocked. | 0 (all queued jobs hit known blockers) | Stripe (permanent), LaunchDarkly (8+ yr min — should never have been queued), HackerRank/Razorpay (assessment gates), Samsara/Toast (access restricted). Board scan not due until 2026-06-04. | Clean the queue: remove LaunchDarkly (score fail), save HackerRank/Razorpay/Samsara/Toast to pipeline, skip Stripe. Known-blocker table in greenhouse.md now enables short-circuit in < 5 tool calls. Human must grant browser permissions. |

## Pipeline Processing (STAGE 4 — after Naukri/Instahyre, before LinkedIn)

`data/pipeline.md` accumulates external ATS redirects from Naukri scans, Greenhouse-inside-LinkedIn detections, and manually saved URLs. The CEO must process this as a dedicated stage every nightly run.

**Who processes what:**
- `boards.greenhouse.io` / `job-boards.greenhouse.io` URLs → route to greenhouse-agent (score via API first, no browser needed for scoring)
- `jobs.lever.co` / `jobs.ashbyhq.com` / `apply.workable.com` / other ATS URLs → route to generic-apply-agent after CEO scores the title+role
- Already-applied companies (check `db.py list`) → mark as `Applied` in pipeline.md and skip

**CEO pipeline processing workflow:**
1. Read `data/pipeline.md` — collect all rows with `Status: Pending`
2. Dedupe against `python3 scripts/db.py list` — mark matches `Applied` in the table
3. Score remaining rows: title + company → apply profile scoring rules. Skip score < 4.
4. Split qualifying rows by ATS type (Greenhouse vs. other)
5. For Greenhouse URLs: pass to greenhouse-agent batch (API scoring first, no browser until apply)
6. For other ATS URLs: pass to generic-apply-agent in batches of 3-5 per run
7. After processing, update `Status` in pipeline.md: `Applied`, `Skipped (score N)`, `Queued (next run)`, or `Blocked (reason)`
8. Budget: ~10 tool calls for CEO pipeline triage + agent budgets per platform

**Budget for pipeline apply agents:**
- Greenhouse pipeline batch: up to 10 applications, 20 tool calls delegated to greenhouse-agent
- Generic-apply pipeline batch: up to 5 applications, 15 tool calls each

Note: pipeline.md currently has 54+ Pending entries from 2026-04-12. Many are high-score AI/backend roles (Perplexity, Palantir, Replit, Cohere, Notion, etc.). These should be processed before adding new pipeline entries.

## Agent Budgets (revised 2026-05-29)

| Agent | Budget | Stop rule | Efficiency note |
| --- | --- | --- | --- |
| CEO preflight | 6 tool calls / 8k tokens max | Return remaining quotas and dup list only. | — |
| Status/Gmail | 6 tool calls / 5k tokens max | Incremental Gmail only; no portal status checks. | — |
| Resume strategy | 3 tool calls / 4k tokens max | Reuse cached PDFs unless a concrete JD requires tuning. | — |
| Naukri apply | 45 tool calls / 25k tokens max | Stop at 15 applied or budget limit. Flush every 3-4 apps. Re-read dup list before batch. | ~3 tool calls per apply expected via NopeRi. Budget allows ~12-15 applies plus scan overhead. |
| Instahyre apply | 35 tool calls / 18k tokens max | Skip if matching queue empty (confirmed in < 5 tool calls); otherwise stop at 15 or budget. | Queue check costs 2-3 tool calls. If empty, use remaining 32 for other stage or stop. |
| LinkedIn apply | 12 tool calls / 8k tokens max | Fallback only; Easy Apply only; cap 3-5. **Max 10 tool calls per individual job.** Pre-score ALL cards before opening any. | Budget breakdown: 3 calls for page scan/scoring, ~3 calls per Easy Apply submit. |
| Greenhouse apply | 20 tool calls / 12k tokens max | Check known-blocker list first in < 5 calls. Only open browser if permissions confirmed. | If all queued jobs are known-blocked, report in < 5 calls and stop. Do not re-evaluate known blockers. |
| Final log | 4 tool calls / 4k tokens max | Compact summary only; do not invoke long CEO log mode after failure. | — |

If any stage reports `You've hit your session limit`, stop the run immediately after flushing already-applied jobs. Do not retry, do not spawn more agents, and do not run CEO log mode.

## Known Permanent Skips

Skip in 0 tool calls — structural, not fixable by permissions.

| Company | Platform | Blocker |
| --- | --- | --- |
| Stripe (all roles) | Greenhouse | CEO safety restriction — permanent employer block |
| LaunchDarkly | Greenhouse | Hard 8+ year experience minimum — score < 4; remove from queue |

## Permission-Gated Companies (high value — worth unlocking)

These are blocked only because browser permissions have not been granted. They should be applied to. User must run `/mcp` → Claude in Chrome → grant the domains below, then they'll flow normally through greenhouse-agent.

| Company | Domain needed | Notes |
| --- | --- | --- |
| Samsara | samsara.com | Strong backend match |
| Toast | toasttab.com | Strong backend match |

## Assessment-Gated Companies (Action Needed — human)

| Company | Gate | Action |
| --- | --- | --- |
| HackerRank | Pre-application assessment | Report in Action Needed; human completes assessment, then re-queue |
| Razorpay | Pre-application assessment | Report in Action Needed; human completes assessment, then re-queue |

## Cross-Platform Patterns

| Pattern | Platform | Action |
| --- | --- | --- |
| G-P (GlobalPay) | LinkedIn Easy Apply | Greenhouse modal embedded inside LinkedIn — extract boards.greenhouse.io URL; apply via greenhouse skill |

## Budget Efficiency Retrospective (2026-05-29)

| Agent | Tool calls used | Applies delivered | Calls/apply | Root cause of waste |
| --- | ---: | ---: | --- | --- |
| Naukri | ~40 | 3 | 13.3x (should be ~3x) | Keyword "Java developer" — low yield; ~65% external redirects wasted scan budget |
| Instahyre | 12 | 0 | N/A | Queue empty — correctly detected and stopped. Efficient. |
| LinkedIn | 47 | 0 | N/A (0 applies) | Single stuck job (Greenhouse modal trap) consumed entire budget |
| Greenhouse | 30 | 0 | N/A (0 applies) | Re-discovered same blockers as prior run; 3 tool calls per already-known blocker |

Target efficiency:
- Naukri: < 6 tool calls per successful apply (NopeRi is API-driven; most cost is scan, not submit)
- Instahyre: ~2 tool calls per apply when queue is active
- LinkedIn: 8-10 tool calls per Easy Apply (it is genuinely expensive; keep cap at 3 applies max)
- Greenhouse: < 5 total calls if all queued jobs are known-blocked

## Run Learnings

- 2026-05-29 (retrospective): LinkedIn 47-call budget trap. G-P Staff AI Fullstack embedded a Greenhouse modal inside LinkedIn Easy Apply. Agent failed to detect the pattern and spent entire LinkedIn budget on 1 job. Fix: score all cards first, detect Greenhouse-inside-LinkedIn immediately, skip and save. See linkedin.md for detection signals.
- 2026-05-29 (retrospective): Greenhouse 30-call re-discovery waste. All 10 queued jobs were blocked for reasons already known from 2026-05-28. Known-blocker table now in greenhouse.md. Next run should handle all 10 in < 5 tool calls total.
- 2026-05-29 (retrospective): LaunchDarkly 8+ yr minimum escaped scoring. Scoring rule patched in greenhouse.md: extract hard experience minimum from JD; if > 5 years, score < 4, do not queue.
- 2026-05-29 (retrospective): Naukri keyword "Java developer" is low-quality — walk-in events, LAMP stacks, mass-hiring portals. Only 3 applies from 43 scans. Switch to "Java backend", "Spring Boot", "backend engineer" for next run.
- 2026-05-29 (retrospective): Sandhata dupe was caught by db_batch_insert but agent still attempted it (wasted 1 slot and some tool calls). Fix: re-read db.py list right before building NopeRi submission batch, not just at plan time.
- 2026-05-29 (run 2): Naukri produced 3 new apps (TCS walk-in, Persistent Appworks, Nustar walk-in) via keyword "Java developer". Sandhata was a dupe (already applied same company+role+platform). DB now has 50 Naukri apps total, 75 overall. Walk-in roles score 4 but are lower-value targets.
- 2026-05-29 (run 2): db_batch_insert.py dupe-check works correctly — Sandhata silently skipped. Always compare inserted vs attempted counts.
- 2026-05-29 (run 2): LinkedIn G-P Staff AI Fullstack (score 5) had a Greenhouse form embedded inside the LinkedIn Easy Apply modal. This is a recurring pattern — extract the Greenhouse board token and apply directly via the greenhouse skill instead.
- 2026-05-29 (run 2): Greenhouse 10 queued jobs all blocked for a third consecutive run (permissions + hard minimums).
- 2026-05-29 (run 2): Gmail scan found 3 emails but all pre-dated the last scan window. No new status signals.
- 2026-05-29: Naukri direct-apply has partially dried up — ~65% redirecting to external ATS. Pipeline has 122 saved Naukri redirect URLs.
- 2026-05-29: LinkedIn Easy Apply volume is extremely low with broad keywords. Must use narrower, startup-skewed keyword phrases.
- 2026-05-29: Greenhouse board scan not due (next eligible 2026-06-04). 10 high-score jobs queued but all blocked.
- 2026-05-28: Plugin memory initialized. Next run should replace placeholder platform health with measured outcomes.
- 2026-05-28 (run 2): ALL THREE platforms blocked by session limit before apply stage. Run was scheduled too early. Must run after 7pm IST.
- 2026-05-28: `db_batch_insert.py --log-run` does NOT support `--naukri` flag. Log Naukri applied count in `--summary` text only.
- 2026-05-28: LinkedIn first-attempt failure pattern: Cloudflare 522 timeout before session-limit hit. Retry works but session was already expired. Run timing is the root fix.
- 2026-05-28: Goldman Sachs has an incomplete application in-flight. Human must decide whether to complete it.
- 2026-05-28: EPAM sent a "Confirm your application" email — this requires a human email click; agent cannot action it.
- 2026-05-28: Resume strategy: all three archetypes (general-backend/base.pdf, distributed-data/backend-systems.pdf, ai-backend/ai-backend.pdf) were REUSE. 0 tuning needed.
- 2026-05-28 (run 3 — session reset): Session limit confirmed cleared. Previous run applied 24 Instahyre jobs successfully before the limit hit (all logged in DB).
- 2026-05-28: Quota burn root cause was parallel APPLY agent fan-out plus long CEO/profile/log calls. Future runs must use a sequential controller with per-agent budgets.
- 2026-05-28 (run 4 — final log): Naukri 1 applied (IDESLABS). Instahyre 25 apps total. LinkedIn 0 applied. Greenhouse 0 applied.
- 2026-05-28: Naukri questionnaire 406 block pattern: Synaptein, Hour Consulting, NeoSOFT triggered questionnaire blocks. Skip and do not retry.
- 2026-05-28: Greenhouse board token 404s: grammarly, notion, plaid, ramp, rippling, segment. Mark inactive.
- 2026-05-28: LinkedIn "Top Applicant" signal on Peak XV Senior Full-Stack Engineer (job ID 4419048709).
- 2026-05-28: Narendra K. (Honeywell, LinkedIn) sent outreach — human should decide whether to reply.

## Action Items Backlog (requires human)

- Goldman Sachs: incomplete application "Software Engineering - Data, Lakehouse and AI Data Platform Engineer" — decide to complete or abandon.
- EPAM India: "Confirm your application" email — click required, agent cannot action.
- Amazon recruiter Jiani Ji: reply pending after resume sent May 13 — consider follow-up.
- Amazon recruiter Manikanta Bellapu: reply pending after resume sent May 13 — consider follow-up.
- Singapore recruiter Adam Modelski (Legacy Resourcing): reply pending after resume sent May 20 — consider follow-up.
- LinkedIn Narendra K. (Honeywell) outreach: sent Wed 7:25 AM — decide whether to reply.
- Greenhouse browser permissions: grant permissions for boards.greenhouse.io, hackerrank.com, razorpay.com, samsara.com, toast.com to enable autonomous apply next run. (Stripe: do NOT grant — permanent skip.)
- Peak XV Senior Full-Stack Engineer (LinkedIn job 4419048709): Top Applicant signal — check if Easy Apply is still open and prioritize.
- Oracle "Continue to apply" email (GSRecruiting@oracle.com): decide to complete or ignore.
- G-P Staff AI Fullstack: extract Greenhouse board URL from LinkedIn job and apply directly via greenhouse skill (score 5 — high priority).
- Clean Greenhouse pipeline queue: remove LaunchDarkly (hard score fail), mark HackerRank/Razorpay/Samsara/Toast as human-required, confirm Stripe is not in queue.

## Status Updates Needed in DB

- EPAM India — Sr Java Software Developer — Rejected (gmail: "Unfortunately...")
- foodpanda — Backend Software Engineer II — Rejected (gmail: "after careful consideration...")

## Next Run Checklist

- [ ] CRITICAL: Grant browser permissions for boards.greenhouse.io, samsara.com, toasttab.com — these unlock Samsara and Toast queued jobs (strong matches). HackerRank/Razorpay require human assessment first. LaunchDarkly: remove from queue (hard min). Stripe: do NOT grant — permanent CEO skip.
- [ ] PIPELINE: data/pipeline.md has 54+ Pending entries from 2026-04-12 (Perplexity, Palantir, Replit, Cohere, Notion, Reddit, etc.). Run STAGE 4 pipeline processing — CEO pipeline mode will score/route these to greenhouse-agent and generic-apply-agent. High value, previously ignored.
- [ ] Set NAUKRI_USERNAME and NAUKRI_PASSWORD in .env before run — NopeRi adapter needs credentials.
- [ ] Switch Naukri keywords from "Java developer" to: "Java backend", "Spring Boot", "backend engineer", "platform engineer", "Node.js backend" (in this order). Stop using "Java developer".
- [ ] Naukri agent: re-read `python3 scripts/db.py list` immediately before building the NopeRi submission batch (not just at plan time). Prevents dupe attempts.
- [ ] LinkedIn: pre-score ALL visible cards from search results page before opening any individual card. Build ordered apply list first, then open from top.
- [ ] LinkedIn: detect Greenhouse-inside-LinkedIn before spending tool calls. Save detected jobs to pipeline with Greenhouse URL, move to next card. Max 5 tool calls per detection+save.
- [ ] LinkedIn: switch keywords to "Backend Developer India", "Java Spring Boot developer India", "SDE2 India", "Node.js developer India". Avoid broad "Java backend" (400+ results, ~1% Easy Apply rate).
- [ ] Greenhouse: check known-blocker table in greenhouse.md BEFORE opening browser. If all queued jobs are in known-blocker list, report in < 5 tool calls and stop.
- [ ] Greenhouse: clean pipeline queue before run — remove LaunchDarkly, mark assessment/restricted companies as human-required.
- [ ] Run AFTER 7pm IST — session limits reset at 7pm IST on all platforms.
- [ ] Run order: Naukri first through NopeRi only (quota 15), Instahyre second (check queue in < 5 calls; skip if empty), LinkedIn third (Easy Apply only, cap 3-5, per-job cap 10 tool calls), Greenhouse fourth (board scan due 2026-06-04; otherwise known-blocker check + queued jobs if permissions confirmed).
- [ ] Refresh dup list from DB before each platform: `python3 scripts/db.py list`.
- [ ] Do NOT use `--naukri` flag in db_batch_insert.py — it does not exist.
- [ ] Remove or mark inactive Greenhouse boards: grammarly, notion, plaid, ramp, rippling, segment (all returned 404).
- [ ] Flush Naukri apps with `scripts/db_batch_insert.py --apps` after every 3-4 successful applications.
- [ ] LinkedIn: use coordinate-click (not JS click) for Easy Apply modal. Budget ~6-8 tool calls per Easy Apply job.
- [ ] Greenhouse board scan next eligible: 2026-06-04 — do not trigger scan before that date.
- [ ] Instahyre: check matching=true&status=0 first; if empty, confirm in log and skip. Do not attempt Interested queue.
