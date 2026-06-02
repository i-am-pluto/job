---
name: greenhouse
description: This skill should be used when discovering Greenhouse board jobs from public board tokens and applying through Greenhouse job URLs by handing off to generic-apply.
version: 1.0.0
---

# Greenhouse Job Application Skill

Discover backend/SDE jobs from public Greenhouse board APIs via `scripts/greenhouse_apply.py` (zero-browser adapter). Score, dedupe, and prepare all answers autonomously. Submit is gated — the adapter queues qualifying jobs for `generic-apply` browser fallback until the A0 spike confirms the API submit endpoint.

**Trigger:** "apply on Greenhouse", "scan Greenhouse", "greenhouse run", a Greenhouse board token, or LinkedIn/Naukri external links pointing to Greenhouse.
**Target:** 10 submitted applications per nightly run.
**Mode:** Interactive -> stop before submit and confirm through `generic-apply`. Nightly (`nightly-job-apply`) -> run adapter first; if submit is gated, append to pipeline and report.

## Adapter (primary path)

Use `scripts/greenhouse_apply.py` for discovery, scoring, dedupe, resume selection, and answer preparation. No browser needed for these steps:

```bash
# Dry-run: see scored + deduped jobs without any writes
python3 scripts/greenhouse_apply.py --dry-run --limit 10

# Prepare only (score + dedupe + resume, no submit, no pipeline append)
python3 scripts/greenhouse_apply.py --no-apply --limit 10

# Full prepare + queue for generic-apply browser fallback
python3 scripts/greenhouse_apply.py --queue --limit 10
```

The adapter:
- Loads board tokens from `config/greenhouse_boards.yml`
- Fetches jobs via public GET `boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true`
- Gates engineering titles only (filters out sales, legal, marketing, etc.)
- Reuses the Naukri adapter's scoring rules (backend/fullstack >= 4)
- Dedupes against DB via `scripts/db.py list`
- Picks cached resumes via `scripts/pick_resume.py`
- Maps identity answers from the live questions schema (`?questions=true`)
- When submit endpoint is unconfirmed: appends prepared jobs to `data/pipeline.md` for the browser path

## Submit (gated — A0 spike pending)

The adapter's `submit_via_api()` returns a sentinel until the A0 network-capture spike confirms the real Greenhouse submit contract. Until then, all prepared jobs route through the browser `generic-apply` path.

After A0 confirms the endpoint, edit `scripts/greenhouse_apply.py:submit_via_api()` to implement the multipart POST, then remove the queue fallback.

## Agent Budget

- Discovery budget: 4 `curl` calls per board token (adapter uses HTTP GET internally).
- Scan gate: run `python3 scripts/run_state.py greenhouse-due`. If it prints `skip until YYYY-MM-DD` **and** the orchestrator has explicitly set `greenhouse_scan_gate: skipped`, do not scan. But if the orchestrator overrides the gate (passes `greenhouse_scan_gate: override` or total run applications are below 20), scan all boards anyway and mark `last_greenhouse_board_scan_at` after.
- Apply budget: about 8 browser tool calls per application, delegated to `generic-apply` until API submit is confirmed.
- Stop at 10 successful submitted applications, or earlier if the controller passes a smaller remaining budget.
- If any tool reports `You've hit your session limit`, stop immediately after flushing all unflushed DB rows.
- Do not use a browser for discovery. Use browser only after a job is queued for `generic-apply`.

## Board Sources

When the 7-day scan gate is due, load known boards from:

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

Run the adapter with `--dry-run` first to validate boards. The adapter:
- Reports `404` boards so you can mark them `active: false` in `config/greenhouse_boards.yml`
- Skips transient errors without marking inactive
- Handles board staleness internally (30-day `last_active` gate)

After a full board scan completes, run `python3 scripts/run_state.py mark last_greenhouse_board_scan_at`.

## Apply

When submit is still gated (A0 spike pending), apply through `absolute_url` by invoking skill `job-search:generic-apply` via the Skill tool for each queued pipeline entry.

`generic-apply` handles Greenhouse form fields, uploads, screening questions, login/account walls, submit gating, and screenshots. Do not duplicate or specialize that form logic in this skill.

Abort or save for later only when `generic-apply` reports a blocker: CAPTCHA, unresolved login/account wall, required field not derivable from `profile.md`, closed job, or submit failure.

## DB Write

After the A0 spike confirms API submit, the adapter flushes directly via `scripts/db_batch_insert.py --apps`. Until then, `generic-apply` handles DB writes per its own skill.

Accumulate successful applications in memory. Write all rows once per run:

```bash
python3 scripts/db_batch_insert.py --apps '[
  {"company":"X","role":"Y","platform":"greenhouse","score":4,"location":"L","notes":"Greenhouse API + generic-apply"}
]'
```

Do not write per job. Always flush the accumulated batch before returning, including when budget/session limits stop the run. The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability; never open `data/applications.db` directly or retry individual rows after a SQLite error.

## Run Order

1. Run `python3 scripts/run_state.py greenhouse-due`.
2. If it prints `skip until YYYY-MM-DD` AND no override was passed by the orchestrator, skip board scan and report reason. Otherwise proceed.
3. Read `config/greenhouse_boards.yml`.
4. Merge in any Greenhouse board tokens found from LinkedIn/Naukri external links.
5. Run adapter: `python3 scripts/greenhouse_apply.py --no-apply --limit 10` to score + dedupe + prepare.
6. For each prepared job with `unmapped_required` fields, answer them using profile.md.
7. Apply through `absolute_url` by invoking `generic-apply` (until API submit confirmed).
8. Update board `last_active` for boards with qualifying jobs; mark 404 boards `active: false`; do not delete boards.
9. Run `python3 scripts/run_state.py mark last_greenhouse_board_scan_at` after the board scan.
10. Batch log all successful applications once with `db_batch_insert.py --apps`.

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

### Queued for generic-apply (Z jobs)
| Company | Role | Location | Score | Resume | URL |
|---------|------|----------|-------|--------|-----|
| ...     | ...  | Bengaluru | 4/5 | base.pdf | ... |

### Board updates
| Token | Status | Change |
|-------|--------|--------|
| ...   | active | last_active updated |

### Skipped scans
| Source | Reason |
|--------|--------|
| Greenhouse boards | last scanned YYYY-MM-DD, next eligible YYYY-MM-DD |
```
