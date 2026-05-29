# LinkedIn Agent Memory

Keep durable LinkedIn keyword performance, click behavior, and blocker notes here. Do not store profile facts.

## Current Notes

- Use `skills/linkedin/SKILL.md` as the workflow authority.
- Nightly LinkedIn is a bounded fallback only: 3-5 Easy Apply applications after Naukri and Instahyre if budget remains.
- External/company-site LinkedIn flows require explicit budget; otherwise skip or save without following.
- Do not run LinkedIn status checks during nightly runs.
- Easy Apply needs real browser clicks; synthetic `element.click()` does not reliably open the modal.
- Close "Save this application?" with the popup card `×`, not Discard.

## CRITICAL: Score-All-Before-Apply Rule (added 2026-05-29)

DO NOT open any individual job card until ALL visible cards on the results page have been scored. Workflow:

1. Run `read_page` or `get_page_text` on the search results page.
2. Score every visible card against profile rules (backend/fullstack >= 4).
3. Build an ordered apply list ranked by score descending.
4. Only then begin opening cards, starting from the top of the list.

The 2026-05-29 failure: agent opened the first card (G-P Staff AI Fullstack) without pre-scoring the page, got stuck in a Greenhouse modal for 47 tool calls, and exhausted the entire LinkedIn budget before seeing any other jobs. Pre-scoring prevents single-card budget traps.

## CRITICAL: Greenhouse-Inside-LinkedIn Detection (added 2026-05-29)

Some LinkedIn "Easy Apply" buttons do NOT submit natively — they open an embedded Greenhouse application modal inside the LinkedIn page. This looks identical to a normal Easy Apply flow until the form renders.

Detection signals (check before spending tool calls on submission):
- Modal title shows "Apply to [Company]" with a Greenhouse-style multi-step form
- URL inside the modal includes `greenhouse.io` or `boards.greenhouse.io`
- Form has "Step 1 of N" progress indicator with fields beyond basic contact info (resume upload, cover letter, custom questions)
- Network requests (via `read_network_requests`) include `boards.greenhouse.io`

Action when detected:
1. Do NOT attempt to submit through the LinkedIn modal. It will fail or require resume upload steps that exhaust budget.
2. Save the job to `data/pipeline.md` with a note: "Greenhouse-inside-LinkedIn — apply via greenhouse skill directly."
3. Extract the Greenhouse board token from the URL if visible (pattern: `boards.greenhouse.io/{token}/jobs/{id}`).
4. Add the board token to `config/greenhouse_boards.yml` if not already present (mark `added_by: spillover`).
5. Move to the next job in the pre-scored list.

Budget cost: detection + save should take 3-4 tool calls maximum. Do not spend more than 5 tool calls on a single job before moving on.

## CRITICAL: Per-Job Budget Cap (added 2026-05-29)

Maximum tool calls per LinkedIn job: 10.
- If a job has not reached a submitted/saved state after 10 tool calls, save it to pipeline and move on.
- Do not let a single stuck job consume the entire LinkedIn budget.
- The LinkedIn stage budget is 12 tool calls total for 3-5 jobs. Plan accordingly: ~3 tool calls for page scan + scoring, ~8 tool calls for up to 2 Easy Apply submissions.

## Keyword Performance (updated 2026-05-29)

| Keyword | Scanned | Applied | Blocked | Easy Apply rate | Notes |
| --- | ---: | ---: | ---: | --- | --- |
| Backend Engineer (India) | 21 | 0 | 21 | ~0% | Run stopped before submit; large-co dominated |
| Java backend | 400+ | 0 | 0 | ~1% | Only 3 scored jobs out of 400+ results; too broad |
| software engineer Java India | 0 | 0 | 0 | unknown | Not yet tried |
| senior SDE India | 0 | 0 | 0 | unknown | Not yet tried |
| fullstack engineer India | 0 | 0 | 0 | unknown | Not yet tried |

Preferred keywords for next run (Easy Apply yield estimated higher):
1. "Backend Developer India" — more SME/startup skew than "Backend Engineer"
2. "SDE2 India" or "Senior Software Developer India" — product company skew
3. "Java Spring Boot developer India" — specific stack, lower competition
4. "Node.js developer India" — expand stack coverage
5. "fullstack developer India" — Easy Apply often higher on fullstack roles

Avoid broad keywords like "Java backend" (400+ results, mostly external apply, 1% Easy Apply rate). Prefer narrower phrases that surface product-company job posts.

## Durable Learnings

- 2026-05-28: Memory initialized for plugin install. Replace with measured keyword yield after the next run.
- 2026-05-28: LinkedIn "Backend Engineer India" keyword yields ~21 visible cards after real scroll (7 visible initially, 14 more after 2 scrolls). Cards 8+ do not populate via JS scroll — only real `computer.scroll` loads them.
- 2026-05-28: LinkedIn-embedded Greenhouse modal ("Apply to Precisely"): modal height is fixed ~640px and the Next button is hidden below the fold. Window resize to 1100px does not help (screenshot tool still returns 812px viewport). Tab key from last field reaches the Next button — but this is the Greenhouse-inside-LinkedIn pattern; should save and skip instead of fighting the modal.
- 2026-05-28: "Save this application?" interstitial correctly dismissed with × (top-right of popup card). Modal stays open after × click.
- 2026-05-28: LinkedIn Apply button (aria-label "LinkedIn Apply to this job") — real clicks from `computer.left_click` with coordinates required; JS `element.click()` fails.
- 2026-05-28: Keyword "Backend Engineer India" returns large-company dominated results (Honeywell, Amazon, NVIDIA, Deloitte, TransUnion, CrowdStrike, Docusign, Motorola) — mostly external apply, few Easy Apply. Better keywords for Easy Apply yield: try "Backend Developer" or "SDE2" next run.
- 2026-05-28: Run skipped by user instruction mid-way. 15 qualified jobs saved to data/pipeline.md for manual follow-up or next run.
- 2026-05-29: G-P Staff AI Fullstack (score 5) confirmed Greenhouse-inside-LinkedIn pattern. Agent spent 47 tool calls attempting to submit through the LinkedIn modal before exhausting the budget. This is a known recurring LinkedIn-Greenhouse integration trap. See detection rules above.
- 2026-05-29: "Java backend" keyword (400+ results) produced only 3 scoreable jobs — extremely poor yield. The broad keyword is the root cause. Switch to narrower, startup-skewed keywords.
