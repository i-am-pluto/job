---
name: nightly-job-apply
description: Run the user's autonomous nightly job-application workflow. Claude orchestrates all agent dispatch directly.
---

You are the orchestrator for the nightly job-application run. This is authorized for autonomous submission under `nightly-job-apply` mode in `CLAUDE.md`. Follow each stage in order. Do not serialize work that can run in parallel.

Working directory: `/Users/parikshit/Documents/code/job`

**Model dispatch policy:** Platform agents (naukri, instahyre, linkedin, greenhouse, generic-apply, networking) are mechanical executors — dispatch them with `model="haiku"`. job-ceo does planning/judgment — dispatch with `model="sonnet"`.

---

## STAGE 0 — PREP

Invoke `job-ceo` as a **foreground agent** (mode: `plan`). It reads context and returns the run plan. Wait for result.

```
Agent(
  subagent_type="job-search:job-ceo",
  model="sonnet",
  prompt="Mode: plan. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Read CLAUDE.md, profile.md, resumes/cache-index.json, data/memory/ceo.md, data/memory/networking.md, config/greenhouse_boards.yml, run `python3 scripts/db.py list`, and run `python3 scripts/db_networking.py summary`. Return a structured plan block with: quotas (instahyre/naukri/linkedin targets plus greenhouse target 10 and networking outreach budget), resume_archetype_map (signal patterns → PDF paths), dup_list (company+role+platform already applied), networking_goal, scoring_rule summary, and ceo_advice from memory for this run."
)
```

Extract from the result: quotas, resume archetype map, dup list, networking_goal, ceo_advice. You will inject these into later agent prompts.

---

## STAGE 1 — STATUS (incremental Gmail only)

Do not spawn platform status agents during nightly runs. Check Gmail inline only.

Run `python3 scripts/run_state.py gmail-after`, then use browser tools to open Gmail and search:
`subject:(application OR interview OR offer OR rejection OR shortlisted OR regret OR assessment) after:YYYY/MM/DD`

Read subjects/senders only. Do not click links or reply. Skip messages already in `gmail_scan_log` by message ID. Log every processed message with `python3 scripts/db.py log-gmail --message-id "ID" --sender "S" --subject "SUBJ" --action status_updated`, then run `python3 scripts/run_state.py mark last_gmail_status_scan_at`.

---

## STAGE 2 — ACTION

For each clear status signal (interview, rejection, assessment, offer) from any source:
```bash
python3 scripts/db.py update-status --company "X" --role "Y" --platform P --status S --source gmail --notes "..."
```

Collect items requiring human action (recruiter replies, assessments, interview slots, salary questions). Do not reply to emails or click links.

---

## STAGE 3 — SCAN (parallel)

The scan phase covers Instahyre, Naukri through NopeRi, LinkedIn fallback only if budget remains, Greenhouse only when its 7-day board-scan gate is due, and LinkedIn networking outreach. Greenhouse scans use the public Greenhouse API from `config/greenhouse_boards.yml` and do not need a browser during scan.

---

## STAGE 5 — APPLY (sequential)

Run platform agents sequentially in priority order: Naukri, Instahyre, LinkedIn fallback, Greenhouse. Pass quotas, duplicates, CEO advice, and the STAGE 0 resume archetype map. Each platform agent must score all jobs upfront before applying, and must choose resumes per job with `python3 /Users/parikshit/Documents/code/job/scripts/pick_resume.py "<job title + skill tags + JD text>"`. If it returns `REUSE|tag|pdf|score`, use that PDF. If it returns `TUNE|tag|pdf|score`, invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.

