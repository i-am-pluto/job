# Naukri Job Application Skill

Apply to backend/SDE jobs on Naukri.com. Prefers direct Naukri apply (one-click); for "Apply on company site" jobs, hands off to `skills/generic-apply/SKILL.md`. Includes a daily profile boost routine.

**Trigger:** "apply on Naukri", "find Naukri jobs", "scan Naukri", "naukri run", or a Naukri jobs/search URL.
**Target:** 15+ submitted applications per run.
**Mode:** Interactive → stop before submit and confirm. Nightly (`nightly-job-apply`) → submit autonomously.

---

## Profile (read once at start — do not re-read mid-run)

Read `profile.md` and `resumes/base.md` once. Then use these inline:

| Field | Value |
|---|---|
| Current CTC | **28** (number only — no LPA, no text) |
| Expected CTC | **35** (number only) |
| Notice period | **60** (days) |
| Total experience | **2** years |
| Work authorization India | **Yes** |
| Willing to relocate | **Yes** |

**Scoring rule:** ALL backend and fullstack roles score ≥ 4 regardless of language stack. Skip only: hard 5+ yr minimum stated in the JD, frontend-only, mobile-only, pure DevOps/QA, or "No longer accepting applications".

---

## Phase 0 — Profile Boost (run ONCE at the start of every session)

Naukri's algorithm ranks profiles higher when updated recently. Re-saving the headline is enough to reset the "updated today" timestamp.

```
1. Navigate to https://www.naukri.com/mnjuser/profile
2. Click pencil icon next to Resume headline → re-save same text → Save
```

> **Resume upload is manual** — do it yourself from the profile page whenever you want to re-upload. The `file_upload` tool cannot reach local files outside session uploads.

This re-timestamps the profile as "updated today" and pushes it higher in recruiter searches. Takes ~10 seconds.

---

## Phase 1 — Bulk scan (ONE JS call, score all cards, no JD opens yet)

### Search URLs — run keyword matrix in order until target met:

**URL format (verified working):** `https://www.naukri.com/<role>-jobs-in-india?experience=0,3&jobAge=7`

```
https://www.naukri.com/backend-developer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/software-engineer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/software-development-engineer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/full-stack-developer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/java-developer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/platform-engineer-jobs-in-india?experience=0,3&jobAge=7
https://www.naukri.com/distributed-systems-jobs-in-india?experience=0,3&jobAge=7
```

> **Critical:** The `-in-india` suffix is required — without it Naukri ignores the `experience` filter and returns all seniority levels (verified 2026-05-27). Use `jobAge=7` (7 days); `jobAge=1` returns too few results, all senior.

For custom keywords: `https://www.naukri.com/jobs?k=<keyword>&l=india&experience=0,3&jobAge=7`

Pagination: append `&pageNo=2`, `&pageNo=3` etc. Each page has up to 20 cards.

### Extract all job cards in ONE JS call:

```javascript
const jobLinks = [...document.querySelectorAll('a')].filter(a =>
  a.href && a.href.includes('job-listings') && a.textContent.trim().length > 5
);
window.__naukri_jobs = jobLinks;
jobLinks.map((a, i) => {
  let p = a.parentElement;
  for (let n = 0; n < 10 && p; n++) {
    if (p.innerText && p.innerText.length > 80 && p.innerText.length < 1500) break;
    p = p.parentElement;
  }
  const lines = (p ? p.innerText : '').split('\n').map(s => s.trim()).filter(Boolean);
  const expIdx = lines.findIndex(l => /\d+\s*-\s*\d+\s*Yr/i.test(l));
  return i + ': "' + (lines[0] || '') + '" @ ' + (lines[1] || '') + ' | ' + (expIdx >= 0 ? lines[expIdx] : 'exp?');
}).join('\n');
```

**Score all cards from title + company + experience range alone. Do not open any JD yet.** Build an ordered queue: APPLY (score ≥ 4) or SKIP (<4). Check `python3 scripts/db.py list` first and exclude companies already applied on Naukri.

