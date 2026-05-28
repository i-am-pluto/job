---
name: greenhouse
description: This skill should be used when discovering Greenhouse board jobs from public board tokens and applying through Greenhouse job URLs by handing off to generic-apply.
version: 1.0.0
---

# Greenhouse Job Application Skill

Discover backend/SDE jobs from public Greenhouse board APIs, score them before opening a browser, then apply by handing the job URL to skill `job-search:generic-apply`. This skill owns discovery, scoring, dedupe, resume choice, and run tracking only. Do not add Greenhouse form-filling logic here.

**Trigger:** "apply on Greenhouse", "scan Greenhouse", "greenhouse run", a Greenhouse board token, or LinkedIn/Naukri external links pointing to Greenhouse.
**Target:** 10 submitted applications per nightly run.
**Mode:** Interactive -> stop before submit and confirm through `generic-apply`. Nightly (`nightly-job-apply`) -> submit autonomously within cap.

## Agent Budget

- Discovery budget: 4 `curl` calls per board token.
- Apply budget: about 8 browser tool calls per application, delegated to `generic-apply`.
- Stop at 10 successful submitted applications, or earlier if the controller passes a smaller remaining budget.
- If any tool reports `You've hit your session limit`, stop immediately after flushing all unflushed DB rows.
- Do not use a browser for discovery. Use browser only after a job is selected for application.

## Board Sources

Load known boards from:

```bash
config/greenhouse_boards.yml
```

Also accept board tokens dynamically discovered from LinkedIn/Naukri external links. Extract tokens from Greenhouse URLs such as:

```text
https://boards.greenhouse.io/{token}/jobs/{id}
https://job-boards.greenhouse.io/{token}/jobs/{id}
https://boards-api.greenhouse.io/v1/boards/{token}/jobs
```

Normalize tokens to lowercase where the source is lowercase; preserve exact token spelling when a fetched URL only works with that spelling.

## Self-Update Behavior

Validate every board token before scanning:

```bash
curl "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
```

- `200`: board is active; parse returned jobs.
- `404`: mark the board `active: false` in `config/greenhouse_boards.yml`.
- Other transient errors: skip for this run and note the status; do not mark inactive.
- If a board has qualifying jobs, update its `last_active` date.
- Skip boards whose `last_active` is older than 30 days unless the token was newly discovered in this run.
- Do not delete stale or inactive boards.
- For dynamically discovered tokens, add or update the board entry only after the token validates with `200`.

## Primary API Workflow

For each active board token, discover jobs with public GET only:

```bash
curl "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
```

No browser. No auth. No cookies.

Parse each job:

| Field | Source |
|---|---|
| Greenhouse job id | `id` |
| Role title | `title` |
| Location | `location.name` |
| JD content | `content` |
| Apply URL | `absolute_url` |

Treat the board token as the company identifier when no better company name exists in `config/greenhouse_boards.yml`.

## Upfront Scoring

Score from title plus JD content before opening any browser page.

Use the same profile scoring rules as Naukri/LinkedIn:

- Backend and fullstack roles score `4` or higher.
- Skip frontend-only roles.
- Skip mobile-only roles.
- Skip pure DevOps/SRE/platform operations roles unless the JD is clearly backend product engineering.
- Skip hard 5+ year minimum roles.
- Skip roles that are closed, no longer accepting applications, internships, pure QA, recruiter, data analyst, or non-engineering.
- Apply only when score is `>= 4`.

For every qualifying job, extract:

- Role title: normalized from `title`.
- Top 3 JD keywords: concrete backend/infra/product keywords from `content`, such as `Java`, `Python`, `Go`, `distributed systems`, `Kafka`, `PostgreSQL`, `AWS`, `microservices`, `LLM`, `Spring Boot`.

## Dedupe

Before applying, check existing applications:

```bash
python3 scripts/db.py list
```

Skip a job if the existing rows contain the same `(company, role, greenhouse)` combination. Use the board company name or token for `company`, the normalized title for `role`, and `greenhouse` for platform.

## Resume Selection

Pick the resume once per selected job:

```bash
python3 scripts/pick_resume.py "<title + JD keywords>"
```

- `REUSE|tag|pdf|score` means use the returned cached PDF and do not tune.
- `TUNE|tag|pdf|score` means invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.

## Apply

Navigate the browser to the job's `absolute_url`, then invoke skill `job-search:generic-apply` via the Skill tool.

`generic-apply` handles Greenhouse form fields, uploads, screening questions, login/account walls, submit gating, and screenshots. Do not duplicate or specialize that form logic in this skill.

Abort or save for later only when `generic-apply` reports a blocker: CAPTCHA, unresolved login/account wall, required field not derivable from `profile.md`, closed job, or submit failure.

## DB Write

Accumulate successful applications in memory. Write all rows once per run:

```bash
python3 scripts/db_batch_insert.py --apps '[
  {"company":"X","role":"Y","platform":"greenhouse","score":4,"location":"L","notes":"Greenhouse API + generic-apply"}
]'
```

Do not write per job. Always flush the accumulated batch before returning, including when budget/session limits stop the run. The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability; never open `data/applications.db` directly or retry individual rows after a SQLite error.

## Run Order

1. Read `config/greenhouse_boards.yml`.
2. Merge in any Greenhouse board tokens found from LinkedIn/Naukri external links.
3. Validate active or newly discovered tokens with public `curl`.
4. Skip boards stale for more than 30 days unless newly discovered.
5. Fetch jobs with `content=true`, respecting 4 `curl` calls per board.
6. Parse jobs and score upfront.
7. Extract title plus top 3 JD keywords for each score `>= 4` job.
8. Dedupe with `python3 scripts/db.py list`.
9. Pick resume with `python3 scripts/pick_resume.py`.
10. Apply through `absolute_url` by invoking `generic-apply`.
11. Update board `last_active` for boards with qualifying jobs; mark 404 boards `active: false`; do not delete boards.
12. Batch log all successful applications once with `db_batch_insert.py --apps`.

## Output Format

```text
## Greenhouse Run - YYYY-MM-DD

### Applied (X jobs)
| Company | Role | Location | Score | Resume | Notes |
|---------|------|----------|-------|--------|-------|
| ...     | ...  | Bengaluru | 4/5 | base.pdf | Greenhouse API + generic-apply |

### Skipped (Y jobs)
| Company | Role | Reason |
|---------|------|--------|
| ...     | ...  | 5+ yrs experience required |

### Board updates
| Token | Status | Change |
|-------|--------|--------|
| ...   | active | last_active updated |
```
