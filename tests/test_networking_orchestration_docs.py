import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class NetworkingOrchestrationDocsTests(unittest.TestCase):
    def test_nightly_command_dispatches_networking_agent_and_logs_results(self):
        command = (REPO_ROOT / "commands" / "nightly-job-apply.md").read_text()

        self.assertIn("networking-agent", command)
        self.assertIn("job-search:networking-agent", command)
        self.assertIn("NETWORKING results: <INSERT_NETWORKING_RESULTS>", command)
        self.assertIn("Accepted found", command)
        self.assertIn("Messages sent", command)

    def test_ceo_plan_and_log_include_networking_outreach(self):
        ceo = (REPO_ROOT / "agents" / "job-ceo.md").read_text()

        self.assertIn("networking_outreach", ceo)
        self.assertIn("networking:", ceo)
        self.assertIn("networking_goal:", ceo)
        self.assertIn("networking-agent", ceo)
        self.assertIn("data/memory/networking.md", ceo)

    def test_plugin_version_bumped_for_orchestration_change(self):
        manifest = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())

        self.assertEqual(manifest["version"], "1.2.3")


if __name__ == "__main__":
    unittest.main()
