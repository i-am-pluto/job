#!/usr/bin/env python3
"""LinkedIn Control Suite — MCP server backed by a Chrome extension.

Instead of driving a separate headless browser (the old linkedin-selenium),
this server sends commands over a localhost WebSocket to a Chrome extension that
runs them inside the user's already-logged-in LinkedIn session. No credentials,
no bot-detection fight, stable DOM command surface.

Run standalone for testing:
    python3 vendor/linkedin-extension/server/main.py
Or register as an MCP stdio server (see ../.mcp.json and README.md).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from bridge import bridge

mcp = FastMCP("linkedin-extension")


# ------------------------------------------------------------------ #
# Session / status
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_status() -> dict:
    """Report whether the extension is connected and the LinkedIn tab is logged in.
    Returns: {connected: bool, logged_in: bool, active_tab_url: str, ...}
    No credentials needed — uses the user's existing Chrome session.
    """
    data = await bridge.send("status", {})
    return {"connected": bridge.connected, **data}


# ------------------------------------------------------------------ #
# Connections
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_get_connections(max_count: int = 100) -> dict:
    """Fetch the authenticated user's 1st-degree connections.
    Returns: {connections: [{name, profile_url, headline, connected_at}...], total_fetched}
    """
    return await bridge.send("getConnections", {"max_count": max_count}, timeout=120)


# ------------------------------------------------------------------ #
# Messaging
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_get_conversations(limit: int = 20) -> dict:
    """List recent DM conversation threads.
    Returns: {threads: [{thread_id, participants, last_message_preview,
              last_message_time, unread}...]}
    """
    return await bridge.send("getConversations", {"limit": limit})


@mcp.tool()
async def linkedin_get_thread_messages(thread_id: str, limit: int = 50) -> dict:
    """Read messages from a DM thread (thread_id from linkedin_get_conversations).
    Returns: {messages: [{sender, body, timestamp}...], thread_id}
    """
    return await bridge.send(
        "getThreadMessages", {"thread_id": thread_id, "limit": limit}
    )


@mcp.tool()
async def linkedin_send_message(
    profile_url: str, message: str, attachment_path: str = ""
) -> dict:
    """Send a DM to a 1st-degree connection (no Premium required).
    Args:
        profile_url: Full LinkedIn profile URL (https://www.linkedin.com/in/...)
        message: Message body text
        attachment_path: Path to a PDF to attach. NOTE: Chrome blocks programmatic
            file selection from extensions; if set, the text is still sent and the
            result carries error="attachment_unsupported" so you can attach via
            claude-in-chrome separately.
    Returns: {success: bool, error: str|null}
    """
    return await bridge.send(
        "sendMessage",
        {"profile_url": profile_url, "message": message,
         "attachment_path": attachment_path},
    )


# ------------------------------------------------------------------ #
# Networking — connect / sent invites
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_connect(profile_url: str, note: str = "") -> dict:
    """Send a connection request to a profile, optionally with a note (<=300 chars).
    Args:
        profile_url: Full LinkedIn profile URL (https://www.linkedin.com/in/...)
        note: personalized invite note; empty sends without a note
    Returns: {success, status: 'invite_sent'|'pending', error}
    """
    return await bridge.send("connect", {"profile_url": profile_url, "note": note})


@mcp.tool()
async def linkedin_get_sent_invites() -> dict:
    """List currently-pending sent connection invitations (for accepted-invite
    detection: names in the DB but missing here have been accepted/withdrawn).
    Returns: {pending: [{name, profile_url}...], total}
    """
    return await bridge.send("getSentInvites", {}, timeout=90)


# ------------------------------------------------------------------ #
# Post search
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_search_posts(
    keywords: str, date_filter: str = "past-week", limit: int = 15
) -> dict:
    """Search LinkedIn for posts matching keywords.
    Args:
        keywords: e.g. 'hiring backend engineer bangalore'
        date_filter: 'past-24h' | 'past-week' | 'past-month'
        limit: max posts
    Returns: {posts: [{author_name, author_url, author_degree, author_title,
              body, post_url, posted_at}...], query}
    """
    return await bridge.send(
        "searchPosts",
        {"keywords": keywords, "date_filter": date_filter, "limit": limit},
        timeout=90,
    )


# ------------------------------------------------------------------ #
# Jobs
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_open_jobs(
    keywords: str,
    location: str = "",
    easy_apply_only: bool = True,
    date_posted: str = "",
) -> dict:
    """Open the LinkedIn jobs search for the given filters in the active tab.
    Args:
        keywords: job search terms e.g. 'backend engineer'
        location: e.g. 'Bangalore' (optional)
        easy_apply_only: restrict to Easy Apply jobs (f_AL)
        date_posted: '' | 'past-24h' | 'past-week' | 'past-month'
    Returns: {url, opened}
    """
    return await bridge.send(
        "openJobs",
        {"keywords": keywords, "location": location,
         "easy_apply_only": easy_apply_only, "date_posted": date_posted},
    )


@mcp.tool()
async def linkedin_read_jobs(limit: int = 25) -> dict:
    """Read all visible job cards from the current jobs-search results in one pass
    (run linkedin_open_jobs first). Mirrors the 'score all cards before opening' rule.
    Returns: {jobs: [{job_id, title, company, location, easy_apply, promoted, url}...]}
    """
    return await bridge.send("readJobs", {"limit": limit}, timeout=90)


@mcp.tool()
async def linkedin_open_job(job_id: str) -> dict:
    """Open a specific job and return its full detail for scoring.
    Args:
        job_id: numeric id from linkedin_read_jobs
    Returns: {job_id, title, company, location, description, easy_apply, apply_url}
    """
    return await bridge.send("openJob", {"job_id": job_id})


# ------------------------------------------------------------------ #
# Debug / selector-repair tooling
# ------------------------------------------------------------------ #
@mcp.tool()
async def linkedin_goto(url: str) -> dict:
    """Navigate the active LinkedIn tab to a URL (then audit/probe it).
    Returns: {success, url}
    """
    return await bridge.send("goto", {"url": url}, timeout=40)


@mcp.tool()
async def linkedin_audit_selectors() -> dict:
    """Audit every selector in the extension's selectors.js against the CURRENT page.
    For each selector: match count + a text sample + whether it's a valid CSS selector.
    Stale selectors show count 0. Navigate to the relevant page first (linkedin_goto
    or the open_* tools), then audit. Use to find what LinkedIn changed.
    Returns: {url, title, results: {KEY: {selector, count, sample, valid}}}
    """
    return await bridge.send("auditSelectors", {}, timeout=40)


@mcp.tool()
async def linkedin_probe(
    selectors: list[str], limit: int = 3, attr: str = ""
) -> dict:
    """Test candidate CSS selectors against the current page to find replacements.
    Args:
        selectors: list of candidate CSS selectors to test
        limit: max sample elements per selector
        attr: optional attribute name to read from each sample (e.g. 'href')
    Returns: {url, results: {selector: {count, samples:[{tag,text,attr,html}]}}}
    """
    return await bridge.send(
        "probe", {"selectors": selectors, "limit": limit, "attr": attr or None},
        timeout=40,
    )


if __name__ == "__main__":
    mcp.run()
