---
name: nightly-job-apply
description: Run Parikshit's autonomous nightly job-application workflow through the job CEO agent.
---

Invoke `job-ceo` to run Parikshit Dabas's nightly job-application workflow.

This command is authorized for autonomous submission under the `nightly-job-apply` mode described in `AGENTS.md` and `CLAUDE.md`.

Required behavior:

1. Read `AGENTS.md`, `CLAUDE.md`, `profile.md`, `resumes/base.md`, `resumes/cache-index.json`, and `data/memory/ceo.md`.
2. Follow the existing nightly order:
   - STATUS
   - ACTION
   - SCAN
   - RESUME
   - APPLY
   - LOG
3. Delegate platform work to:
   - `naukri-agent`
   - `instahyre-agent`
   - `linkedin-agent`
   - `generic-apply-agent`
4. Delegate resume/cache choices to `profile-agent`.
5. Preserve all non-negotiable rules from `AGENTS.md`.
6. Use existing DB helper commands only. Do not modify or evaluate DB scripts, DB schema, or DB locking behavior in this command.
7. Update `data/memory/ceo.md` and platform memory files with durable lessons from the run.
8. Return the final report in the format required by `AGENTS.md`, with `Agent performance` and `Memory updates` sections from `job-ceo`.
