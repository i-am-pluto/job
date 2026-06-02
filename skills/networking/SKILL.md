---
name: networking
description: This skill should be used when the user asks to run LinkedIn networking outreach, scan LinkedIn hiring posts, send recruiter or hiring-manager connection requests, detect accepted LinkedIn invites, or message accepted networking contacts with a resume.
version: 1.1.0
---

# LinkedIn Networking Outreach Skill

Automate the user's LinkedIn networking workflow for backend hiring posts: scan recent posts, send personalized connection requests, detect accepted invites, and message accepted contacts with a selected resume.

**Working directory:** `/Users/parikshit/Documents/code/job`

## Control surface — MCP tools first

The `linkedin-extension` MCP server drives the user's logged-in Chrome with cheap,
structured tools. Use it for every phase; fall back to claude-in-chrome only when a
tool returns an error envelope or for the resume-PDF attachment (see Phase 4).

- `linkedin_status()` → confirm `connected:true, logged_in:true` first. If down, run the whole skill via claude-in-chrome and note it.
- `linkedin_search_posts(keywords, date_filter="past-week", limit=15)` → SCAN (Phase 1).
- `linkedin_connect(profile_url, note)` → CONNECT (Phase 2).
- `linkedin_get_sent_invites()` → ACCEPTED_SCAN (Phase 3).
- `linkedin_send_message(profile_url, message)` → MESSAGE text (Phase 4). **Attachment caveat:** Chrome blocks programmatic file selection, so the resume PDF cannot be attached by the tool — send the text via the tool, then attach the PDF via claude-in-chrome, OR send the whole message via claude-in-chrome.

**Tracking commands:**

```bash
python3 scripts/init_networking_db.py
python3 scripts/db_networking.py add --name "N" --linkedin-url "URL" --company "C" --title "T" --post-snippet "..." --invite-note "..."
python3 scripts/db_networking.py list --status invite_sent
python3 scripts/db_networking.py update-status --linkedin-slug "slug" --status accepted --notes "Confirmed 1st degree"
python3 scripts/db_networking.py summary
```

## Run Modes

- **Interactive mode:** Stop before sending each connection request and before sending each message. Ask for explicit confirmation.
- **Nightly mode:** Send approved connection requests and messages autonomously within the limits below.

## Phase 1 - SCAN

Rotate one keyword per run, cycling through:

1. `hiring backend engineer bangalore`
2. `hiring software engineer bangalore`
3. `we are hiring backend developer`
4. `SDE backend openings bangalore`

Call:

```text
linkedin_search_posts(keywords="<KEYWORD>", date_filter="past-week", limit=15)
```

This returns `{posts:[{author_name, author_url, author_degree, author_title, body,
post_url, posted_at}]}` — structured, no manual page parsing. Use `author_url` as the
profile URL, `author_title` as title, first 200 chars of `body` as the post snippet.

Fallback (extension down): open `https://www.linkedin.com/search/results/content/?keywords=<URL_ENCODED_KEYWORD>&sortBy=%22date_posted%22&datePosted=%22past-week%22` via claude-in-chrome and parse page text.

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

For each candidate, max 10 per run:

1. Prepare a note of 300 characters or fewer:

```text
Hi [First], saw your post about hiring [role/team]. I'm a backend engineer with 2 yrs exp in Go/Python/distributed systems - would love to connect and explore fit.
```

2. In interactive mode, show `Name | Title | Company | note` and wait for confirmation before sending.
3. Send the request:

```text
linkedin_connect(profile_url="<author_url>", note="<note>")
```

Returns `{success, status, error}`. `status:"pending"` means an invite already
exists — skip and do not write a duplicate DB row. `success:false` with a
"Connect button not found" error means already-connected (handle in MESSAGE phase)
or blocked — skip. On `status:"invite_sent"` continue to record.

Fallback (extension down or connect error): open the profile via claude-in-chrome,
check state (Pending/1st/Connect), click Connect → Add a note → type → Send.

4. Record the invite immediately:

```bash
python3 scripts/db_networking.py add --name "..." --linkedin-url "..." --company "..." --title "..." --post-snippet "..." --invite-note "..."
```

## Phase 3 - ACCEPTED_SCAN

Detect accepted invites by comparing the current sent-invites list with DB rows:

1. Call `linkedin_get_sent_invites()` → `{pending:[{name, profile_url}], total}`.
2. Run `python3 scripts/db_networking.py list --status invite_sent`.
3. For DB names missing from the pending list, open the saved profile URL (via
   `linkedin_send_message` dry-check is not ideal — use claude-in-chrome to view the
   profile) and confirm:
   - `1st` degree or visible Message button -> accepted.
   - Connect button with no Pending state -> declined or withdrawn.
4. Update DB:

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

1. Choose a resume with:

```bash
python3 scripts/pick_resume.py "<role/team/company/post snippet>"
```

Use the returned PDF path. Do not tune a resume unless the user explicitly asks; networking follow-up should stay lightweight.

2. Draft this message, adjusting `[role/team at company]`:

```text
Hi [First],

Thanks for connecting! I came across your post about [role/team at company] and wanted to reach out.

I'm a backend engineer with ~2 years of experience in distributed systems, Go, Python, and cloud infra. I'm currently exploring new opportunities in Bangalore and your team caught my attention.

I've attached my resume - would love to know if there's a fit, or even just get your perspective on the team.

Happy to chat at your convenience!

Best,
Parikshit
```

3. Interactive mode: show `Name | message | resume` and stop before Send. Nightly mode: send autonomously.

4. **Send — attachment matters here, so prefer claude-in-chrome for the full
   message+attach.** The `linkedin_send_message` tool sends text reliably but CANNOT
   attach the PDF (Chrome blocks file selection):
   - **Recommended:** open the profile via claude-in-chrome, click Message, type the
     message, attach the resume PDF with the file-upload tool, then send.
   - **Text-only fallback:** `linkedin_send_message(profile_url, message)` (returns
     `error:"attachment_unsupported"`), then attach the PDF via claude-in-chrome — only
     if the claude-in-chrome compose path is unavailable.
5. Mark complete:

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
  Memory updates:
    - data/memory/networking.md: ...
```

Update `data/memory/networking.md` with durable learnings: keywords that produced strong leads, blocked companies, pending-invite limit hits, profile/connect UI changes, and message-send blockers.
