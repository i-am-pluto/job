---
name: job-apply-status
description: Ask the job CEO agent for a current job-search status report, platform success percentages, blockers, and advice.
---

Invoke `job-ceo` to produce a status-only report.

Required behavior:

1. Read `AGENTS.md`, `profile.md`, `data/pipeline.md`, `data/memory/ceo.md`, `resumes/cache-index.json`, and available run/application summaries.
2. Do not submit applications.
3. Do not modify resumes.
4. Do not evaluate or change DB implementation details.
5. Report:
   - total applications if available
   - recent platform activity
   - action-needed items
   - pipeline blockers
   - resume reuse/tuning signals
   - platform success percentages where enough data exists
   - CEO advice for each agent
