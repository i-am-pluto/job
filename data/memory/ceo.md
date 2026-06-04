# Job CEO Memory

Persistent operational memory for the job-search CEO agent. Durable run learnings only — profile facts belong in `profile.md`.

## Current Priorities

- Score threshold: apply only to score 4 or 5 roles.
- Platforms: Naukri (NopeRi adapter), Instahyre (browser), LinkedIn (Easy Apply fallback 3-5), Networking.
- Single resume: `output/base.pdf` for all platforms. Recompile from `resumes/base.tex` when changed.
- Batch DB writes through helper scripts only.
- Run AFTER 7pm IST — session limits reset at that time.
- Sequential APPLY agents only — never parallel.
- Nightly status checks are Gmail-only and incremental from `data/run-state.json`.

## Platform Health

> Last updated: 2026-06-05

| Platform | Status | Applied this run | Blocker | Notes |
| --- | --- | --- | --- | --- |
| Naukri | HEALTHY | 15 | None — run from user's machine. Sandbox HTTP 000 block persists for scheduled runs. | Broad backend keywords working: "Java backend", "Spring Boot", "backend engineer", "full stack developer". |
| Instahyre | SUSPENDED | 0 | 7+ consecutive empty runs — matching feed not refreshing. | Do not allocate budget until user confirms feed has fresh jobs. |
| LinkedIn | ACTIVE | 2 | Form issues + closed roles not pre-filtered. | Keep 3-5 fallback cap. Pre-check job status before attempting. 10-tool-call hard cap per job. |
| Networking | PARTIAL | 0 | linkedin-extension MCP times out — always fall back to claude-in-chrome immediately. | 21 pending invites as of 2026-06-05. Resume for accepted: output/base.pdf. |

## Agent Budgets

| Agent | Budget | Stop rule |
| --- | --- | --- |
| CEO preflight | 6 tool calls | Return quotas and dup list only. |
| Status/Gmail | 6 tool calls | Incremental Gmail only; no portal status checks. |
| Naukri apply | 45 tool calls | Stop at 15 applied or budget. Flush every 3-4 apps. |
| Instahyre apply | 35 tool calls | Skip if matching queue empty (< 5 tool calls to confirm). |
| LinkedIn apply | 12 tool calls | Fallback only; Easy Apply only; cap 3-5. Max 10 tool calls per job. |
| Networking | 30 tool calls | Scan posts → connect → detect accepted → message. |
| Final log | 4 tool calls | Compact summary only. |

## Assessment-Gated Companies (Action Needed — human)

| Company | Gate | Action |
| --- | --- | --- |
| BiztechAnalytics | "Project Terminus" assessment | Complete manually — URGENT |
| Turing | Python/FastAPI assessment | Complete on desktop |
| Razorpay | Pre-application assessment | Complete, then re-queue |

## Run Learnings

- 2026-06-05: 17 applies (15 Naukri + 2 LinkedIn). Naukri NopeRi healthy from user's machine (sandbox HTTP 000 is the only blocker). LinkedIn: Curefit SDE3 + JioHotstar SDE2 applied; Crossing Hurdles form issues after 2 attempts, Pro5.ai closed. Networking: linkedin-extension MCP timeout — fallback not executed; fix: fire claude-in-chrome fallback on first MCP timeout. Status: Amazon SDE II Alexa → Rejected. myKaarma hiring paused (not in DB). Total DB: 241.
- 2026-06-03: Naukri 30 applied (exceeded quota via two-phase run). LinkedIn SDUI gate lifted as of 2026-06-03; Easy Apply operational. Networking: 11 invites sent (claude-in-chrome reliable; linkedin-extension times out on searchPosts/connect).
- 2026-06-02: Naukri 0 (NopeRi HTTPCloakError). LinkedIn 5 from earlier session. Networking blocked (browser unavailable in scheduled run — pre-open Chrome tab before run starts).
- 2026-05-30: Instahyre empty 6+ consecutive runs — formally suspended. LinkedIn Kake custom dropdown consumed entire budget (40 calls, 0 applies). Hard 10-call cap per job enforced from next run.
- 2026-05-29: Naukri "Java developer" keyword low-yield (65% external redirects). Switch to "Java backend", "Spring Boot", "backend engineer" — confirmed higher yield.
- 2026-05-28: `db_batch_insert.py --log-run` does NOT support `--naukri` flag. Log Naukri count in `--summary` text only.
- 2026-05-28: Run timing: ALL platforms blocked by session limit when run before 7pm IST. Always run after 7pm IST.

## Action Items Backlog (requires human)

- BiztechAnalytics "Project Terminus": assessment — URGENT
- Turing Python/FastAPI BE Developer: complete assessment on desktop
- Amazon Alexa Connect Kit (ID 3201122): "incomplete" warning — check Amazon Jobs dashboard
- Goldman Sachs: incomplete application — decide to complete or abandon
- EPAM India: "Confirm your application" email — click required
- Naukri 4 status notifications (2026-06-05): check Naukri portal for company details
- Dhanraj G (Quickhyre CTO): LinkedIn slug `dhanraj-g` resolves to IBM consultant — find correct URL

## Next Run Checklist

- [ ] Naukri: run from user's machine. Quota 15. Keywords: "Java backend", "Spring Boot", "backend engineer", "full stack developer", "SDE", "platform engineering". Flush every 3-4 apps.
- [ ] Instahyre: SUSPENDED — skip entirely. No budget allocation.
- [ ] LinkedIn: 3-5 Easy Apply fallback. Skip job after 2 failed fills. Skip closed roles before attempting. 10-call hard cap per job.
- [ ] Networking: on linkedin-extension timeout, immediately fall back to claude-in-chrome. Monitor ~21 pending invites. Message accepted with output/base.pdf. Muskan Singh cooldown until 2026-07-02.
- [ ] Run AFTER 7pm IST.
- [ ] Refresh dup list from DB before each platform: `python3 scripts/db.py list`.
- [ ] Do NOT use `--naukri` flag in db_batch_insert.py.
- [ ] Flush Naukri apps every 3-4 successful applications.
