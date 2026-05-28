import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SETUP_PATH = REPO_ROOT / "scripts" / "setup.py"


def load_setup_module():
    spec = importlib.util.spec_from_file_location("job_setup", SETUP_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["job_setup"] = module
    spec.loader.exec_module(module)
    return module


class SetupScriptTests(unittest.TestCase):
    def setUp(self):
        self.setup = load_setup_module()
        self.answers = {
            "full_name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "+91 99999 00000",
            "location": "Bengaluru, India",
            "linkedin": "linkedin.com/in/janesmith",
            "github": "github.com/janesmith",
            "current_company": "ExampleCorp",
            "current_title": "Backend Engineer",
            "experience_years": "4",
            "current_ctc": "20 LPA",
            "expected_ctc": "32 LPA",
            "notice_days": "30",
            "target_roles": ["Backend Engineer", "Platform Engineer"],
            "skills_years": {"Python": "4", "Kubernetes": "2"},
            "work_auth_india": "Yes",
            "willing_to_relocate": "No",
            "highest_education": "B.Tech Computer Science",
            "graduation_year": "2022",
            "gpa": "8.7",
            "remote_preference": "Remote preferred",
        }

    def test_build_user_config_contains_identity_and_application_answers(self):
        config = self.setup.build_user_config(self.answers)

        self.assertEqual(config["identity"]["full_name"], "Jane Smith")
        self.assertEqual(config["current_role"]["current_company"], "ExampleCorp")
        self.assertEqual(config["application_answers"]["notice_days"], "30")
        self.assertEqual(config["application_answers"]["skills_years"]["Python"], "4")
        self.assertEqual(config["targeting"]["target_roles"], ["Backend Engineer", "Platform Engineer"])

    def test_render_profile_uses_answers_without_placeholder_tokens(self):
        profile = self.setup.render_profile(self.answers)

        self.assertIn("# Jane Smith Job Search Profile", profile)
        self.assertIn("- Email: jane@example.com", profile)
        self.assertIn("- Current company: ExampleCorp", profile)
        self.assertIn("- Years of Python experience: 4", profile)
        self.assertNotIn("{{", profile)

    def test_render_base_resume_skeleton_uses_contact_line(self):
        resume = self.setup.render_base_resume(self.answers)

        self.assertIn("# Jane Smith", resume)
        self.assertIn("+91 99999 00000 | jane@example.com | Bengaluru, India", resume)
        self.assertIn("linkedin.com/in/janesmith | github.com/janesmith", resume)
        self.assertIn("## EXPERIENCE", resume)

    def test_render_user_yml_keeps_empty_lists_and_maps_inline(self):
        answers = dict(self.answers)
        answers["target_roles"] = []
        answers["skills_years"] = {}

        rendered = self.setup.render_user_yml(answers)

        self.assertIn("target_roles: []", rendered)
        self.assertIn("skills_years: {}", rendered)
        self.assertNotIn("target_roles:\n    []", rendered)


if __name__ == "__main__":
    unittest.main()
