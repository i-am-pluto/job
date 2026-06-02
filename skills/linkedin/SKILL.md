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

Easy Apply now uses a hybrid approach: two new MCP tools handle the modal except
the file-input step (Chrome MV3 blocks programmatic file selection from extensions).
See Path B for the updated sequence — only 3 tool calls instead of 6–8.

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

### Path B — Easy Apply (hybrid: extension + one chrome file_upload call)

**Primary path: 3 tool calls total** using the new extension tools. Only fall back to
full claude-in-chrome if the extension reports `connected:false`.

```
Step 1 — Extension starts the modal and fills Contact step:
  linkedin_start_easy_apply(job_id="<id>")
  → returns {step, file_input_visible, has_existing_resume, file_input_selector}

Step 2 — Resume step (extension cannot touch file inputs due to Chrome MV3):
  If file_input_visible=true:
    mcp__claude-in-chrome__file_upload(file_path="<pdf from pick_resume>",
                                       selector="input[type='file']")
  If has_existing_resume=true and correct variant already selected:
    skip (LinkedIn auto-selected; extension already passed the step)
  If has_existing_resume=true but wrong variant:
    find("Select a resume") → form_input or computer.left_click the correct one

Step 3 — Extension fills questions and submits:
  linkedin_continue_easy_apply(
    answers={"notice period": "30", "current ctc": "<from profile>",
             "expected ctc": "<from profile>"},
    submit=True
  )
  → returns {success, submitted, steps_traversed}
```

**Interstitial handled automatically** by `linkedin_start_easy_apply` — it dismisses
the "Save this application?" popup by clicking the `aria-label=Dismiss` button before
advancing to Contact step. Do not handle it manually.

**If `linkedin_start_easy_apply` returns `success:false`** (modal not found, button not
found): fall back to full claude-in-chrome. Use `computer.left_click` with ref from
`find("Easy Apply")`, then handle the interstitial ×, then fill all steps manually.

**If extension is down (`connected:false`):** fall back to the legacy claude-in-chrome
sequence (screenshot → coordinates → click → interstitial → steps) for the whole modal.

**Resume step fallback details** (when `has_existing_resume=false` and `file_input_visible=false`):
- LinkedIn may be on a later step already (extension auto-advanced past a pre-selected resume).
- Call `linkedin_continue_easy_apply` immediately — it will fill questions and submit.

**Additional questions step:** `linkedin_continue_easy_apply` fills fields by label
substring matching. Pass the common fields via `answers={}`. If a field asks to
"fill external Google Form" → extension will not find a matching input → check
`submitted=false` in the response, then save URL to `data/pipeline.md` and move on.

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
