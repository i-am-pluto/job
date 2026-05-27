#!/usr/bin/env python3
"""
pick_resume.py - Deterministically pick the best cached resume for a job.

Zero LLM tokens: matches job text against signal keywords in
resumes/cache-index.json. The nightly task calls this per job so it
REUSES a cached PDF instead of re-tuning every time.

Usage:
    python3 scripts/pick_resume.py "job title + skill tags + jd text"

Output (one line, pipe-delimited):
    REUSE|<tag>|<pdf_path>|<score>          -> use this cached PDF, apply now
    TUNE|<closest_tag>|<closest_pdf>|<score> -> weak match; tuning would help

Decision rule: if the best archetype/tuned match scores >= 2 signal hits,
REUSE it. Otherwise recommend TUNE (but still return the closest PDF as a
safe fallback so the task never blocks).
"""
import sys
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "resumes" / "cache-index.json"
REUSE_THRESHOLD = 2


def score(job_text: str, signals: list) -> int:
    job = job_text.lower()
    hits = 0
    for sig in signals:
        s = sig.lower()
        if re.search(r"\b" + re.escape(s) + r"\b", job):
            hits += 1
    return hits


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/pick_resume.py \"<job text>\"")
        sys.exit(1)
    job_text = " ".join(sys.argv[1:])

    data = json.loads(INDEX.read_text())
    candidates = []
    for a in data.get("archetypes", []):
        candidates.append((a["tag"], a["pdf"], score(job_text, a.get("signals", []))))
    for t in data.get("tuned", []):
        candidates.append((t["tag"], t["pdf"], score(job_text, t.get("signals", []))))

    candidates.sort(key=lambda c: c[2], reverse=True)
    tag, pdf, sc = candidates[0]

    # general-backend is the safe default if nothing matches well
    if sc < REUSE_THRESHOLD:
        default = next((a for a in data["archetypes"]
                        if a["tag"] == "general-backend"), data["archetypes"][0])
        print(f"TUNE|{tag}|{default['pdf']}|{sc}")
    else:
        print(f"REUSE|{tag}|{pdf}|{sc}")


if __name__ == "__main__":
    main()
