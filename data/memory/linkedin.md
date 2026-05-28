# LinkedIn Agent Memory

Keep durable LinkedIn keyword performance, click behavior, and blocker notes here. Do not store profile facts.

## Current Notes

- Use `skills/linkedin/SKILL.md` as the workflow authority.
- Nightly LinkedIn is a bounded fallback only: 3-5 Easy Apply applications after Naukri and Instahyre if budget remains.
- External/company-site LinkedIn flows require explicit budget; otherwise skip or save without following.
- Do not run LinkedIn status checks during nightly runs.
- Easy Apply needs real browser clicks; synthetic `element.click()` does not reliably open the modal.
- Close "Save this application?" with the popup card `x`, not Discard.

## Keyword Performance

| Keyword | Scanned | Applied | Blocked | Notes |
| --- | ---: | ---: | ---: | --- |
| Backend Engineer (India) | 21 | 0 | 21 | Run stopped by user before any submission |
| software engineer Java India | 0 | 0 | 0 | Not reached this run |
| senior SDE India | 0 | 0 | 0 | Not reached this run |
| fullstack engineer India | 0 | 0 | 0 | Not reached this run |

## Durable Learnings

- 2026-05-28: Memory initialized for plugin install. Replace with measured keyword yield after the next run.
- 2026-05-28: LinkedIn "Backend Engineer India" keyword yields ~21 visible cards after real scroll (7 visible initially, 14 more after 2 scrolls). Cards 8+ do not populate via JS scroll — only real `computer.scroll` loads them.
- 2026-05-28: LinkedIn-embedded Greenhouse modal ("Apply to Precisely"): modal height is fixed ~640px and the Next button is hidden below the fold. Window resize to 1100px does not help (screenshot tool still returns 812px viewport). Tab key from last field reaches the Next button — should press Enter after Tab to submit.
- 2026-05-28: "Save this application?" interstitial correctly dismissed with × (top-right of popup card). Modal stays open after × click.
- 2026-05-28: LinkedIn Apply button (aria-label "LinkedIn Apply to this job") opens an in-page Greenhouse-embedded modal, not a new tab. Contact info pre-fills from profile (name, phone, email). Location (city) field requires autocomplete selection from dropdown — type city name, wait for dropdown, click first option.
- 2026-05-28: Keyword "Backend Engineer India" returns large-company dominated results (Honeywell, Amazon, NVIDIA, Deloitte, TransUnion, CrowdStrike, Docusign, Motorola) — mostly external apply, few Easy Apply. Better keywords for Easy Apply yield: try "Backend Developer" or "SDE2" next run.
- 2026-05-28: Run skipped by user instruction mid-way. 15 qualified jobs saved to data/pipeline.md for manual follow-up or next run.
