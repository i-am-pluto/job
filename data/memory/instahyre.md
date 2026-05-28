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

## Avoid Rules Confirmed

- Skip any card showing 5+ year minimum (e.g. "5 - 9 years") — confirmed Infosys Java Developer Guwahati.
- Location Guwahati not in preferred/open list but still valid India location; only skip if hard experience mismatch.

## Pagination

- 141 Interested jobs, 30 per page, no visible "Next" button — uses scroll-based lazy load or URL pagination parameter.
- URL pattern: `?matching=true&status=1` loads Interested queue; `status=0` for Undecided; `status=2` for Not Interested.
