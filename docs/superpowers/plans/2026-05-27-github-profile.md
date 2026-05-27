# GitHub Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a polished personal GitHub profile README for `i-am-pluto` with a cosmic-hacker and indie-builder voice.

**Architecture:** This is a static Markdown artifact. The profile lives in `github-profile/i-am-pluto/README.md`, using only GitHub-rendered Markdown, badge images, repo links, and GitHub stats image URLs.

**Tech Stack:** Markdown, GitHub profile README conventions, shields.io badges, GitHub stats cards.

---

## File Structure

- Create: `github-profile/i-am-pluto/README.md`
  - Main GitHub profile README content.
- Create: `github-profile/i-am-pluto/NOTES.md`
  - Short publishing notes for creating or updating the `i-am-pluto/i-am-pluto` GitHub repo.

### Task 1: Create Profile README

**Files:**
- Create: `github-profile/i-am-pluto/README.md`

- [ ] **Step 1: Create the directory**

Run:

```bash
mkdir -p github-profile/i-am-pluto
```

Expected: directory exists at `github-profile/i-am-pluto`.

- [ ] **Step 2: Add the README**

Create `github-profile/i-am-pluto/README.md` with:

```markdown
<h1 align="center">hi, i'm pluto</h1>

<p align="center">
  backend systems engineer · ai-tooling tinkerer · indie builder
</p>

<p align="center">
  <a href="https://github.com/i-am-pluto?tab=repositories"><img src="https://img.shields.io/badge/orbit-public%20repos-8A2BE2?style=flat-square" alt="public repos"></a>
  <a href="https://www.linkedin.com/in/parikshit-dabas"><img src="https://img.shields.io/badge/channel-linkedin-0A66C2?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn"></a>
  <a href="mailto:parikshit.p2002@gmail.com"><img src="https://img.shields.io/badge/ping-email-EA4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"></a>
</p>

---

### currently orbiting

I build backend platforms, data systems, and small AI-powered tools. Most days I am somewhere between JVM services, Kubernetes workloads, Spark jobs, observability dashboards, and experiments that start with "what if this could be automated?"

- Shipping production backend systems in Java/Kotlin, Spring Boot, AWS, and Kubernetes.
- Building data-platform pieces around Spark, Delta Lake, schema management, cost telemetry, and workflow automation.
- Exploring agentic developer tooling with MCP, LLM APIs, Bedrock, GitLab, Jira, and Slack integrations.
- Keeping side projects alive when they are useful, strange, or both.

### things i build

| Signal | Transmission |
| --- | --- |
| systems | backend APIs, platform automation, data pipelines, observability, reliability work |
| agents | release helpers, workflow bots, LLM-backed internal tools, automation glue |
| experiments | web apps, portfolio systems, productivity tools, Discord/Telegram bots |
| ml/cv | assistive navigation, geotagging, prediction notebooks, PySpark modeling |
| low-level | Linux/container experiments, C/C++, competitive programming traces |

### featured transmissions

- [Ai_Portfolio_AN](https://github.com/i-am-pluto/Ai_Portfolio_AN) — AI/portfolio experiment space.
- [HabitForge](https://github.com/i-am-pluto/HabitForge) — habit and productivity builder with a shipped Replit deployment.
- [solid-couscous](https://github.com/i-am-pluto/solid-couscous) — TypeScript web experiment, live on Vercel.
- [paras-website](https://github.com/i-am-pluto/paras-website) — personal web experiment, live on Vercel.
- [indoor-positioning-system-for-visually-impaired](https://github.com/i-am-pluto/indoor-positioning-system-for-visually-impaired) — assistive-tech ML/CV project for indoor navigation.
- [discordBot](https://github.com/i-am-pluto/discordBot) — early Python automation project.

### stack constellation

```text
backend        Java · Kotlin · Spring Boot · REST APIs · microservices
data systems   Spark · Delta Lake · Kafka · Airflow · Snowflake · PostgreSQL
cloud/infra    AWS · Kubernetes · Docker · Terraform · Argo Workflows
ai tooling     MCP · LLM APIs · AWS Bedrock · RAG patterns · developer automation
observability  Prometheus · Grafana · Datadog · cost and usage telemetry
experiments    Python · TypeScript · JavaScript · C/C++ · TensorFlow · OpenCV
```

### telemetry

<p>
  <img src="https://github-readme-stats.vercel.app/api?username=i-am-pluto&show_icons=true&theme=tokyonight&hide_border=true" alt="GitHub stats" height="160">
  <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=i-am-pluto&layout=compact&theme=tokyonight&hide_border=true" alt="Top languages" height="160">
</p>

### open channels

- LinkedIn: [linkedin.com/in/parikshit-dabas](https://www.linkedin.com/in/parikshit-dabas)
- GitHub: [github.com/i-am-pluto](https://github.com/i-am-pluto)
- Email: [parikshit.p2002@gmail.com](mailto:parikshit.p2002@gmail.com)
```

- [ ] **Step 3: Inspect README rendering-sensitive syntax**

Run:

```bash
sed -n '1,220p' github-profile/i-am-pluto/README.md
```

Expected: Markdown contains no placeholder text, no broken table rows, and all fenced code blocks are closed.

### Task 2: Add Publishing Notes

**Files:**
- Create: `github-profile/i-am-pluto/NOTES.md`

- [ ] **Step 1: Add publishing notes**

Create `github-profile/i-am-pluto/NOTES.md` with:

```markdown
# Publishing Notes

This directory is the local source for the `i-am-pluto` GitHub profile README.

To publish it:

1. Create a public GitHub repository named `i-am-pluto` under the `i-am-pluto` account.
2. Put `README.md` at the repository root.
3. Push to the default branch.

GitHub renders that README on `https://github.com/i-am-pluto`.
```

- [ ] **Step 2: Inspect notes**

Run:

```bash
sed -n '1,120p' github-profile/i-am-pluto/NOTES.md
```

Expected: notes describe the special profile repo flow and contain no secrets.

### Task 3: Verify Artifact

**Files:**
- Read: `github-profile/i-am-pluto/README.md`
- Read: `github-profile/i-am-pluto/NOTES.md`

- [ ] **Step 1: Check generated files**

Run:

```bash
find github-profile/i-am-pluto -maxdepth 1 -type f -print | sort
```

Expected:

```text
github-profile/i-am-pluto/NOTES.md
github-profile/i-am-pluto/README.md
```

- [ ] **Step 2: Check links and obvious Markdown issues**

Run:

```bash
rg -n "TODO|TBD|github.com/i-am-pluto|linkedin.com/in/parikshit-dabas|mailto:" github-profile/i-am-pluto
```

Expected: no `TODO` or `TBD`; expected profile, repo, LinkedIn, and email links appear.

- [ ] **Step 3: Review git diff**

Run:

```bash
git diff -- docs/superpowers github-profile
```

Expected: diff contains only the approved design, implementation plan, README, and notes.
