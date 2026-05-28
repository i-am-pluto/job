# Greenhouse Memory

Persistent operational memory for Greenhouse-hosted job discovery and application runs.

## Current Rules

- Discover jobs through the public Greenhouse Job Board API before opening a browser.
- Apply only to backend/fullstack roles with score 4 or higher.
- Use `generic-apply` for Greenhouse forms; do not duplicate form-fill logic in the Greenhouse skill.
- Batch successful applications with `scripts/db_batch_insert.py --apps`.
- Log nightly Greenhouse totals with `scripts/db_batch_insert.py --log-run --greenhouse N`.

## Board Registry Notes

- Source of truth: `config/greenhouse_boards.yml`.
- Mark 404 boards as `active: false`.
- Update `last_active` when a board returns qualifying jobs.
- Skip stale boards older than 30 days, but do not delete them.
