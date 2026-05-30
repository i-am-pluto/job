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
| Instahyre | Queue exhausted 2026-05-30 (FIFTH consecutive run). 25 total apps in DB. Feed has not refreshed in 5 runs. | 0 (queue empty) | Matching feed not refreshing for this account. | Consider disabling Instahyre stage until account shows new cards. Spend < 3 tool calls on check only. |
| Naukri | 15 applied 2026-05-30 via NopeRi (Quantum Phinance, Intellemo, Verdantis, Amazon, Nxtwave, Tekskills x3, Bluescope, Tracxn, ti Steps, Arshil LLC, Oriserve, EY, Nexgensis). 4 skipped. 138 external redirects saved to pipeline. 69 total Naukri apps in DB. | 15 (target met) | 138 external redirect URLs saved to pipeline but not yet applied. Pipeline backlog is primary untapped apply source. | Route pipeline Greenhouse URLs to greenhouse-agent; route other ATS URLs to generic-apply-agent in batches of 3-5. |
| LinkedIn | 0 applied 2026-05-30. Kake application blocked by custom non-interactable dropdown (~40 tool calls consumed). | 0 | Custom dropdown form components blocked Easy Apply. ~40 tool calls wasted. | Pre-check form interactability before spending tool calls. Skip jobs with custom non-standard dropdown immediately. Max 10 tool calls per job hard cap. |
| Greenhouse | 0 applied. Board scan NOT due until 2026-06-05. New entries found via Gmail: Lenskart (Software Developer - Java Backend) and Razorpay (Full Stack Builder). Razorpay is assessment-gated. | 0 (scan not due) | Board scan due 2026-06-05. Razorpay assessment-gated (human action needed). | Board scan on 2026-06-05 will replenish queue. Lenskart and Razorpay added via gmail confirmation emails. |
| Networking | 0 invites sent 2026-05-30. 83 pending invites exceeds 80-invite gate threshold. | 0 (gate blocked) | Pending invite count 83 > 80 threshold gate. | Wait for accepts/withdrawals before next outreach attempt. Check count at run start. |

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

Note: The entire 2026-04-12 pipeline batch (87 entries: 33 Greenhouse, 14 Lever, 18 Ashby+Workable, 22 generic) is now DEAD — confirmed 2026-05-29. Do not reprocess these URLs. Lever entries returned 404 (expired). Greenhouse entries were US-only requiring sponsorship. Generic batch (Samsara, Toast, Palantir, Perplexity, Cohere, Notion, Replit, Onehouse) all US-only or seniority mismatch. Remove all 2026-04-12 entries from pipeline or mark Cleared.

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
| LaunchDarkly | Greenhouse | Hard 8+ year experience minimum — score < 4; confirmed 2026-05-29, remove from queue |
| Samsara | Greenhouse | Seniority mismatch — scored <4 (2026-05-29), remove from queue permanently |
| Toast | Greenhouse | Seniority mismatch — scored <4 (2026-05-29), remove from queue permanently |

## Permission-Gated Companies (high value — worth unlocking)

These are blocked only because browser permissions have not been granted. They should be applied to. User must run `/mcp` → Claude in Chrome → grant the domains below, then they'll flow normally through greenhouse-agent.

| Company | Domain needed | Notes |
| --- | --- | --- |
| ~~Samsara~~ | ~~samsara.com~~ | Removed 2026-05-29 — scored <4, seniority mismatch. Moved to permanent skips. |
| ~~Toast~~ | ~~toasttab.com~~ | Removed 2026-05-29 — scored <4, seniority mismatch. Moved to permanent skips. |

## Assessment-Gated Companies (Action Needed — human)

| Company | Gate | Action |
| --- | --- | --- |
| HackerRank | Pre-application assessment | Report in Action Needed; human completes assessment, then re-queue |
| Razorpay | Pre-application assessment | Report in Action Needed; human completes assessment, then re-queue |

## Cross-Platform Patterns

| Pattern | Platform | Action |
| --- | --- | --- |
| G-P (GlobalPay) | LinkedIn Easy Apply | Greenhouse modal embedded inside LinkedIn — extract boards.greenhouse.io URL; apply via greenhouse skill |

## Budget Efficiency Retrospective (2026-05-30 — second run, user overrides)

