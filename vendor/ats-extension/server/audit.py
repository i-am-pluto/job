#!/usr/bin/env python3
"""Live selector-audit driver for the ATS extension.

Unlike LinkedIn (fixed URLs), ATS forms are tenant- and step-specific, so this
audits whatever page is currently open. Open a real Workday application step in
Chrome, then run this to see which selectors match (count>0), are stale (count=0),
or are invalid CSS. Step through the form (Next) and re-run to audit each step.

Usage:
    python3 vendor/ats-extension/server/audit.py

Requires: extension loaded (reloaded after content.js/selectors changes) and a
Workday/Greenhouse application tab open and logged in.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bridge import bridge  # noqa: E402


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
    print("Extension connected.\n")

    detect = await bridge.send("detect", {}, timeout=10)
    print(f"ATS={detect.get('ats')!r}  step={detect.get('step')!r}\n{detect.get('url')}\n")

    audit = await bridge.send("auditSelectors", {}, timeout=30)
    results = audit.get("results", {})
    if not results:
        print(f"audit returned nothing: {audit}")
        return
    print(f"selector_version={audit.get('selector_version')}\n")
    for key, r in results.items():
        if not isinstance(r, dict):
            continue
        if not r.get("valid", True):
            flag = "XX"  # invalid CSS
        elif r.get("count", 0) > 0:
            flag = "OK"
        else:
            flag = "!!"  # stale / wrong step
        print(f"  {flag} {key:18} count={r.get('count'):>3}  sample={r.get('sample','')[:48]!r}")

    print("\nAudit complete. XX=invalid CSS, !!=count 0 (drift or wrong step), OK=matched.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        import os
        sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
