#!/usr/bin/env python3
"""ATS Control Suite — MCP server backed by a Chrome extension.

Sends commands over a localhost WebSocket to a Chrome extension that runs them
inside the user's already-logged-in ATS session (Workday, Greenhouse, etc.).
No credentials, no bot-detection fight, no screenshots.

Run standalone for testing:
    python3 vendor/ats-extension/server/main.py
Or register as an MCP stdio server (see .mcp.json and README.md).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from bridge import bridge

mcp = FastMCP("ats-extension")


# ------------------------------------------------------------------ #
# Session / status
# ------------------------------------------------------------------ #
@mcp.tool()
async def ats_status() -> dict:
    """Report whether the ATS extension is connected and logged in.
    Returns: {connected, ats: 'workday'|'greenhouse', logged_in, active_tab_url,
              selector_version}
    """
    data = await bridge.send("status", {})
    return {"connected": bridge.connected, **data}


# ------------------------------------------------------------------ #
# ATS detection
# ------------------------------------------------------------------ #
@mcp.tool()
async def ats_detect() -> dict:
    """Detect which ATS the active tab is on, and which step of the form.
    Returns: {ats: 'workday'|'greenhouse', step: str, url: str}
    """
    return await bridge.send("detect", {})


# ------------------------------------------------------------------ #
# Form operations
# ------------------------------------------------------------------ #
@mcp.tool()
async def ats_read_form() -> dict:
    """Read all visible fields in the current ATS form step.
    Returns: {ats, step, fields: [{label, type, value, required, options, id}...]}
    Only visible fields (offsetParent !== null) are returned — avoids
    get_page_text lies about hidden elements.
    """
    return await bridge.send("readForm", {})


@mcp.tool()
async def ats_fill_form(answers: dict) -> dict:
    """Fill form fields by label text. Accepts {labelFragment: value} map.
    Args:
        answers: dict of label substring -> value to fill
    Returns: {filled: int, notFound: [str], step: str}
    Example:
        ats_fill_form({"First Name": "Parikshit", "Last Name": "Dabas", "City": "Bangalore"})
    """
    return await bridge.send("fillForm", {"answers": answers})


# ------------------------------------------------------------------ #
# Resume upload
# ------------------------------------------------------------------ #
@mcp.tool()
async def ats_upload_resume(file_path: str = "") -> dict:
    """Trigger resume upload on the current ATS form step.
    NOTE: Chrome extensions cannot programmatically set file input values for
    security reasons. This tool detects the file input and returns its selector
    so you can call file_upload via claude-in-chrome MCP. If a resume is already
    present it returns success with reason='resume_already_present'.
    Args:
        file_path: path to the PDF resume (used for reference; actual upload
                  requires browser file_upload tool)
    Returns: {success, native_file_dialog, selector, reason} or {success, error}
    """
    return await bridge.send("uploadResume", {"filePath": file_path})


# ------------------------------------------------------------------ #
# Navigation / progression
# ------------------------------------------------------------------ #
@mcp.tool()
async def ats_next_step() -> dict:
    """Click the Next / Save and Continue button and wait for the next step.
    Handles scroll-before-click (Workday panels cut off below fold).
    Returns: {success, step_before, step_after, has_errors}
    """
    return await bridge.send("nextStep", {})


@mcp.tool()
async def ats_submit() -> dict:
    """Click the Submit Application button and confirm submission.
    Returns: {success, submitted: bool}
    """
    return await bridge.send("submit", {})


# ------------------------------------------------------------------ #
# Debug / selector maintenance
# ------------------------------------------------------------------ #
@mcp.tool()
async def ats_audit_selectors() -> dict:
    """Audit every ATS selector against the current page for drift detection.
    Reports match count + sample for each selector so you can spot count=0.
    Returns: {url, ats, selector_version, results: {key: {selector, count, sample, valid}}}
    """
    return await bridge.send("auditSelectors", {})


@mcp.tool()
async def ats_probe(selectors: list[str], limit: int = 3, attr: str = "") -> dict:
    """Test one or more candidate selectors and return match counts + samples.
    Use this to iterate toward a working replacement when audit shows count=0.
    Args:
        selectors: list of CSS selector strings to test
        limit: max samples per selector
        attr: optional attribute to extract (e.g. 'data-automation-id')
    Returns: {url, results: {selector: {count, samples: [{tag, text, attr, html}...]}}}
    """
    return await bridge.send("probe", {"selectors": selectors, "limit": limit, "attr": attr})


if __name__ == "__main__":
    mcp.run()
