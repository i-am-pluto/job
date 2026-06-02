#!/usr/bin/env python3
"""
Greenhouse API adapter — NopeRi-style, zero-browser discovery + scoring + dedupe
+ resume selection + answer preparation for Greenhouse-hosted job boards.

Why this exists
---------------
Good companies cluster on Greenhouse, but the only apply path today is the
browser `generic-apply` flow (screenshots + coordinate clicks), which is
expensive and fragile. Greenhouse already exposes a fully public read API, so
discovery/scoring/dedupe/answer-prep need no browser at all.

Submit is GATED (see A0 in the plan)
------------------------------------
Greenhouse hosted-board *submission* is NOT openly public:
  - boards-api `POST /v1/boards/{token}/jobs/{id}` requires a per-board
    "Job Board API key" (HTTP Basic) that we do not have.
  - The hosted form submit (boards.greenhouse.io / job-boards.greenhouse.io)
    posts multipart form-data with a CSRF/authenticity token scraped from the
    rendered page.
The exact contract must be confirmed with a live network-capture spike before we
trust an API submit. Until then this adapter prepares each application fully
(scored, deduped, resume chosen, identity answers mapped from the live questions
schema) and DEGRADES GRACEFULLY: it queues qualifying jobs for the browser
`generic-apply` path (and can append them to data/pipeline.md) instead of
blocking. `submit_via_api()` is the single, clearly-marked place to wire the
confirmed endpoint after the spike.

Public read endpoints used (no auth, no cookies):
  GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true
  GET https://boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}?questions=true
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
PROFILE_PATH = REPO_ROOT / "profile.md"
BOARDS_PATH = REPO_ROOT / "config" / "greenhouse_boards.yml"
PIPELINE_PATH = REPO_ROOT / "data" / "pipeline.md"

# Reuse the Naukri adapter's scoring + dedupe + profile parsing rather than
# reinventing them. Its vendored NopeRi imports are deferred inside functions,
# so importing the module here does not require NopeRi to be installed.
sys.path.insert(0, str(SCRIPTS_DIR))
import naukri_noperi_apply as nk  # noqa: E402

API_BASE = "https://boards-api.greenhouse.io/v1/boards"


# --------------------------------------------------------------------------- #
# Board config (hand-parsed; pyyaml is not installed in this environment)
# --------------------------------------------------------------------------- #
def load_boards(path: Path) -> list[dict]:
    """Parse the simple list-of-mappings greenhouse_boards.yml without pyyaml."""
    boards: list[dict] = []
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"\s*-\s*company:\s*(.+)$", line)
        if m:
            if current:
                boards.append(current)
            current = {"company": _yaml_scalar(m.group(1))}
            continue
        if current is None:
            continue
        m = re.match(r"\s+(\w+):\s*(.+)$", line)
        if m:
            current[m.group(1)] = _yaml_scalar(m.group(2))
    if current:
        boards.append(current)
    return boards


def _yaml_scalar(v: str) -> str:
    return v.strip().strip('"').strip("'")


def is_board_active(board: dict) -> bool:
    return str(board.get("active", "true")).lower() != "false"


# --------------------------------------------------------------------------- #
# Public Greenhouse read API
# --------------------------------------------------------------------------- #
def http_get_json(url: str, timeout: int = 20) -> tuple[int, dict | None]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 greenhouse-adapter"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"  ! fetch error for {url}: {exc}", file=sys.stderr)
        return 0, None


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = text.replace("&amp;", "&").replace("&nbsp;", " ").replace("&#39;", "'")
    return re.sub(r"\s+", " ", text).strip()


def fetch_board_jobs(token: str) -> tuple[int, list[dict]]:
    status, data = http_get_json(f"{API_BASE}/{token}/jobs?content=true")
    if status != 200 or not data:
        return status, []
    return status, data.get("jobs", []) or []


def fetch_job_questions(token: str, job_id) -> list[dict]:
    status, data = http_get_json(f"{API_BASE}/{token}/jobs/{job_id}?questions=true")
    if status != 200 or not data:
        return []
    return data.get("questions", []) or []


# --------------------------------------------------------------------------- #
# Job model + scoring (reuse Naukri scoring rules)
# --------------------------------------------------------------------------- #
def _experience_hint(content: str) -> str:
    """Pull a '5+ years' style minimum out of JD text for nk.score_job."""
    m = re.search(r"(\d+)\+?\s*years", content or "", re.I)
    return f"{m.group(1)} years" if m else ""


def _job_age_days(job: dict) -> int | None:
    raw = job.get("updated_at") or job.get("first_published")
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).days
    except ValueError:
        return None


def to_record(company: str, job: dict) -> SimpleNamespace:
    content = _strip_html(job.get("content", ""))
    return SimpleNamespace(
        job_id=str(job.get("id")),
        company=company,
        title=job.get("title", "").strip(),
        location=(job.get("location") or {}).get("name", "").strip(),
        description=content,
        tags=[],
        experience=_experience_hint(content),
        absolute_url=job.get("absolute_url", ""),
        age_days=_job_age_days(job),
    )


# Greenhouse boards list EVERY department (sales, legal, marketing...), unlike a
# Naukri engineering search. Gate to engineering titles before applying the shared
# scorer, otherwise non-eng roles whose JD merely mentions "API"/"platform" leak through.
ENG_TITLE_SIGNALS = (
    "engineer", "developer", "sde", "swe", "programmer", "architect", "software",
    "backend", "back end", "back-end", "full stack", "fullstack", "full-stack",
    "platform engineer", "infrastructure engineer",
)
NON_ENG_TITLE_SIGNALS = (
    "account executive", "sales", "marketing", "recruit", "counsel", "legal",
    "designer", "customer success", "support", "accountant", "finance",
    "partnerships", "solutions consultant", "business development", "account manager",
    "manager",  # IC candidate — exclude Engineering/people-management roles
    "director", "head of", "vp ", "vice president", "intern",
)


def is_engineering_title(title: str) -> bool:
    t = (title or "").lower()
    if any(bad in t for bad in NON_ENG_TITLE_SIGNALS):
        return False
    return any(sig in t for sig in ENG_TITLE_SIGNALS)


def jd_keywords(rec: SimpleNamespace, limit: int = 3) -> list[str]:
    vocab = [
        "Java", "Kotlin", "Python", "Go", "Golang", "Spring Boot", "distributed systems",
        "Kafka", "PostgreSQL", "MySQL", "AWS", "GCP", "Kubernetes", "Docker",
        "microservices", "LLM", "RAG", "Spark", "gRPC", "REST", "GraphQL", "Redis",
    ]
    hay = (rec.title + " " + rec.description).lower()
    hits = [kw for kw in vocab if kw.lower() in hay]
    return hits[:limit]


# --------------------------------------------------------------------------- #
# Answer mapping (identity fields from the live questions schema)
# --------------------------------------------------------------------------- #
def map_identity_answers(questions: list[dict], profile_answers: dict) -> tuple[dict, list[str]]:
    """Map standard Greenhouse identity fields. Returns (answers, unmapped_required)."""
    name = "Parikshit Dabas"
    parts = name.split()
    standard = {
        "first_name": parts[0],
        "last_name": parts[-1],
        "email": profile_answers.get("email", ""),
        "phone": profile_answers.get("phone", ""),
    }
    answers: dict = {}
    unmapped_required: list[str] = []
    for q in questions:
        field_names = [f.get("name", "") for f in q.get("fields", [])]
        label = (q.get("label") or "").strip()
        mapped = False
        for fname in field_names:
            base = fname.rstrip("[]")
            if base in standard and standard[base]:
                answers[base] = standard[base]
                mapped = True
            elif base in ("resume", "cover_letter"):
                mapped = True  # handled at upload time, not a text answer
        if not mapped and q.get("required") and not any(
            b.rstrip("[]") in ("resume", "cover_letter", "resume_text", "cover_letter_text")
            for b in field_names
        ):
            unmapped_required.append(label or ",".join(field_names))
    return answers, unmapped_required


# --------------------------------------------------------------------------- #
# Resume selection
# --------------------------------------------------------------------------- #
def pick_resume(rec: SimpleNamespace) -> str:
    query = f"{rec.title} {' '.join(jd_keywords(rec))} {rec.description[:400]}"
    try:
        out = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "pick_resume.py"), query],
            capture_output=True, text=True, timeout=30,
        ).stdout.strip()
        # Format: REUSE|tag|pdf|score  or  TUNE|tag|pdf|score
        parts = out.split("|")
        if len(parts) >= 3:
            return parts[2]
    except Exception as exc:  # noqa: BLE001
        print(f"  ! pick_resume failed: {exc}", file=sys.stderr)
    return "output/base.pdf"


# --------------------------------------------------------------------------- #
# Submit — GATED. Wire the confirmed endpoint here after the A0 spike.
# --------------------------------------------------------------------------- #
def submit_via_api(rec, answers, resume_pdf) -> dict:
    """Intentionally NOT implemented — degrade to the browser generic-apply path.

    A0 spike conclusion (2026-06-03, inspected job-boards.greenhouse.io live):
      - New Greenhouse hosted boards are a React SPA. Application fields use `id`
        (first_name, last_name, email, country, phone) with NO `name` attribute,
        no inline authenticity_token, and no csrf-token meta — state is React-held.
      - Submit fires via a JS fetch to a non-public API endpoint, observable only
        by capturing a real submission POST (an irreversible apply we won't do for
        a spike). Even then it rides the SPA's session/anti-bot tokens, so a
        headless urllib submit would be fragile per-board.
      - The public boards-api (read) has no public write counterpart without a
        per-board Job Board API key we do not possess.
    Therefore: discovery/score/dedupe/prepare stay here (zero-browser, high value),
    and the actual submit is done by the browser `generic-apply` flow in the
    logged-in session where the SPA manages its own CSRF/session. This is final,
    not a TODO.
    """
    return {"submitted": False, "reason": "no_public_submit_api_use_generic_apply"}


# --------------------------------------------------------------------------- #
# Pipeline queueing (degrade path)
# --------------------------------------------------------------------------- #
def append_to_pipeline(prepared: list[dict]) -> None:
    if not prepared:
        return
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [f"\n## Greenhouse — API-prepared, route to generic-apply ({today})\n"]
    for p in prepared:
        lines.append(
            f"- {p['company']} | {p['role']} | {p['location']} | score {p['score']} "
            f"| resume {p['resume']} | {p['url']}"
        )
    with PIPELINE_PATH.open("a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Appended {len(prepared)} prepared Greenhouse jobs to {PIPELINE_PATH}")


# --------------------------------------------------------------------------- #
# Main run
# --------------------------------------------------------------------------- #
def run(args: argparse.Namespace) -> int:
    profile_answers = nk.parse_profile_answers(PROFILE_PATH.read_text(encoding="utf-8"))
    # parse_profile_answers does not capture phone; add it for Greenhouse forms.
    profile_answers.setdefault("phone", _profile_phone())
    existing = nk.get_existing_applications()

    boards = [b for b in load_boards(BOARDS_PATH) if is_board_active(b)]
    print(f"Scanning {len(boards)} active Greenhouse boards (limit {args.limit} applies)\n")

    prepared: list[dict] = []
    skipped: list[tuple[str, str, str]] = []
    applied_db_rows: list[dict] = []

    for board in boards:
        if len(prepared) >= args.limit:
            break
        company = board.get("company") or board["token"]
        token = board["token"]
        status, jobs = fetch_board_jobs(token)
        if status == 404:
            print(f"[{company}] 404 — board inactive (mark active:false manually)")
            continue
        if status != 200:
            print(f"[{company}] status {status} — skipping this run")
            continue

        for job in jobs:
            if len(prepared) >= args.limit:
                break
            rec = to_record(company, job)
            if rec.age_days is not None and rec.age_days > args.job_age:
                continue
            if not is_engineering_title(rec.title):
                skipped.append((company, rec.title, "non-engineering role"))
                continue
            decision = nk.score_job(rec)
            if not decision.should_apply:
                skipped.append((company, rec.title, decision.reason))
                continue
            key = (company.lower(), rec.title.lower(), "greenhouse")
            if key in existing:
                skipped.append((company, rec.title, "duplicate (already in DB)"))
                continue

            questions = fetch_job_questions(token, rec.job_id)
            answers, unmapped = map_identity_answers(questions, profile_answers)
            resume_pdf = pick_resume(rec)

            entry = {
                "company": company,
                "role": rec.title,
                "location": rec.location,
                "score": decision.score,
                "resume": resume_pdf,
                "url": rec.absolute_url,
                "unmapped_required": unmapped,
            }
            prepared.append(entry)
            existing.add(key)

            if args.dry_run or args.no_apply:
                continue

            # Try API submit (gated). Degrade to generic-apply queue otherwise.
            result = submit_via_api(rec, answers, resume_pdf)
            if result.get("submitted"):
                applied_db_rows.append({
                    "company": company, "role": rec.title, "platform": "greenhouse",
                    "score": decision.score, "status": "Applied", "location": rec.location,
                    "notes": "Greenhouse API direct submit",
                })

    _report(prepared, skipped)

    if args.dry_run:
        print("\n[dry-run] no submit, no DB write, no pipeline append.")
        return 0

    if applied_db_rows:
        _flush_db(applied_db_rows)
    if args.queue or (not args.no_apply and not applied_db_rows):
        # Submit endpoint not yet confirmed -> hand prepared jobs to browser path.
        append_to_pipeline(prepared)
    return 0


def _profile_phone() -> str:
    m = re.search(r"^\s*-\s*Phone\s*:\s*(.+)$", PROFILE_PATH.read_text(encoding="utf-8"), re.I | re.M)
    return m.group(1).strip() if m else ""


def _flush_db(rows: list[dict]) -> None:
    try:
        subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "db_batch_insert.py"), "--apps", json.dumps(rows)],
            check=True, timeout=60,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"! DB flush failed (continuing): {exc}", file=sys.stderr)


def _report(prepared: list[dict], skipped: list[tuple[str, str, str]]) -> None:
    print(f"\n=== Prepared {len(prepared)} qualifying jobs ===")
    for p in prepared:
        flag = f"  [needs custom answers: {', '.join(p['unmapped_required'])}]" if p["unmapped_required"] else ""
        print(f"  + {p['company']} | {p['role']} | {p['location']} | {p['score']}/5 | {p['resume']}{flag}")
    print(f"\n=== Skipped {len(skipped)} ===")
    for company, title, reason in skipped[:25]:
        print(f"  - {company} | {title} | {reason}")
    if len(skipped) > 25:
        print(f"  ... and {len(skipped) - 25} more")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Greenhouse API adapter (zero-browser discovery + prepare).")
    p.add_argument("--limit", type=int, default=10, help="max qualifying jobs to prepare/apply")
    p.add_argument("--job-age", type=int, default=7, help="max job age in days")
    p.add_argument("--boards", type=Path, default=BOARDS_PATH, help="boards yml path")
    p.add_argument("--dry-run", action="store_true", help="score+dedupe+prepare; no submit, no writes")
    p.add_argument("--no-apply", action="store_true", help="prepare only; no submit, no pipeline append")
    p.add_argument("--queue", action="store_true", help="append prepared jobs to data/pipeline.md for generic-apply")
    return p


if __name__ == "__main__":
    sys.exit(run(build_parser().parse_args()))
