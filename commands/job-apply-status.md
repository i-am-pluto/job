---
name: job-apply-status
description: Ask the job CEO agent for an incremental Gmail-only job-search status report, blockers, and advice.
---

Invoke `job-ceo` to produce a status-only report.

Required behavior:

1. Read `profile.md`, `data/pipeline.md`, `data/memory/ceo.md`, `data/run-state.json`, `resumes/cache-index.json`, and available run/application summaries.
2. Do not submit applications.
3. Do not modify resumes.
4. Do not evaluate or change DB implementation details.
5. Status source is incremental Gmail only:
   - Run `python3 scripts/run_state.py gmail-after`.
   - Search Gmail with `subject:(application OR interview OR offer OR rejection OR shortlisted OR regret OR assessment) after:YYYY/MM/DD`.
   - Skip messages already logged in `gmail_scan_log`.
   - Log every processed message with `python3 scripts/db.py log-gmail --message-id "ID" --sender "S" --subject "SUBJ" --action status_updated`.
   - Mark the checkpoint with `python3 scripts/run_state.py mark last_gmail_status_scan_at`.
6. Do not check Instahyre, Naukri, or LinkedIn portal status unless the user explicitly asks for that platform.
7. Report:
   - total applications if available
   - incremental Gmail status findings only
   - action-needed items
   - pipeline blockers
   - resume reuse/tuning signals
   - platform success percentages where enough data exists
   - CEO advice for each agent
