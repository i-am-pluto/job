#!/usr/bin/env python3
"""Interactive onboarding for the job-search plugin.

No external dependencies. Generates:
- config/user.yml
- profile.md
- resumes/base.md starter skeleton
- data/applications.db via scripts/init_db.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "config" / "user.yml"
PROFILE_TEMPLATE_PATH = REPO_ROOT / "profile.template.md"
PROFILE_PATH = REPO_ROOT / "profile.md"
BASE_RESUME_PATH = REPO_ROOT / "resumes" / "base.md"


def prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def prompt_list(label: str) -> list[str]:
    raw = prompt(f"{label} (comma-separated)")
    return [item.strip() for item in raw.split(",") if item.strip()]


def prompt_skills() -> dict[str, str]:
    print("\nTech stack")
    print("Enter one skill per line as: Skill, years. Leave blank when done.")
    skills: dict[str, str] = {}
    while True:
        raw = input("Skill, years: ").strip()
        if not raw:
            break
        if "," not in raw:
            print("Please use: Skill, years")
            continue
        skill, years = [part.strip() for part in raw.split(",", 1)]
        if skill:
            skills[skill] = years
    return skills


def collect_answers() -> dict:
    print("Job Search Plugin Setup\n")

    print("1. Identity")
    full_name = prompt("Full name")
    email = prompt("Email")
    phone = prompt("Phone")
    location = prompt("Location")
    linkedin = prompt("LinkedIn URL")
    github = prompt("GitHub URL")

    print("\n2. Current role")
    current_company = prompt("Current company")
    current_title = prompt("Current title")
    experience_years = prompt("Total years of experience")

    print("\n3. Target roles")
    target_roles = prompt_list("Target roles")

    skills_years = prompt_skills()

    print("\n5. Locations")
    remote_preference = prompt("Remote/hybrid preference")
    willing_to_relocate = prompt("Willing to relocate? (Yes/No)")

    print("\n6. Compensation")
    current_ctc = prompt("Current compensation")
    expected_ctc = prompt("Expected compensation")
    notice_days = prompt("Notice period in days")
    currency = prompt("Currency", "INR")

    print("\n7. Work authorization")
    work_auth_india = prompt("Authorized to work in India? (Yes/No)")
    highest_education = prompt("Highest education")
    graduation_year = prompt("Graduation year")
    gpa = prompt("GPA")

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "location": location,
        "linkedin": linkedin,
        "github": github,
        "current_company": current_company,
        "current_title": current_title,
        "experience_years": experience_years,
        "target_roles": target_roles,
        "skills_years": skills_years,
        "remote_preference": remote_preference,
        "willing_to_relocate": willing_to_relocate,
        "current_ctc": current_ctc,
        "expected_ctc": expected_ctc,
        "notice_days": notice_days,
        "currency": currency,
        "work_auth_india": work_auth_india,
        "highest_education": highest_education,
        "graduation_year": graduation_year,
        "gpa": gpa,
    }


def build_user_config(answers: dict) -> dict:
    return {
        "identity": {
            "full_name": answers.get("full_name", ""),
            "email": answers.get("email", ""),
            "phone": answers.get("phone", ""),
            "location": answers.get("location", ""),
            "linkedin": answers.get("linkedin", ""),
            "github": answers.get("github", ""),
        },
        "current_role": {
            "current_company": answers.get("current_company", ""),
            "current_title": answers.get("current_title", ""),
            "experience_years": answers.get("experience_years", ""),
        },
        "targeting": {
            "target_roles": answers.get("target_roles", []),
            "remote_preference": answers.get("remote_preference", ""),
            "willing_to_relocate": answers.get("willing_to_relocate", ""),
        },
        "application_answers": {
            "current_ctc": answers.get("current_ctc", ""),
            "expected_ctc": answers.get("expected_ctc", ""),
            "notice_days": answers.get("notice_days", ""),
            "currency": answers.get("currency", ""),
            "work_auth_india": answers.get("work_auth_india", ""),
            "skills_years": answers.get("skills_years", {}),
            "highest_education": answers.get("highest_education", ""),
            "graduation_year": answers.get("graduation_year", ""),
            "gpa": answers.get("gpa", ""),
        },
    }


def yaml_scalar(value: object) -> str:
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def dump_yaml(data: object, indent: int = 0) -> str:
    spaces = " " * indent
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if value == []:
                lines.append(f"{spaces}{key}: []")
            elif value == {}:
                lines.append(f"{spaces}{key}: {{}}")
            elif isinstance(value, (dict, list)):
                lines.append(f"{spaces}{key}:")
                nested = dump_yaml(value, indent + 2)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{spaces}{key}: {yaml_scalar(value)}")
        return "\n".join(lines)
    if isinstance(data, list):
        if not data:
            return f"{spaces}[]"
        return "\n".join(f"{spaces}- {yaml_scalar(item)}" for item in data)
    return f"{spaces}{yaml_scalar(data)}"


def render_user_yml(answers: dict) -> str:
    return (
        "# Job Search User Configuration\n"
        "# Generated by scripts/setup.py. Keep identity and application-answer facts here.\n\n"
        + dump_yaml(build_user_config(answers))
        + "\n"
    )


def bullet_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Add target roles"


def skill_year_lines(skills: dict[str, str]) -> str:
    if not skills:
        return "- Add skill experience answers"
    return "\n".join(f"- Years of {skill} experience: {years}" for skill, years in skills.items())


def render_profile(answers: dict) -> str:
    template = PROFILE_TEMPLATE_PATH.read_text(encoding="utf-8")
    skills = answers.get("skills_years", {})
    replacements = {
        "FULL_NAME": answers.get("full_name", ""),
        "EMAIL": answers.get("email", ""),
        "PHONE": answers.get("phone", ""),
        "LOCATION": answers.get("location", ""),
        "LINKEDIN": answers.get("linkedin", ""),
        "GITHUB": answers.get("github", ""),
        "CURRENT_COMPANY": answers.get("current_company", ""),
        "CURRENT_TITLE": answers.get("current_title", ""),
        "EXPERIENCE_YEARS": answers.get("experience_years", ""),
        "TARGET_ROLES": bullet_list(answers.get("target_roles", [])),
        "STRONG_FIT_SIGNALS": bullet_list(list(skills.keys())),
        "REMOTE_PREFERENCE": answers.get("remote_preference", ""),
        "WILLING_TO_RELOCATE": answers.get("willing_to_relocate", ""),
        "WORK_AUTH_INDIA": answers.get("work_auth_india", ""),
        "CURRENT_CTC": answers.get("current_ctc", ""),
        "EXPECTED_CTC": answers.get("expected_ctc", ""),
        "NOTICE_DAYS": answers.get("notice_days", ""),
        "SKILLS_YEARS": skill_year_lines(skills),
        "HIGHEST_EDUCATION": answers.get("highest_education", ""),
        "GRADUATION_YEAR": answers.get("graduation_year", ""),
        "GPA": answers.get("gpa", ""),
    }
    for key, value in replacements.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def render_base_resume(answers: dict) -> str:
    contact = " | ".join(
        part
        for part in [
            answers.get("phone", ""),
            answers.get("email", ""),
            answers.get("location", ""),
            answers.get("linkedin", ""),
            answers.get("github", ""),
        ]
        if part
    )
    return f"""# {answers.get("full_name", "")}
{contact}

