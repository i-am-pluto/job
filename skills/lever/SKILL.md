---
name: lever
description: This skill should be used when applying to jobs hosted on Lever ATS (jobs.lever.co URLs). Handles single-page form fill, resume upload, free-text questions, duplicate checking, and DB logging.
version: 1.0.0
---

# Lever Job Application Skill

Apply to jobs on `jobs.lever.co`. Single-page form — no multi-step flow. Faster than generic portals.

**Trigger:** `jobs.lever.co` URL, "apply on Lever", LinkedIn external link pointing to Lever.
**Mode:** Interactive → stop before submit. Nightly (`nightly-job-apply`) → submit autonomously within quota.

---

## Pre-flight (before opening browser)

1. **Dedupe:** `python3 scripts/db.py list` — skip if company+role+platform `lever` already exists.
2. **Score:** load `profile.md` scoring rules. Skip if score < 4.
3. **Resume:** `python3 scripts/pick_resume.py "<job title + top 3 JD skills>"` — use returned PDF.

---

## Form layout (`jobs.lever.co`)

Single page, fields in this order:

| Field | Source | Notes |
|-------|--------|-------|
| Full name | `profile.md` Identity | One field — first + last |
| Email | `profile.md` Identity | |
| Phone | `profile.md` Identity | |
| Current company | `profile.md` Identity | Current employer |
| LinkedIn URL | `profile.md` Identity | |
| GitHub URL | `profile.md` Identity | |
| Portfolio / Website | `profile.md` Identity | Skip if optional |
| Resume | picked PDF | `find("resume")` → `file_upload` |
| Free-text questions | varies | See below |

Free-text question strategy:
- "Why this role?" / "Why us?" — 2 sentences: one JD-aligned reason + one achievement from resume truth pool.
- "Tell us about a challenging project" — use strongest matching project from `profile.md`.
- "Years of experience in X" — answer from `profile.md` Common Application Answers.
- Required field not in profile.md → stop (nightly: log + skip; interactive: ask user).

---

## Exact workflow (minimal tool calls)

**Step 1 — Navigate + read (one batch):**
```
browser_batch: [navigate to URL] → [wait 2s] → [get_page_text]
```
Confirm it's a Lever page (`jobs.lever.co` in URL or Lever footer). Extract job title, company, location.

**Step 2 — Score + resume pick:**
```bash
python3 scripts/pick_resume.py "<title + top skills>"
```

**Step 3 — Read all fields:**
```
read_page filter=interactive
```
One call. Get all field refs before touching any.

**Step 4 — Fill all fields:**
- Text fields: `triple_click → type` using refs.
- File: `find("resume upload")` → `file_upload`.
- Numbers only for CTC/notice/years — no units.
- Cover letter: skip unless marked required; if required, 3 sentences inline.

**Step 5 — Submit:**
- Interactive: `read_page` review section → print summary → wait for "yes".
- Nightly: click "Submit Application" or "Apply" button directly.
- One screenshot after submit for confirmation.

**Step 6 — Log:**
```bash
python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"lever","score":N,"status":"Applied","location":"L","notes":"Lever direct apply; resume Z.pdf"}]'
```

---

## Login walls

Lever sometimes shows a LinkedIn Quick Apply overlay. Dismiss it and use the direct form instead:
- `find("×")` or `find("close")` on the LinkedIn overlay → click → fill native form.
- If only LinkedIn Apply is shown and no native form exists → save URL to `data/pipeline.md` and skip.

---

## Skip conditions

- Score < 4 per `profile.md`
- Already applied (dedupe check)
- Job posting returns 404 / "This position is no longer available"
- Required field not in `profile.md` and cannot be inferred
- CAPTCHA or manual password required

Save blocked URLs with reason to `data/pipeline.md`.
