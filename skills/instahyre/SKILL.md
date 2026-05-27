# Instahyre Job Application Skill

Use Instahyre as a job-discovery source, then prefer applying on the company's own careers/ATS site through `skills/generic-apply/SKILL.md`. Instahyre one-click apply is fallback when no reliable external company-site application path is available or when the company-site path is blocked.

## How Instahyre apply works (observed from live testing)
1. Navigate to `https://www.instahyre.com/candidate/opportunities/?matching=true`
2. Each card shows company, role, location, skills tags, and a **"View »"** button
3. Clicking **View »** opens a modal with the full JD + an **Instamatch score** (HIGH / MEDIUM / LOW)
4. Clicking **Apply** in the modal instantly submits your profile — no additional form
5. A "Share on social media for Premium" popup appears → click the "No thanks" link
6. A "Want to apply to other similar jobs?" popup appears → click **Cancel** (always)
7. Bottom-right shows "Application sent to [Company]!" toast

## Company-site preference

For every strong match, first try to locate and use the company's direct application flow:
- If the modal/JD includes an "Apply on company website", careers URL, ATS link, or external apply link, open it and hand off to `skills/generic-apply/SKILL.md`.
- If no direct link is visible but the company is high quality, briefly check the company website/careers page when it can be found without derailing the run.
- Use Instahyre's one-click **Apply** only after the company-site route is unavailable, unreliable, or blocked.

Login/account blockers on the external site are handled by `generic-apply`: first try Google login with **parikshit.p2002@gmail.com**; if Google login is unavailable but email sign-up exists, sign up with **parikshit.p2002@gmail.com**. Never enter or invent a password manually.

## When this skill triggers
User says anything like: "apply to Instahyre jobs", "find me jobs on Instahyre", "scan Instahyre", "apply to matching jobs", or pastes the Instahyre opportunities URL.

## Prerequisites
- The user must be logged into Instahyre in Chrome
- Use the already-open Instahyre tab (find it via `tabs_context_mcp`); if not open, navigate `https://www.instahyre.com/candidate/opportunities/?matching=true` in an existing tab

## Profile source
Before scoring or applying, read:
- `profile.md` for targeting rules, avoid rules, location preferences, and fit scoring.
- Key rule: ALL backend and fullstack roles score ≥ 4 regardless of language stack.

## Workflow

### Step 1 — Navigate and load jobs
```
navigate → https://www.instahyre.com/candidate/opportunities/?matching=true
```
Use `read_page(filter=all, depth=4)` to get all job cards. This returns the full list without screenshots.

### Step 2 — Dismiss startup popups immediately
Before doing anything else, check for and dismiss these overlays using JavaScript — they block all interactions:

```javascript
// Check which popups are visible (broaden to <a> too for the "No thanks" link)
const cancelBtns = Array.from(document.querySelectorAll('button')).filter(b => b.textContent.trim() === 'Cancel' && b.offsetParent !== null);
const noThanks = Array.from(document.querySelectorAll('a, button')).filter(b => /no thanks/i.test(b.textContent) && b.offsetParent !== null);
cancelBtns.forEach(b => b.click());
noThanks.forEach(b => b.click());
```

**Live snippet — extract & score all cards in ONE call (use this as the canonical scan):**
```javascript
const cards = Array.from(document.querySelectorAll('button, a')).filter(b => /^view\s*»?$/i.test(b.textContent.trim()) && b.offsetParent !== null);
window.__opp_cards = cards;
cards.map((c, i) => {
  let p = c.closest('li, div, article'); let n = 0;
  while (p && n < 8) { if (p.innerText && p.innerText.length > 50 && p.innerText.length < 2000) break; p = p.parentElement; n++; }
  const lines = (p ? p.innerText : '').split('\n').map(s=>s.trim()).filter(s=>s);
  return `${i}: ${lines[0]||''} [${(lines.find(l=>/job available/i.test(l))||'').replace('Job available in ','')}]`;
}).join('\n')
```

**IMPORTANT:** `get_page_text` returns ALL DOM content including hidden elements — it CANNOT tell you if a popup is visible. Always use JavaScript `offsetParent !== null` to check actual visibility.

Known popups (check visibility via JS before clicking):
- "Are you looking for a job actively?" → Cancel button (ref varies)
- "Want to apply to other similar jobs?" → Cancel button
- "Share on social media for Premium" → "No thanks, I want to continue as non-premium" link

### Step 3 — Score every job up front
From the `read_page` output, score ALL cards 1-5 before opening any modal. Build an ordered plan: APPLY (≥4) or SKIP (<4). Per `profile.md`: all backend and fullstack roles score ≥ 4 regardless of language.

