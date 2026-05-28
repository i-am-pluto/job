---
name: tune-job-search
description: Ask the profile agent to review active job patterns and improve resume/cache strategy without changing DB evaluation logic.
---

Invoke `profile-agent` for resume and profile strategy.

Required behavior:

1. Read `profile.md`, `resumes/base.md`, `resumes/backend-systems.md`, `resumes/ai-backend.md`, `resumes/cache-index.json`, `data/pipeline.md`, and `data/memory/ceo.md`.
2. Identify active job patterns from available pipeline entries, recent prompts, and CEO-provided context.
3. Use `scripts/pick_resume.py` before recommending any tuning.
4. Follow `skills/resume-tuner/SKILL.md` if a concrete tune is justified.
5. Never fabricate profile or resume facts.
6. Do not modify DB files, DB scripts, or DB evaluation logic.
7. Return resume decisions, proposed cache changes, truthful gaps, and CEO-facing advice.
