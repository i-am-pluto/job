# Instahyre Agent Memory

Keep durable Instahyre selectors, popup behavior, and run learnings here. Do not store profile facts.

## Current Notes

- Use `skills/instahyre/SKILL.md` as the workflow authority.
- Check popup visibility with JavaScript `offsetParent !== null`; hidden DOM text is not reliable.
- After Apply, inspect whether the card count dropped before assuming success.

## Keyword And Role Signals

- Backend, fullstack, platform, distributed systems, data platform, cloud backend, and AI-backend roles are eligible when score is 4 or 5.

## Durable Learnings

- 2026-05-28: Memory initialized for plugin install. Replace with measured selectors and blocker notes after the next run.
- 2026-05-28 (run 2): matching=true&status=0 (Undecided) showed 0 cards. All new matching opportunities were already processed earlier in the nightly run. The "Interested" queue (status=1) had 141 jobs; 30 were shown on page 1. 24 were already applied in the prior session invocation (showed as "Applied today" in card DOM). 1 card (Infosys - Java Developer, Guwahati) was unapplied but skipped due to 5-9 year hard minimum (profile rule: skip 5+ year hard min).
- 2026-05-29 (nightly run): Matching queue still empty at 09:40 UTC+5:30. No new matching opportunities overnight. Previous session (2026-05-28) had 25 applications approved, bringing total Instahyre applications to 25 for the day. Next refresh expected same time next day.
- 2026-05-29 (nightly run, second check): Matching=true queue (Undecided, status=0) shows 0 cards at time of nightly agent run. Interested queue (status=1) has 187 pre-decided jobs. Per CEO rule: do not apply from Interested queue when Undecided is empty — would create duplicates. Instahyre matching queue refresh is async and rate-limited; no further applications possible until next queue refresh window.

## Selector Notes

- "View »" buttons: `Array.from(document.querySelectorAll('button, a')).filter(b => /^view\s*»?$/i.test(b.textContent.trim()) && b.offsetParent !== null)`
- "Applied today" detection: look for `/applied today/i` in parent element `.innerText` — reliable without modal open.
- Modal visibility: `document.querySelector('[class*="modal"]').offsetParent !== null` — check before clicking Apply.
- Apply button: `Array.from(document.querySelectorAll('button')).filter(b => /^apply$/i.test(b.textContent.trim()) && b.offsetParent !== null)`
- After Apply: check `__opp_cards.length` drop to verify application succeeded.

## Popup Behavior

- "Similar jobs" Cancel closes the main modal — must click View » manually for next card.
- "Are you actively looking" Cancel: separate button, do not batch with "similar jobs" Cancel.
- "No thanks, I want to continue as non-premium" link for premium popup.
- Startup: page shows "Fetching" briefly on load; wait for Instahyre DOM to populate before scanning cards.

## Queue Exhaustion Pattern

- 2026-05-28 (run 3 — second session): After 25 applications submitted in the same day's earlier sessions, the `matching=true` (Undecided) queue shows "No matching opportunities found :( Undecided (0)". This is normal — Instahyre refreshes the matching queue asynchronously. No rate-limit or cap error; queue is simply empty. No further applications possible in same-day session.
- 2026-05-29 (nightly run): Matching queue still empty at 09:40 UTC+5:30. No new matching opportunities overnight. Previous session (2026-05-28) had 25 applications approved, bringing total Instahyre applications to 25 for the day. Next refresh expected same time next day.
- 2026-05-29 (nightly run, final): Matching queue (Undecided/status=0) confirmed empty with 0 cards. Interested queue (status=1) has 187 pre-decided jobs. Per CEO guidance: do NOT apply from Interested to avoid duplicates. Instahyre matching queue refresh is scheduled asynchronously and not under agent control. No further Instahyre applications possible until queue refreshes (estimated next 24h).

## Avoid Rules Confirmed

- Skip any card showing 5+ year minimum (e.g. "5 - 9 years") — confirmed Infosys Java Developer Guwahati.
- Location Guwahati not in preferred/open list but still valid India location; only skip if hard experience mismatch.

## Pagination

- 141 Interested jobs, 30 per page, no visible "Next" button — uses scroll-based lazy load or URL pagination parameter.
- URL pattern: `?matching=true&status=1` loads Interested queue; `status=0` for Undecided; `status=2` for Not Interested.
