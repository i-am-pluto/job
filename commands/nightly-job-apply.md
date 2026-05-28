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
  prompt="Mode: plan. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Read CLAUDE.md, profile.md, resumes/cache-index.json, data/memory/ceo.md, and run `python3 scripts/db.py list`. Return a structured plan block with: quotas (instahyre/naukri/linkedin targets), resume_archetype_map (signal patterns → PDF paths), dup_list (company+role+platform already applied), scoring_rule summary, and ceo_advice from memory for this run."
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

## STAGE 3 — RESUME

Invoke `profile-agent` as a **foreground agent**. Wait for result before APPLY.

```
Agent(
  subagent_type="job-search:profile-agent",
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Review active job patterns from data/memory/ceo.md and profile.md. Determine resume strategy for today's run (which archetypes to reuse, whether tuning is justified for any patterns). Invoke skill job-search:resume-tuner via the Skill tool if tuning is needed. Return: resume decisions (REUSE/TUNE per pattern with PDF path), tuning budget used, CEO advice for the apply phase."
)
```

Extract resume decisions. Combine with STAGE 0 resume archetype map. Inject into STAGE 4 prompts.

---

## STAGE 4 — APPLY (parallel)

In **one message**, spawn all three platform agents in the background simultaneously. Pass resume decisions and quotas from STAGE 0/3.

```
Agent(subagent_type="job-search:naukri-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <NAUKRI_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume strategy: <INSERT_RESUME_DECISIONS>. Invoke skill job-search:naukri via the Skill tool. Run full Naukri workflow: profile boost, scan, score all cards upfront, apply to score>=4 only. Use generic-apply-agent for external ATS redirects. Batch all DB writes with db_batch_insert.py at end. Return: applied list, skipped list, blocked list, resume stats, memory updates for data/memory/naukri.md.")

Agent(subagent_type="job-search:instahyre-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <INSTAHYRE_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume strategy: <INSERT_RESUME_DECISIONS>. Invoke skill job-search:instahyre via the Skill tool. Run full Instahyre workflow: scan matching jobs, score all cards upfront, apply to score>=4 only. Use generic-apply-agent for external paths. Batch all DB writes with db_batch_insert.py at end. Return: applied list, skipped list, blocked list, resume stats, memory updates for data/memory/instahyre.md.")

Agent(subagent_type="job-search:linkedin-agent", run_in_background=True,
  prompt="Mode: nightly-job-apply. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Quota: <LINKEDIN_QUOTA> applications. Already applied (skip these): <DUP_LIST>. Resume strategy: <INSERT_RESUME_DECISIONS>. Invoke skill job-search:linkedin via the Skill tool. Run full LinkedIn workflow: keyword scan, score all cards upfront, apply to score>=4 only (external-first, Easy Apply fallback). Use generic-apply-agent for external paths. Save blocked/CAPTCHA URLs to data/pipeline.md. Batch all DB writes with db_batch_insert.py at end. Return: applied list (Easy Apply + external), pipeline saved, skipped list, keyword performance, memory updates for data/memory/linkedin.md.")
```

Wait for all three to complete. Collect all results.

---

## STAGE 5 — LOG

Invoke `job-ceo` as a **foreground agent** (mode: `log`). Pass all collected results. Wait for final report.

```
Agent(
  subagent_type="job-search:job-ceo",
  prompt="Mode: log. Working dir: /Users/parikshit/Documents/code/job. Date: <TODAY>. Here are the combined results from the nightly run:

STATUS results: <INSERT_STATUS_RESULTS>
ACTION items: <INSERT_ACTION_ITEMS>
RESUME decisions: <INSERT_RESUME_DECISIONS>
APPLY results:
  Instahyre: <INSERT_INSTAHYRE_RESULTS>
  Naukri: <INSERT_NAUKRI_RESULTS>
  LinkedIn: <INSERT_LINKEDIN_RESULTS>

Tasks:
1. Write run log: `python3 scripts/db_batch_insert.py --log-run --instahyre N --linkedin N --naukri N --status-updates N --summary '...'`
2. Print DB summary: `python3 scripts/db.py summary`
3. Update data/memory/ceo.md with platform health table, durable lessons, next-run checklist.
4. Return final report in the format required by CLAUDE.md, including Agent performance and Memory updates sections."
)
```

Print the final report returned by job-ceo.
