#!/usr/bin/env python3
"""
Robust batch DB insert for application tracking.

Handles the virtiofs disk I/O error that occurs when writing directly to
the mounted job folder. Strategy: copy DB to /var/tmp, do all writes,
copy back.

Usage:
    python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"instahyre","score":4,"status":"Applied","location":"Bangalore","notes":"..."}]'

Or import and call insert_applications(apps_list) directly.
"""

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DB_PATH = REPO_ROOT / "data" / "applications.db"
import os, tempfile
# Try multiple temp paths; use first writable
_candidates = ["/var/tmp/apps_work.db", "/tmp/jobdb/apps_work.db", str(Path(tempfile.gettempdir()) / "apps_work.db")]
TMP_DB = None
for _p in _candidates:
    try:
        Path(_p).parent.mkdir(parents=True, exist_ok=True)
        with open(_p, "ab") as _f:
            pass
        TMP_DB = Path(_p)
        break
    except (PermissionError, OSError):
        continue
if TMP_DB is None:
    TMP_DB = Path("/tmp/apps_work.db")


def get_working_db() -> Path:
    """Copy DB to /var/tmp to avoid virtiofs locking, return working path."""
    shutil.copy(DB_PATH, TMP_DB)
    return TMP_DB


def write_back(tmp: Path):
    """Copy modified DB back to mounted folder."""
    shutil.copy(tmp, DB_PATH)


def insert_applications(apps: list[dict], dry_run: bool = False) -> dict:
    """
    Insert a list of application dicts. Skips duplicates (company+role+platform).

    Each dict should have:
        company, role, platform, score, status, location, notes
    Optional: applied_at (ISO string), resume_used, url

    Returns {"inserted": N, "skipped": N, "total": N}
    """
    tmp = get_working_db()
    conn = sqlite3.connect(tmp)
    c = conn.cursor()

    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0

    for app in apps:
        company = app["company"]
        role = app["role"]
        platform = app.get("platform", "unknown")

        # Duplicate check
        c.execute(
            "SELECT id FROM applications WHERE company=? AND role=? AND platform=?",
            (company, role, platform),
        )
        if c.fetchone():
            print(f"  SKIP (dupe): {company} — {role} [{platform}]")
            skipped += 1
            continue

        if not dry_run:
            c.execute(
                """INSERT INTO applications
                   (company, role, platform, score, status, applied_at, location, notes, resume_used, url)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    company,
                    role,
                    platform,
                    app.get("score", 4),
                    app.get("status", "Applied"),
                    app.get("applied_at", now),
                    app.get("location", ""),
                    app.get("notes", ""),
                    app.get("resume_used", ""),
                    app.get("url", ""),
                ),
            )
        print(f"  INSERT: {company} — {role} [{platform}] score={app.get('score',4)}")
        inserted += 1

    c.execute("SELECT count(*) FROM applications")
    total = c.fetchone()[0]

    conn.commit()
    conn.close()

    if not dry_run:
        write_back(tmp)

    return {"inserted": inserted, "skipped": skipped, "total": total}


def log_run(
    instahyre: int = 0,
    linkedin: int = 0,
    status_updates: int = 0,
    summary: str = "",
):
    """Write a run log entry."""
    tmp = get_working_db()
    conn = sqlite3.connect(tmp)
    c = conn.cursor()

    try:
        c.execute(
            """INSERT INTO run_logs (run_at, instahyre_applied, linkedin_applied, status_updates, summary)
               VALUES (?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                instahyre,
                linkedin,
                status_updates,
                summary,
            ),
        )
        conn.commit()
        print(f"Run logged: instahyre={instahyre} linkedin={linkedin}")
    except sqlite3.OperationalError as e:
        print(f"Warning: run_log table may not exist ({e}). Skipping run log.")
    finally:
        conn.close()
        write_back(tmp)


def main():
    parser = argparse.ArgumentParser(description="Batch insert applications into DB")
    parser.add_argument("--apps", help="JSON array of application dicts")
    parser.add_argument("--file", help="Path to JSON file with application list")
    parser.add_argument("--dry-run", action="store_true", help="Print without inserting")
    parser.add_argument("--summary", action="store_true", help="Print DB summary and exit")
    args = parser.parse_args()

    if args.summary:
        tmp = get_working_db()
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT count(*) FROM applications")
        total = c.fetchone()[0]
        c.execute("SELECT platform, count(*) FROM applications GROUP BY platform")
        by_platform = c.fetchall()
        c.execute("SELECT status, count(*) FROM applications GROUP BY status")
        by_status = c.fetchall()
        conn.close()
        print(f"Total applications: {total}")
        print(f"By platform: {dict(by_platform)}")
        print(f"By status: {dict(by_status)}")
        return

    if args.file:
        apps = json.loads(Path(args.file).read_text())
    elif args.apps:
        apps = json.loads(args.apps)
    else:
        print("Provide --apps JSON or --file path")
        sys.exit(1)

    result = insert_applications(apps, dry_run=args.dry_run)
    print(f"\nResult: inserted={result['inserted']} skipped={result['skipped']} total={result['total']}")


if __name__ == "__main__":
    main()
