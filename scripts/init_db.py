#!/usr/bin/env python3
"""
Initialize (or migrate) applications.db in the job/ directory.
Safe to run multiple times — uses CREATE IF NOT EXISTS.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "applications.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # Main applications table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company     TEXT    NOT NULL,
            role        TEXT    NOT NULL,
            platform    TEXT    NOT NULL,          -- instahyre | linkedin | greenhouse | lever | workday | other
            url         TEXT,                      -- job posting URL if available
            score       REAL,                      -- 1-5 fit score
            status      TEXT    NOT NULL DEFAULT 'Applied',
            applied_at  TEXT    NOT NULL,          -- ISO datetime
            resume_used TEXT,                      -- which resume variant
            location    TEXT,
            salary_range TEXT,
            notes       TEXT,
            UNIQUE(company, role, platform)        -- prevent duplicate rows
        )
    """)

    # Status history — one row per status change
    cur.execute("""
        CREATE TABLE IF NOT EXISTS status_history (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id  INTEGER NOT NULL REFERENCES applications(id),
            old_status      TEXT,
            new_status      TEXT    NOT NULL,
            changed_at      TEXT    NOT NULL,      -- ISO datetime
            source          TEXT,                  -- gmail | portal | manual
            notes           TEXT
        )
    """)

    # Gmail scan log — track which emails were already processed
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gmail_scan_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id  TEXT    NOT NULL UNIQUE,   -- Gmail message ID
            sender      TEXT,
            subject     TEXT,
            received_at TEXT,
            action_taken TEXT,                     -- status_updated | ignored | flagged
            scanned_at  TEXT    NOT NULL
        )
    """)

    # Nightly run log — one row per scheduled run
    cur.execute("""
        CREATE TABLE IF NOT EXISTS run_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at          TEXT NOT NULL,
            instahyre_applied   INTEGER DEFAULT 0,
            linkedin_applied    INTEGER DEFAULT 0,
            greenhouse_applied  INTEGER DEFAULT 0,
            status_updates      INTEGER DEFAULT 0,
            errors          TEXT,
            summary         TEXT
        )
    """)

    try:
        cur.execute("ALTER TABLE run_log ADD COLUMN greenhouse_applied INTEGER DEFAULT 0")
    except sqlite3.OperationalError as exc:
        if "duplicate column name" not in str(exc).lower():
            raise

    con.commit()
    con.close()
    print(f"✓ DB initialized at {DB_PATH}")

if __name__ == "__main__":
    init()
