#!/usr/bin/env python3
"""
Robust batch DB insert for application tracking.

Handles mounted-filesystem SQLite I/O failures through scripts/db_safe.py.
Strategy: lock, copy DB to a writable temp path, do the SQLite work there,
then copy back.

Usage:
    python3 scripts/db_batch_insert.py --apps '[{"company":"X","role":"Y","platform":"instahyre","score":4,"status":"Applied","location":"Bangalore","notes":"..."}]'
    python3 scripts/db_batch_insert.py --log-run --instahyre 12 --linkedin 5 --status-updates 3 --summary "..."

Or import and call insert_applications(apps_list) directly.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from db_safe import safe_connection


def insert_applications(apps: list[dict], dry_run: bool = False) -> dict:
    """
    Insert a list of application dicts. Skips duplicates (company+role+platform).

    Each dict should have:
        company, role, platform, score, status, location, notes
    Optional: applied_at (ISO string), resume_used, url

    Returns {"inserted": N, "skipped": N, "total": N}
    """
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    skipped = 0

    with safe_connection(write=not dry_run) as conn:
        c = conn.cursor()

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
                status = app.get("status", "Applied")
                c.execute(
                    """INSERT INTO applications
                       (company, role, platform, score, status, applied_at, location, notes, resume_used, url)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        company,
                        role,
                        platform,
                        app.get("score", 4),
                        status,
                        app.get("applied_at", now),
                        app.get("location", ""),
                        app.get("notes", ""),
                        app.get("resume_used", ""),
                        app.get("url", ""),
                    ),
                )
                app_id = c.lastrowid
                c.execute(
                    """INSERT INTO status_history
                       (application_id, old_status, new_status, changed_at, source, notes)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (app_id, None, status, now, "add", app.get("notes", "")),
                )
            print(f"  INSERT: {company} — {role} [{platform}] score={app.get('score',4)}")
            inserted += 1

        c.execute("SELECT count(*) FROM applications")
        total = c.fetchone()[0]

    return {"inserted": inserted, "skipped": skipped, "total": total}


def log_run(
    instahyre: int = 0,
    linkedin: int = 0,
    status_updates: int = 0,
    errors: str = "",
    summary: str = "",
):
    """Write a run log entry."""
    with safe_connection(write=True) as conn:
        c = conn.cursor()
        c.execute(
            """INSERT INTO run_log
               (run_at, instahyre_applied, linkedin_applied, status_updates, errors, summary)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                instahyre,
                linkedin,
                status_updates,
                errors,
                summary,
            ),
        )
    print(f"Run logged: instahyre={instahyre} linkedin={linkedin} status_updates={status_updates}")


def main():
    parser = argparse.ArgumentParser(description="Batch insert applications into DB")
    parser.add_argument("--apps", help="JSON array of application dicts")
    parser.add_argument("--file", help="Path to JSON file with application list")
    parser.add_argument("--dry-run", action="store_true", help="Print without inserting")
    parser.add_argument("--summary", nargs="?", const=True, help="Print DB summary, or run summary text with --log-run")
    parser.add_argument("--log-run", action="store_true", help="Write a run_log row")
    parser.add_argument("--instahyre", type=int, default=0)
    parser.add_argument("--linkedin", type=int, default=0)
    parser.add_argument("--status-updates", type=int, default=0, dest="status_updates")
    parser.add_argument("--errors", default="")
    args = parser.parse_args()

    if args.log_run:
        log_run(
            instahyre=args.instahyre,
            linkedin=args.linkedin,
            status_updates=args.status_updates,
            errors=args.errors,
            summary="" if args.summary is True or args.summary is None else args.summary,
        )
        return

    if args.summary is True:
        with safe_connection(write=False) as conn:
            c = conn.cursor()
            c.execute("SELECT count(*) FROM applications")
            total = c.fetchone()[0]
            c.execute("SELECT platform, count(*) FROM applications GROUP BY platform")
            by_platform = c.fetchall()
            c.execute("SELECT status, count(*) FROM applications GROUP BY status")
            by_status = c.fetchall()
        print(f"Total applications: {total}")
        print(f"By platform: {dict(by_platform)}")
        print(f"By status: {dict(by_status)}")
        return

    if args.summary and not args.log_run:
        print("Use --summary without a value for DB summary, or combine summary text with --log-run")
        sys.exit(1)

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
