#!/usr/bin/env python3
"""
DB helper — called by Claude during nightly runs to read/write applications.db.
Usage:
  python3 scripts/db.py add   --company "Arcana" --role "SDE2 Backend" --platform instahyre --score 4.5 --status Applied --location Bangalore --notes "Strong Kafka match"
  python3 scripts/db.py update-status --company "Arcana" --role "SDE2 Backend" --platform instahyre --status Interview --source gmail --notes "Got interview invite"
  python3 scripts/db.py list   [--status Applied] [--platform instahyre]
  python3 scripts/db.py summary
  python3 scripts/db.py log-run --instahyre 12 --linkedin 5 --status-updates 3 --summary "..."
  python3 scripts/db.py log-gmail --message-id "abc123" --sender "no-reply@linkedin.com" --subject "..." --action status_updated
"""

import sqlite3
import argparse
from datetime import datetime, timezone
from db_safe import safe_connection

def now():
    return datetime.now(timezone.utc).isoformat()

def add_application(args):
    try:
        with safe_connection(write=True) as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO applications (company, role, platform, url, score, status, applied_at, resume_used, location, salary_range, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (args.company, args.role, args.platform, getattr(args, 'url', None),
                  getattr(args, 'score', None), args.status or 'Applied', now(),
                  getattr(args, 'resume', None), getattr(args, 'location', None),
                  getattr(args, 'salary', None), getattr(args, 'notes', None)))
            app_id = cur.lastrowid
            cur.execute("""
                INSERT INTO status_history (application_id, old_status, new_status, changed_at, source, notes)
                VALUES (?, ?, ?, ?, 'add', ?)
            """, (app_id, None, args.status or 'Applied', now(), getattr(args, 'notes', None)))
        print(f"✓ Added: {args.company} — {args.role} [{args.platform}]")
    except sqlite3.IntegrityError:
        print(f"⚠ Already exists: {args.company} — {args.role} [{args.platform}] (use update-status)")

def update_status(args):
    with safe_connection(write=True) as con:
        cur = con.cursor()
        if getattr(args, 'platform', None):
            cur.execute("SELECT id, status FROM applications WHERE company=? AND role=? AND platform=?",
                        (args.company, args.role, args.platform))
        else:
            cur.execute("SELECT id, status FROM applications WHERE company=? AND role=?",
                        (args.company, args.role))
        row = cur.fetchone()
        if not row:
            suffix = f" [{args.platform}]" if getattr(args, 'platform', None) else ""
            print(f"✗ Not found: {args.company} — {args.role}{suffix}")
            return
        old_status = row['status']
        cur.execute("UPDATE applications SET status=? WHERE id=?", (args.status, row['id']))
        cur.execute("""
            INSERT INTO status_history (application_id, old_status, new_status, changed_at, source, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (row['id'], old_status, args.status, now(),
              getattr(args, 'source', 'manual'), getattr(args, 'notes', None)))
    print(f"✓ Updated: {args.company} — {args.role}: {old_status} → {args.status}")

def list_applications(args):
    with safe_connection(write=False) as con:
        cur = con.cursor()
        query = "SELECT company, role, platform, status, score, applied_at, location, notes FROM applications WHERE 1=1"
        params = []
        if getattr(args, 'status', None):
            query += " AND status=?"
            params.append(args.status)
        if getattr(args, 'platform', None):
            query += " AND platform=?"
            params.append(args.platform)
        query += " ORDER BY applied_at DESC"
        cur.execute(query, params)
        rows = cur.fetchall()

    if not rows:
        print("No applications found.")
        return

    print(f"\n{'Company':<25} {'Role':<30} {'Platform':<12} {'Status':<12} {'Score':<6} {'Date':<12}")
    print("-" * 100)
    for r in rows:
        date = r['applied_at'][:10] if r['applied_at'] else '-'
        score = f"{r['score']:.1f}" if r['score'] else '-'
        print(f"{r['company']:<25} {r['role']:<30} {r['platform']:<12} {r['status']:<12} {score:<6} {date:<12}")
    print(f"\nTotal: {len(rows)}")

def summary(args):
    with safe_connection(write=False) as con:
        cur = con.cursor()
        cur.execute("SELECT status, COUNT(*) as cnt FROM applications GROUP BY status ORDER BY cnt DESC")
        rows = cur.fetchall()
        cur.execute("SELECT platform, COUNT(*) as cnt FROM applications GROUP BY platform ORDER BY cnt DESC")
        platforms = cur.fetchall()
        cur.execute("SELECT COUNT(*) as cnt FROM applications WHERE applied_at >= date('now', '-7 days')")
        week = cur.fetchone()

    print("\n=== Application Summary ===")
    print("\nBy Status:")
    for r in rows:
        print(f"  {r['status']:<15}: {r['cnt']}")
    print("\nBy Platform:")
    for r in platforms:
        print(f"  {r['platform']:<15}: {r['cnt']}")
    print(f"\nLast 7 days: {week['cnt']} applications")

def log_run(args):
    with safe_connection(write=True) as con:
        cur = con.cursor()
        cur.execute("""
            INSERT INTO run_log (run_at, instahyre_applied, linkedin_applied, status_updates, errors, summary)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (now(), getattr(args, 'instahyre', 0), getattr(args, 'linkedin', 0),
              getattr(args, 'status_updates', 0), getattr(args, 'errors', None),
              getattr(args, 'summary', None)))
    print(f"✓ Run logged: Instahyre={args.instahyre}, LinkedIn={args.linkedin}, StatusUpdates={args.status_updates}")

