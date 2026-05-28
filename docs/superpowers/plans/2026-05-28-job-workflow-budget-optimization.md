# Job Workflow Budget Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent nightly job-apply runs from burning session quota without applications by adding per-agent budgets, sequential apply execution, and platform-specific caps.

**Architecture:** Keep the current markdown-driven workflow, but make the CEO agent act as a budgeted controller instead of launching all apply agents at once. Platform agents receive explicit job/tool budgets and must stop with partial results before consuming the whole session. Naukri and Instahyre are prioritized; LinkedIn is a bounded fallback.

**Tech Stack:** Markdown workflow prompts and local job-search skill files.

---

### Task 1: Add Controller Budget Rules

**Files:**
- Modify: `data/nightly-prompt.md`
- Modify: `data/memory/ceo.md`

- [ ] **Step 1: Add an organization budget contract**

Add a budget table that limits CEO, status, Instahyre, Naukri, LinkedIn, resume, and logging work. Include a hard rule: no parallel apply agents.

- [ ] **Step 2: Change apply order**

Set apply order to `Naukri -> Instahyre -> LinkedIn fallback`. Instahyre must be skipped when today's DB count already meets or exceeds its cap.

- [ ] **Step 3: Add session-limit stop behavior**

If any agent sees `You've hit your session limit`, stop the whole run. Do not invoke CEO log mode, retry agents, or launch another platform.

### Task 2: Remove Naukri Profile Boost

**Files:**
- Modify: `skills/naukri/SKILL.md`
- Modify: `data/nightly-prompt.md`

- [ ] **Step 1: Remove profile boost language**

Delete the profile boost phase from the Naukri skill and remove the nightly instruction to re-save the profile headline.

- [ ] **Step 2: Renumber Naukri phases**

Make Naukri start at bulk scan. Keep direct Naukri apply as the preferred fast path.

### Task 3: Add Platform Agent Budgets

**Files:**
- Modify: `skills/naukri/SKILL.md`
- Modify: `skills/instahyre/SKILL.md`
- Modify: `skills/linkedin/SKILL.md`

- [ ] **Step 1: Add Naukri budget**

Give Naukri priority with a target of 15, stop cap of 15 submitted jobs, and a tool-budget rule that prefers direct Naukri applies over external redirects.

- [ ] **Step 2: Add Instahyre budget**

Give Instahyre a target of 15 only when today's remaining quota is positive. Stop immediately at 15 submitted jobs.

- [ ] **Step 3: Add LinkedIn fallback budget**

Limit LinkedIn to leftover session budget. Prefer Easy Apply only after Naukri/Instahyre, and avoid external ATS rabbit holes.

### Task 4: Align DB Flush Rules

**Files:**
- Modify: `skills/naukri/SKILL.md`
- Modify: `skills/instahyre/SKILL.md`
- Modify: `skills/linkedin/SKILL.md`

- [ ] **Step 1: Replace end-only DB writes**

Change platform skills to flush every 3-4 successful applications, matching the nightly prompt.

- [ ] **Step 2: Preserve partial progress**

If a budget or session limit stops a platform, the agent must flush any unflushed applications before returning.

### Task 5: Verify Text Consistency

**Files:**
- Check: `data/nightly-prompt.md`
- Check: `data/memory/ceo.md`
- Check: `skills/naukri/SKILL.md`
- Check: `skills/instahyre/SKILL.md`
- Check: `skills/linkedin/SKILL.md`

- [ ] **Step 1: Search for removed/contradictory rules**

Run:
```bash
rg -n "parallel|Profile Boost|profile boost|re-save|once at the end|all at once|all three|15/15/15|session limit" data/nightly-prompt.md data/memory/ceo.md skills
```

Expected: no remaining instruction to parallelize apply agents, run Naukri profile boost, or write platform DB results only at the end.

- [ ] **Step 2: Review diff**

Run:
```bash
git diff -- data/nightly-prompt.md data/memory/ceo.md skills/naukri/SKILL.md skills/instahyre/SKILL.md skills/linkedin/SKILL.md docs/superpowers/plans/2026-05-28-job-workflow-budget-optimization.md
```

Expected: changes are limited to quota optimization and Naukri profile boost removal.
