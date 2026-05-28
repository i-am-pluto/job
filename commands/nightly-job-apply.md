---
name: nightly-job-apply
description: Run the user's autonomous nightly job-application workflow. Claude orchestrates all agent dispatch directly.
---

You are the orchestrator for the nightly job-application run. This is authorized for autonomous submission under `nightly-job-apply` mode in `CLAUDE.md`. Follow each stage in order. Do not serialize work that can run in parallel.

Working directory: `/Users/parikshit/Documents/code/job`

---

## STAGE 0 — PREP

Invoke `job-ceo` as a **foreground agent** (mode: `plan`). It reads context and returns the run plan. Wait for result.

```
Agent(
  subagent_type="job-search:job-ceo",
  prompt="Mode: plan. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Read CLAUDE.md, profile.md, resumes/cache-index.json, data/memory/ceo.md, config/greenhouse_boards.yml, and run `python3 scripts/db.py list`. Return a structured plan block with: quotas (instahyre/naukri/linkedin targets plus greenhouse target 10), resume_archetype_map (signal patterns → PDF paths), dup_list (company+role+platform already applied), scoring_rule summary, and ceo_advice from memory for this run."
)
```

Extract from the result: quotas, resume archetype map, dup list, ceo_advice. You will inject these into later agent prompts.

---

## STAGE 1 — STATUS (parallel)

In **one message**, spawn all three platform agents in the background simultaneously. Check Gmail inline while they run.

```
Agent(subagent_type="job-search:instahyre-agent", run_in_background=True,
  prompt="Mode: status-only. Working dir: /Users/parikshit/Documents/code/job. Check the Instahyre Activity tab for any recruiter responses, messages, or status changes on past applications. Do not scan jobs. Do not apply. Return what you find.")

Agent(subagent_type="job-search:naukri-agent", run_in_background=True,
  prompt="Mode: status-only. Working dir: /Users/parikshit/Documents/code/job. Check Naukri for recruiter messages, application status changes, or activity notifications on past applications. Do not scan jobs. Do not apply. Return what you find.")

Agent(subagent_type="job-search:linkedin-agent", run_in_background=True,
  prompt="Mode: status-only. Working dir: /Users/parikshit/Documents/code/job. Check LinkedIn notifications and messages for recruiter replies, interview requests, or application status updates on past applications. Do not scan jobs. Do not apply. Return what you find.")
```

**Gmail (inline while agents run):** Use browser tools to open Gmail and search:
`subject:(application OR interview OR offer OR rejection OR shortlisted OR regret OR assessment) newer_than:7d`

Wait for all three background agents to complete. Collect all four signal sources together.

---

## STAGE 2 — ACTION

For each clear status signal (interview, rejection, assessment, offer) from any source:
```bash
python3 scripts/db.py update-status --company "X" --role "Y" --platform P --status S --source gmail --notes "..."
```

Collect items requiring human action (recruiter replies, assessments, interview slots, salary questions). Do not reply to emails or click links.

---

## STAGE 3 — SCAN (parallel)

The scan phase covers Instahyre, Naukri, LinkedIn, and Greenhouse. Greenhouse scans use the public Greenhouse API from `config/greenhouse_boards.yml` and do not need a browser during scan.

---

## STAGE 5 — APPLY (parallel)

In **one message**, spawn all four platform agents in the background simultaneously. Pass quotas, duplicates, CEO advice, and the STAGE 0 resume archetype map. Each platform agent must score all jobs upfront before applying, and must choose resumes per job with `python3 /Users/parikshit/Documents/code/job/scripts/pick_resume.py "<job title + skill tags + JD text>"`. If it returns `REUSE|tag|pdf|score`, use that PDF. If it returns `TUNE|tag|pdf|score`, invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.

```
Agent(subagent_type="job-search:naukri-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <NAUKRI_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:naukri via the Skill tool. Run full Naukri workflow: profile boost, scan, score all cards upfront, apply to score>=4 only. Pick resumes per job with pick_resume.py; invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Use generic-apply-agent for external ATS redirects. Batch all DB writes with db_batch_insert.py at end. Return: applied list, skipped list, blocked list, resume stats, memory updates for data/memory/naukri.md.")

Agent(subagent_type="job-search:instahyre-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <INSTAHYRE_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:instahyre via the Skill tool. Run full Instahyre workflow: scan matching jobs, score all cards upfront, apply to score>=4 only. Instahyre one-click apply does not upload a resume; for external paths, pick resumes per job with pick_resume.py and invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Use generic-apply-agent for external paths. Batch all DB writes with db_batch_insert.py at end. Return: applied list, skipped list, blocked list, resume stats, memory updates for data/memory/instahyre.md.")

Agent(subagent_type="job-search:linkedin-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <LINKEDIN_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:linkedin via the Skill tool. Run full LinkedIn workflow: keyword scan, score all cards upfront, apply to score>=4 only (external-first, Easy Apply fallback). Pick resumes per job with pick_resume.py; invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Use generic-apply-agent for external paths. Save blocked/CAPTCHA URLs to data/pipeline.md. Batch all DB writes with db_batch_insert.py at end. Return: applied list (Easy Apply + external), pipeline saved, skipped list, keyword performance, memory updates for data/memory/linkedin.md.")

Agent(subagent_type="job-search:greenhouse-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <GREENHOUSE_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume archetype map: <INSERT_RESUME_ARCHETYPE_MAP>. CEO advice: <INSERT_CEO_ADVICE>. Invoke skill job-search:greenhouse via the Skill tool. Run full Greenhouse workflow: scan config/greenhouse_boards.yml via Greenhouse API with no browser needed during scan, score all jobs upfront, apply to score>=4 only. Pick resumes per job with pick_resume.py; invoke job-search:resume-tuner only when pick_resume returns TUNE and tuning is justified/budgeted, otherwise use the returned fallback PDF. Use browser only when the final apply form requires it. Batch all DB writes with db_batch_insert.py at end. Return exactly: {applied: N, skipped: N, boards_scanned: N, errors: []}.")
```

Wait for all four to complete. Collect all results.

---

## STAGE 6 — LOG

Invoke `job-ceo` as a **foreground agent** (mode: `log`). Pass all collected results. Wait for final report.

```
Agent(
  subagent_type="job-search:job-ceo",
  prompt="Mode: log. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Here are the combined results from the nightly run:

STATUS results: <INSERT_STATUS_RESULTS>
ACTION items: <INSERT_ACTION_ITEMS>
RESUME archetype map: <INSERT_RESUME_ARCHETYPE_MAP>
APPLY results:
  Instahyre: <INSERT_INSTAHYRE_RESULTS>
  Naukri: <INSERT_NAUKRI_RESULTS>
  LinkedIn: <INSERT_LINKEDIN_RESULTS>
  Greenhouse: <INSERT_GREENHOUSE_RESULTS>

Tasks:
1. Write run log: `python3 scripts/db_batch_insert.py --log-run --instahyre N --linkedin N --greenhouse X --status-updates N --summary 'Naukri: N applied. ...'`
2. Print DB summary: `python3 scripts/db.py summary`
3. Update data/memory/ceo.md with platform health table, durable lessons, next-run checklist.
4. Return final report in the format required by CLAUDE.md, including `Greenhouse: X applied`, Agent performance, and Memory updates sections."
)
```

Print the final report returned by job-ceo.