```
Agent(subagent_type="job-search:naukri-agent", model="haiku", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <NAUKRI_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:naukri via the Skill tool. Run Naukri through scripts/naukri_noperi_apply.py only: scan, score, apply direct Naukri jobs with score>=4, skip external redirects by default. Do not use browser/Chrome Naukri scan in nightly mode. Pick resumes per job with pick_resume.py; invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Batch all DB writes with db_batch_insert.py during the run. Return: applied list, skipped list, blocked list, resume stats, memory updates for data/memory/naukri.md.")

Agent(subagent_type="job-search:instahyre-agent", model="haiku", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <INSTAHYRE_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:instahyre via the Skill tool. Run full Instahyre workflow: scan matching jobs, score all cards upfront, apply to score>=4 only. Instahyre one-click apply does not upload a resume; for external paths, pick resumes per job with pick_resume.py and invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Use generic-apply-agent for external paths. Batch all DB writes with db_batch_insert.py at end. Return: applied list, skipped list, blocked list, resume stats, memory updates for data/memory/instahyre.md.")

Agent(subagent_type="job-search:linkedin-agent", model="haiku", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: 3-5 fallback Easy Apply applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:linkedin via the Skill tool. Run LinkedIn only if Naukri + Instahyre leave budget. Easy Apply only by default; skip or save external/company-site paths unless explicit external budget is assigned. Pick resumes per job with pick_resume.py; invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Batch all DB writes with db_batch_insert.py during the run. Return: applied list, skipped list, keyword performance, memory updates for data/memory/linkedin.md.")

Agent(subagent_type="job-search:greenhouse-agent", model="haiku", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <GREENHOUSE_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:greenhouse via the Skill tool. Run python3 scripts/run_state.py greenhouse-due first. If due, scan config/greenhouse_boards.yml via Greenhouse API, then mark last_greenhouse_board_scan_at after the scan. If not due, do not scan boards; process queued Greenhouse pipeline jobs only if permissions and budget allow. Pick resumes per job with pick_resume.py; invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Use browser only when the final apply form requires it. Batch all DB writes with db_batch_insert.py during the run. Return exactly: {applied: N, skipped: N, boards_scanned: N, skipped_scan_reason: \"...\", errors: []}.")
```

Wait for all four to complete. Collect all results.

---

## STAGE 5B — NETWORKING OUTREACH

Run LinkedIn networking after the application agents. Networking uses LinkedIn content search and the `networking_outreach` table, not the applications table. It is allowed to send connection requests and follow-up messages in nightly mode within the skill limits.

```
Agent(subagent_type="job-search:networking-agent", model="haiku", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Networking goal: <NETWORKING_GOAL>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:networking via the Skill tool. Run all four phases: SCAN recent LinkedIn hiring posts, CONNECT up to 10 qualified leads only if pending invites are below 80, ACCEPTED_SCAN by diffing sent invites against scripts/db_networking.py list --status invite_sent, and MESSAGE up to 5 accepted contacts with a resume selected by pick_resume.py. Initialize the table with scripts/init_networking_db.py if needed. Respect nightly mode: autonomous sends are allowed within limits, but skip CAPTCHA/password/unknown file-upload blockers. Return: scanned count, invited list, accepted found, messages sent, skipped list, rate-limit state, memory updates for data/memory/networking.md.")
```

Wait for networking-agent to complete. Collect `NETWORKING results: <INSERT_NETWORKING_RESULTS>`, including `Accepted found` and `Messages sent`.

---

## STAGE 6 — LOG

Invoke `job-ceo` as a **foreground agent** (mode: `log`). Pass all collected results. Wait for final report.

```
Agent(
  subagent_type="job-search:job-ceo",
  model="sonnet",
  prompt="Mode: log. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Here are the combined results from the nightly run:

STATUS results: <INSERT_STATUS_RESULTS>
ACTION items: <INSERT_ACTION_ITEMS>
RESUME archetype map: <INSERT_RESUME_ARCHETYPE_MAP>
APPLY results:
  Instahyre: <INSERT_INSTAHYRE_RESULTS>
  Naukri: <INSERT_NAUKRI_RESULTS>
  LinkedIn: <INSERT_LINKEDIN_RESULTS>
  Greenhouse: <INSERT_GREENHOUSE_RESULTS>
NETWORKING results: <INSERT_NETWORKING_RESULTS>

Tasks:
1. Write run log: `python3 scripts/db_batch_insert.py --log-run --instahyre N --linkedin N --greenhouse X --status-updates N --summary 'Naukri: N applied. ...'`
2. Print DB summary: `python3 scripts/db.py summary`
3. Print networking summary: `python3 scripts/db_networking.py summary`
4. Update data/memory/ceo.md with platform health table, durable lessons, networking outreach summary, next-run checklist.
5. Return final report in the format required by CLAUDE.md, including `Greenhouse: X applied`, `Networking: X invited, Y accepted found, Z messages sent`, Agent performance, and Memory updates sections."
)
```

Print the final report returned by job-ceo.
