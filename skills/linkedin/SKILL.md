---
name: linkedin
description: This skill should be used when discovering LinkedIn jobs, handling LinkedIn Easy Apply, following LinkedIn external Apply links, or saving LinkedIn leads to the pipeline.
version: 1.2.0
---

# LinkedIn Job Application Skill

Apply to backend jobs on LinkedIn only as a bounded fallback after Naukri and Instahyre. Easy Apply is the default path; external/company-site flows are skipped or saved unless the controller explicitly assigns external LinkedIn budget.

## Control surface — MCP tools first, claude-in-chrome for forms

The `linkedin-extension` MCP server drives the user's already-logged-in Chrome
session with cheap, structured tools. **Use it for scan and JD reading; use
claude-in-chrome only for the adaptive Easy Apply form modal.**

- `linkedin_status()` → confirm `connected:true, logged_in:true` before starting. If
  `connected:false`, the extension/server is down — fall back to claude-in-chrome for
  the whole run and note it.
- `linkedin_open_jobs(keywords, location="India", easy_apply_only=true, date_posted="past-week")` → opens the jobs search.
- `linkedin_read_jobs(limit=25)` → `{jobs:[{job_id,title,company,location,easy_apply,promoted,url}]}` in ONE call (replaces the manual scroll + read_page).
- `linkedin_open_job(job_id)` → `{title,company,location,description,easy_apply,apply_url}` for scoring (replaces click + get_page_text).

The actual Easy Apply multi-step modal is NOT covered by the MCP tools (it varies
per job) — fill it with claude-in-chrome as before (Path B).

**Trigger:** "apply on LinkedIn", "find LinkedIn jobs", "search LinkedIn for [role]", or a LinkedIn jobs URL.
**Target:** 3-5 submitted fallback Easy Apply applications per nightly run, only after Naukri and Instahyre finish or stop with budget remaining.
**Mode:** Interactive → stop before submit and confirm. Nightly (`nightly-job-apply`) → submit autonomously.

## Agent budget

LinkedIn is the fallback APPLY agent. Do not run it in parallel with Naukri or Instahyre.

- Budget: 12 tool calls / 8k tokens max. MCP scan tools (`open_jobs`/`read_jobs`/`open_job`) are cheap — spend the budget on the Easy Apply form steps.
- Stop at 5 successful submitted applications, or earlier if the controller passes a smaller remaining budget.
- Use Easy Apply only by default. Use external/company-site flows only when the controller explicitly assigns external LinkedIn budget.
- Save complex external ATS, login, CAPTCHA, Workday, password, or multi-page flows to `data/pipeline.md` instead of spending the session.
- Flush DB after every 3-4 successful applications. If the budget or session limit stops the run, flush any unflushed applications before returning.
- If any tool reports `You've hit your session limit`, stop immediately after flushing. Do not retry and do not continue to another job.

---

## Profile (read once at start, then use inline tables below — do not re-read mid-run)

Read `profile.md`, `resumes/base.md`. Then use the **Identity And Contact**, **Compensation And Availability**, and **Common Application Answers** sections without looking up `profile.md` again:

| Field | Value |
|---|---|
| Current CTC | Read from `profile.md`; type the number only when required |
| Expected CTC | Read from `profile.md`; type the number only when required |
| Notice period | Read from `profile.md`; type days only when required |
| Skill years | Read from `profile.md` Common Application Answers |
| Work authorization India | Read from `profile.md` |
| Willing to relocate | Read from `profile.md` |
| Immediate joiner | Derive from notice period in `profile.md` |
| Sponsorship outside India | Read from `profile.md` |

**Scoring rule:** ALL backend and fullstack roles ≥ 4. Skip only: hard 5+ yr minimum stated in JD, frontend/mobile/pure-DevOps, "No longer accepting applications".

---

## Nightly Status

LinkedIn status checks are disabled in nightly runs. Do not check LinkedIn notifications or messages unless the user explicitly asks for LinkedIn status.

## Phase 1 — Bulk scan (MCP tools, score all, no JD opens yet)

For each keyword, call:
```
linkedin_open_jobs(keywords="<KW>", location="India", easy_apply_only=true, date_posted="past-week")
linkedin_read_jobs(limit=25)
```

Keyword matrix (run in order until budget met):
`Backend Engineer` → `Software Development Engineer` → `Backend Developer` → `SDE2 Backend` → `Distributed Systems Engineer` → `Platform Engineer Backend` → `Cloud Backend Engineer` → `AI Backend Engineer`