| Agent | Tool calls used | Applies delivered | Calls/apply | Root cause of waste |
| --- | ---: | ---: | --- | --- |
| Naukri | 0 | 0 | N/A | User override — skipped |
| Instahyre | 0 | 0 | N/A | User override — skipped |
| LinkedIn | budget exhausted | 0 | N/A (0 applies) | 5 candidates pre-scored (scores 4-5) but no tool calls remaining to submit. Saved to pipeline.md. |
| Greenhouse | < 3 | 0 | N/A | All pipeline URLs were dupes; scan not due until 2026-06-05. |
| Networking | < 3 | 0 | N/A | Gate triggered (83 pending > 80 threshold). |

## Budget Efficiency Retrospective (2026-05-30)

| Agent | Tool calls used | Applies delivered | Calls/apply | Root cause of waste |
| --- | ---: | ---: | --- | --- |
| Naukri | ~45 | 15 | 3x (on target) | Target met. 138 external redirect pipeline saves. Adapter --limit 15 respected. |
| Instahyre | < 3 | 0 | N/A | Queue empty x5 — correctly detected fast. |
| LinkedIn | ~40 | 0 | N/A (0 applies) | Kake custom dropdown not interactable. Entire budget consumed on 1 job. |
| Greenhouse | < 3 | 0 | N/A | Scan not due. Known-blocker check only. |
| Networking | < 3 | 0 | N/A | Gate triggered (83 pending > 80 threshold). |

## Budget Efficiency Retrospective (2026-05-29 pipeline-clear run)

| Agent | Tool calls used | Applies delivered | Calls/apply | Root cause of waste |
| --- | ---: | ---: | --- | --- |
| Naukri | ~N/A | 3 | ~N/A | NopeRi --limit not enforced; adapter reported 48 but only 3 net new. Overshoot on API calls. |
| Instahyre | < 3 | 0 | N/A | Queue empty x4 consecutive — correctly detected fast. |
| LinkedIn | ~12 | 1 | 12 | JoVE Easy Apply success. 11 externals saved. 3 closed jobs (TransUnion, CrowdStrike, Dassault). |
| Greenhouse pipeline | ~15 | 0 | N/A | Entire 2026-04-12 batch dead (87 entries cleared). 2026-05-28 section: assess-gated or low-score. |

## Budget Efficiency Retrospective (2026-05-29 run 3)

| Agent | Tool calls used | Applies delivered | Calls/apply | Root cause of waste |
| --- | ---: | ---: | --- | --- |
| Naukri | ~75 | 1 | 75x (target < 6x) | 65%+ external redirects; 5 dupes caught; questionnaire blocks. 120 jobs saved to pipeline but not applied. |
| Instahyre | < 5 | 0 | N/A | Queue empty — correctly detected and stopped in < 5 tool calls. Efficient. |
| LinkedIn | 12 | 0 | N/A | Budget (12 calls) insufficient for even 1 Easy Apply. Broad keyword; fallback correctly skipped. |
| Greenhouse | < 5 | 0 | N/A | All 15 queued jobs cleared as blocked/stale/low-score using known-blocker table. Efficient. |

Previous retrospective (2026-05-29 earlier runs):

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

