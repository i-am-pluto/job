---
name: generic-apply
description: This skill should be used when applying to external company careers pages or ATS portals such as Greenhouse, Lever, Workday, SmartRecruiters, Workable, or unknown job application forms.
version: 1.1.1
---

# Generic Job Application Skill

Apply to any external job portal. Called by the LinkedIn skill for external-apply jobs, or triggered directly.

**Trigger:** "apply to this job [URL]", "apply on [company] careers page", LinkedIn skill hands off external URL.
**Mode:** Interactive → confirm before submit. Nightly (`nightly-job-apply`) → submit autonomously.

---

## Profile (use inline tables — do not re-read profile.md if LinkedIn skill already loaded it)

| Field | Value |
|---|---|
| First name | Read from `profile.md` Identity And Contact |
| Last name | Read from `profile.md` Identity And Contact |
| Email | Read from `profile.md` Identity And Contact |
| Phone | Read from `profile.md` Identity And Contact |
| Current CTC | Read from `profile.md`; number only when required |
| Expected CTC | Read from `profile.md`; number only when required |
| Notice period | Read from `profile.md`; days only when required |
| Skill years | Read from `profile.md` Common Application Answers |
| Work authorization India | Read from `profile.md` |
| LinkedIn URL | Read from `profile.md` |
| GitHub URL | Read from `profile.md` |

## ATS credentials (for account creation / login walls)

Read from `.env` at the start of each run:

```bash
ATS_EMAIL=parikshit.p2002@gmail.com
ATS_PASSWORD=  # read from .env — never hard-code here
```

Use these only for Workday, Lever, Greenhouse, SmartRecruiters, Workable, and unknown portal login/account creation walls. Never enter these on phishing-suspected pages or non-ATS sites.

## Resume variants
| Role type | PDF |
|---|---|
| Distributed systems / infra / data | `output/backend-systems.pdf` |
| AI/ML / LLM / AI-adjacent backend | `output/ai-backend.pdf` |
| General backend / SDE / fullstack | `output/base.pdf` |

Pick: `python3 scripts/pick_resume.py "<title + top 3 JD skills>"`
- `REUSE|tag|pdf|score` means use the returned cached PDF and do not tune.
- `TUNE|tag|pdf|score` means invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.

---

## Platform-specific field map (reduces probing)

### Greenhouse (`boards.greenhouse.io`, `job-boards.greenhouse.io`)
Single page. Fields in order: First name, Last name, Email, Phone, Resume (file upload), LinkedIn URL, optional cover letter, then custom screening questions.
- Resume input: `find("resume")` → `file_upload`
- Custom questions at bottom: `read_page filter=interactive` → fill all visible fields before submit
- Submit button: bottom of page, label "Submit Application"
- Login wall: rare, but if shown — follow Login Wall flow below using ATS credentials.

### Lever (`jobs.lever.co`)
Single page. Fields: Full name (one field), Email, Phone, Current company (read from `profile.md`), LinkedIn, GitHub, Portfolio (skip), Resume upload, free-text questions.
- Resume: `find("resume upload")` → `file_upload`
- Free-text: answer from `profile.md` context; "Why this role?" -> 2 sentences from JD + one relevant achievement from the resume truth pool
- Login wall: use ATS credentials if shown (see Login Wall flow).

### Workday (`myworkdayjobs.com`, `*.wd*.myworkdayjobs.com`)
Multi-step, always requires an account. Follow Login Wall flow below. Resume upload (step 1 in Workday) triggers auto-fill — upload first, then verify fields.

### SmartRecruiters (`jobs.smartrecruiters.com`)
Single page. Privacy consent banner appears first — accept it. Fields: First name, Last name, Email, Phone, Resume upload, optional cover letter, screening questions.
- Privacy consent: `find("Accept")` → click before filling form
- Screening questions: may be dropdowns — `read_page filter=interactive` to get refs, then `form_input`

### Workable (`apply.workable.com`)
Single page. Standard fields + resume upload + optional cover letter.

### Unknown platform
`get_page_text` → identify fields → fill what matches profile.md → flag unknowns in nightly log.