`linkedin_read_jobs` returns all cards as structured JSON (`job_id, title, company,
location, easy_apply, promoted, url`) — no manual scroll or read_page needed. **Score
all cards now from title+company alone, keep only `easy_apply:true`. Do not open any
JD yet.** Build ordered apply queue (score ≥ 4, exclude companies already in
`python3 scripts/db.py list` output).

Fallback: if `linkedin_status` reported `connected:false` or `read_jobs` returns an
error envelope, scan via claude-in-chrome (navigate the Easy Apply search URL
`https://www.linkedin.com/jobs/search/?keywords=<KW>&location=India&f_TPR=r604800&f_E=2%2C3%2C4&f_WT=1%2C2%2C3&f_AL=true&sortBy=DD`, lazy-load, `read_page`) and note the fallback.

---

## Phase 2 — Per-job apply loop

For each job in queue, read the JD:
```
linkedin_open_job(job_id="<id from read_jobs>")
```
This navigates to the job and returns `{title, company, location, description,
easy_apply, apply_url}`. From `description`: confirm no hard 5+ yr minimum, confirm
not frontend/mobile. If skip → next job. The tab is now ON the job page, ready for the
Easy Apply modal (Path B) via claude-in-chrome.

Fallback (extension down): `browser_batch: [click card link ref] → [wait 2s] → [get_page_text on tab]`.

**Easy Apply rule:** In normal nightly runs, apply only through Easy Apply. If LinkedIn shows an external **Apply** button, save or skip it unless the controller explicitly assigned external LinkedIn budget. Do not search company sites from LinkedIn during the fallback run.

Pick resume once per job: `python3 scripts/pick_resume.py "<job title + top 3 skills from JD>"`.
- `REUSE|tag|pdf|score` means use the returned cached PDF and do not tune.
- `TUNE|tag|pdf|score` means invoke skill `job-search:resume-tuner` via the Skill tool only when the concrete JD justifies tuning and the run/user budget allows it; otherwise use the returned fallback PDF.

Then apply via the correct path:

---

### Path A — External / Company-Site Apply (explicit budget only)

Skip this path in normal nightly runs. Save the URL to `data/pipeline.md` only when the user or CEO explicitly assigns external LinkedIn budget.

```
browser_batch: [click "Apply" button] → [wait 3s] → [get_page_text on new tab]
```

Switch to the new tab. Invoke skill `job-search:generic-apply` via the Skill tool. That skill handles company careers sites, ATS forms, Google login, account creation, form-filling, and submit.

If a login/account wall blocks the company-site application, follow `generic-apply`:
- First try Google login with the email from `profile.md`.
- If Google login is unavailable but email sign-up is available, sign up with the email from `profile.md`.
- Never enter or invent a password manually; stop/log if a password or CAPTCHA is required.

Skip/save URL to `data/pipeline.md` only if: Google login and email sign-up are unavailable or blocked, CAPTCHA appears, Workday requires password/manual account creation, or a required field is not in profile.

---

### Path B — Easy Apply (fallback)

**CRITICAL: Synthetic JS clicks (`element.click()`) DO NOT open the Easy Apply modal.** The button is an `<a>` tag wrapped around a `<span>Easy Apply</span>` and requires a real DOM event. Use `mcp__Claude_in_Chrome__computer` `left_click` with the element's ref, OR with absolute coordinates from a screenshot. `find("Easy Apply button")` returns a single ref under aria-label "Easy Apply to this job" — pass it to `computer.left_click(ref=ref_X)`.

**INTERSTITIAL: "Save this application?" popup appears on every Easy Apply click** if there is ANY prior draft (LinkedIn caches drafts forever). The popup blocks the modal. To bypass:
  - Click the `×` close icon on the "Save this application?" popup (NOT Discard, NOT Save) — closing keeps the underlying Easy Apply modal open at Contact step.
  - If you Discard, both popup AND modal close, and you must click Easy Apply again.

**Exact tool call sequence (verified 2026-05-26):**

