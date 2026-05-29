# Nightly Job Apply — Scheduled Prompt

> Source of truth for the external scheduled task prompt.
> Keep this wrapper thin. Do not copy workflow, profile, scoring, platform, or
> safety rules here; those live in the repo files listed below.
> Last updated: 2026-05-29

Nightly job apply — run every night at 11:35 PM.

You are running the user's autonomous nightly job application workflow. The user
is NOT present. Apply autonomously under `nightly-job-apply` mode.

## Workspace

`/Users/parikshit/Documents/code/job`

## Required Sources

Read these in order before acting:

1. `CLAUDE.md` — global source of truth: profile/resume ownership, safety rules,
   DB rules, status handling, nightly run order, final report format.
2. `commands/nightly-job-apply.md` — orchestration source of truth: CEO planning,
   agent dispatch order, prompts, and logging handoff.
3. `profile.md` — application answers and fit scoring. Do not use profile facts
   from any prompt.
4. The invoked platform skill files under `skills/*/SKILL.md` — platform-specific
   mechanics only when that platform is run.
5. `data/memory/*.md` — durable run learnings and temporary platform health notes.

## Execution Contract

Run `/nightly-job-apply` exactly as defined in
`commands/nightly-job-apply.md`. Do not inline or reinterpret the platform
workflows here.

Hard-stop rule: if any tool or agent reports `You've hit your session limit`,
flush already-applied jobs through the DB helpers, write a compact note if
possible, and stop the whole run.
