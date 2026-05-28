import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "run_state.py"


def load_module():
    spec = importlib.util.spec_from_file_location("run_state", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RunStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_path = Path(self.tmp.name) / "run-state.json"

    def test_load_state_returns_defaults_when_missing(self):
        run_state = load_module()

        state = run_state.load_state(self.state_path)

        self.assertEqual(state["last_gmail_status_scan_at"], "")
        self.assertEqual(state["last_greenhouse_board_scan_at"], "")
        self.assertEqual(state["platform_status_scan_at"], {})

    def test_load_state_recovers_from_invalid_json(self):
        run_state = load_module()
        self.state_path.write_text("{not-json", encoding="utf-8")

        state = run_state.load_state(self.state_path)

        self.assertEqual(state["last_gmail_status_scan_at"], "")
        self.assertEqual(state["last_greenhouse_board_scan_at"], "")

    def test_save_state_writes_iso_utc_atomically(self):
        run_state = load_module()
        state = run_state.load_state(self.state_path)
        stamp = run_state.now_utc_iso()
        state["last_gmail_status_scan_at"] = stamp

        run_state.save_state(state, self.state_path)
        loaded = run_state.load_state(self.state_path)

        self.assertEqual(loaded["last_gmail_status_scan_at"], stamp)
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        self.assertEqual(parsed.tzinfo, timezone.utc)

    def test_greenhouse_scan_requires_seven_days_between_runs(self):
        run_state = load_module()
        state = run_state.default_state()
        now = datetime(2026, 6, 4, 12, 0, tzinfo=timezone.utc)

        state["last_greenhouse_board_scan_at"] = "2026-05-28T12:00:00Z"
        self.assertTrue(run_state.greenhouse_scan_due(state, now=now))

        state["last_greenhouse_board_scan_at"] = "2026-05-29T12:00:00Z"
        self.assertFalse(run_state.greenhouse_scan_due(state, now=now))

    def test_gmail_after_date_falls_back_to_seven_days_when_never_scanned(self):
        run_state = load_module()
        state = run_state.default_state()
        now = datetime(2026, 6, 4, 12, 0, tzinfo=timezone.utc)

        self.assertEqual(run_state.gmail_after_date(state, now=now), "2026/05/28")

        state["last_gmail_status_scan_at"] = "2026-06-02T03:04:05Z"
        self.assertEqual(run_state.gmail_after_date(state, now=now), "2026/06/02")


if __name__ == "__main__":
    unittest.main()
