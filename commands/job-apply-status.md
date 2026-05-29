---
name: job-apply-status
description: Ask the job CEO agent for an incremental Gmail-only job-search status report, blockers, and advice.
---

Invoke `job-ceo` to produce a status-only report.

Single source of truth: `CLAUDE.md` owns status handling. Follow its
Gmail-only incremental status rules and do not duplicate them here.

Command-specific requirements:

1. Do not submit applications.
2. Do not modify resumes.
3. Do not evaluate or change DB implementation details.
4. Do not check Instahyre, Naukri, LinkedIn, or other portal status unless the
   user explicitly asks for that platform.
5. Report total applications if available, incremental Gmail findings,
   action-needed items, pipeline blockers, resume reuse/tuning signals,
   platform success percentages where enough data exists, and CEO advice for
   each agent.
