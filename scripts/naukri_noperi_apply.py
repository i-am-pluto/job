#!/usr/bin/env -S /Users/parikshit/.pyenv/versions/3.12.0/bin/python3
"""
Naukri adapter backed by the vendored NopeRi API client.

This script deliberately wraps only the safe workflow surface used by this
workspace. It does not run NopeRi's upstream apply_agent.py, does not use its
CSV store, and does not use its hardcoded profile/scoring pipeline.
"""

from __future__ import annotations

import argparse
import json
import os

from dotenv import load_dotenv

load_dotenv()
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = REPO_ROOT / "vendor" / "NopeRi"
PROFILE_PATH = REPO_ROOT / "profile.md"
PIPELINE_PATH = REPO_ROOT / "data" / "pipeline.md"

SEARCH_QUERIES = [
    {"keyword": "backend developer", "location": ""},
    {"keyword": "software engineer", "location": ""},
    {"keyword": "software development engineer", "location": ""},
    {"keyword": "full stack developer", "location": ""},
    {"keyword": "java developer", "location": ""},
    {"keyword": "platform engineer", "location": ""},
    {"keyword": "distributed systems", "location": ""},
]

SKIP_TITLE_PATTERNS = [
    "frontend",
    "front-end",
    "front end",
    "android",
    "ios",
    "flutter",
    "mobile",
    "qa",
    "quality analyst",
    "quality assurance",
    "tester",
    "testing",
    "recruiter",
    "hr ",
    "data analyst",
]

DEVOPS_ONLY_PATTERNS = [
    "devops engineer",
    "site reliability",
    "sre",
    "cloud operations",
    "system administrator",
]

BACKEND_SIGNALS = [
    "backend",
    "back-end",
    "back end",
    "full stack",
    "fullstack",
    "software engineer",
    "software developer",
    "sde",
    "swe",
    "developer",
    "java",
    "kotlin",
    "spring",
    "python",
    "node",
    "golang",
    "api",
    "microservice",
    "distributed",
    "platform",
    "data platform",
]

COMMERCIAL_NOTIFICATION_PATTERNS = [
    "nvite",
    "profile view",
    "viewed your profile",
    "appeared in search",
    "application booster",
    "promote",
    "paid service",
    "recruiter action",
]

ACTIONABLE_NOTIFICATION_PATTERNS = [
    "interview",
    "message",
    "assessment",
    "shortlist",
    "shortlisted",
    "selected",
    "offer",
    "rejected",
    "not moving forward",
]


class JobRecord:
    def __init__(
        self,
        job_id: str,
        title: str,
        company: str,
        location: str,
        experience: str,
        apply_link: str,
        description: str = "",
        tags: list[str] | None = None,
    ):
        self.job_id = str(job_id or "")
        self.title = title or ""
        self.company = company or ""
        self.location = location or ""
        self.experience = experience or ""
        self.apply_link = apply_link or ""
        self.description = description or ""
        self.tags = tags or []


class ScoreDecision:
    def __init__(self, score: int, should_apply: bool, reason: str):
        self.score = score
        self.should_apply = should_apply
        self.reason = reason


def _first_number(text: str) -> str:
    match = re.search(r"\d+(?:\.\d+)?", text or "")
    return match.group(0) if match else ""


def _line_value(profile_text: str, label: str) -> str:
    pattern = re.compile(rf"^\s*-\s*{re.escape(label)}\s*:\s*(.+?)\s*$", re.I | re.M)
    match = pattern.search(profile_text)
    return match.group(1).strip() if match else ""


def parse_profile_answers(profile_text: str) -> dict:
    skill_years = {}
    for match in re.finditer(r"^\s*-\s*Years of (.+?) experience\s*:\s*(.+?)\s*$", profile_text, re.I | re.M):
        skill = match.group(1).strip().lower()
        skill_years[skill] = _first_number(match.group(2))

    expected_ctc = _line_value(profile_text, "Expected CTC for SDE2-level roles")
    if not expected_ctc:
        expected_ctc = _line_value(profile_text, "Expected CTC")

    return {
        "email": _line_value(profile_text, "Email"),
        "location": _line_value(profile_text, "Location"),
        "current_ctc": _first_number(_line_value(profile_text, "Current CTC")),
        "expected_ctc": _first_number(expected_ctc),
        "notice_days": _first_number(_line_value(profile_text, "Notice period")),
        "work_authorization_india": _line_value(profile_text, "Authorized to work in India"),
        "highest_education": _line_value(profile_text, "Highest education"),
        "skill_years": skill_years,
    }


