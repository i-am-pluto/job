#!/usr/bin/env python3
"""Live smoke test for the ATS extension.

Starts the WS bridge, waits for the extension to connect, then exercises the
read-only tools (status, detect, read_form, audit) against whatever ATS page is
open in Chrome. Run this with a Workday job-application tab open and logged in.

Usage:
    python3 vendor/ats-extension/server/verify.py

Requires: extension loaded (reloaded after any content.js/selectors change) and a
Workday/Greenhouse application tab open in a Chrome window.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bridge import bridge  # noqa: E402

WANT_VERSION = "2026-06-v2"


async def main() -> None:
    await bridge.ensure_started()
    print("WS server up on 8766; waiting for extension (reload + open an ATS tab)...")
    for _ in range(120):
        if bridge.connected:
            break
        await asyncio.sleep(1.0)
    if not bridge.connected:
        print("Extension never connected. Load it at chrome://extensions and open a Workday tab.")
        return

    status = await bridge.send("status", {}, timeout=10)
    print(f"\nstatus -> {status}")
    ver = status.get("selector_version")
    if ver != WANT_VERSION:
        print(f"  ! selector bundle is {ver!r}, expected {WANT_VERSION!r} — reload extension + refresh tab.")
    if not status.get("logged_in", True):
        print("  ! not logged in to this Workday tenant — log in once in Chrome, then re-run.")

    detect = await bridge.send("detect", {}, timeout=10)
    print(f"\ndetect -> ats={detect.get('ats')!r} step={detect.get('step')!r}")
    print(f"          url={detect.get('url')}")

    form = await bridge.send("readForm", {}, timeout=20)
    fields = form.get("fields", [])
    print(f"\nreadForm -> step={form.get('step')!r}, {len(fields)} visible fields")
    for f in fields[:12]:
        req = "*" if f.get("required") else " "
        print(f"   {req} [{f.get('type'):8}] {f.get('label','')[:50]!r}"
              f"{' opts=' + str(len(f['options'])) if f.get('options') else ''}")

    audit = await bridge.send("auditSelectors", {}, timeout=20)
    results = audit.get("results", {})
    stale = [k for k, r in results.items() if isinstance(r, dict) and r.get("count") == 0]
    invalid = [k for k, r in results.items() if isinstance(r, dict) and not r.get("valid", True)]
    print(f"\nauditSelectors -> {len(results)} selectors; "
          f"{len(stale)} stale(count=0), {len(invalid)} invalid-CSS")
    if invalid:
        print(f"   invalid CSS (fix in selectors/workday.js): {invalid}")
    if stale:
        print(f"   stale (count=0 — may be wrong step or drifted): {stale}")

    print("\nVerification done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        import os
        sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
