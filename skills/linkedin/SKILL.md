---
name: linkedin
description: This skill should be used when discovering LinkedIn jobs, handling LinkedIn Easy Apply, following LinkedIn external Apply links, or saving LinkedIn leads to the pipeline.
version: 1.1.0
---

# LinkedIn Job Application Skill

Apply to backend jobs with a strong preference for the company's own careers/ATS site by invoking skill `job-search:generic-apply` via the Skill tool. LinkedIn is primarily a discovery source; Easy Apply is fallback when no company-site path is available. Both external and Easy Apply submissions count toward target.

**Trigger:** "apply on LinkedIn", "find LinkedIn jobs", "search LinkedIn for [role]", or a LinkedIn jobs URL.
**Target:** 15+ submitted applications per run, prioritizing external company-site submissions.
**Mode:** Interactive → stop before submit and confirm. Nightly (`nightly-job-apply`) → submit autonomously.

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

## Phase 1 — Bulk scan (ONE read_page, score all, no JD opens yet)

Navigate to search URL (NO `f_AL` — include external-apply jobs):
```
https://www.linkedin.com/jobs/search/?keywords=<KW>&location=India&f_TPR=r604800&f_E=2%2C3%2C4&f_WT=1%2C2%2C3&sortBy=DD
```

Keyword matrix (run in order until 15 applied):
`Backend Engineer` → `Software Development Engineer` → `Backend Developer` → `SDE2 Backend` → `Distributed Systems Engineer` → `Platform Engineer Backend` → `Cloud Backend Engineer` → `AI Backend Engineer`

**Lazy-load all cards first (one JS call):**
```javascript
const p=document.querySelector('.jobs-search-results-list');
if(p){let s=0;const t=setInterval(()=>{p.scrollTop+=1500;if(++s>8)clearInterval(t);},400);}
```
Wait 4 seconds, then: `read_page(filter=all, depth=6, ref_id=<list element ref>)`

From the single read, extract for each card: title, company, location, Easy Apply badge (yes/no), card link ref. **Score all cards now from title+company alone. Do not open any JD yet.** Build ordered apply queue (score ≥ 4, exclude companies already in `python3 scripts/db.py list` output).

Page deeper with `&start=25`, `&start=50` if needed.

---

## Phase 2 — Per-job apply loop

For each job in queue, execute one `browser_batch` to open + read:
```
[click card link ref] → [wait 2s] → [get_page_text on tab]
```

From the JD text: confirm no hard 5+ yr minimum, confirm not frontend/mobile. If skip → dismiss card, next.

**External-first rule:** For every qualifying company, prefer applying on the company's own careers page or ATS by invoking skill `job-search:generic-apply` via the Skill tool. Good companies usually host jobs on their own careers sites, Greenhouse, Lever, Ashby, SmartRecruiters, Workable, or similar. If LinkedIn shows an external **Apply** button, use that path before Easy Apply. If LinkedIn only shows Easy Apply but the company is strong, first check the JD/company site for a direct careers URL when it can be found without a long search; if found, invoke generic-apply skill. Use Easy Apply only when no reliable external/company-site path is available or the external path is blocked.

Pick resume once per job: `python3 scripts/pick_resume.py "<job title + top 3 skills from JD>"` → note the PDF path. Then apply via the correct path:

---

### Path A — External / Company-Site Apply (preferred)

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
1. navigate to https://www.linkedin.com/jobs/view/<JOB_ID>/   (direct view URL skips list pane)
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

## Phase 4 — DB write (once, after all jobs)

Accumulate all applied jobs in memory. After finishing the full run:
```bash
python3 scripts/db_batch_insert.py --apps '[
  {"company":"X","role":"Y","platform":"linkedin","score":4,"location":"L","notes":"Easy Apply"},
  {"company":"A","role":"B","platform":"external","score":4,"location":"M","notes":"Greenhouse"}
]'
```

**Do not write per-job.** Batch at the end. The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability; never open `data/applications.db` directly or retry individual rows after a SQLite error. `db_batch_insert.py --apps` also writes initial `status_history` rows.

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
