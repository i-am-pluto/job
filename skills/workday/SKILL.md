---
name: workday
description: This skill should be used when applying to jobs on Workday ATS (myworkdayjobs.com, *.wd*.myworkdayjobs.com). Handles multi-step flow, resume auto-fill, Google SSO, email+password account creation, and DB logging.
version: 1.2.0
---

# Workday Job Application Skill

Apply to jobs on Workday-hosted career pages. Multi-step flow with resume auto-fill. Always requires an account — try Google SSO first, then email+password login or account creation using ATS credentials from `.env`.

**Trigger:** `myworkdayjobs.com` URL, `*.wd*.myworkdayjobs.com` URL, "apply on Workday", company career page backed by Workday.
**Mode:** Interactive → stop before final submit. Nightly (`nightly-job-apply`) → submit autonomously within quota.

---

## Pre-flight (before opening browser)

1. **Dedupe:** `python3 scripts/db.py list` — skip if company+role+platform `workday` already exists.
2. **Score:** load `profile.md` scoring rules. Skip if score < 4.
3. **Resume:** `python3 scripts/pick_resume.py "<job title + top 3 JD skills>"` — use returned PDF.

---

## Primary path: `ats-extension` MCP (preferred — no screenshots)

The `ats-extension` Chrome-extension MCP drives Workday DOM-natively inside the
user's already-logged-in session. It eliminates screenshots, coordinate clicks,
below-fold scroll guesswork, and "Save vs Next" ambiguity (the content script
sees the full DOM, visible-only). Use this whenever the extension is connected.

**Login policy (do NOT automate account creation).** Workday account creation /
email-verification is exactly what fails today (see `data/pipeline.md`: Motorola
"email verification endpoint broken"). So:
1. `ats_status` → if `logged_in: false` for this tenant, the human logs into that
   Workday tenant ONCE in Chrome. The session persists; future applies reuse it.
   Do not run the email+password/account-creation flow via automation.
2. If the extension is disconnected (`connected: false`) or this is a tenant the
   user has not logged into, fall back to the browser flow below.

**Flow (one MCP tool per step — cheap, no images):**
1. `ats_status` → confirm `connected` + `logged_in`; note `selector_version`.
2. `ats_detect` → confirm `ats: "workday"` and the current `step`.
3. `ats_upload_resume` → it returns the file input selector + `native_file_dialog:true`
   (extensions cannot set file inputs); call claude-in-chrome `file_upload` with the
   picked PDF on that selector. Wait ~3s for auto-fill.
4. Per step: `ats_read_form` → get visible `{label,type,value,required,options,id}`
   → build a `{labelFragment: value}` map from `profile.md` → `ats_fill_form(map)`.
   - Authorized to work in India → Yes; visa sponsorship → No; notice/CTC/experience
     from `profile.md`; Voluntary Disclosures → "Prefer not to say".
   - For a required field not derivable from `profile.md`/`resumes/base.md`, use the
     **Questionnaire Unknown Field** escalation below before skipping.
5. `ats_next_step` → advances and returns `step_after` + `has_errors`. If
   `has_errors`, re-`ats_read_form`, fix flagged fields, retry.
6. Repeat 4–5 through My Information → My Experience → Application Questions →
   Voluntary Disclosures → Review.
7. Interactive: `ats_read_form` the review step, print a one-line summary, wait for
   "yes". Nightly: `ats_submit` → check `submitted: true`.
8. Log with `db_batch_insert.py --apps` (note: "Workday via ats-extension MCP").

**Selector drift:** if `ats_read_form` returns 0 fields or `ats_status`
`selector_version` is unexpected, run `python3 vendor/ats-extension/server/audit.py`
(or `verify.py`), fix `count=0`/invalid-CSS entries in
`vendor/ats-extension/extension/selectors/workday.js`, bump `SELECTOR_VERSION`,
reload the extension, refresh the tab.

---

## Fallback (browser automation) — only when the extension is disconnected

Use the screenshot/coordinate browser flow below ONLY when `ats-extension` is not
connected, or for a tenant the user has not yet logged into. This is the legacy
path; prefer the MCP path above.

## Authentication flow (in order — stop at first that works)