- 2026-05-30 (second run, user overrides): Naukri and Instahyre skipped by user override. LinkedIn pre-scored 5 candidates (Acumatica SDE 4, Kake Senior SWE LLM 5, Bright Matrix .Net 4, Jobgether Python 4, TAVIG Digital SWE 4) but exhausted tool budget before submitting any. All 5 saved to pipeline.md. Greenhouse: Lenskart was a dupe (applied 2026-05-29); Razorpay assessment-gated. Networking blocked at 83 pending invites. Total: 0 applies this run. CRISIS threshold not triggered (user intentionally overrode all primary platforms).
- 2026-05-30: Naukri hit target of 15 applies via NopeRi (Quantum Phinance, Intellemo, Verdantis, Amazon, Nxtwave, Tekskills x3, Bluescope, Tracxn, ti Steps, Arshil LLC, Oriserve, EY, Nexgensis). 4 skipped. 138 external redirects saved to pipeline — pipeline backlog continues to grow.
- 2026-05-30: Instahyre empty for FIFTH consecutive run. Evaluate whether to suspend Instahyre stage entirely. Feed is likely not refreshing for this account. Set a human alert.
- 2026-05-30: LinkedIn Kake application blocked ~40 tool calls on a custom dropdown not interactable by MCP tools. Hard rule: if a form element is not interactable after 2 attempts, skip that job immediately. Per-job cap of 10 tool calls must be enforced without exception.
- 2026-05-30: Networking gate triggered at 83 pending invites (threshold 80). No outreach possible. Must wait for withdrawals or accepts before next run.
- 2026-05-30: Gmail scan found Lenskart and Razorpay Greenhouse confirmations — these were added as new DB entries. Razorpay is assessment-gated (Full Stack Builder). Monitor for HackerRank invite.
- 2026-05-30: Qurex Health Backend Developer status updated to Responded (recruiter activity via Naukri). No human action needed — recruiter activity, not a reply requiring response.
- 2026-05-30: Airamatrix and Paypay India showed recruiter activity in Naukri emails but are not in DB (untracked older applications). Ignore — not from our system.
- 2026-05-29 (pipeline-clear run): Entire 2026-04-12 pipeline batch (87 entries) confirmed dead — Lever 404, Greenhouse US-only/sponsorship, Ashby/Workable specialized/niche, generic batch US-only or seniority mismatch. Do NOT reprocess. Mark all 2026-04-12 entries as Cleared.
- 2026-05-29 (pipeline-clear run): NopeRi --limit flag not enforced. Adapter reported 48 but only 3 net new entries in DB. Must audit adapter behavior — add explicit cap check before batch or after batch using DB delta.
- 2026-05-29 (pipeline-clear run): Instahyre empty for FOURTH consecutive run. Skip stage in < 3 tool calls from now on. Feed may not be refreshing for this account.
- 2026-05-29 (pipeline-clear run): LinkedIn JoVE/Software Engineer/Delhi Remote successfully applied via Easy Apply (1 apply). Turing and Precisely still in LinkedIn queue — add to next run.
- 2026-05-29 (pipeline-clear run): Greenhouse 2026-05-28 section: HackerRank and Razorpay are assessment-gated (human must complete assessment before re-queue). Samsara and Toast scored <4 (seniority mismatch) — moved to permanent skips. LaunchDarkly confirmed permanent skip.
- 2026-05-29 (run 3): Naukri yielded only 1 apply from 75+ scanned jobs (Uprise Labs). 120 new external redirect URLs saved to pipeline. Pipeline.md backlog is now the primary untapped apply source — must route to greenhouse-agent and generic-apply-agent in next run's STAGE 4.
- 2026-05-29 (run 3): Instahyre queue empty for third consecutive run. No bug — feed refreshes daily. Confirmed correctly in < 5 tool calls.
- 2026-05-29 (run 3): LinkedIn 12-call budget is too thin for even one Easy Apply. Either allocate at least 15 calls or skip LinkedIn entirely. Broad "Backend Engineer" keyword generates volume but low Easy Apply rate.
- 2026-05-29 (run 3): Greenhouse queue fully cleared — all 15 entries were blocked, low-score, or stale. Board scan due 2026-06-05 will replenish. The Greenhouse stage currently delivers 0 value without browser permissions; unlocking samsara.com and toasttab.com is the single highest-ROI human action available.
- 2026-05-29 (run 3): Gmail scan found 9 emails (8 new), all LinkedIn notifications or job alerts — no status signals (no interview/rejection/offer). Status stage was correct and fast.
- 2026-05-29 (run 3): EPAM India and foodpanda rejection statuses from prior run still not updated in DB (companies not matched). Needs manual DB update or CEO fix.
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
- Greenhouse browser permissions: grant permissions for boards.greenhouse.io before 2026-06-05 board scan. (Stripe: do NOT grant — permanent skip.)
- Peak XV Senior Full-Stack Engineer (LinkedIn job 4419048709): Top Applicant signal — check if Easy Apply is still open and prioritize.
- Oracle "Continue to apply" email (GSRecruiting@oracle.com): decide to complete or ignore.
- G-P Staff AI Fullstack: extract Greenhouse board URL from LinkedIn job and apply directly via greenhouse skill (score 5 — high priority).
- Razorpay Full Stack Builder (Greenhouse, added 2026-05-30): assessment-gated — monitor for HackerRank invite. Complete assessment, then re-queue.
- LinkedIn networking: 83 pending invites currently blocking outreach gate. Consider withdrawing stale invites (sent > 3 weeks ago with no response) to drop below 80 threshold.

## Status Updates Needed in DB

