# LinkedIn Networking Memory

Durable notes for LinkedIn networking outreach: keyword quality, rate-limit behavior, company blocklists, profile UI changes, and follow-up message blockers.

## Rate-Limit State

| Date | Pending invites | Gate threshold | Action |
| --- | --- | --- | --- |
| 2026-05-30 | 83 | < 80 | Gate triggered — 0 invites sent. Wait for accepts/withdrawals. |

## Gate Rule

Do not send any connection requests when pending invite count >= 80. Check count at run start using `python3 scripts/db_networking.py summary` and LinkedIn pending invites count before attempting any outreach.

## Outreach Summary

- Total invites sent to date: 0 (via automated agent)
- Accepted contacts found: 0
- Messages sent: 0
- Last run: 2026-05-30 — gate blocked (83 pending > 80 threshold)

## Next Run

Check pending invite count before any outreach. If still >= 80, skip networking stage entirely. Do not attempt workarounds. Log gate state in run report.