1. **Google SSO:** `find("Sign in with Google")` or `find("Continue with Google")` → click → select `parikshit.p2002@gmail.com` in the account picker → approve. If already signed in, auto-selects → approve. Continue to form.
2. **Email + password login:** Look for "Sign in" with email and password fields.
   - Email: `ATS_EMAIL` from `.env`
   - Password: `ATS_PASSWORD` from `.env`
   - Fill and submit.
3. **Account creation:** If login says "no account" or offers a "Create account" / "Sign up" link:
   - Register with `ATS_EMAIL` + `ATS_PASSWORD` from `.env`.
   - If email verification required → open Gmail tab (`mail.google.com`) → find Workday verification email → click verification link → return to Workday.
   - If OTP sent to email → open Gmail tab → copy OTP → enter it → continue.
4. **Stop:** Only skip if CAPTCHA or phone-number verification is required → save URL to `data/pipeline.md` with note "Workday: CAPTCHA or phone verification required".

Never use a password not stored in `.env`. Never enter phone numbers or government IDs.

---

## Workday form workflow

Workday is multi-step. Each step is a scrollable panel — scroll to reveal all fields before filling.

**Step 1 — Navigate + detect:**
```
browser_batch: [navigate to URL] → [wait 3s] → [get_page_text]
```
Confirm Workday page. If "Sign In" or account wall appears → run Authentication flow above before continuing.

**Step 2 — Resume upload (do this first — triggers auto-fill):**
```
find("resume upload")  →  file_upload with picked PDF
```
Wait 3s after upload for auto-fill to propagate. Then `read_page filter=interactive` to check what was populated.

**Step 3 — Review and fill each step:**

Common Workday steps in order:
1. **My Information** — First/Last name, Email, Phone, Address (city + country). Auto-filled from resume; verify and fix mismatches.
2. **My Experience** — Work history, Education. Auto-filled; verify top entries match profile.md.
3. **Application Questions** — Role-specific dropdowns and text fields. Fill from `profile.md`:
   - Authorized to work in India: Yes
   - Require visa sponsorship: No
   - Notice period: read from `profile.md` (days, number only)
   - Years of experience: read from `profile.md` Common Application Answers
   - Current CTC / Expected CTC: read from `profile.md` (number only, no units)
   - Unknown required field → **Questionnaire Unknown Field** escalation below.
4. **Voluntary Disclosures** — Gender, Ethnicity, Disability, Veteran status → "Prefer not to say" / "I do not wish to answer" for all.
5. **Review** — Confirm all sections, then submit.

**Step 4 — Navigation between steps:**
- `find("Next")` or `find("Save and Continue")` → click → wait 2s → `get_page_text` to detect next step.
- Do NOT screenshot between steps — use `get_page_text` or `read_page filter=interactive`.
- If a required field is missing from profile.md → escalate to CEO before skipping (see below).

**Step 5 — Submit:**
- Interactive: `read_page` the review step → print one-line summary → wait for "yes".
- Nightly: click "Submit" or "Apply" on the review step directly.
- One screenshot after submit for confirmation.

**Step 6 — Log:**
```bash
python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"workday","score":N,"status":"Applied","location":"L","notes":"Workday multi-step apply; resume Z.pdf; Google SSO / email+password used"}]'
```

---

## Questionnaire Unknown Field — escalate to job-ceo before skipping

When a required field cannot be answered from `profile.md` or `resumes/base.md`:

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
5. If `UNKNOWN`: log the question, skip this job, save URL to `data/pipeline.md` with note "Questionnaire blocker: <question>".

---

## Common Workday pitfalls

- **Scroll to reveal fields:** Workday panels cut off below the fold. Always scroll down within the panel before declaring a step complete.
- **Auto-fill lag:** After resume upload, wait 3s before reading fields — auto-fill is async.
- **Duplicate questions:** Workday sometimes shows the same field in multiple steps. Answer consistently from profile.md.
- **"Save" vs "Next":** Some steps have a Save button that does not advance — look for "Next" or "Save and Continue" specifically.
- **Session timeout:** If page goes blank or redirects to login, re-run the Authentication flow.
- **`get_page_text` hidden content:** Use `el.offsetParent !== null` in JavaScript to check real visibility when needed.

---

## Skip conditions

- Score < 4 per `profile.md`
- Already applied (dedupe check)
- CAPTCHA or phone verification required during account creation
- Job posting closed / "No longer accepting applications"
- Required field unresolvable after CEO escalation

Save blocked URLs with reason to `data/pipeline.md`.
