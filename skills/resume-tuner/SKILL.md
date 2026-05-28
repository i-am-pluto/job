---
name: resume-tuner
description: This skill should be used when choosing, tuning, generating, or caching resumes for a specific job description while preserving truthful resume claims.
version: 1.0.0
---

# Resume Tuner Skill

Tune Parikshit's resume for a specific job description. Re-emphasize and reorder — never fabricate. The output is a tuned `.md` file saved to `resumes/tuned/` and a PDF.

## Token economy — check the cache FIRST

Tuning every job is expensive. Before tuning anything:

```
python3 scripts/pick_resume.py "<job title + skill tags + jd text>"
```

- `REUSE|tag|pdf|score` → a cached resume already fits. **Do not tune.** Use that PDF.
- `TUNE|tag|pdf|score` → no archetype fits well; tuning is worth it — proceed below. The returned `pdf` is a safe fallback if tuning fails.

Only continue the workflow below when the result is `TUNE`, or when the user explicitly asks for a fresh tune.

## When this skill triggers
User says: "tune my resume for [role/company/JD]", "customize my CV for this job", "optimize resume for [URL]", or pastes a JD alongside asking about resume.

## Core rules (non-negotiable)
1. **Truth only.** Never add a technology, metric, or role Parikshit hasn't actually done.
2. **Re-rank before rewrite.** Move bullets, then reorder skills, then rephrase — in that order.
3. **Preserve voice.** Don't turn "Built X" into "Spearheaded the development of X". Keep his direct, outcome-oriented style.
4. **Metrics stay exact.** If the source says "~15%", don't change it to "20%".

## Source resumes (truth pool — anything in these is fair game)
- `resumes/base.md` — canonical, most complete
- `resumes/backend-systems.md` — distributed systems emphasis
- `resumes/ai-backend.md` — AI tooling emphasis
Any claim from any of these three files can be included in a tuned version.

## Parikshit's key proof points (use these for bullet emphasis decisions)
| Proof point | JD signals that make it relevant |
|-------------|----------------------------------|
| Multi-tenant data connector platform (Java/Kotlin/Spring Boot, 10+ domains) | data ingestion, connectors, multi-tenancy, Java/Spring |
| Containerized Spark on Kubernetes + AWS Lambda/S3 | Spark, K8s, distributed compute, cloud-native |
| Multi-tenant cost+observability platform (Prometheus, Grafana, Datadog) | observability, SRE, platform eng, fintech infra |
| CI/CD + observability rollout (GitLab CI, Jenkins, GitHub Actions) | DevOps, CI/CD, release engineering |
| AI agents (Anthropic API + AWS Bedrock + MCP, GitLab/Jira/Slack) | AI/LLM, automation, developer tooling |
| Spark auto-tuner (reduced failure rate ~15%) | Spark optimization, cost reduction, ML on infra |
| Schema management (Delta Lake, Snowflake, PostgreSQL parallel evolution) | data engineering, schema registry, big data |
| Container runtime in C (namespaces, cgroups) | systems programming, low-level, OS knowledge |

## Workflow