def _experience_min(experience: str) -> int | None:
    nums = [int(n) for n in re.findall(r"\d+", experience or "")]
    if not nums:
        return None
    return nums[0]


def score_job(job: JobRecord) -> ScoreDecision:
    title = job.title.lower()
    haystack = " ".join([job.title, job.description, " ".join(job.tags)]).lower()
    exp_min = _experience_min(job.experience)

    if exp_min is not None and exp_min >= 5:
        return ScoreDecision(3, False, "Hard 5+ year minimum")

    if any(pattern in title for pattern in SKIP_TITLE_PATTERNS):
        return ScoreDecision(1, False, "Frontend/mobile/QA/recruiter mismatch")

    if any(pattern in title for pattern in DEVOPS_ONLY_PATTERNS) and not any(
        signal in haystack for signal in ["backend", "api", "developer", "software"]
    ):
        return ScoreDecision(2, False, "Pure DevOps/SRE role without backend ownership")

    if any(signal in haystack for signal in BACKEND_SIGNALS):
        return ScoreDecision(4, True, "Backend/fullstack role; workspace scoring rule applies")

    return ScoreDecision(3, False, "Backend ownership unclear")


def should_skip_external_redirect(job: JobRecord, allow_external: bool = False) -> bool:
    return not allow_external


def is_actionable_naukri_notification(text: str) -> bool:
    normalized = (text or "").lower()
    if not normalized.strip():
        return False
    if any(pattern in normalized for pattern in ACTIONABLE_NOTIFICATION_PATTERNS):
        return True
    if any(pattern in normalized for pattern in COMMERCIAL_NOTIFICATION_PATTERNS):
        return False
    return False


def parse_existing_applications(output: str) -> set[tuple[str, str, str]]:
    existing = set()
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("-") or line.startswith("Company") or line.startswith("Total:"):
            continue
        parts = re.split(r"\s{2,}", line)
        if len(parts) < 3:
            continue
        company, role, platform = parts[0], parts[1], parts[2]
        existing.add((company.lower(), role.lower(), platform.lower()))
    return existing


def build_db_payload(job: JobRecord, resume_used: str = "", notes: str = "") -> dict:
    return {
        "company": job.company,
        "role": job.title,
        "platform": "naukri",
        "score": 4,
        "status": "Applied",
        "location": job.location,
        "notes": notes,
        "resume_used": resume_used,
        "url": job.apply_link,
    }


def normalize_job(job) -> JobRecord:
    return JobRecord(
        job_id=getattr(job, "job_id", "") or getattr(job, "id", ""),
        title=getattr(job, "title", ""),
        company=getattr(job, "company", ""),
        location=getattr(job, "location", ""),
        experience=getattr(job, "experience", ""),
        apply_link=getattr(job, "apply_link", ""),
        description=getattr(job, "description", ""),
        tags=list(getattr(job, "tags", []) or []),
    )


def load_noperi_clients():
    vendor_path = str(VENDOR_ROOT)
    if vendor_path not in sys.path:
        sys.path.insert(0, vendor_path)
    from src.client.job_client import NaukriJobClient
    from src.client.naukri_client import NaukriLoginClient
    from src.exceptions.exceptions import NaukriAuthError
    from src.models.models import NaukriSession

    class _CompatLoginClient(NaukriLoginClient):
        """Wraps NaukriLoginClient to fix httpcloak Session.cookies compat.

        httpcloak returns cookies as a list; vendor code calls .get() expecting
        a dict. Override login/verify_otp to use get_cookie() instead.
        """

        def _get_token(self):
            c = self.session.get_cookie("nauk_at")
            return c.value if c else None

        def login(self):
            res = self._login_request()
            if not res.ok:
                raise NaukriAuthError("Login failed")
            token = self._get_token()
            if not token:
                raise NaukriAuthError("No token")
            self.naukri_session = NaukriSession(token, self.session.cookies)
            try:
                self.cache["form_key"] = self.get_form_key2()
            except Exception:
                pass
            return self.naukri_session

        def verify_otp(self, otp: str, username: str = None, is_mobile: bool = True):
            res = self._verify_otp_request(username or self.username, otp, is_mobile)
            if not res.ok:
                raise NaukriAuthError(f"OTP verification failed ({res.status_code})")
            token = self._get_token()
            if not token:
                try:
                    token = res.json().get("authToken") or res.json().get("token")
                except Exception:
                    pass
            if not token:
                raise NaukriAuthError("OTP verified but no auth token received")
            self.naukri_session = NaukriSession(token, self.session.cookies)
            try:
                self.cache["form_key"] = self.get_form_key2()
            except Exception:
                pass
            return self.naukri_session

    return _CompatLoginClient, NaukriJobClient


