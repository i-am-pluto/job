---
name: nightly-job-apply
description: Run the user's autonomous nightly job-application workflow. Claude orchestrates all agent dispatch directly.
---

You are the orchestrator for the nightly job-application run. This is authorized
for autonomous submission under `nightly-job-apply` mode in `CLAUDE.md`.

Working directory: `/Users/parikshit/Documents/code/job`

## Knowledge Ownership

- `CLAUDE.md` owns global policy: source files, safety, scoring, duplicate rules,
  DB helpers, status handling, nightly order, and final report format.
- `profile.md` owns user/application facts. Do not copy profile facts into prompts.
- `skills/*/SKILL.md` owns platform mechanics.
- `agents/*.md` owns agent identity and routing boundaries.
- `data/memory/*.md` owns durable platform learnings.

Do not restate platform workflows in this command. Pass quotas, duplicate data,
resume map, CEO advice, and mode, then require each agent to invoke its skill.

**Model dispatch policy:** platform agents are mechanical executors and should
use `model="haiku"`. `job-ceo` does planning/judgment and should use
`model="sonnet"`.

## Stage 0 — Plan

Invoke `job-ceo` as a foreground agent in `plan` mode. It must read the sources
defined in `agents/job-ceo.md` and return the structured `PLAN` block described
there.

Extract:

- quotas
- resume archetype map
- duplicate list
- networking goal
- Greenhouse scan gate
- status scope
- CEO advice

## Stage 1 — Status

Perform the incremental Gmail-only status pass exactly as defined in
`CLAUDE.md`. Do not run portal status checks unless the user explicitly asked
for a platform status check.

## Stage 2 — Action

Update DB statuses only for clear Gmail-derived signals and collect
human-needed action items. Do not reply to emails and do not click email links.

## Stage 3 — Apply Agents

Run platform apply agents sequentially in this priority order:

1. `job-search:naukri-agent`
2. `job-search:instahyre-agent`
3. `job-search:linkedin-agent`
4. `job-search:greenhouse-agent`

For each agent prompt, include only:

- mode: `nightly-job-apply`
- working directory
- date
- assigned quota or skip reason
- duplicate list from Stage 0
- resume archetype map from Stage 0
- CEO advice from Stage 0
- instruction to invoke the platform skill via the Skill tool
- instruction to return the output format defined by that agent/skill

Each platform skill owns scan/apply mechanics, resume picking, DB flush cadence,
blocked-flow handling, memory updates, and platform-specific limits.

## Stage 4 — Networking

After application agents complete, run `job-search:networking-agent` with
`model="haiku"` if the CEO plan assigns a networking goal. Prompt it with mode,
working directory, date, networking goal, CEO advice, and the instruction to
invoke `job-search:networking`.

Networking mechanics and limits live only in `skills/networking/SKILL.md`.

## Stage 5 — Log

Invoke `job-ceo` as a foreground agent in `log` mode. Pass the collected status,
action, resume, apply, and networking results. `job-ceo` owns DB run-log writes,
memory updates, summaries, and final report formatting as defined in
`agents/job-ceo.md` and `CLAUDE.md`.

When passing networking output, include this labeled block so `job-ceo` can
extract it without re-reading agent logs:

```text
NETWORKING results: <INSERT_NETWORKING_RESULTS>
Accepted found: <N or list>
Messages sent: <N or list>
```

Print the final report returned by `job-ceo`.

## Hard Stop

If any tool or agent reports `You've hit your session limit`, stop dispatching
new work immediately. Flush any already-applied jobs through the DB helpers when
possible, write a compact note if possible, and return.
