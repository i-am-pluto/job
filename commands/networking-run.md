---
name: networking-run
description: Run LinkedIn networking outreach interactively.
---

Run the LinkedIn networking workflow interactively.

Working directory: `/Users/parikshit/Documents/code/job`

Single source of truth: invoke skill `job-search:networking` via the Skill tool
and follow it exactly. Do not restate or override the scan, connect,
accepted-scan, message, rate-limit, resume, DB, or memory rules here.

Command-specific requirements:

1. Run `python3 scripts/init_networking_db.py` before the first networking DB read/write.
2. Run `python3 scripts/db_networking.py summary` at the start and end.
3. Interactive gates are mandatory: stop before each LinkedIn connection request
   is sent and before each accepted-contact message is sent.
4. Return the final report using the format from `skills/networking/SKILL.md`.