def log_gmail(args):
    try:
        with safe_connection(write=True) as con:
            cur = con.cursor()
            cur.execute("""
                INSERT INTO gmail_scan_log (message_id, sender, subject, received_at, action_taken, scanned_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (args.message_id, getattr(args, 'sender', None), getattr(args, 'subject', None),
                  getattr(args, 'received', None), getattr(args, 'action', 'ignored'), now()))
        print(f"✓ Gmail message logged: {args.message_id}")
    except sqlite3.IntegrityError:
        print(f"⚠ Already logged: {args.message_id}")

def main():
    parser = argparse.ArgumentParser(description="Job applications DB helper")
    sub = parser.add_subparsers(dest='cmd')

    # add
    p = sub.add_parser('add')
    p.add_argument('--company', required=True)
    p.add_argument('--role', required=True)
    p.add_argument('--platform', required=True)
    p.add_argument('--url')
    p.add_argument('--score', type=float)
    p.add_argument('--status', default='Applied')
    p.add_argument('--resume')
    p.add_argument('--location')
    p.add_argument('--salary')
    p.add_argument('--notes')

    # update-status
    p = sub.add_parser('update-status')
    p.add_argument('--company', required=True)
    p.add_argument('--role', required=True)
    p.add_argument('--status', required=True)
    p.add_argument('--platform')
    p.add_argument('--source', default='manual')
    p.add_argument('--notes')

    # list
    p = sub.add_parser('list')
    p.add_argument('--status')
    p.add_argument('--platform')

    # summary
    sub.add_parser('summary')

    # log-run
    p = sub.add_parser('log-run')
    p.add_argument('--instahyre', type=int, default=0)
    p.add_argument('--linkedin', type=int, default=0)
    p.add_argument('--status-updates', type=int, default=0, dest='status_updates')
    p.add_argument('--errors')
    p.add_argument('--summary')

    # log-gmail
    p = sub.add_parser('log-gmail')
    p.add_argument('--message-id', required=True, dest='message_id')
    p.add_argument('--sender')
    p.add_argument('--subject')
    p.add_argument('--received')
    p.add_argument('--action', default='ignored')

    args = parser.parse_args()
    {'add': add_application, 'update-status': update_status, 'list': list_applications,
     'summary': summary, 'log-run': log_run, 'log-gmail': log_gmail}.get(args.cmd, lambda _: parser.print_help())(args)

if __name__ == "__main__":
    main()
