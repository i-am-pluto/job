#!/usr/bin/env python3
"""Create or migrate the LinkedIn networking outreach table."""

from __future__ import annotations

from db_safe import db_path, safe_connection


def migrate_networking(cur) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS networking_outreach (
          id               INTEGER PRIMARY KEY AUTOINCREMENT,
          name             TEXT NOT NULL,
          linkedin_slug    TEXT NOT NULL UNIQUE,
          linkedin_url     TEXT NOT NULL,
          company          TEXT,
          title            TEXT,
          post_snippet     TEXT,
          invite_sent_at   DATETIME,
          invite_note      TEXT,
          status           TEXT DEFAULT 'invite_sent',
          message_sent_at  DATETIME,
          resume_used      TEXT,
          notes            TEXT,
          created_at       DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def init() -> None:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch(exist_ok=True)
    with safe_connection(write=True) as con:
        migrate_networking(con.cursor())
    print(f"✓ Networking DB initialized at {path}")


if __name__ == "__main__":
    init()
