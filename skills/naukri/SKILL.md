---
name: naukri
description: This skill should be used when scanning Naukri jobs, applying directly on Naukri through the NopeRi API adapter, or saving Naukri external company-site redirects.
version: 2.0.0
---

# Naukri Job Application Skill

Apply to backend/SDE jobs on Naukri through the local NopeRi adapter. The adapter wraps `vendor/NopeRi` but keeps this workspace's rules: `profile.md` for answers, `scripts/pick_resume.py` for resume choice, and `scripts/db_batch_insert.py` for tracking. In nightly mode, the adapter is mandatory for scan, analysis, scoring, and apply.

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

The adapter must remain the source of truth for Naukri API execution. Do not run `vendor/NopeRi/apply_agent.py`; it uses upstream CSV tracking, hardcoded profile values, and a hardcoded AI scorer that do not match this workspace. Do not use Chrome/browser scanning for nightly Naukri work.

## Rules Preserved By The Adapter

- Check duplicates through `scripts/db.py list`; never use NopeRi's `applied_jobs.csv`.
- Score with workspace policy: backend and fullstack roles score `4`; skip frontend-only, mobile-only, pure QA/DevOps, recruiter/data analyst roles, and hard 5+ year minimum roles.
- Pick resumes with `scripts/pick_resume.py`.
  - `REUSE|tag|pdf|score` means use the returned cached PDF and do not tune.
  - `TUNE|tag|pdf|score` means invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.
- Apply only to direct Naukri jobs through NopeRi `NaukriJobClient.apply_job`.
- Skip external company-site redirects by default; save them to `data/pipeline.md` only when the controller explicitly passes `--allow-external-pipeline`.
- **Always answer questionnaires autonomously — never skip a job due to an unknown field.** The adapter answers most fields deterministically from `profile.md` + the answer table below. Fields it cannot map are escalated to YOU via the two-phase agent-answer loop (see "Two-Phase Questionnaire Answering"); they are never silently skipped. Complete that loop before declaring the run done.
- Flush successful applications through `scripts/db_batch_insert.py --apps`, every 3-4 applications and at the end.

## Two-Phase Questionnaire Answering

The adapter answers known questionnaire fields itself, then escalates the residue
to the agent. Both phases are mandatory in a full run.

**Phase 1 — deterministic + escalate.** `python3 scripts/naukri_noperi_apply.py`
maps every field it can from `profile.md` and the answer table. Any question it
cannot answer is recorded to `data/naukri_agent_unknowns.json` and the job is held
in "Needs agent answers" (NOT applied, NOT skipped). The run report ends with
`### Needs agent answers (N jobs)`.

**Phase 2 — agent answers + retry.** When that file is non-empty:
1. Read `data/naukri_agent_unknowns.json`. Each entry has `job_id`, `company`,
   `title`, and `questions[]` with `questionName`, `answerOption` (full
   `{key: value}` map), `questionType`, and `answerFormat`.
2. Choose a truthful, reasonable answer per question from `profile.md` / `resumes/base.md`.
   - `answerFormat: "free_text"` → the literal string answer.
   - `answerFormat: "list_of_option_keys"` → the option **key** (or label — the
     adapter normalizes either to the key). Multi-select returns several keys.
3. Write an answers file shaped as a list of
   `{"job_id": "...", "answers": {"<questionId>": <answer>}}`.
4. Re-run with the answers:
   ```bash
   python3 scripts/naukri_noperi_apply.py --retry-unanswered data/naukri_agent_answers.json
   ```
   Retry mode injects your answers for those question IDs and submits.

Only genuinely unanswerable identity-document questions (employee IDs, govt IDs,
financial credentials) may remain deferred — answer "NA"/"No" where truthful.

## Agent Budget

- Naukri is the first-priority APPLY agent.
- Budget: 45 tool calls / 25k tokens max.
- Stop at 15 successful submitted applications.
- If any tool reports `You've hit your session limit`, stop immediately after flushing.
- If API login, `nkparam`, or Naukri API responses fail, stop and report the adapter blocker. Nightly mode must not switch to browser scanning.

## Manual Browser Fallback Only

