# Naukri Agent Memory

Keep durable Naukri selectors, keyword performance, apply path behavior, and blocker notes here. Do not store profile facts.

## Current Notes

- Use `skills/naukri/SKILL.md` as the workflow authority.
- Primary workflow is `scripts/naukri_noperi_apply.py`, backed by vendored NopeRi APIs.
- Browser search/apply is fallback only when API login, token, or apply calls fail.
- In browser fallback, use `-in-india` URL suffixes with experience filters; Apply may require coordinate clicks from screenshots.

## Keyword Performance

| Keyword | Scanned | Applied | Blocked | Notes |
| --- | ---: | ---: | ---: | --- |
| backend developer | 0 | 0 | 0 | Initialize after next run. |
| java developer | 0 | 0 | 0 | Initialize after next run. |
| software engineer | 0 | 0 | 0 | Initialize after next run. |

## Durable Learnings

- 2026-05-28: Switched Naukri primary workflow to the NopeRi API adapter. Keep durable notes on API login/token failures, questionnaire misses, and external redirect rates after the next run.
