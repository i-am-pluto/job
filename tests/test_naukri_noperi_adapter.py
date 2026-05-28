import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "naukri_noperi_apply.py"


def load_module():
    spec = importlib.util.spec_from_file_location("naukri_noperi_apply", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NaukriNopeRiAdapterTests(unittest.TestCase):
    def test_parse_profile_answers_extracts_numbers_and_identity(self):
        adapter = load_module()
        profile = """
        ## Identity And Contact
        - Email: user@example.com
        - Location: Delhi, India
        ## Compensation And Availability
        - Current CTC: 28 LPA
        - Expected CTC for SDE2-level roles: 35 LPA minimum
        - Notice period: 60 days
        ## Common Application Answers
        - Years of Java experience: 2
        - Years of Python experience: 3
        - Authorized to work in India: Yes
        - Highest education: B.Tech Computer Science
        """

        answers = adapter.parse_profile_answers(profile)

        self.assertEqual(answers["email"], "user@example.com")
        self.assertEqual(answers["current_ctc"], "28")
        self.assertEqual(answers["expected_ctc"], "35")
        self.assertEqual(answers["notice_days"], "60")
        self.assertEqual(answers["skill_years"]["java"], "2")
        self.assertEqual(answers["skill_years"]["python"], "3")
        self.assertEqual(answers["work_authorization_india"], "Yes")

    def test_score_job_applies_backend_roles_and_skips_hard_mismatches(self):
        adapter = load_module()

        backend = adapter.JobRecord(
            job_id="1",
            title="Ruby Backend Engineer",
            company="Acme",
            location="Bangalore",
            experience="2-4 Yrs",
            apply_link="https://www.naukri.com/job-listings-1",
            description="Build APIs and services",
            tags=["ruby", "api"],
        )
        frontend = adapter.JobRecord(
            job_id="2",
            title="Frontend Developer",
            company="Acme",
            location="Bangalore",
            experience="1-3 Yrs",
            apply_link="https://www.naukri.com/job-listings-2",
            description="React UI role",
            tags=["react"],
        )
        senior = adapter.JobRecord(
            job_id="3",
            title="Backend Engineer",
            company="Acme",
            location="Bangalore",
            experience="5-8 Yrs",
            apply_link="https://www.naukri.com/job-listings-3",
            description="Backend systems",
            tags=["java"],
        )

        self.assertEqual(adapter.score_job(backend).score, 4)
        self.assertTrue(adapter.score_job(backend).should_apply)
        self.assertFalse(adapter.score_job(frontend).should_apply)
        self.assertIn("frontend", adapter.score_job(frontend).reason.lower())
        self.assertFalse(adapter.score_job(senior).should_apply)
        self.assertIn("5+ year", adapter.score_job(senior).reason.lower())

    def test_parse_db_list_output_returns_platform_specific_keys(self):
        adapter = load_module()
        output = """
Company                   Role                           Platform     Status       Score  Date
----------------------------------------------------------------------------------------------------
Trade Brains              Backend Developer              naukri       Applied      4.0    2026-05-28
Acme Labs                 SDE                            linkedin     Applied      4.0    2026-05-27

Total: 2
"""

        keys = adapter.parse_existing_applications(output)

        self.assertIn(("trade brains", "backend developer", "naukri"), keys)
        self.assertIn(("acme labs", "sde", "linkedin"), keys)

    def test_build_db_payload_matches_batch_insert_schema(self):
        adapter = load_module()
        job = adapter.JobRecord(
            job_id="42",
            title="Backend Engineer",
            company="Acme",
            location="Gurugram",
            experience="1-3 Yrs",
            apply_link="https://www.naukri.com/job-listings-42",
            description="Backend APIs",
            tags=["java", "spring"],
        )

        payload = adapter.build_db_payload(job, resume_used="output/base.pdf", notes="Direct API apply")

        self.assertEqual(payload["company"], "Acme")
        self.assertEqual(payload["role"], "Backend Engineer")
        self.assertEqual(payload["platform"], "naukri")
        self.assertEqual(payload["score"], 4)
        self.assertEqual(payload["status"], "Applied")
        self.assertEqual(payload["location"], "Gurugram")
        self.assertEqual(payload["resume_used"], "output/base.pdf")
        self.assertEqual(payload["url"], "https://www.naukri.com/job-listings-42")
        json.dumps([payload])


if __name__ == "__main__":
    unittest.main()
