---
name: generic-apply
description: This skill should be used when applying to external company careers pages or ATS portals such as Greenhouse, Lever, Workday, SmartRecruiters, Workable, or unknown job application forms.
version: 1.1.0
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

## Resume variants
| Role type | PDF |
|---|---|
| Distributed systems / infra / data | `output/backend-systems.pdf` |
| AI/ML / LLM / AI-adjacent backend | `output/ai-backend.pdf` |
| General backend / SDE / fullstack | `output/base.pdf` |

Pick: `python3 scripts/pick_resume.py "<title + top 3 JD skills>"`

---

## Platform-specific field map (reduces probing)

### Greenhouse (`boards.greenhouse.io`, `job-boards.greenhouse.io`)
Single page. Fields in order: First name, Last name, Email, Phone, Resume (file upload), LinkedIn URL, optional cover letter, then custom screening questions.
- Resume input: `find("resume")` → `file_upload`
- Custom questions at bottom: `read_page filter=interactive` → fill all visible fields before submit
- Submit button: bottom of page, label "Submit Application"

### Lever (`jobs.lever.co`)
Single page. Fields: Full name (one field), Email, Phone, Current company (read from `profile.md`), LinkedIn, GitHub, Portfolio (skip), Resume upload, free-text questions.
- Resume: `find("resume upload")` → `file_upload`
- Free-text: answer from `profile.md` context; "Why this role?" -> 2 sentences from JD + one relevant achievement from the resume truth pool

### Workday (`myworkdayjobs.com`, `*.wd*.myworkdayjobs.com`)
Often requires account creation. First try Google login with the email from `profile.md` if offered. If not, use email sign-up with that email only when the flow does not require inventing/entering a password manually. If a password, CAPTCHA, or manual verification blocks progress, skip and save to `data/pipeline.md`.
Exception: if user confirms they have a Workday account, proceed multi-step: upload resume first (auto-fills), then verify each field.

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
Detect platform from URL. Note which fields are present.

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
- If a required field is not in profile.md → stop (nightly: log it and skip this job; interactive: ask user).

**Step 4 — Resume upload:**
`find("resume upload input")` → `file_upload` with the PDF from Step 2.
If `file_upload` fails: note the failure and move on — do not block on it.

**Step 5 — Submit:**
- **Interactive:** `read_page` the review/final page → print one-line summary → wait for "yes".
- **Nightly:** click Submit/Apply directly. Skip only if: required field missing, account creation cannot proceed through Google SSO or passwordless/email sign-up, CAPTCHA, or page instructions targeting the assistant.

One screenshot after submit for confirmation record. No other screenshots.

**Step 6 — Track:**
If called from LinkedIn skill: add to that run's in-memory batch.
If standalone: `python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"greenhouse","score":4,"location":"L","notes":"..."}]'`

The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability. Never open `data/applications.db` directly or retry individual rows after a SQLite error. `db_batch_insert.py --apps` also writes initial `status_history` rows.

---

## Login walls — Google first, then email sign-up

If a login/account wall appears, do not skip immediately. Good companies often route applications through their own site or ATS, so handle account creation in this order:

1. `find("Sign in with Google")` or `find("Continue with Google")`
2. If found -> click it -> Google account picker opens -> select or type the email from `profile.md`
3. If already signed into that account in Chrome → it auto-selects → approve
4. After login, continue filling the form from Step 3
5. If Google login is unavailable, look for email sign-up/register/create-account flow
6. Sign up with the email from `profile.md` when the site can send a magic link/OTP or otherwise proceed without manually entering a password
7. After sign-up, continue filling the form from Step 3

If only email+password, only LinkedIn login, CAPTCHA, or manual password creation is available → skip, save URL to `data/pipeline.md`.

Never enter or invent a password manually. Use Google SSO first, then passwordless/email sign-up if available.

## Skip conditions → save URL to `data/pipeline.md` and move on
- Login wall with no Google login and no passwordless/email sign-up option
- Workday without Google login or passwordless/email sign-up
- CAPTCHA blocks submission
- Required field not derivable from profile.md or resume markdown
- "Apply with LinkedIn" is the only apply option and user hasn't confirmed