### Step 4 — Apply loop using JavaScript modal inspection

Before clicking Instahyre **Apply**, inspect the visible modal/JD for a company-site, careers, ATS, or external application link. If present, open it in a new tab and hand off to `skills/generic-apply/SKILL.md`. If no external path is available or it is blocked under the skip rules in `generic-apply`, return to the Instahyre modal and use the one-click flow below.

**CRITICAL LEARNINGS from live runs:**

1. **Do NOT use `get_page_text` to check modal state** — it returns hidden DOM content and lies about what's visible. Use JavaScript instead:
   ```javascript
   const modal = document.querySelector('.candidate-apply-modal');
   modal ? modal.innerText.slice(0, 300) : 'no modal'
   ```

2. **The "similar jobs" Cancel click closes the MAIN modal too.** After clicking Cancel on the similar-jobs popup, the main modal is gone. You must manually click `View »` on the next card — the modal does NOT auto-advance after Cancel.

3. **Apply flow per card — single browser_batch (5 actions):**

   The fastest verified pattern. Auto-advance behavior: after the FIRST Apply, the modal auto-advances to the next card AND the "similar jobs" popup overlays it. Track applied jobs by the drop in `__opp_cards.length` between calls.

   ```
   batch [
     a. JS: window.__opp_cards[<idx>].click(); 'View clicked'
     b. JS wait 2s then click Apply: const btns = Array.from(document.querySelectorAll('button')).filter(b => b.offsetParent !== null && /^apply$/i.test(b.textContent.trim())); btns.length ? btns[0].click() : 0
     c. JS wait 2.5s then capture {titles: visible h2/h3, cancelBtns: count of visible Cancel buttons}
     d. JS: cancel similar-jobs popup — c = Array.from(document.querySelectorAll('button')).filter(b => b.textContent.trim() === 'Cancel' && b.offsetParent !== null); c.forEach(b => b.click())
     e. JS wait 1.5s then rebuild __opp_cards and report new count + first 10 titles
   ]
   ```

   **Verification rule:** The card was applied IF and ONLY IF the `__opp_cards.length` dropped by 1 between calls. If the list count is unchanged, the apply was intercepted by the popup — re-open that card manually (click `__opp_cards[<idx>]`) and click Apply a second time.

   **Index tracking:** After each successful apply the list re-indexes. The card currently in the modal is usually the OLD index+1 (auto-advance), so to apply it directly just click Apply (no View click needed). Otherwise click `__opp_cards[<new idx>]` for the next target. ALWAYS rebuild the list from DOM after each Cancel — do not cache stale references.

4. **Never click both "similar jobs Cancel" AND "actively looking Cancel" in the same batch** — the refs may overlap and one will be wrong.

5. **Check for duplicate companies:** Never apply twice to same company+role+platform. If you just applied to "Adobe SDE2" and the next card is also "Adobe SDE2" (different city), skip it.

6. **The Instahyre list shows 30 cards per page.** After exhausting visible cards, check for a "Next" pagination button.

### Step 5 — Track (batched, once at the end)

Do NOT call db.py per job. Keep an in-memory list. At the end, write all at once using:

```bash
python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"instahyre","score":4,"status":"Applied","location":"Bangalore","notes":"..."}]'
```

The DB helpers use a safe temp-copy + lock strategy for mounted SQLite reliability. Never open `data/applications.db` directly, never write one row at a time after each apply, and never retry individual rows after a SQLite error. `db_batch_insert.py --apps` also writes initial `status_history` rows.

## Error handling

| Error | Fix |
|-------|-----|
| Modal doesn't open after View » click | Wait 2s, retry click once |
| `get_page_text` shows popup content but JS shows no visible popup | Ignore — get_page_text includes hidden DOM. Use JS to verify |
| "Dispatch Network" / stuck modal | Refresh page (`navigate → same URL`), re-read card list |
| Similar jobs popup Cancel closes main modal | Expected behavior — click View » on next card manually |
| "Already marked not interested" error | Refresh page — the card list resets to undecided |
| DB disk I/O error | Retry the same DB helper once after `mkdir -p /tmp/jobdb`; do not switch to raw SQLite or per-row writes |

## Output format (end of run)
```
## Instahyre Run — [date]

### Applied (X jobs)
| Company | Role | Location | Score | Notes |
|---------|------|----------|-------|-------|
| ...     | ...  | 4/5      | Java/Kafka match |

### Skipped (Y jobs)
| Company | Role | Reason |
|---------|------|--------|
| ...     | ...  | Duplicate (already applied same company this run) |
```
