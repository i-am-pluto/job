# Job Search Plugin

Automated job-search workspace for scanning jobs, choosing resumes, filling applications, tracking status, and running an autonomous nightly application flow.

## Prerequisites

- Claude Code with this repo installed as a plugin
- Claude-in-Chrome MCP/browser access for Gmail, Instahyre, LinkedIn, and Naukri
- Python 3.10+
- `wkhtmltopdf` is optional; PDF generation in this repo uses `scripts/resume_pdf.py`

## Setup

```bash
git clone <repo-url>
cd job
python3 scripts/setup.py
```

The setup script creates:

- `config/user.yml`
- `profile.md`
- `resumes/base.md`
- `data/applications.db`

After setup, fill in the missing resume bullets in `resumes/base.md`, then generate the PDF:

```bash
python3 scripts/resume_pdf.py resumes/base.md output/base.pdf
```

## Plugin Commands

- `nightly-job-apply` - run the autonomous nightly workflow
- `job-apply-status` - summarize applications, blockers, and action-needed items
- `tune-job-search` - review resume/cache strategy and tune when justified

## Resume Workflow

Markdown is the source of truth for resumes. Edit markdown, then regenerate PDFs:

```bash
python3 scripts/resume_pdf.py resumes/base.md output/base.pdf
python3 scripts/resume_pdf.py resumes/backend-systems.md output/backend-systems.pdf
python3 scripts/resume_pdf.py resumes/ai-backend.md output/ai-backend.pdf
```

The application agents choose cached PDFs through:

```bash
python3 scripts/pick_resume.py "<job title + skill tags + JD text>"
```

## Customization

- Edit `config/user.yml` for identity and standard application-answer facts.
- Regenerate `profile.md` with `scripts/setup.py` when onboarding a new user.
- Edit `profile.md` for scoring rules, target roles, avoid rules, location preferences, and fit policy.
- Keep generated PDFs in `output/`; never edit PDFs directly.
