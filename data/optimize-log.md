# Skill Optimization Log

Each nightly run appends one line per change made to skill files.
Format: YYYY-MM-DD: [skill file] — [what changed and why]

---

2026-05-26: Initial log created. Key learnings from first live run documented in instahyre/SKILL.md and linkedin/SKILL.md.
2026-05-26: Instahyre: documented auto-advance + popup-overlay pattern. LinkedIn: documented synthetic-click failure, Save-this-application interstitial, lazy-load limit. CLAUDE.md: added rules 11-14 for DB temp fallback, LinkedIn click failure, interstitial bypass, lazy-load limit. db_batch_insert.py: added /tmp/jobdb fallback path.
2026-05-26: LinkedIn/Instahyre/Generic Apply: made company careers/ATS via generic-apply the preferred route over in-platform apply; login blockers now try Google with the email from profile.md, then passwordless/email sign-up with the same address before skipping.
2026-05-27: LinkedIn — if the scheduled Codex session has no callable in-app browser/Chrome tool, stop immediately, log 0 LinkedIn applications, and do not attempt a web-only fallback because the logged-in session cannot be accessed.