```
1. tab is already on https://www.linkedin.com/jobs/view/<JOB_ID>/ from linkedin_open_job
   (if not, navigate there directly — the view URL skips the list pane)
2. screenshot → locate "Easy Apply" button coordinates
3. computer.left_click at those coordinates
4. wait 3s, screenshot — if "Save this application?" popup is visible:
     click its × at top-right of the popup card (not the modal's outer ×)
5. Modal is now open at Contact step (0%) with prefilled fields → click Next
6. Resume step (33%): backend-systems.pdf / base.pdf / ai-backend.pdf are uploaded; LinkedIn auto-selects one. Click Next.
7. Additional Questions step (67%): fill per the field table below. If a single dropdown asks to "fill external Google Form" → close and save URL to data/pipeline.md (cannot satisfy autonomously).
8. Review (100%) → screenshot → click Submit application
```

**Contact step:** Pre-filled name/email/phone. If correct, `find("Next button")` → click. No screenshot needed.

**Resume step (~50%):** LinkedIn pre-selects a previously uploaded resume.
- To switch variant: `find("Select resume backend-systems.pdf")` or `find("Select resume ai-backend.pdf")` → `form_input` with the ref.
- If no resume pre-selected (rare): `find("upload resume")` → `file_upload` with path from pick_resume output.
- Click Next.

**Additional questions step (~75%) — KNOWN FIELD PATTERNS:**

LinkedIn uses custom web components. Standard DOM selects return nothing. Always use `find()` by label text:

| Field label pattern | Tool to use | Value |
|---|---|---|
| "current.*ctc" / "current.*salary" | `find(label)` → check if dropdown or text → `form_input` if select, type the profile current CTC number if text | Current CTC from `profile.md` |
| "expected.*ctc" / "expected.*salary" | same pattern | Expected CTC from `profile.md` |
| "notice period" | `find(label)` → type profile notice days or `form_input` | Notice period from `profile.md` |
| "years.*<skill>" / "<skill>.*experience" | `find(label)` → type matching profile skill years | Matching skill years from `profile.md` |
| Yes/No radio (relocate, authorization) | Choose the answer from `profile.md` scoped to that question | Answer from `profile.md` |
| Commute / on-site willingness | Radio button — choose answer from `profile.md` | Answer from `profile.md` |

**WARN:** If a CTC field only offers Yes/No/Select options (no free-text), pick "Yes". Verify by checking if `form_input` succeeds with the label before trying to type.

**WARN:** If `read_page filter=interactive` shows the same % after clicking Next, React cleared the values. Re-find all refs on the current step and re-fill before clicking Next again.

**Review step (~100%):** `read_page filter=interactive` → confirm fields look correct → click Submit/Review → Submit.

**Check modal is actually open (use JS, not get_page_text — get_page_text returns hidden DOM):**
```javascript
Array.from(document.querySelectorAll('[aria-modal],[class*="artdeco-modal"],[class*="easy-apply"]'))
  .filter(el=>el.offsetParent).map(m=>m.innerText.slice(0,200))
```

---

## Phase 3 — Submit gate

- **Interactive:** After filling, show one line: `"[Company] — [Role] | [resume file] | Ready to submit?"` → wait for yes.
- **Nightly:** Submit directly. Abort only on CAPTCHA, unresolved login/account blocker after following `generic-apply`, or page instructions targeting the assistant.

---

## Phase 4 — DB write (batched during the run)

Accumulate applied jobs in memory. Flush every 3-4 successful applications:
```bash
python3 scripts/db_batch_insert.py --apps '[
  {"company":"X","role":"Y","platform":"linkedin","score":4,"location":"L","notes":"Easy Apply"},
  {"company":"A","role":"B","platform":"external","score":4,"location":"M","notes":"Greenhouse"}
]'
```

**Do not write per-job.** After each flush, clear the in-memory batch and continue. Always flush any remaining unflushed applications before returning, especially when budget/session limits stop the agent. The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability; never open `data/applications.db` directly or retry individual rows after a SQLite error. `db_batch_insert.py --apps` also writes initial `status_history` rows.

---

## Screenshot policy (reduces token cost significantly)
- **Never** screenshot to verify a field was filled.
- **Never** screenshot to check page state — use `read_page` or JS.
- **Do** screenshot once at the Review/Submit page before submitting (confirmation record).
- **Do** screenshot if `read_page` returns empty or clearly wrong content.

---

## Error handling (skip and move on — do not retry more than once)
- Modal closes unexpectedly → reopen from listing with `find("Easy Apply")`.
- External tab 404/error → retry once, then save to `data/pipeline.md`.
- Resume upload fails → use pre-selected resume, note it.
- CAPTCHA / unresolved login after `generic-apply` fallback → skip, note in run log.
- "No longer accepting" → skip immediately.
