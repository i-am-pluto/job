import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


SCHEMA = """
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT NOT NULL,
    role TEXT NOT NULL,
    platform TEXT NOT NULL,
    url TEXT,
    score REAL,
    status TEXT NOT NULL DEFAULT 'Applied',
    applied_at TEXT NOT NULL,
    resume_used TEXT,
    location TEXT,
    salary_range TEXT,
    notes TEXT,
    UNIQUE(company, role, platform)
);

CREATE TABLE status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    source TEXT,
    notes TEXT
);

CREATE TABLE gmail_scan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id TEXT NOT NULL UNIQUE,
    sender TEXT,
    subject TEXT,
    received_at TEXT,
    action_taken TEXT,
    scanned_at TEXT NOT NULL
);

CREATE TABLE run_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT NOT NULL,
    instahyre_applied INTEGER DEFAULT 0,
    linkedin_applied INTEGER DEFAULT 0,
    status_updates INTEGER DEFAULT 0,
    errors TEXT,
    summary TEXT
);
"""


class DbToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)
        self.db_path = self.tmp_path / "applications.db"
        self.work_dir = self.tmp_path / "work"
        self.work_dir.mkdir()

        con = sqlite3.connect(self.db_path)
        con.executescript(SCHEMA)
        con.execute(
            """
            INSERT INTO applications
              (company, role, platform, status, applied_at, score)
            VALUES
              ('Acme', 'Backend Engineer', 'linkedin', 'Applied', '2026-05-27T00:00:00+00:00', 4)
            """
        )
        con.commit()
        con.close()

    def run_script(self, *args):
        env = os.environ.copy()
        env["JOB_DB_PATH"] = str(self.db_path)
        env["JOB_DB_TMP_DIR"] = str(self.work_dir)
        return subprocess.run(
            [sys.executable, *args],
            cwd=REPO_ROOT,
            env=env,
            text=True,
            capture_output=True,
        )

    def fetch_one(self, query, params=()):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        row = con.execute(query, params).fetchone()
        con.close()
        return row

    def test_db_py_update_status_uses_injected_database_and_writes_history(self):
        result = self.run_script(
            "scripts/db.py",
            "update-status",
            "--company",
            "Acme",
            "--role",
            "Backend Engineer",
            "--platform",
            "linkedin",
            "--status",
            "Interview",
            "--source",
            "gmail",
            "--notes",
            "Recruiter replied",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        app = self.fetch_one("SELECT status FROM applications WHERE company='Acme'")
        history = self.fetch_one(
            """
            SELECT old_status, new_status, source, notes
            FROM status_history
            WHERE application_id = 1
            ORDER BY id DESC
            """
        )
        self.assertEqual(app["status"], "Interview")
        self.assertEqual(dict(history), {
            "old_status": "Applied",
            "new_status": "Interview",
            "source": "gmail",
            "notes": "Recruiter replied",
        })

    def test_batch_tool_logs_run_to_run_log_table(self):
        result = self.run_script(
            "scripts/db_batch_insert.py",
            "--log-run",
            "--instahyre",
            "3",
            "--linkedin",
            "2",
            "--greenhouse",
            "1",
            "--status-updates",
            "1",
            "--summary",
            "nightly ok",
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        row = self.fetch_one(
            """
            SELECT instahyre_applied, linkedin_applied, greenhouse_applied, status_updates, summary
            FROM run_log
            ORDER BY id DESC
            """
        )
        self.assertEqual(dict(row), {
            "instahyre_applied": 3,
            "linkedin_applied": 2,
            "greenhouse_applied": 1,
            "status_updates": 1,
            "summary": "nightly ok",
        })

    def test_batch_insert_adds_status_history_for_new_applications(self):
        apps_json = (
            '[{"company":"Beta","role":"SDE","platform":"naukri",'
            '"score":4,"status":"Applied","location":"India","notes":"Direct apply"}]'
        )
        result = self.run_script("scripts/db_batch_insert.py", "--apps", apps_json)

        self.assertEqual(result.returncode, 0, result.stderr)
        app = self.fetch_one(
            "SELECT id, company, role, platform FROM applications WHERE company='Beta'"
        )
        history = self.fetch_one(
            "SELECT new_status, source, notes FROM status_history WHERE application_id=?",
            (app["id"],),
        )
        self.assertEqual(dict(history), {
            "new_status": "Applied",
            "source": "add",
            "notes": "Direct apply",
        })


if __name__ == "__main__":
    unittest.main()
