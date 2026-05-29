---
name: workday
description: This skill should be used when applying to jobs on Workday ATS (myworkdayjobs.com, *.wd*.myworkdayjobs.com). Handles multi-step flow, resume auto-fill, Google SSO or email sign-up, and DB logging. Skips if password or CAPTCHA is required.
version: 1.0.0
---

# Workday Job Application Skill

Apply to jobs on Workday-hosted career pages. Multi-step flow with resume auto-fill. Requires account — try Google SSO first, then email sign-up; skip if only password works.

**Trigger:** `myworkdayjobs.com` URL, `*.wd*.myworkdayjobs.com` URL, "apply on Workday", company career page backed by Workday.
**Mode:** Interactive → stop before final submit. Nightly (`nightly-job-apply`) → submit autonomously within quota; skip on login wall if no Google/passwordless option.

---

## Pre-flight (before opening browser)

1. **Dedupe:** `python3 scripts/db.py list` — skip if company+role+platform `workday` already exists.
2. **Score:** load `profile.md` scoring rules. Skip if score < 4.
3. **Resume:** `python3 scripts/pick_resume.py "<job title + top 3 JD skills>"` — use returned PDF.

---

## Authentication flow (in order — stop at first that works)

1. **Google SSO:** `find("Sign in with Google")` or `find("Continue with Google")` → click → select email from `profile.md` in the account picker → approve. Continue to form.
2. **Email sign-up / magic link:** Look for "Create account", "Sign up", "Get started" → use email from `profile.md` → complete email-only verification (magic link or OTP to that inbox). Continue to form.
3. **Passwordless / LinkedIn login:** If available and user has pre-authorized, use it.
4. **Stop:** If only password entry, LinkedIn-only, or CAPTCHA → save URL to `data/pipeline.md` with note "Workday login required" and skip.

Never invent or enter a password. Never use "Apply with LinkedIn" unless explicitly authorized.

---

## Workday form workflow

Workday is multi-step. Each step is a scrollable panel — scroll to reveal all fields before filling.

**Step 1 — Navigate + detect:**
```
browser_batch: [navigate to URL] → [wait 3s] → [get_page_text]
```
Confirm Workday page. If "Sign In" or account wall appears → run Authentication flow above.

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
4. **Voluntary Disclosures** — Gender, Ethnicity, Disability, Veteran status → "Prefer not to say" / "I do not wish to answer" for all.
5. **Review** — Confirm all sections, then submit.

**Step 4 — Navigation between steps:**
- `find("Next")` or `find("Save and Continue")` → click → wait 2s → `get_page_text` to detect next step.
- Do NOT screenshot between steps — use `get_page_text` or `read_page filter=interactive`.
- If a required field is missing from profile.md → stop (nightly: log + skip; interactive: ask user).

**Step 5 — Submit:**
- Interactive: `read_page` the review step → print one-line summary → wait for "yes".
- Nightly: click "Submit" or "Apply" on the review step directly.
- One screenshot after submit for confirmation.

**Step 6 — Log:**
```bash
python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"workday","score":N,"status":"Applied","location":"L","notes":"Workday multi-step apply; resume Z.pdf; Google SSO used"}]'
```

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
- Login wall with password only, CAPTCHA, or no Google/passwordless option
- Job posting closed / "No longer accepting applications"
- Required field not in profile.md and cannot be inferred

Save blocked URLs with reason to `data/pipeline.md`.
