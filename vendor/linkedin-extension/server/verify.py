#!/usr/bin/env python3
"""Verify the repaired actions live: sent-invites, job open, status.
Waits for selector_version 2026-06-v3 (proves the new bundle is injected)."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bridge import bridge  # noqa: E402

WANT = "2026-06-v3"


async def main():
    await bridge.ensure_started()
    print("Waiting for extension + new bundle (reload extension + refresh tab)...")
    ver = None
    for _ in range(200):
        if bridge.connected:
            s = await bridge.send("status", {}, timeout=8)
            ver = s.get("selector_version")
            if ver == WANT:
                print(f"status: {s}")
                break
        await asyncio.sleep(1.0)
    if ver != WANT:
        print(f"New bundle not loaded (got {ver!r}, want {WANT!r}). Reload + refresh.")
        return

    # 1) Sent invites
    si = await bridge.send("getSentInvites", {}, timeout=60)
    print(f"\ngetSentInvites -> total={si.get('total')}, error={si.get('error')}")
    for p in (si.get("pending") or [])[:5]:
        print(f"   - {p.get('name')!r}  {p.get('profile_url')}")

    # 2) Jobs: open search, read, open first job
    await bridge.send("openJobs", {"keywords": "backend engineer",
                                   "location": "India"}, timeout=40)
    await asyncio.sleep(3.0)
    rj = await bridge.send("readJobs", {"limit": 5}, timeout=60)
    jobs = rj.get("jobs", [])
    print(f"\nreadJobs -> {len(jobs)} jobs")
    if jobs:
        oj = await bridge.send("openJob", {"job_id": jobs[0]["job_id"]}, timeout=60)
        print(f"openJob -> title={oj.get('title')!r}")
        print(f"          company={oj.get('company')!r} easy_apply={oj.get('easy_apply')}")
        print(f"          desc_len={len(oj.get('description',''))}")
        print(f"          desc_head={oj.get('description','')[:160]!r}")

    print("\nVerification done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        import os
        sys.stdout.flush(); sys.stderr.flush(); os._exit(0)