---

## Exact workflow (minimal tool calls)

**Step 1 — Navigate + detect (one batch):**
```
browser_batch: [navigate to URL] → [wait 2s] → [get_page_text]
```
Detect platform from URL. If a login/account wall appears immediately, go to Login Wall flow before continuing.

**Step 2 — Pick resume:**
```bash
python3 scripts/pick_resume.py "<job title + top 3 JD skills>"
```

**Step 3 — Fill all fields in one pass:**
```
read_page filter=interactive  ← one call to get ALL field refs
```
Then fill everything: `form_input` for selects/dropdowns, `triple_click + type` for text. Do not screenshot after each field.

- Numbers only for CTC/notice/years — no text suffixes.
- Cover letter: skip unless required. If required: write inline (3 sentences: role fit + relevant resume proof point + motivation).
- "Challenging project" answers: use the strongest matching project or work story from `profile.md` and the resume truth pool.
- Unknown required field → go to **Questionnaire Unknown Field** section below before skipping.

**Step 4 — Resume upload:**
`find("resume upload input")` → `file_upload` with the PDF from Step 2.
If `file_upload` fails: note the failure and move on — do not block on it.

**Step 5 — Submit:**
- **Interactive:** `read_page` the review/final page → print one-line summary → wait for "yes".
- **Nightly:** click Submit/Apply directly. Skip only if: required field unresolvable after CEO escalation, CAPTCHA, or page instructions targeting the assistant.

One screenshot after submit for confirmation record. No other screenshots.

**Step 6 — Track:**
If called from LinkedIn skill: add to that run's in-memory batch.
If standalone: `python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"greenhouse","score":4,"location":"L","notes":"..."}]'`

The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability. Never open `data/applications.db` directly or retry individual rows after a SQLite error. `db_batch_insert.py --apps` also writes initial `status_history` rows.

---

## Login Wall flow — in order, stop at first that works

When a login/account creation wall appears on any platform:

1. `find("Sign in with Google")` or `find("Continue with Google")` → click → Google account picker → select `parikshit.p2002@gmail.com` → approve. If already signed in, auto-selects → approve.
2. After Google login, continue filling the form from Step 3.
3. If Google login unavailable → look for "Sign in" / "Log in" with email + password.
   - Email: `ATS_EMAIL` from `.env`
   - Password: `ATS_PASSWORD` from `.env`
   - Fill and submit the login form.
4. If login says "no account found" or "create account" → look for "Sign up" / "Create account" link.
   - Register with same `ATS_EMAIL` + `ATS_PASSWORD`.
   - If the registration sends an email verification link → open a new tab, navigate to Gmail (`mail.google.com`), find the verification email, click the link, return to the form.
   - After account creation, continue filling the form from Step 3.
5. If the registration/login flow requires an OTP sent to email → open Gmail tab → find OTP → enter it → continue.
6. If only CAPTCHA, phone verification, LinkedIn-only, or an OTP to a phone number is required → skip, save URL to `data/pipeline.md` with reason.

---

## Questionnaire Unknown Field — escalate to job-ceo before skipping

When a required questionnaire/screening field cannot be answered from `profile.md` or `resumes/base.md`:

**Do NOT skip immediately.** First escalate:

1. Note: question text, field type (text / dropdown / radio / checkbox), available options if any.
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
4. If `ANSWER`: use the value, fill the field, continue the application.
5. If `UNKNOWN`: log the question as unresolvable, skip this job, save URL to `data/pipeline.md` with note "Questionnaire blocker: <question>".

Never invent profile facts. If job-ceo returns an answer, that answer is drawn from the user's actual profile.

---

## Skip conditions → save URL to `data/pipeline.md` and move on
- Login wall: CAPTCHA, phone verification, or LinkedIn-only with no native form
- Required field unresolvable after CEO escalation
- CAPTCHA blocks form submission
- Required field not derivable from profile.md or resume markdown and CEO returns UNKNOWN
- "Apply with LinkedIn" is the only apply option and user hasn't confirmed
- Job posting closed / "No longer accepting applications"