def run_command(args: list[str]) -> str:
    result = subprocess.run(args, cwd=REPO_ROOT, check=True, text=True, capture_output=True)
    return result.stdout


def get_existing_applications() -> set[tuple[str, str, str]]:
    output = run_command([sys.executable, "scripts/db.py", "list"])
    return parse_existing_applications(output)


def pick_resume(job: JobRecord) -> str:
    job_text = " ".join([job.title, " ".join(job.tags), job.description[:500]]).strip()
    output = run_command([sys.executable, "scripts/pick_resume.py", job_text])
    match = re.search(r"(?:REUSE|TUNE)\|[^|]*\|([^|]+)\|", output)
    if match:
        return match.group(1).strip()
    for token in output.split():
        if token.endswith(".pdf"):
            return token
    return ""


def flush_applications(apps: list[dict], dry_run: bool) -> None:
    if not apps:
        return
    payload = json.dumps(apps)
    cmd = [sys.executable, "scripts/db_batch_insert.py", "--apps", payload]
    if dry_run:
        cmd.append("--dry-run")
    print(run_command(cmd), end="")


def save_pipeline(job: JobRecord, reason: str) -> None:
    PIPELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PIPELINE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"- Naukri | {job.company} | {job.title} | {reason} | {job.apply_link}\n")


def search_jobs(jc, pages: int, job_age: int) -> list[JobRecord]:
    seen = set()
    jobs: list[JobRecord] = []
    for query in SEARCH_QUERIES:
        for page in range(1, pages + 1):
            raw_jobs = jc.search_jobs(
                keyword=query["keyword"],
                location=query["location"],
                experience=3,
                job_age=job_age,
                page=page,
            )
            for raw_job in raw_jobs:
                job = normalize_job(raw_job)
                if not job.job_id or job.job_id in seen:
                    continue
                seen.add(job.job_id)
                jobs.append(job)
            time.sleep(1)
    return jobs


def answer_questionnaire(jc, raw_job, questionnaire, sid: str, profile_answers: dict, source: str):
    def answer_for(question: dict):
        qtext = (question.get("questionName") or "").lower()
        qtype = (question.get("questionType") or "").lower()
        options = question.get("answerOption") or {}

        if "current ctc" in qtext or "current salary" in qtext:
            return profile_answers["current_ctc"]
        if "expected ctc" in qtext or "expected salary" in qtext:
            return profile_answers["expected_ctc"]
        if "notice" in qtext:
            if options:
                for key, value in options.items():
                    if profile_answers["notice_days"] and profile_answers["notice_days"] in value:
                        return [key]
                for key, value in options.items():
                    if "2 month" in value.lower() or "60" in value:
                        return [key]
            return profile_answers["notice_days"]
        if "authorized" in qtext and "india" in qtext:
            if options:
                for key, value in options.items():
                    if "yes" in value.lower():
                        return [key]
            return profile_answers["work_authorization_india"] or "Yes"
        if "highest" in qtext and "qualification" in qtext:
            return profile_answers["highest_education"]
        for skill, years in profile_answers["skill_years"].items():
            if skill in qtext and "experience" in qtext:
                return years
        if qtype == "text box":
            return None
        if options:
            for key, value in options.items():
                if "yes" in value.lower():
                    return [key]
        return None

    answers = {}
    for question in questionnaire:
        value = answer_for(question)
        if value in (None, ""):
            raise ValueError(f"Unknown questionnaire field: {question.get('questionName')}")
        answers[question["questionId"]] = value

    from src.client.job_client import APPLY_SRC_MAP
    from src.config.constants import APPLY_JOB_URL

    apply_src, logstr_template = APPLY_SRC_MAP.get(source, APPLY_SRC_MAP["recommended"])
    tags = list(getattr(raw_job, "tags", []) or [])
    payload = {
        "strJobsarr": [raw_job.job_id],
        "logstr": logstr_template.format(sid=sid),
        "flowtype": "show",
        "crossdomain": True,
        "jquery": 1,
        "rdxMsgId": "",
        "chatBotSDK": True,
        "mandatory_skills": tags[:2],
        "optional_skills": tags[2:],
        "applyTypeId": "107",
        "closebtn": "y",
        "applySrc": apply_src,
        "sid": sid,
        "mid": "",
        "applyData": {raw_job.job_id: {"answers": answers}},
    }
    response = jc._session.post(APPLY_JOB_URL, headers=jc._client._build_headers(auth=True), json=payload)
    if not response.ok:
        raise RuntimeError(f"Questionnaire apply failed: {response.status_code} {response.text[:200]}")
    return response.json()