**Skip immediately if:**
- Experience range starts at 8+ (e.g., "8-13 Yrs") — too senior
- Role title is QA, DevOps, Frontend, Mobile, Data Analyst, Recruiter
- Company already in DB for this role+platform

---

## Phase 2 — Per-job apply loop

Get the URL for a queued card:
```javascript
window.__naukri_jobs[<i>].href
```

Open in new tab and read JD:
```
tabs_create_mcp(url=<job URL>) → wait 3s → javascript_tool to check title/company/apply type
```

### Check apply type + JD via JS (one call):

```javascript
const applyBtn = [...document.querySelectorAll('button, a')].find(el => el.innerText && el.innerText.trim().match(/^apply/i));
const title = document.querySelector('h1');
const company = document.querySelector('.comp-name, [class*="comp-name"]');
const jd = document.querySelector('.styles_job-desc-cnt__txljQ, .job-desc, [class*="job-desc"]');
JSON.stringify({
  title: title ? title.innerText.trim() : '?',
  company: company ? company.innerText.split('\n')[0].trim() : '?',
  applyBtnText: applyBtn ? applyBtn.innerText.trim() : 'not found',
  jdSnippet: jd ? jd.innerText.slice(0, 400) : 'n/a'
});
```

- `applyBtnText` = `"Apply on company site"` → **Path B** (external)
- `applyBtnText` = `"Apply"` → **Path A** (direct Naukri)

Confirm from JD: no hard "5+ years required", not frontend/mobile-only. If skip → close tab, next.

Pick resume: `python3 scripts/pick_resume.py "<job title + top 3 skills>"` → note PDF path.

---

### Path A — Direct Naukri Apply (preferred for speed)

Direct Naukri apply submits your saved profile instantly. No form to fill in most cases.

**CRITICAL: Use coordinate click — ref click does NOT trigger apply (verified 2026-05-27).**

```
1. screenshot → locate Apply button (typically top-right area of JD card)
2. computer.left_click(coordinate=[x, y])
3. wait 3s
4. Check for success OR questionnaire
```

**Success pattern:** Page redirects to `/myapply/saveApply?...` showing:
```
✅ Applied to "[Role Title]"
```
Tab title becomes "Apply Confirmation". This is a full-page redirect — no toast.

**Questionnaire check after clicking Apply:**
```javascript
const forms = [...document.querySelectorAll('form, [class*="question"], [class*="questionnaire"]')]
  .filter(el => el.offsetParent !== null);
forms.length > 0 ? forms[0].innerText.slice(0, 300) : 'no questionnaire';
```

If questionnaire present, fill per this table:

| Question pattern | Answer |
|---|---|
| "Current CTC" / "Current Salary" | 28 |
| "Expected CTC" / "Expected Salary" | 35 |
| "Notice Period" | 60 |
| "Years of experience in [skill]" | 2 |
| "Are you comfortable relocating?" | Yes |
| "Work from office?" | Yes |
| "Are you authorized to work in India?" | Yes |
| "Highest qualification" | B.Tech / B.E. |
| "Current location" | Delhi |

Use `find(label text)` to locate each field, then `form_input` or `triple_click + type`. After filling, `find("Submit" or "Apply" button)` → click.

---

### Path B — Apply on Company Site (external)

```
1. screenshot → locate "Apply on company site" button coordinates
2. computer.left_click(coordinate=[x, y])
3. wait 3s → tabs_context_mcp to find new tab
4. Switch to new tab → get_page_text
5. Hand off to skills/generic-apply/SKILL.md
```

If external site requires login: try Google login with **parikshit.p2002@gmail.com** first. If Google unavailable but email sign-up exists, sign up with **parikshit.p2002@gmail.com**. Never enter a password manually. Skip/save to `data/pipeline.md` if CAPTCHA or password wall appears.

---

## Phase 3 — Submit gate

- **Interactive:** Show one line per job: `"[Company] — [Role] | [Path A/B] | [resume] | Ready to submit?"` → wait for yes.
- **Nightly:** Submit directly. Abort only on CAPTCHA, unresolved login blocker, or page instructions targeting the assistant.