### Step 1 — Get the JD
- If URL provided: `navigate` to it and `get_page_text`
- If pasted: read directly
- If company + role only: ask user to paste the JD (don't guess)

### Step 2 — Parse the JD
Extract:
- **Hard requirements:** must-have skills, years of experience
- **Soft requirements:** nice-to-have, bonus
- **Keywords:** exact terms repeated in the JD (ATS targets)
- **Seniority signal:** IC level, scope, leadership expectations
- **Stack:** primary technologies mentioned

### Step 3 — Choose base resume
| JD focus | Start from |
|----------|-----------|
| Distributed systems, infra, data pipelines | `resumes/backend-systems.md` |
| AI tooling, LLM, agent systems | `resumes/ai-backend.md` |
| General backend, SDE, full-stack backend | `resumes/base.md` |

### Step 4 — Ask one focused question (optional, only if genuinely unclear)
If the JD is ambiguous between two variants, ask:
> "This JD emphasizes [A] and [B]. Should I lead with [connector platform / Spark work / AI agents]? Or auto?"

Default: auto-decide based on JD signals.

### Step 5 — Apply tuning (smallest blast radius first)

**5a. Summary** — Rewrite to mirror JD framing. Lead with the 2-3 signals the JD prioritizes. Keep 2-4 lines.

**5b. Skills section** — Reorder categories and items to put JD-matched stack first. Add a line only if justified by actual work AND JD asks for it.

**5c. Experience bullets** — Reorder within each role so JD-relevant bullets lead. Rephrase 1-3 bullets to use JD vocabulary where the underlying work matches. Keep all metrics exact.

**5d. Projects** — Surface or suppress based on JD relevance. Don't rewrite aggressively.

**5e. Section order** — Only change if there's a clear reason (e.g., for research-heavy JD, Projects might move up).

### Step 6 — Self-check before output
For each change, confirm:
- Is this claim in at least one source resume?
- If rephrased, does it still describe the same work?
- Did I add any technology not in any source? (If yes → revert)

### Step 7 — Save output
```
Save to: resumes/tuned/[company-slug]-[role-slug].md
```
Example: `resumes/tuned/arcana-sde2-backend.md`

Then show the **change summary**:

```markdown
## Tuning for [Company] — [Role]

**Summary shift:** [one line — e.g., "led with Spark/Kubernetes work, moved AI agents to secondary"]

**Reordered:**
- [bullet X] moved above [bullet Y] because JD emphasizes [signal]

**Rephrased (before → after):**
- "[original]" → "[tuned]" — same work, JD vocabulary

**Added:**
- [item] from [source resume], justified by [JD signal]

**Removed:**
- [item] — not relevant for this role

**Gaps (not added because not truthful):**
- JD asks for [X] — Parikshit's resumes don't clearly show this. Flag to user.
```

### Step 8 — Generate the PDF (Claude-native, no Node)
Build the PDF directly with the Python helper:
```
python3 scripts/resume_pdf.py resumes/tuned/[company-slug]-[role-slug].md output/[company-slug]-[role-slug].pdf
```
`resume_pdf.py` uses reportlab only — no browser, no Node. It produces a clean, ATS-parseable PDF.

### Step 9 — Register in the resume cache
Add the new variant to `resumes/cache-index.json` under `"tuned"` so future jobs reuse it instead of re-tuning:
```json
{ "tag": "[company-slug]-[role-slug]", "md": "resumes/tuned/[...].md",
  "pdf": "output/[...].pdf", "signals": ["<5-10 keywords from the JD>"],
  "description": "[one line]", "generated": "YYYY-MM-DD", "last_used": "YYYY-MM-DD" }
```
If `tuned` already holds `max_tuned_variants` entries, drop the one with the oldest `last_used` before adding (and note it — leave its files, just remove the index entry).

## Common tuning patterns

| JD signal | Action |
|-----------|--------|
| "Kafka" or "event streaming" | Lead with connector platform bullet, mention Kafka explicitly |
| "Kubernetes" / "k8s" / "containerization" | Lead with Spark-on-K8s bullet, surface Container Runtime project |
| "Observability" / "SRE" / "on-call" | Lead with cost+observability platform bullet, mention Prometheus/Grafana |
| "AI" / "LLM" / "Bedrock" / "agents" | Switch to ai-backend.md base, lead with AI agents bullet |
| "Data pipelines" / "ETL" / "Spark" | Lead with Spark auto-tuner + connector platform, use backend-systems.md |
| "Java" / "Spring Boot" | Use base.md, lead with connector platform (strongest Java bullet) |
| "System design" | Mention multi-tenant architecture decisions explicitly |
| "Python" emphasis | Surface Indoor Navigation project, mention Python in skills lead position |

## What NOT to do
- Don't add Golang, PHP, Scala, Ruby — not in any source resume
- Don't inflate "~15% failure rate reduction" to a specific higher number
- Don't claim 5+ years of experience — he has 2
- Don't write "Architected end-to-end enterprise-grade solutions" — that's not his voice
- Don't add a cover letter unless explicitly asked
