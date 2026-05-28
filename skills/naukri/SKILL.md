---
name: naukri
description: This skill should be used when scanning Naukri jobs, applying directly on Naukri through the NopeRi API adapter, or saving Naukri external company-site redirects.
version: 2.0.0
---

# Naukri Job Application Skill

Apply to backend/SDE jobs on Naukri through the local NopeRi adapter. The adapter wraps `vendor/NopeRi` but keeps this workspace's rules: `profile.md` for answers, `scripts/pick_resume.py` for resume choice, and `scripts/db_batch_insert.py` for tracking.

**Trigger:** "apply on Naukri", "find Naukri jobs", "scan Naukri", "naukri run", or a Naukri jobs/search URL.
**Target:** Up to 15 submitted direct Naukri applications per run.
**Mode:** Interactive -> run `--no-apply` first and ask before live submit. Nightly (`nightly-job-apply`) -> submit autonomously within cap.

## Primary API Workflow

Use the adapter first:

```bash
python3 scripts/naukri_noperi_apply.py --dry-run --limit 15 --pages 1 --job-age 7
```

Interactive live submit, only after user confirmation:

```bash
python3 scripts/naukri_noperi_apply.py --limit 15 --pages 1 --job-age 7
```

Nightly live submit:

```bash
python3 scripts/naukri_noperi_apply.py --limit 15 --pages 1 --job-age 7
```

Environment requirements:

- `NAUKRI_USERNAME` and `NAUKRI_PASSWORD`, or fallback `USERNAME` and `PASSWORD`.
- Dependencies from `vendor/NopeRi/requirements.txt` must be importable.
- Do not put credentials in prompts, skill files, logs, or DB notes.

The adapter must remain the source of truth for Naukri API execution. Do not run `vendor/NopeRi/apply_agent.py`; it uses upstream CSV tracking, hardcoded profile values, and a hardcoded AI scorer that do not match this workspace.

## Rules Preserved By The Adapter

- Check duplicates through `scripts/db.py list`; never use NopeRi's `applied_jobs.csv`.
- Score with workspace policy: backend and fullstack roles score `4`; skip frontend-only, mobile-only, pure QA/DevOps, recruiter/data analyst roles, and hard 5+ year minimum roles.
- Pick resumes with `scripts/pick_resume.py`.
  - `REUSE|tag|pdf|score` means use the returned cached PDF and do not tune.
  - `TUNE|tag|pdf|score` means invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.
- Apply only to direct Naukri jobs through NopeRi `NaukriJobClient.apply_job`.
- Save external company-site jobs to `data/pipeline.md`; use `generic-apply` only if the controller explicitly allocates budget.
- Answer questionnaires only when every required answer can be derived from `profile.md`; otherwise save the job to pipeline.
- Flush successful applications through `scripts/db_batch_insert.py --apps`, every 3-4 applications and at the end.

## Agent Budget

- Naukri is the first-priority APPLY agent.
- Budget: 45 tool calls / 25k tokens max.
- Stop at 15 successful submitted applications.
- If any tool reports `You've hit your session limit`, stop immediately after flushing.
- If API login, `nkparam`, or Naukri API responses fail, stop the adapter path and use the browser fallback only if session budget remains.

## Browser Fallback Only

Use the browser flow only when the API adapter cannot proceed because of login/MFA, token, or API response issues.

Fallback search URLs still need the `-in-india` suffix:

```text
https://www.naukri.com/backend-developer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/software-engineer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/software-development-engineer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/full-stack-developer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/java-developer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/platform-engineer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/distributed-systems-jobs-in-india?experience=0,3&jobAge=7
```

Fallback quirks:

- Use JavaScript/text extraction for scanning; avoid screenshots except for final click coordinates.
- Browser direct apply may require a coordinate click on the Apply button; this is not part of the primary API path.
- Success is usually a full-page redirect to `/myapply/saveApply?...`.
- Save external/CAPTCHA/password-wall jobs to `data/pipeline.md`.

## Output Format

```text
## Naukri Run — YYYY-MM-DD

### Applied (X jobs)
| Company | Role | Location | Score | Type | Notes |
|---------|------|----------|-------|------|-------|
| ...     | ...  | Bengaluru | 4/5 | Direct API | NopeRi adapter |

### Skipped (Y jobs)
| Company | Role | Reason |
|---------|------|--------|
| ...     | ...  | 5+ yrs experience required |

### Saved to pipeline (Z jobs)
| Company | Role | Reason | URL |
|---------|------|--------|-----|
| ...     | ...  | External company-site apply | ... |
```
