import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class NetworkingDbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.tmp_path = Path(self.tmp.name)
        self.db_path = self.tmp_path / "applications.db"
        self.work_dir = self.tmp_path / "work"
        self.work_dir.mkdir()
        sqlite3.connect(self.db_path).close()

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

    def test_init_networking_db_creates_outreach_table(self):
        result = self.run_script("scripts/init_networking_db.py")

        self.assertEqual(result.returncode, 0, result.stderr)
        table = self.fetch_one(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='networking_outreach'"
        )
        self.assertIsNotNone(table)
        columns = self.fetch_one(
            "SELECT COUNT(*) AS cnt FROM pragma_table_info('networking_outreach')"
        )
        self.assertEqual(columns["cnt"], 14)

    def test_add_derives_slug_from_linkedin_url_and_prevents_duplicates(self):
        self.run_script("scripts/init_networking_db.py")

        first = self.run_script(
            "scripts/db_networking.py",
            "add",
            "--name",
            "Rashid Naseem",
            "--linkedin-url",
            "https://www.linkedin.com/in/rashidnaseem/?miniProfileUrn=abc",
            "--company",
            "Acme",
            "--title",
            "Engineering Manager",
            "--post-snippet",
            "Hiring backend engineers for distributed systems work.",
            "--invite-note",
            "Hi Rashid, saw your post about hiring backend engineers.",
        )
        second = self.run_script(
            "scripts/db_networking.py",
            "add",
            "--name",
            "Rashid Naseem",
            "--linkedin-url",
            "https://linkedin.com/in/rashidnaseem",
            "--invite-note",
            "Duplicate",
        )

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        row = self.fetch_one(
            """
            SELECT name, linkedin_slug, company, title, status, invite_note
            FROM networking_outreach
            WHERE linkedin_slug='rashidnaseem'
            """
        )
        self.assertEqual(dict(row), {
            "name": "Rashid Naseem",
            "linkedin_slug": "rashidnaseem",
            "company": "Acme",
            "title": "Engineering Manager",
            "status": "invite_sent",
            "invite_note": "Hi Rashid, saw your post about hiring backend engineers.",
        })
        count = self.fetch_one("SELECT COUNT(*) AS cnt FROM networking_outreach")
        self.assertEqual(count["cnt"], 1)

    def test_update_status_list_and_summary(self):
        self.run_script("scripts/init_networking_db.py")
        self.run_script(
            "scripts/db_networking.py",
            "add",
            "--name",
            "Mira Shah",
            "--linkedin-url",
            "https://www.linkedin.com/in/mira-shah",
            "--invite-note",
            "Hi Mira, saw your backend hiring post.",
        )

        update = self.run_script(
            "scripts/db_networking.py",
            "update-status",
            "--linkedin-slug",
            "mira-shah",
            "--status",
            "accepted",
            "--notes",
            "Confirmed 1st degree",
        )
        listed = self.run_script("scripts/db_networking.py", "list", "--status", "accepted")
        summary = self.run_script("scripts/db_networking.py", "summary")

        self.assertEqual(update.returncode, 0, update.stderr)
        self.assertIn("Mira Shah", listed.stdout)
        self.assertIn("accepted", listed.stdout)
        self.assertIn("accepted", summary.stdout)
        row = self.fetch_one(
            """
            SELECT status, notes
            FROM networking_outreach
            WHERE linkedin_slug='mira-shah'
            """
        )
        self.assertEqual(dict(row), {
            "status": "accepted",
            "notes": "Confirmed 1st degree",
        })


if __name__ == "__main__":
    unittest.main()
