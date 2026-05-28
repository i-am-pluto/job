# Job CEO Memory

This is persistent operational memory for the job-search CEO agent. Keep it focused on durable run learnings, not profile facts. Profile facts belong in `profile.md`; resume facts belong in `resumes/*.md`.

## Current Priorities

- Preserve quality threshold: apply only to score 4 or 5 roles.
- Keep platform agents focused on backend/fullstack roles in India or India-compatible remote roles.
- Prefer cached resumes unless a concrete JD justifies tuning.
- Batch DB writes through helper scripts only.

## Platform Health

| Platform | Recent signal | Next adjustment |
| --- | --- | --- |
| Instahyre | Not measured yet after plugin install. | Capture applied/qualified/blocked counts after next run. |
| Naukri | Not measured yet after plugin install. | Capture direct vs external apply success after next run. |
| LinkedIn | Not measured yet after plugin install. | Capture keyword yield and external-vs-Easy-Apply split after next run. |

## Run Learnings

- 2026-05-28: Plugin memory initialized. Next run should replace placeholder platform health with measured outcomes.

## Next Run Checklist

- Read `AGENTS.md`, `CLAUDE.md`, `profile.md`, and this file before dispatching agents.
- Check duplicates through `python3 scripts/db.py list`.
- Flush applications with `scripts/db_batch_insert.py --apps`.
- Append only durable lessons to memory files.
