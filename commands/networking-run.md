---
name: networking-run
description: Run LinkedIn networking outreach: scan hiring posts, connect, detect accepted invites, and message accepted contacts.
---

Run the LinkedIn networking workflow interactively.

Working directory: `/Users/parikshit/Documents/code/job`

Required behavior:

1. Invoke skill `job-search:networking` via the Skill tool.
2. Run `python3 scripts/init_networking_db.py`.
3. Execute all four phases in order: SCAN, CONNECT, ACCEPTED_SCAN, MESSAGE.
4. Interactive gates are mandatory:
   - Stop before each LinkedIn connection request is sent.
   - Stop before each accepted-contact message is sent.
5. Use `python3 scripts/db_networking.py summary` at the start and end.
6. Respect the sent-invite pending limit. If pending invites are `>= 80`, skip CONNECT but still run ACCEPTED_SCAN and MESSAGE.
7. Use `python3 scripts/pick_resume.py "<role/team/company/post snippet>"` before attaching a resume.
8. Update `data/memory/networking.md` with durable learnings.
9. Return the final report in this format:

```text
Networking run YYYY-MM-DD:
  Scanned: N LinkedIn hiring posts
  Candidates: N qualified
  Invited: N
  Accepted found: N
  Messages sent: N
  Pending invite gate: N pending / skipped or ok

Invited:
  - Name | Title | Company | Profile

Accepted found:
  - Name | Company | Evidence

Messages sent:
  - Name | Company | Resume

Skipped:
  - Name | Reason

Memory updates:
  - data/memory/networking.md: ...
```