Use the browser flow only during explicit manual troubleshooting when the API adapter cannot proceed because of login/MFA, token, or API response issues. Never use this path in `nightly-job-apply`.

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

Fallback quirks (verified 2026-05-28):

- Use JavaScript/text extraction for scanning; avoid screenshots except for final click coordinates.
- **Most established companies use "Apply on company site"** — Accenture, Infosys, Home Credit, Comviva, Bahwan CyberTek, TCS all redirect. Only small/mid companies have direct Naukri apply. Expect ~20-30% direct-apply rate.
- **Direct apply detection**: `Array.from(document.querySelectorAll('button,a')).filter(b=>(/^apply/i.test(b.textContent.trim()))&&b.offsetParent!==null).map(b=>b.textContent.trim())` — if result is `["Apply"]` it's direct; if `["Apply on company site"]` save to pipeline.
- **Direct apply flow** (verified): JS `btn.click()` works for the Apply button → redirects to `/myapply/saveApply?...` on success. No coordinate click needed.
- **Chatbot/questionnaire screening**: Always answer. Never close and save to pipeline. Use the answer table below for any field.

## Questionnaire Answer Table

Answer every field — never block on unknown values. Use this table first; fall back to best-guess for anything not listed.

| Field pattern | Answer |
|---|---|
| Current CTC / current salary / current annual salary | 2800000 (or "28" if asking in LPA) |
| Expected CTC / expected salary / desired CTC | 3300000 (or "33" if asking in LPA) |
| Notice period (days) | 60 |
| Notice period (months) | 2 |
| Current location / present location | Bangalore |
| Total experience / overall experience (years) | 2 |
| Years in Java / J2EE / Core Java | 2 |
| Years in Kotlin | 2 |
| Years in Python | 2 |
| Years in Spring Boot / Spring | 2 |
| Years in AWS | 2 |
| Years in Kubernetes / K8s / Docker | 2 |
| Years in Spark / PySpark | 2 |
| Years in Kafka | 2 |
| Years in Node.js / NodeJS | 1 |
| Years in React / ReactJS / React.Js | 1 |
| Years in Angular | 1 |
| Years in DSA / Data Structures | 2 |
| Years in Microservices | 2 |
| Years in REST / REST APIs | 2 |
| Years in Golang / Go | 1 |
| Years in Fullstack / Full Stack Development | 2 |
| Years in Backend Development | 2 |
| Years in .Net / ASP.Net / C# | 0 |
| Years in PHP / Laravel | 0 |
| Years in Ruby / Rails | 0 |
| Years in MLOps | 1 |
| Years in GenAI / LLM / AI | 1 |
| Years in [any other skill not listed] | 1 (safe default) |
| Ex-[company] employee? (Infosys, TCS, etc.) | No / NA |
| Comfortable with contract role? | No |
| Willing to relocate? | Yes |
| Work authorization India? | Yes |
| Immediate joiner? | No (60 days notice) |
| Graduation year | 2024 |
| Highest education | B.Tech Computer Science |
| GPA / CGPA | 8.5 |
| Any open-ended describe/explain question | Write 2–3 sentences using profile skills relevant to the question topic |
- **Success confirmation**: `document.title === 'Apply Confirmation'` and `window.location.pathname === '/myapply/saveApply'`. No screenshot needed.
- Success is usually a full-page redirect to `/myapply/saveApply?...`.
- Skip external/CAPTCHA/password-wall jobs unless explicit pipeline budget was assigned.
- **Skip low-salary listings**: Skip any job with salary listed below 20 LPA (e.g. "8-11 Lacs PA", "7-11 Lacs PA", "2.5-4.75 Lacs PA") to avoid mismatched expectations.

## Status/Notification Handling

Naukri portal status is not part of nightly status checks. If the user explicitly asks for Naukri status, inspect notifications only for actionable recruiter/application signals:

- Actionable: recruiter message, interview, assessment, shortlist/selected, offer, rejection/not moving forward.
- Ignore commercial/incentivized noise: NVites, profile views, appeared in search, application booster/promote/paid-service prompts, generic recruiter activity without a message or application outcome.

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
