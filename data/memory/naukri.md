# Naukri Agent Memory

Keep durable Naukri selectors, keyword performance, apply path behavior, and blocker notes here. Do not store profile facts.

## Current Notes

- Use `skills/naukri/SKILL.md` as the workflow authority.
- Primary workflow is `scripts/naukri_noperi_apply.py`, backed by vendored NopeRi APIs. Requires `NAUKRI_USERNAME` / `NAUKRI_PASSWORD` env vars — set these in `.env` to enable API path.
- Nightly workflow must use the NopeRi adapter only; browser/Chrome scanning is manual troubleshooting.
- Skip external company-site redirects by default to avoid low-value commercial redirect floods.
- Ignore commercial notification noise such as NVites/profile views; only recruiter messages and concrete application outcomes are actionable.

## Dupe-Check Rule (CRITICAL — updated 2026-05-29)

Run `python3 scripts/db.py list` BEFORE each NopeRi batch submission, not just once at the start of the run. The DB may have been written to by an earlier platform agent in the same nightly run. Re-reading the dup list ensures Naukri does not attempt a company+role already inserted mid-run by another agent.

Pattern that caused the Sandhata miss: dup list was read at plan time, Naukri agent applied Sandhata, then db_batch_insert correctly skipped it — but the agent still ATTEMPTED it and wasted a slot. The fix is to re-read db.py list right before building the NopeRi submission batch, not just at plan-generation time.

## Keywords To Use (updated 2026-05-29)

Retire: "Java developer" — too generic; surfaces walk-in events (TCS, Nustar), LAMP/PHP stacks, and infra-heavy roles. Wastes quota.

Use these in order:
1. "Java backend" — higher signal-to-noise for backend API roles
2. "Spring Boot" — product-company microservices roles
3. "backend engineer" — startup and mid-size product companies
4. "platform engineer" — distributed systems, infra-adjacent backend
5. "Node.js backend" — fullstack-adjacent backend roles
6. "Python backend" — data-adjacent backend roles (use if slots remain after above)

Walk-in event jobs (TCS, Infosys mass hiring drives, "Nustar walk-in") score 4 per profile rules but are lower-value targets. If quota is not met after running quality keywords, walk-in roles are acceptable. If quota is met, skip walk-in roles.

## Keyword Performance (cumulative)

| Keyword | Scanned | Applied | Blocked | Quality | Notes |
| --- | ---: | ---: | ---: | --- | --- |
| backend developer | 43 | 4 | ~11 | Medium | External-redirect rate ~65%; questionnaire blocks ~25% |
| Java developer | 43 | 0 | 0 | Low | Walk-ins, LAMP roles, generic mass-hiring; do not reuse |

## Browser Apply Mechanics (confirmed 2026-05-28)

- **Apply button**: use `find("Apply button")` → `scroll_to(ref)` → `left_click(ref)`. Coordinate clicks miss due to chatbot overlay.
- **Chatbot overlay** (`DIV.chatbot_Overlay.show`) intercepts coordinate clicks. Dismiss first via JS: `document.querySelector('.chatbot_Overlay').style.pointerEvents='none'` — but `ref`-based clicks via the MCP tool bypass this automatically.
- **Success**: page redirects to `/myapply/saveApply?...&multiApplyResp={"jobId":200}` — HTTP 200 = applied.
- **Questionnaire failure**: same redirect but `multiApplyResp={"jobId":406}` — required questionnaire not filled; application NOT submitted.
- **External redirect**: button text is "Apply on company site" not "Apply" — save to `data/pipeline.md`.
- **Already applied**: no Apply button found, shows "Applied" status indicator.

## Durable Learnings

- 2026-05-28: API adapter blocked — no credentials in env. Browser fallback used.
- 2026-05-28: NopeRi deps installed (`requests`, `httpcloak`, `pycryptodome`, `python-dotenv`, `colorama`) via pip. Set `NAUKRI_USERNAME`/`NAUKRI_PASSWORD` in `.env` to unlock API path for future runs.
- 2026-05-28: "Backend developer" search (experience=0-3, jobAge=7): 20 results, ~10 external, ~5 questionnaire-blocked (406), ~5 no-questionnaire direct applies possible.
- 2026-05-28: Questionnaire jobs often ask Node.js/Python/FastAPI years — profile has 2 years Python, but questionnaires offer only 3+ options; these become 406 blocks. Cannot answer truthfully.
- 2026-05-28: Run stopped early by user. Applied: 1 (IDESLABS BackEnd Developer, 200 OK). 5 saved to pipeline as external.
- 2026-05-29: API adapter fully working with credentials in env. Full scan: 43 jobs, 4 direct applies (TCS, Persistent, Sandhata, Nustar walk-in events). External redirect rate ~65% (expected). CTC questionnaire blocks ~12 jobs. Unknown profile fields blocks ~25 jobs (DOB, INFY ID, microservices years, etc.). Base.pdf reused 4x, no tuning needed.
- 2026-05-29: NopeRi adapter stable; no login failures, token generation working. Duplicate detection vs. DB working (Sandhata correctly skipped by db_batch_insert) but agent still ATTEMPTED it — wasted 1 slot. Fix: re-read dup list right before building submission batch.
- 2026-05-29: Walk-in roles (TCS, Nustar) scored 4 and were applied. Lower strategic value than product/startup backend roles but valid fillers when quota not met.
- 2026-05-29: 122 jobs saved to pipeline for manual company-site follow-up. Direct-apply volume expected to remain low. Consider adding expected CTC to profile.md if user wants auto-answer support for CTC questionnaire blocks.
