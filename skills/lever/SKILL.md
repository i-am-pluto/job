---
name: lever
description: This skill should be used when applying to jobs hosted on Lever ATS (jobs.lever.co URLs). Handles single-page form fill, resume upload, email+password account creation, free-text questions, duplicate checking, and DB logging.
version: 1.1.0
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
- Unknown required field → **Questionnaire Unknown Field** escalation below before skipping.

---

## Exact workflow (minimal tool calls)

**Step 1 — Navigate + read (one batch):**
```
browser_batch: [navigate to URL] → [wait 2s] → [get_page_text]
```
Confirm it's a Lever page (`jobs.lever.co` in URL or Lever footer). If a login/account wall appears → run Login Wall flow before continuing.

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

## Login Wall flow (if Lever shows account/login gate)

Lever forms are usually open (no login required), but some employers enable a login gate. In order:

1. `find("Sign in with Google")` or `find("Continue with Google")` → click → select `parikshit.p2002@gmail.com` → approve.
2. If Google unavailable → `find("Sign in")` or `find("Log in")` with email + password:
   - Email: `ATS_EMAIL` from `.env`
   - Password: `ATS_PASSWORD` from `.env`
3. If "no account" / "Create account" prompt → register with `ATS_EMAIL` + `ATS_PASSWORD`.
   - Email verification → open Gmail tab → find Lever email → click verification link → return.
   - OTP to email → open Gmail tab → copy OTP → enter it → continue.
4. LinkedIn Quick Apply overlay → dismiss: `find("×")` or `find("close")` on the overlay → click → fill native form instead.
5. Only skip if: CAPTCHA, phone verification, or "only LinkedIn Apply" with no native form → save URL to `data/pipeline.md`.

---

## Questionnaire Unknown Field — escalate to job-ceo before skipping

When a required free-text or screening field cannot be answered from `profile.md` or `resumes/base.md`:

**Do NOT skip immediately.** First escalate:

1. Note: question text, field type (text / dropdown / radio), available options if any.
2. Invoke the job-ceo agent with:
   ```
   Mode: questionnaire-answer
   Company: <X>
   Role: <Y>
   Question: "<exact question text>"
   Type: <text|dropdown|radio>
   Options: [<option1>, <option2>, ...]  (if applicable)
   ```
3. job-ceo returns `ANSWER: <value>` or `UNKNOWN: <reason>`.
4. If `ANSWER`: use the value, fill the field, continue.
5. If `UNKNOWN`: log the question, skip, save URL to `data/pipeline.md` with note "Questionnaire blocker: <question>".

---

## Skip conditions

- Score < 4 per `profile.md`
- Already applied (dedupe check)
- Job posting returns 404 / "This position is no longer available"
- Login wall: CAPTCHA or phone verification required
- "Only LinkedIn Apply" available and no native form exists
- Required field unresolvable after CEO escalation

Save blocked URLs with reason to `data/pipeline.md`.