## SUMMARY

Add a 2-4 line summary tailored to your target roles.

## EXPERIENCE

**Company - Title** | Location | Dates
- Add truthful impact bullets with metrics where available.

## PROJECTS

**Project Name** | Tech stack
- Add concise project bullets relevant to your target roles.

## EDUCATION

**School** | Degree | GPA | Dates

## SKILLS

**Languages:** Add languages
**Backend:** Add backend frameworks and APIs
**Cloud/Data/Infra:** Add cloud, data, and infrastructure tools
"""


def write_generated_files(answers: dict) -> None:
    (REPO_ROOT / "config").mkdir(exist_ok=True)
    (REPO_ROOT / "resumes").mkdir(exist_ok=True)
    CONFIG_PATH.write_text(render_user_yml(answers), encoding="utf-8")
    PROFILE_PATH.write_text(render_profile(answers), encoding="utf-8")
    BASE_RESUME_PATH.write_text(render_base_resume(answers), encoding="utf-8")


def init_db() -> None:
    subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "init_db.py")], check=True)


def main() -> int:
    answers = collect_answers()
    write_generated_files(answers)
    init_db()
    print("\nSetup complete.")
    print("\nNext steps:")
    print("- Fill out resume bullets in resumes/base.md.")
    print("- Generate a PDF with: python3 scripts/resume_pdf.py resumes/base.md output/base.pdf")
    print("- Review profile.md scoring rules and target roles.")
    print("- Add the plugin from this repo in Claude Code.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
