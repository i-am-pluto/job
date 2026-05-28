# Naukri Agent Memory

Keep durable Naukri selectors, keyword performance, apply path behavior, and blocker notes here. Do not store profile facts.

## Current Notes

- Use `skills/naukri/SKILL.md` as the workflow authority.
- Primary workflow is `scripts/naukri_noperi_apply.py`, backed by vendored NopeRi APIs. Requires `NAUKRI_USERNAME` / `NAUKRI_PASSWORD` env vars — not yet set. Set these in `.env` to enable API path.
- Nightly workflow must use the NopeRi adapter only; browser/Chrome scanning is manual troubleshooting.
- Skip external company-site redirects by default to avoid low-value commercial redirect floods.
- Ignore commercial notification noise such as NVites/profile views; only recruiter messages and concrete application outcomes are actionable.

## Browser Apply Mechanics (confirmed 2026-05-28)

- **Apply button**: use `find("Apply button")` → `scroll_to(ref)` → `left_click(ref)`. Coordinate clicks miss due to chatbot overlay.
- **Chatbot overlay** (`DIV.chatbot_Overlay.show`) intercepts coordinate clicks. Dismiss first via JS: `document.querySelector('.chatbot_Overlay').style.pointerEvents='none'` — but `ref`-based clicks via the MCP tool bypass this automatically.
- **Success**: page redirects to `/myapply/saveApply?...&multiApplyResp={"jobId":200}` — HTTP 200 = applied.
- **Questionnaire failure**: same redirect but `multiApplyResp={"jobId":406}` — required questionnaire not filled; application NOT submitted.
- **External redirect**: button text is "Apply on company site" not "Apply" — save to `data/pipeline.md`.
- **Already applied**: no Apply button found, shows "Applied" status indicator.

## Keyword Performance (2026-05-28 run)

| Keyword | Scanned | Applied | Blocked | Notes |
| --- | ---: | ---: | ---: | --- |
| backend developer | 20 | 1 | ~10 | High external-redirect rate (~50%); questionnaire blocks ~25% |
| java developer | 0 | 0 | 0 | Not scanned this run (stopped early). |
| software engineer | 0 | 0 | 0 | Not scanned this run (stopped early). |

## Durable Learnings

- 2026-05-28: API adapter blocked — no credentials in env. Browser fallback used.
- 2026-05-28: NopeRi deps installed (`requests`, `httpcloak`, `pycryptodome`, `python-dotenv`, `colorama`) via pip. Set `NAUKRI_USERNAME`/`NAUKRI_PASSWORD` in `.env` to unlock API path for future runs.
- 2026-05-28: "Backend developer" search (experience=0-3, jobAge=7): 20 results, ~10 external, ~5 questionnaire-blocked (406), ~5 no-questionnaire direct applies possible.
- 2026-05-28: Questionnaire jobs often ask Node.js/Python/FastAPI years — profile has 2 years Python, but questionnaires offer only 3+ options; these become 406 blocks. Cannot answer truthfully.
- 2026-05-28: Run stopped early by user. Applied: 1 (IDESLABS BackEnd Developer, 200 OK). 5 saved to pipeline as external.