- EPAM India — Sr Java Software Developer — Rejected (gmail: "Unfortunately...")
- foodpanda — Backend Software Engineer II — Rejected (gmail: "after careful consideration...")

## Next Run Checklist

- [ ] CRITICAL: LinkedIn pipeline has 5 pre-scored leads (Acumatica SDE 4, Kake Senior SWE LLM 5, Bright Matrix .Net 4, Jobgether Python 4, TAVIG Digital SWE 4) saved to pipeline.md from 2026-05-30 run. Prioritize these in next LinkedIn session. NOTE: Kake may have custom dropdown — skip immediately if form is not interactable after 2 attempts.
- [ ] CRITICAL: The 2026-04-12 pipeline batch (87 entries) is DEAD. Do not reprocess. Mark all 2026-04-12 entries as Cleared in pipeline.md before adding any new ones.
- [ ] CRITICAL: Instahyre empty x5 consecutive. Consider suspending Instahyre stage entirely until human confirms account shows fresh cards. Check in < 3 tool calls; if empty again, log and skip with no retry.
- [ ] CRITICAL: LinkedIn per-job hard cap of 10 tool calls must be enforced without exception. If any form element is not interactable after 2 attempts, skip that job immediately. Do NOT spend 40 calls on one blocked job.
- [ ] PIPELINE (high priority): data/pipeline.md has 138+ new Naukri redirect entries from today's run plus prior batches. Route Greenhouse-pattern URLs (boards.greenhouse.io) to greenhouse-agent (API score first), other ATS to generic-apply-agent in batches of 3-5.
- [ ] Greenhouse board scan due 2026-06-05 — trigger on that date. Queue may have Lenskart (Software Developer - Java Backend) and Razorpay (Full Stack Builder, assessment-gated). Lenskart: apply directly. Razorpay: human must complete assessment first.
- [ ] Grant browser permissions for boards.greenhouse.io — needed for 2026-06-05 Greenhouse board scan. Stripe: do NOT grant — permanent CEO skip.
- [ ] Networking: check pending invite count before run. Do not attempt outreach if count >= 80. Today was 83 — must drop below 80 before next networking run.
- [ ] Fix DB status for EPAM India and foodpanda: both need Rejected status. Use `python3 scripts/db.py list` to confirm exact strings, then `db.py update-status`.
- [ ] Naukri keywords (in order): "Java backend", "Spring Boot", "backend engineer", "platform engineer", "Node.js backend". Never use "Java developer".
- [ ] Naukri agent: re-read `python3 scripts/db.py list` immediately before building the NopeRi submission batch (not just at plan time). Prevents dupe attempts.
- [ ] LinkedIn: allocate at least 15 tool calls or skip entirely. Use narrow keywords: "Backend Developer India", "SDE2 India", "Java Spring Boot developer India". Pre-score ALL cards before opening any. Use coordinate-click not JS click.
- [ ] LinkedIn: detect Greenhouse-inside-LinkedIn before spending tool calls. Save to pipeline with Greenhouse URL, skip. Max 5 tool calls per detection+save.
- [ ] Run AFTER 7pm IST — session limits reset at 7pm IST on all platforms.
- [ ] Run order: STATUS (Gmail incremental), Naukri first (NopeRi, quota 15), Instahyre second (queue check < 3 calls; skip if empty), PIPELINE stage third (score/route pending entries), LinkedIn fourth (Easy Apply only, cap 3-5, per-job hard cap 10 tool calls; skip if budget < 15 calls), Greenhouse fifth (board scan due 2026-06-05; otherwise known-blocker check only), Networking last (only if pending invites < 80).
- [ ] Refresh dup list from DB before each platform: `python3 scripts/db.py list`.
- [ ] Do NOT use `--naukri` flag in db_batch_insert.py — it does not exist. Log Naukri count in --summary text only.
- [ ] Remove or mark inactive Greenhouse boards: grammarly, notion, plaid, ramp, rippling, segment (all returned 404).
- [ ] Flush Naukri apps with `scripts/db_batch_insert.py --apps` after every 3-4 successful applications.
- [ ] Greenhouse board scan next eligible: 2026-06-05 — do not trigger before that date.
- [ ] Instahyre: check matching=true&status=0 first; if empty, confirm in log in < 3 tool calls and skip. Do not attempt Interested queue. Do not retry or investigate.
- [ ] NopeRi --limit enforcement: verify adapter respects --limit 15. Check DB delta after batch (compare DB total before/after).
