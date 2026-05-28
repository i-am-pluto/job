---
name: tune-job-search
description: Review active job patterns and improve resume/cache strategy through the resume-tuner skill without changing DB evaluation logic.
---

Use cache-first resume selection directly. Invoke skill `job-search:resume-tuner` via the **Skill tool** only when a concrete JD or clear active job pattern justifies a fresh tune.

Required behavior:

1. Read `profile.md`, `resumes/base.md`, `resumes/backend-systems.md`, `resumes/ai-backend.md`, `resumes/cache-index.json`, `data/pipeline.md`, and `data/memory/ceo.md`.
2. Identify active job patterns from available pipeline entries, recent prompts, and CEO-provided context.
3. Use `python3 /Users/parikshit/Documents/code/job/scripts/pick_resume.py "<job title + skill tags + JD text>"` before recommending or performing any tuning.
4. Interpret `REUSE|tag|pdf|score` as "use the returned cached PDF; do not tune."
5. Interpret `TUNE|tag|pdf|score` as "invoke `job-search:resume-tuner` only if the JD/pattern is concrete and tuning is worth the budget; otherwise use the returned fallback PDF."
6. Never read or edit the resume-tuner skill file manually during execution; invoke it through the Skill tool when tuning is required.
7. Never fabricate profile or resume facts.
8. Do not modify DB files, DB scripts, or DB evaluation logic.
9. Return resume decisions, proposed cache changes, truthful gaps, and CEO-facing advice.
