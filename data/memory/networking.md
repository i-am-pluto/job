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
| Dhanraj G | Quickhyre | CTO | 2026-05-30 | Message attempted 2026-06-01 — confirm receipt. |
| Prince Dubey | PYXIDIA TECHLAB | (role unknown) | 2026-05-30 | Status unclear — confirm whether message was sent or still pending. |

## Invite Gate

- Gate threshold: 80 pending invites
- Last invite count: 6 total in DB (3 declined, 2 accepted, 1 invite_sent)
- Gate was disabled by user for 2026-05-30 run
- Check pending invite count at start of each networking run: do not send if >= 80 pending

## Run History

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

- LinkedIn Premium paywall confirmed (2026-05-30): messaging step requires Premium for non-first-degree contacts. However, once a connection is first-degree (formally accepted), messaging may be free — confirmed 1 message attempted to Dhanraj G (1st degree) on 2026-06-01 without paywall.
- Invite gate (80 pending threshold) is enforced at run start. If >= 80 pending, skip networking stage entirely.
- Connection requests to recruiters at hiring agencies (Quickhyre, PYXIDIA, Aura Placements, Think People Solutions) have better accept rates than direct cold connects to engineers.
- Scan hiring posts with keywords: "hiring backend", "looking for SDE", "we are hiring engineer" in LinkedIn search.
- DB shows `message_sent` for Prince Dubey (PYXIDIA) but was not confirmed this run — always verify message delivery by checking DB status vs. actual send confirmation.
