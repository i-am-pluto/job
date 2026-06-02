#!/usr/bin/env python3
"""Live selector-audit driver for the LinkedIn extension.

Starts the WS bridge, waits for the extension to connect, then navigates to each
key LinkedIn page and audits every selector in selectors.js against it. Prints a
report of which selectors are stale (count 0) per page so they can be repaired.

Usage:
    python3 vendor/linkedin-extension/server/audit.py

Requires: extension loaded (reloaded after content.js changes) and a logged-in
Chrome window open.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bridge import bridge  # noqa: E402

# page key -> (url, [selector keys expected to match on that page])
PAGES = {
    "feed": ("https://www.linkedin.com/feed/", ["NAV_ME"]),
    "connections": (
        "https://www.linkedin.com/mynetwork/invite-connect/connections/",
        ["CONNECTION_CARD"],
    ),
    "messaging": (
        "https://www.linkedin.com/messaging/",
        ["MSG_THREAD", "MSG_PARTICIPANTS", "MSG_SNIPPET", "MSG_TIME"],
    ),
    "sent_invites": (
        "https://www.linkedin.com/mynetwork/invitation-manager/sent/",
        ["SENT_INVITE_ITEM", "SENT_INVITE_NAME"],
    ),
    "jobs": (
        "https://www.linkedin.com/jobs/search/?keywords=backend%20engineer&f_AL=true",
        ["JOB_CARD", "JOB_TITLE", "JOB_COMPANY", "JOB_LOCATION", "JOB_FOOTER"],
    ),
    "posts": (
        'https://www.linkedin.com/search/results/content/?keywords=hiring%20backend'
        "&datePosted=%22r604800%22",
        ["POST_CARD", "POST_BODY"],
    ),
}


async def main() -> None:
    await bridge.ensure_started()
    print("WS server up; waiting for extension...")
    for _ in range(80):
        if bridge.connected:
            break
        await asyncio.sleep(0.25)
    if not bridge.connected:
        print("Extension never connected. Reload it at chrome://extensions and retry.")
        return
    print("Extension connected.")

    # Wait for the NEW content.js (with goto/auditSelectors) to be injected. The
    # user must reload the extension AND refresh the LinkedIn tab. Poll until ready.
    print("Checking for new content.js actions (reload extension + refresh the "
          "LinkedIn tab now if needed)...")
    ready = False
    for i in range(60):  # up to ~2.5 min
        r = await bridge.send("auditSelectors", {}, timeout=10)
        if isinstance(r.get("results"), dict):
            ready = True
            break
        if i % 4 == 0:
            print(f"  still old content.js ({r.get('error','?')}) — reload + refresh tab...")
        await asyncio.sleep(2.5)
    if not ready:
        print("New content.js never loaded. At chrome://extensions click ↻ on the "
              "extension, then refresh the linkedin.com tab, then re-run.")
        return
    print("New content.js live.\n")

    for key, (url, expected) in PAGES.items():
        print(f"=== {key}: {url}")
        nav = await bridge.send("goto", {"url": url}, timeout=40)
        if not nav or nav.get("success") is False and "error" in nav:
            print(f"  goto failed: {nav}")
            continue
        await asyncio.sleep(2.0)  # let SPA render
        audit = await bridge.send("auditSelectors", {}, timeout=40)
        results = audit.get("results", {})
        if not results:
            print(f"  audit returned nothing: {audit}")
            continue
        for sk in expected:
            r = results.get(sk)
            if not r:
                print(f"  {sk:18} <not in selectors.js>")
                continue
            flag = "OK " if r["count"] > 0 else "!! "
            print(f"  {flag}{sk:18} count={r['count']:3}  sample={r['sample'][:50]!r}")
        print()

    print("Audit complete.")


if __name__ == "__main__":
    asyncio.run(main())
