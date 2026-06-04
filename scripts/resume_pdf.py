#!/usr/bin/env python3
"""
resume_pdf.py - Compile a LaTeX resume to PDF using pdflatex.

Usage:
    python3 scripts/resume_pdf.py resumes/base.tex output/base.pdf
"""
import subprocess
import shutil
import sys
import os
import tempfile
from pathlib import Path


def build_pdf(tex_path: str, out_pdf: str):
    tex = Path(tex_path).resolve()
    out = Path(out_pdf).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={tmp}",
                str(tex),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout[-3000:])
            print(result.stderr[-1000:])
            raise RuntimeError(f"pdflatex failed (exit {result.returncode})")

        generated = Path(tmp) / (tex.stem + ".pdf")
        if not generated.exists():
            raise FileNotFoundError(f"pdflatex ran but {generated} not found")
        shutil.copy2(generated, out)

    print(f"Built: {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/resume_pdf.py <input.tex> <output.pdf>")
        sys.exit(1)
    build_pdf(sys.argv[1], sys.argv[2])