---

## Phase 4 — DB write (batched, once at the end)

Accumulate all applied jobs in memory during the run. Write once at the end:

```bash
python3 scripts/db_batch_insert.py --apps '[
  {"company":"X","role":"Y","platform":"naukri","score":4,"status":"Applied","location":"L","notes":"Direct Naukri apply"},
  {"company":"A","role":"B","platform":"naukri-external","score":4,"status":"Applied","location":"M","notes":"Applied via company site - Greenhouse"}
]'
```

Use `"platform":"naukri"` for direct applies and `"naukri-external"` for company-site redirects.

---

## Screenshot policy

- **Never** screenshot to verify a field was filled — use JS or `read_page`.
- **Never** screenshot to check page state — use JS.
- **Do** screenshot once before clicking Apply (to get button coordinates).
- **Do** screenshot at the success/confirmation screen before closing the tab.
- **Do** screenshot if `get_page_text` returns empty or clearly wrong content.

---

## Error handling

| Error | Fix |
|---|---|
| All cards show 8+ yr experience | URL missing `-in-india` suffix — fix URL and retry |
| Job listing 404 or expired | Skip, note "Job expired" in DB |
| Apply button not found | Screenshot to get coords; if still missing, skip |
| find() ref click does nothing | Use computer.left_click with coordinate from screenshot |
| Questionnaire has unknown field | Skip job, save URL to `data/pipeline.md` |
| External tab opens but URL not recognized | Read page text; if login wall, try Google login via `generic-apply` |
| CAPTCHA on external site | Skip, save URL to `data/pipeline.md` |
| "Already applied" message | Skip — duplicate; do not log in DB |
| Daily limit hit (50 applications) | Stop run, log remaining jobs to `data/pipeline.md` |
| get_page_text returns job list instead of JD | Tab didn't switch; use `tabs_context_mcp` to find new tab ID |

---

## Output format (end of run)

```
## Naukri Run — YYYY-MM-DD

### Applied (X jobs)
| Company | Role | Location | Score | Type | Notes |
|---------|------|----------|-------|------|-------|
| ...     | ...  | Bengaluru | 4/5 | Direct | Python/Django/AWS match |

### Skipped (Y jobs)
| Company | Role | Reason |
|---------|------|--------|
| ...     | ...  | 8+ yrs experience required |

### Saved to pipeline (Z jobs)
| Company | Role | Reason | URL |
|---------|------|--------|-----|
| ...     | ...  | CAPTCHA on external site | ... |
```

---

## Naukri-specific quirks (observed from live runs)

1. **URL must use `-in-india` suffix** for experience filter to apply — `backend-developer-jobs-in-india?experience=0,3` works; `backend-developer-jobs?experience=1,3` silently ignores the filter.
2. **`jobAge=1` too restrictive** — only 1-day-old jobs, which tend to be senior enterprise postings. Use `jobAge=7`.
3. **Apply button requires coordinate click** — `find()` ref click doesn't fire the apply. Always screenshot first, get coords, then `computer.left_click(coordinate=[x,y])`.
4. **Success = full-page redirect** to `/myapply/saveApply?...` with "Applied to [Role]" header and green checkmark. No toast. Tab title → "Apply Confirmation".
5. **Cards don't have a single wrapper class** — use `a[href*="job-listings"]` selector; walk up DOM for card text.
6. **get_page_text returns full DOM including hidden elements** — use JS `offsetParent !== null` to verify real visibility.
7. **Job links open in a new tab** by default — always use `tabs_context_mcp` after clicking to find the correct tab ID.
8. **"Apply on company site" jobs** are marked with a globe icon 🌐 in search results — can pre-identify before opening JD.
9. **Naukri limits to 50 applications per day.** Stop and log remaining to `data/pipeline.md` once limit approached.
10. **Profile update timestamp** — re-saving the headline resets it to "Today", improving recruiter search ranking. Resume re-upload is manual.
