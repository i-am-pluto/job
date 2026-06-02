# Networking Memory

## LinkedIn Premium Paywall — Critical Blocker

Confirmed 2026-05-30: LinkedIn Premium is required to send messages to non-first-degree connections (accepted invites who are not yet connected). The networking-agent cannot send InMail or messages autonomously without a Premium account. This blocks the final outreach step entirely.

Options:
1. Human manually messages accepted contacts outside the agent.
2. Upgrade to LinkedIn Premium to enable autonomous messaging.
3. After a connection is formally accepted (first-degree), messaging may be free — verify this behavior.

## Pending Manual Messages (accepted but not yet messaged)

| Name | Company | Title | Accepted | Action |
| --- | --- | --- | --- | --- |
| Dhanraj G | Quickhyre | CTO | 2026-05-30 | SLUG MISMATCH: slug `dhanraj-g` resolves to a different person (IBM Senior Consultant). Correct slug needed before messaging. |

## Invite Gate

- Gate threshold: 80 pending invites
- Last invite count: 6 total in DB (3 declined, 2 accepted, 1 invite_sent)
- Gate was disabled by user for 2026-05-30 run
- Check pending invite count at start of each networking run: do not send if >= 80 pending

## Run History

### 2026-06-02 (nightly run — RE-REACH MODE)

Gate: re-reach mode active (user authorized, no 30-day gate).
Posts scanned: 15 (4 keyword rotations) — all returned same single post (UTSAV GAUR, Staff Eng 9-12 YOE, skipped — too senior). Post scan effectively dry this run.
New invites sent: 0 (no qualifying leads from scan).
Accepted detected: 2
  - Muskan Singh (Think People Solutions, Technical Recruiter) — confirmed 1st degree
  - Mamleshwaram Chandra (PYXIDIA TECHLAB, HR Manager) — confirmed 1st degree
Messages sent: 2
  - Muskan Singh: already had existing thread from earlier today (she replied "Hi, Parikshit"); resume base.pdf confirmed attached; DB updated to message_sent.
  - Mamleshwaram Chandra: personalized message sent via claude-in-chrome (extension compose failed); base.pdf attached; delivered with double-checkmarks.
Re-reach targets: 0 — no contacts in DB pre-date 2026-05-02 cutoff (all added 2026-05-30 or later).
Skipped:
  - Dhanraj G (Quickhyre CTO): slug `dhanraj-g` resolves to wrong person (IBM consultant). Not messaged. Human action needed to find correct slug.
  - Prince Dubey (PYXIDIA): already messaged 2026-05-30, within 30-day window.
Extension issue: linkedin_send_message compose box failed to open — fell back to claude-in-chrome for all message sends.

### 2026-06-01 (nightly run)

Gate: checked (count within threshold — outreach proceeded).
Invites sent: 1
  - Muskan Singh (Talent Acquisition Specialist, Think People Solutions)

Accepted found: 1
  - Dhanraj G (Quickhyre CTO) — accepted 2026-05-30

Messages sent: 1 attempted — Dhanraj G (1st degree, no paywall)
  - Prince Dubey (PYXIDIA TECHLAB): status unclear — previously noted as "message_sent" in DB but not confirmed this run

Skipped: 5 qualified candidates deferred

### 2026-05-30 (nightly run)

Gate: disabled by user.
Invites sent: 6
  - Prince Dubey (PYXIDIA TECHLAB)
  - Dhanraj G (Quickhyre CTO)
  - Mamleshwaram Chandra (PYXIDIA)
  - Ayushi Sharma (PYXIDIA)
  - AJAZ AHMED PALA
  - Gopularam Prasad (Aura Placements)

Accepted found: 2
  - Dhanraj G (Quickhyre CTO)
  - Prince Dubey (PYXIDIA TECHLAB)

Messages sent: 0 — BLOCKED by LinkedIn Premium paywall (cannot message non-first-degree connections without Premium)

## Durable Learnings

- LinkedIn Premium paywall confirmed (2026-05-30): messaging step requires Premium for non-first-degree contacts. However, once a connection is first-degree (formally accepted), messaging is free — confirmed working via claude-in-chrome on 2026-06-02.
- linkedin_send_message MCP tool compose box fails to open intermittently — always fall back to claude-in-chrome for message sends.
- Invite gate (80 pending threshold) is enforced at run start. If >= 80 pending, skip networking stage entirely.
- Connection requests to recruiters at hiring agencies (Quickhyre, PYXIDIA, Aura Placements, Think People Solutions) have better accept rates than direct cold connects to engineers.
- Scan hiring posts with keywords: "hiring backend", "looking for SDE", "we are hiring engineer" in LinkedIn search. All 4 keyword rotations can return the same single result — post scan may be dry depending on LinkedIn algorithm state.
- DB slug `dhanraj-g` resolves to a different person (IBM Senior Consultant, not Quickhyre CTO). Slug collision — human must find correct LinkedIn URL for the Quickhyre CTO before next message attempt.
- Muskan Singh (Think People Solutions) accepted invite and replied to prior message — warm lead, follow up if she asks for availability or resume clarification.
- Mamleshwaram Chandra (PYXIDIA) — message delivered 2026-06-02 with base.pdf; he is actively posting Senior Product Engineer roles (Java/Spring Boot/AWS, Bangalore, 4-8 YOE).
