#!/usr/bin/env python3
"""LinkedIn networking outreach DB helper."""

from __future__ import annotations

import argparse
import re
import sqlite3
from datetime import datetime, timezone
from urllib.parse import urlparse

from db_safe import safe_connection
from init_networking_db import migrate_networking


VALID_STATUSES = {"invite_sent", "accepted", "message_sent", "no_response", "declined"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def linkedin_slug(linkedin_url: str) -> str:
    parsed = urlparse(linkedin_url.strip())
    path = parsed.path if parsed.scheme else urlparse(f"https://{linkedin_url.strip()}").path
    parts = [part for part in path.split("/") if part]
    if "in" in parts:
        index = parts.index("in")
        if index + 1 < len(parts):
            return parts[index + 1].strip().lower()
    if parts:
        return parts[-1].strip().lower()
    raise ValueError(f"Could not derive LinkedIn slug from URL: {linkedin_url}")


def truncate_snippet(value: str | None) -> str | None:
    if value is None:
        return None
    value = re.sub(r"\s+", " ", value).strip()
    return value[:200]


def ensure_table(cur) -> None:
    migrate_networking(cur)


def add_contact(args) -> None:
    slug = linkedin_slug(args.linkedin_url)
    try:
        with safe_connection(write=True) as con:
            cur = con.cursor()
            ensure_table(cur)
            cur.execute(
                """
                INSERT INTO networking_outreach
                  (name, linkedin_slug, linkedin_url, company, title, post_snippet,
                   invite_sent_at, invite_note, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'invite_sent')
                """,
                (
                    args.name,
                    slug,
                    args.linkedin_url,
                    getattr(args, "company", None),
                    getattr(args, "title", None),
                    truncate_snippet(getattr(args, "post_snippet", None)),
                    now(),
                    args.invite_note,
                ),
            )
        print(f"✓ Added networking contact: {args.name} [{slug}]")
    except sqlite3.IntegrityError:
        print(f"⚠ Already exists: {args.name} [{slug}]")


def list_contacts(args) -> None:
    with safe_connection(write=False) as con:
        cur = con.cursor()
        ensure_table(cur)
        query = """
            SELECT name, linkedin_slug, linkedin_url, company, title, status, invite_sent_at,
                   message_sent_at, resume_used, notes
            FROM networking_outreach
            WHERE 1=1
        """
        params: list[str] = []
        if getattr(args, "status", None):
            query += " AND status=?"
            params.append(args.status)
        query += " ORDER BY created_at DESC, id DESC"
        cur.execute(query, params)
        rows = cur.fetchall()

    if not rows:
        print("No networking contacts found.")
        return

    print(f"\n{'Name':<24} {'Company':<22} {'Title':<28} {'Status':<14} {'Slug':<24} URL")
    print("-" * 156)
    for row in rows:
        print(
            f"{row['name']:<24} "
            f"{(row['company'] or '-'):<22} "
            f"{(row['title'] or '-')[:27]:<28} "
            f"{row['status']:<14} "
            f"{row['linkedin_slug']:<24} "
            f"{row['linkedin_url']}"
        )
    print(f"\nTotal: {len(rows)}")


def update_status(args) -> None:
    if args.status not in VALID_STATUSES:
        raise SystemExit(f"Invalid status: {args.status}. Use one of: {', '.join(sorted(VALID_STATUSES))}")

    with safe_connection(write=True) as con:
        cur = con.cursor()
        ensure_table(cur)
        cur.execute(
            "SELECT id, name, status FROM networking_outreach WHERE linkedin_slug=?",
            (args.linkedin_slug,),
        )
        row = cur.fetchone()
        if not row:
            print(f"✗ Not found: {args.linkedin_slug}")
            return

        updates = ["status=?"]
        params: list[str | None] = [args.status]
        if args.status == "message_sent":
            updates.append("message_sent_at=?")
            params.append(now())
        if getattr(args, "resume_used", None):
            updates.append("resume_used=?")
            params.append(args.resume_used)
        if getattr(args, "notes", None):
            updates.append("notes=?")
            params.append(args.notes)
        params.append(args.linkedin_slug)

        cur.execute(
            f"UPDATE networking_outreach SET {', '.join(updates)} WHERE linkedin_slug=?",
            params,
        )
    print(f"✓ Updated networking contact: {row['name']}: {row['status']} → {args.status}")


def summary(args) -> None:
    with safe_connection(write=False) as con:
        cur = con.cursor()
        ensure_table(cur)
        cur.execute("SELECT status, COUNT(*) AS cnt FROM networking_outreach GROUP BY status ORDER BY cnt DESC")
        rows = cur.fetchall()
        cur.execute("SELECT COUNT(*) AS cnt FROM networking_outreach")
        total = cur.fetchone()["cnt"]

    print("\n=== Networking Outreach Summary ===")
    print(f"Total: {total}")
    print("\nBy Status:")
    if not rows:
        print("  none           : 0")
        return
    for row in rows:
        print(f"  {row['status']:<15}: {row['cnt']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="LinkedIn networking outreach DB helper")
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("add")
    p.add_argument("--name", required=True)
    p.add_argument("--linkedin-url", required=True)
    p.add_argument("--company")
    p.add_argument("--title")
    p.add_argument("--post-snippet")
    p.add_argument("--invite-note", required=True)

    p = sub.add_parser("list")
    p.add_argument("--status", choices=sorted(VALID_STATUSES))

    p = sub.add_parser("update-status")
    p.add_argument("--linkedin-slug", required=True)
    p.add_argument("--status", required=True, choices=sorted(VALID_STATUSES))
    p.add_argument("--notes")
    p.add_argument("--resume-used")

    sub.add_parser("summary")

    args = parser.parse_args()
    {
        "add": add_contact,
        "list": list_contacts,
        "update-status": update_status,
        "summary": summary,
    }.get(args.cmd, lambda _: parser.print_help())(args)


if __name__ == "__main__":
    main()
