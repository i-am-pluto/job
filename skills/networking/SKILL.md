---
name: networking
description: This skill should be used when the user asks to run LinkedIn networking outreach, scan LinkedIn hiring posts, send recruiter or hiring-manager connection requests, detect accepted LinkedIn invites, or message accepted networking contacts with a resume.
version: 1.0.0
---

# LinkedIn Networking Outreach Skill

Automate the user's LinkedIn networking workflow for backend hiring posts: scan recent posts, send personalized connection requests, detect accepted invites, and message accepted contacts with a selected resume.

**Working directory:** `/Users/parikshit/Documents/code/job`

**Tracking commands:**

```bash
python3 scripts/init_networking_db.py
python3 scripts/db_networking.py add --name "N" --linkedin-url "URL" --company "C" --title "T" --post-snippet "..." --invite-note "..."
python3 scripts/db_networking.py list --status invite_sent
python3 scripts/db_networking.py update-status --linkedin-slug "slug" --status accepted --notes "Confirmed 1st degree"
python3 scripts/db_networking.py summary
```

Use browser page text first. Use screenshots only when element visibility or coordinates cannot be determined from page text or interactive refs.

## Run Modes

- **Interactive mode:** Stop before sending each connection request and before sending each message. Ask for explicit confirmation.
- **Nightly mode:** Send approved connection requests and messages autonomously within the limits below.

## Phase 1 - SCAN

Rotate one keyword per run, cycling through:

1. `hiring backend engineer bangalore`
2. `hiring software engineer bangalore`
3. `we are hiring backend developer`
4. `SDE backend openings bangalore`

Open:

```text
https://www.linkedin.com/search/results/content/?keywords=<URL_ENCODED_KEYWORD>&sortBy=%22date_posted%22&datePosted=%22past-week%22
```

Read page text and parse post blocks in this shape:

```text
Name • Degree
Title
Post text
```

Extract: name, degree, profile URL when available, title, company if obvious, and the first 200 characters of post text.

Filter out:

- Company pages or posts without a `/in/` profile URL.
- 1st-degree profiles unless they should be checked in MESSAGE phase.
- Profiles already present in `python3 scripts/db_networking.py list`.
- DevOps-only, mobile-only, frontend-only, QA-only, or internship-only posts.
- Posts that do not mention hiring/open roles/referrals for backend, software engineer, SDE, platform, infra, distributed systems, cloud backend, or similar roles.

Prioritize:

1. Engineering managers, tech leads, staff/principal engineers, CTOs, founders.
2. In-house recruiters and talent partners.
3. External agency recruiters only when the role/company signal is strong.

Return an ordered candidate list of up to 15 leads with:

```text
Name | Degree | Title | Company | Profile URL | Role/team signal | Score reason
```

## Phase 2 - CONNECT

Before sending new invites, enforce the pending-invite gate:

1. Open `https://www.linkedin.com/mynetwork/invitation-manager/sent/`.
2. Read page text.
3. If a `People (N)` count or equivalent pending count is `>= 80`, skip new invites for this run and report the limit.

For each candidate, max 10 per run:

1. Open the profile URL.
2. Check visible state:
   - `Pending` means skip and do not write a duplicate DB row.
   - `1st` means mark/check for MESSAGE phase.
   - Direct `Connect` button or `More` -> `Connect` means eligible.
3. Prepare a note of 300 characters or fewer:

```text
Hi [First], saw your post about hiring [role/team]. I'm a backend engineer with 2 yrs exp in Go/Python/distributed systems - would love to connect and explore fit.
```

4. In interactive mode, show `Name | Title | Company | note` and wait for confirmation before clicking Send.
5. Click Connect, Add a note, type the note, and send.
6. Record the invite immediately:

```bash
python3 scripts/db_networking.py add --name "..." --linkedin-url "..." --company "..." --title "..." --post-snippet "..." --invite-note "..."
```

## Phase 3 - ACCEPTED_SCAN

Detect accepted invites by comparing the current sent-invites page with DB rows:

1. Open `https://www.linkedin.com/mynetwork/invitation-manager/sent/`.
2. Extract all names currently pending.
3. Run `python3 scripts/db_networking.py list --status invite_sent`.
4. For DB names missing from the pending page, open the saved profile URL and confirm:
   - `1st` degree or visible Message button -> accepted.
   - Connect button with no Pending state -> declined or withdrawn.
5. Update DB:

```bash
python3 scripts/db_networking.py update-status --linkedin-slug "slug" --status accepted --notes "Confirmed 1st degree"
python3 scripts/db_networking.py update-status --linkedin-slug "slug" --status declined --notes "Connect button visible after invite disappeared"
```

## Phase 4 - MESSAGE

Run:

```bash
python3 scripts/db_networking.py list --status accepted
```

Message at most 5 accepted contacts per run.

For each contact:

1. Open the profile URL.
2. Click Message and wait for the compose window.
3. Choose a resume with:

```bash
python3 scripts/pick_resume.py "<role/team/company/post snippet>"
```

Use the returned PDF path. Do not tune a resume unless the user explicitly asks; networking follow-up should stay lightweight.

4. Draft this message, adjusting `[role/team at company]`:

```text
Hi [First],

Thanks for connecting! I came across your post about [role/team at company] and wanted to reach out.

I'm a backend engineer with ~2 years of experience in distributed systems, Go, Python, and cloud infra. I'm currently exploring new opportunities in Bangalore and your team caught my attention.

I've attached my resume - would love to know if there's a fit, or even just get your perspective on the team.

Happy to chat at your convenience!

Best,
Parikshit
```

5. Attach the PDF with the available browser file-upload tool.
6. Interactive mode: stop before Send and ask for confirmation. Nightly mode: send autonomously.
7. Mark complete:

```bash
python3 scripts/db_networking.py update-status --linkedin-slug "slug" --status message_sent --resume-used "output/base.pdf" --notes "resume: output/base.pdf"
```

## Final Report

Return:

```text
Networking result:
  Scanned: N
  Invited: N
  Accepted found: N
  Messages sent: N
  Skipped:
    - Name | Reason
  Rate limits:
    - pending invites: N
  Memory updates:
    - data/memory/networking.md: ...
```

Update `data/memory/networking.md` with durable learnings: keywords that produced strong leads, blocked companies, pending-invite limit hits, profile/connect UI changes, and message-send blockers.