def run(args: argparse.Namespace) -> int:
    profile_answers = parse_profile_answers(PROFILE_PATH.read_text(encoding="utf-8"))
    existing = get_existing_applications()

    username = os.getenv("NAUKRI_USERNAME") or os.getenv("USERNAME")
    password = os.getenv("NAUKRI_PASSWORD") or os.getenv("PASSWORD")
    if not username or not password:
        raise SystemExit("Set NAUKRI_USERNAME/NAUKRI_PASSWORD or USERNAME/PASSWORD in the environment.")

    NaukriLoginClient, NaukriJobClient = load_noperi_clients()
    client = NaukriLoginClient(username, password)
    client.login()
    jc = NaukriJobClient(client)

    jobs = search_jobs(jc, pages=args.pages, job_age=args.job_age)
    applied_batch = []
    applied = []
    skipped = []
    blocked = []

    for job in jobs:
        if len(applied) >= args.limit:
            break

        key = (job.company.lower(), job.title.lower(), "naukri")
        if key in existing:
            skipped.append((job, "duplicate in DB"))
            continue

        decision = score_job(job)
        if not decision.should_apply:
            skipped.append((job, decision.reason))
            continue

        is_external = jc.is_external_apply(job.job_id)
        if is_external:
            reason = "external company-site apply skipped by default"
            blocked.append((job, reason))
            if args.allow_external_pipeline:
                save_pipeline(job, reason)
            continue

        resume = pick_resume(job)
        notes = f"Direct Naukri API apply via NopeRi adapter; {decision.reason}"

        print(f"READY: {job.company} — {job.title} | score={decision.score} | resume={resume}")
        if args.dry_run or args.no_apply:
            applied_batch.append(build_db_payload(job, resume_used=resume, notes=notes))
            continue

        raw_job = next(raw for raw in jobs if raw.job_id == job.job_id)
        result = jc.apply_job(raw_job, mandatory_skills=job.tags[:2], optional_skills=job.tags[2:], source="search")
        first_result = (result.get("jobs") or [{}])[0]
        if first_result.get("questionnaire"):
            sid = time.strftime("%Y%m%d%H%M%S") + "0000000"
            try:
                answer_questionnaire(jc, raw_job, first_result["questionnaire"], sid, profile_answers, source="search")
            except ValueError as exc:
                blocked.append((job, str(exc)))
                save_pipeline(job, str(exc))
                continue

        payload = build_db_payload(job, resume_used=resume, notes=notes)
        applied_batch.append(payload)
        applied.append(job)
        existing.add(key)

        if len(applied_batch) >= 4:
            flush_applications(applied_batch, dry_run=False)
            applied_batch.clear()

    if applied_batch:
        flush_applications(applied_batch, dry_run=args.dry_run or args.no_apply)

    print_report(applied, skipped, blocked)
    return 0


def print_report(applied: list[JobRecord], skipped: list[tuple[JobRecord, str]], blocked: list[tuple[JobRecord, str]]) -> None:
    print("\n## Naukri Run")
    print(f"\n### Applied ({len(applied)} jobs)")
    for job in applied:
        print(f"- {job.company} | {job.title} | {job.location} | 4/5 | Direct API")
    print(f"\n### Skipped ({len(skipped)} jobs)")
    for job, reason in skipped[:50]:
        print(f"- {job.company} | {job.title} | {reason}")
    print(f"\n### Saved to pipeline ({len(blocked)} jobs)")
    for job, reason in blocked:
        print(f"- {job.company} | {job.title} | {reason} | {job.apply_link}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply to Naukri jobs through the vendored NopeRi API client.")
    parser.add_argument("--dry-run", action="store_true", help="Search, score, and print DB payloads without applying.")
    parser.add_argument("--no-apply", action="store_true", help="Do not submit applications; useful for interactive review.")
    parser.add_argument("--limit", type=int, default=15, help="Maximum direct Naukri applications to submit.")
    parser.add_argument("--pages", type=int, default=1, help="Search pages per keyword.")
    parser.add_argument("--job-age", type=int, default=7, help="Naukri jobAge filter in days.")
    parser.add_argument("--allow-external-pipeline", action="store_true", help="Save external redirects to data/pipeline.md.")
    parser.set_defaults(browser_fallback=False)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
