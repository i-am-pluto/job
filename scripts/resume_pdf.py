#!/usr/bin/env python3
"""
resume_pdf.py - Markdown resume -> clean, ATS-friendly, ONE-PAGE PDF.

Claude-native PDF generation (reportlab only - no node, no browser).

Layout goal: a polished single page that FILLS the page - company/role on
the left, location/dates right-aligned, section rules, tight spacing.
The output must never exceed one page; the script warns loudly if it does.

Usage:
    python3 scripts/resume_pdf.py resumes/base.md output/base.pdf

Markdown format (see resumes/base.md):
    # NAME
    contact | line | here

    ## EXPERIENCE
    **Company - Title** | Location | Dates
    - bullet

    ## PROJECTS
    **Project Name** | Tech, Stack
    - bullet

    ## EDUCATION
    **School** | Degree | GPA: x | Dates
    Coursework: ...

    ## SKILLS
    **Category:** items
"""
import sys
import re
import tempfile
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Flowable, Table, TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas as _canvas

INK = HexColor("#1a1a2e")
ACCENT = HexColor("#23234d")
RULE = HexColor("#9a9ab0")


def normalize_ats(text: str) -> str:
    """Replace characters that trip up ATS parsers."""
    repl = {
        "—": " - ", "–": "-", "‘": "'", "’": "'",
        "“": '"', "”": '"', "…": "...", " ": " ",
        "​": "", "⁠": "", "﻿": "",
    }
    for k, v in repl.items():
        text = text.replace(k, v)
    return text


def md_inline(text: str) -> str:
    """Convert **bold** / *italic* markdown to reportlab markup; escape the rest."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    return text


class HRule(Flowable):
    """A thin horizontal rule used under section headers."""
    def __init__(self, width, thickness=0.45, color=RULE,
                 space_before=0.4, space_after=1.4):
        super().__init__()
        self.width = width
        self.thickness = thickness
        self.color = color
        self.space_before = space_before
        self.space_after = space_after

    def wrap(self, aw, ah):
        return (self.width, self.thickness + self.space_before + self.space_after)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        y = self.space_after
        self.canv.line(0, y, self.width, y)


def build_styles(font_scale=1.0, spacing_scale=1.0):
    def fs(value):
        return value * font_scale

    def ls(value):
        return value * font_scale * spacing_scale

    def sp(value):
        return value * spacing_scale

    ss = getSampleStyleSheet()
    base = ss["Normal"]
    return {
        "name": ParagraphStyle("name", parent=base, fontName="Helvetica-Bold",
                               fontSize=fs(15.5), leading=ls(17.2),
                               alignment=TA_CENTER, textColor=INK,
                               spaceAfter=sp(1.2)),
        "contact": ParagraphStyle("contact", parent=base, fontName="Helvetica",
                                  fontSize=fs(7.7), leading=ls(9),
                                  alignment=TA_CENTER, textColor=INK,
                                  spaceAfter=0),
        "section": ParagraphStyle("section", parent=base,
                                  fontName="Helvetica-Bold", fontSize=fs(8.8),
                                  leading=ls(9.8), textColor=ACCENT,
                                  spaceBefore=sp(4)),
        "company": ParagraphStyle("company", parent=base,
                                  fontName="Helvetica-Bold", fontSize=fs(8.35),
                                  leading=ls(9.4), textColor=INK),
        "role": ParagraphStyle("role", parent=base, fontName="Helvetica-Oblique",
                               fontSize=fs(8.1), leading=ls(9.1),
                               textColor=INK),
        "meta": ParagraphStyle("meta", parent=base, fontName="Helvetica",
                               fontSize=fs(7.2), leading=ls(8.4),
                               textColor=INK,
                               alignment=TA_RIGHT),
        "meta_i": ParagraphStyle("meta_i", parent=base,
                                 fontName="Helvetica-Oblique",
                                 fontSize=fs(7.5), leading=ls(8.6),
                                 textColor=INK,
                                 alignment=TA_RIGHT),
        "body": ParagraphStyle("body", parent=base, fontName="Helvetica",
                               fontSize=fs(7.9), leading=ls(9.1),
                               textColor=INK, spaceAfter=sp(0.6)),
        "bullet": ParagraphStyle("bullet", parent=base, fontName="Helvetica",
                                 fontSize=fs(7.85), leading=ls(8.75),
                                 textColor=INK, leftIndent=sp(9.2),
                                 bulletIndent=sp(0.5), spaceBefore=0,
                                 spaceAfter=sp(0.7),
                                 bulletFontName="Helvetica",
                                 bulletFontSize=fs(6.6)),
    }


def parse_md(md: str):
    """Parse resume markdown into (name, contact, [(section, [blocks])])."""
    lines = [l.rstrip() for l in md.splitlines()]
    name, contact = "", ""
    sections, cur_section, cur_blocks = [], None, None
    i = 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("# ") and not name:
            name = l[2:].strip()
        elif l.startswith("## "):
            break
        elif l.strip() and name and not contact:
            contact = l.strip()
        i += 1
    while i < len(lines):
        l = lines[i]
        if l.startswith("## "):
            if cur_section is not None:
                sections.append((cur_section, cur_blocks))
            cur_section, cur_blocks = l[3:].strip(), []
        elif cur_section is not None:
            if l.startswith("- "):
                cur_blocks.append(("bullet", l[2:].strip()))
            elif l.strip().startswith("**"):
                cur_blocks.append(("entry", l.strip()))
            elif l.strip():
                cur_blocks.append(("text", l.strip()))
        i += 1
    if cur_section is not None:
        sections.append((cur_section, cur_blocks))
    return name, contact, sections


def two_col_table(left_flow, right_flow, lw, rw):
    """A borderless 2-column row: left-aligned + right-aligned."""
    t = Table([[left_flow, right_flow]], colWidths=[lw, rw])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def render_entry(section, text, styles, lw, rw):
    """Render an entry header. Layout depends on the section."""
    raw = text.strip()
    raw = re.sub(r"^\*\*|\*\*$", "", raw)  # strip outer ** on the first token
    # split on ' | ' but the bold token is only the part before the first ' | '
    parts = [p.strip() for p in text.split("|")]
    head = re.sub(r"\*\*", "", parts[0]).strip()
    rest = [p for p in parts[1:]]

    sec = section.upper()
    flows = []
    if sec.startswith("EXPERIENCE") or sec.startswith("WORK"):
        # head = "Company - Title"
        if " - " in head:
            company, role = head.split(" - ", 1)
        else:
            company, role = head, ""
        location = rest[0] if len(rest) >= 1 else ""
        dates = rest[-1] if len(rest) >= 2 else (rest[0] if not location else "")
        if len(rest) >= 2:
            location, dates = rest[0], rest[-1]
        flows.append(two_col_table(
            Paragraph(md_inline(company), styles["company"]),
            Paragraph(md_inline(location), styles["meta"]), lw, rw))
        if role or dates:
            flows.append(two_col_table(
                Paragraph(md_inline(role), styles["role"]),
                Paragraph(md_inline(dates), styles["meta_i"]), lw, rw))
    elif sec.startswith("PROJECT"):
        tech = rest[0] if rest else ""
        flows.append(two_col_table(
            Paragraph(md_inline(head), styles["company"]),
            Paragraph(md_inline(tech), styles["meta"]), lw, rw))
    elif sec.startswith("EDUCATION"):
        dates = rest[-1] if len(rest) >= 1 else ""
        mid = rest[:-1] if len(rest) >= 1 else []
        left = head
        if mid:
            left = head + "  -  " + "  |  ".join(mid)
        flows.append(two_col_table(
            Paragraph("<b>%s</b>" % md_inline(left), styles["body"]),
            Paragraph(md_inline(dates), styles["meta"]), lw, rw))
    else:
        flows.append(Paragraph(md_inline(text), styles["body"]))
    return flows


def count_pages(pdf_path):
    try:
        import pypdf
        return len(pypdf.PdfReader(pdf_path).pages)
    except Exception:
        return "?"


def render_pdf(name, contact, sections, pdf_path, font_scale=1.0,
               spacing_scale=1.0):
    styles = build_styles(font_scale, spacing_scale)
    margin = 0.44 * inch
    top = 0.36 * inch
    content_w = A4[0] - 2 * margin
    lw = content_w * 0.66
    rw = content_w * 0.34

    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4, leftMargin=margin, rightMargin=margin,
        topMargin=top, bottomMargin=0.34 * inch,
        title="%s - Resume" % name, author=name)

    story = []
    if name:
        story.append(Paragraph(md_inline(name), styles["name"]))
    if contact:
        story.append(Paragraph(md_inline(contact), styles["contact"]))

    for section, blocks in sections:
        story.append(Paragraph(section.upper(), styles["section"]))
        story.append(HRule(content_w, thickness=0.45,
                           space_before=0.5 * spacing_scale,
                           space_after=1.8 * spacing_scale))
        pending = []

        def flush():
            for b in pending:
                story.append(Paragraph(md_inline(b), styles["bullet"],
                                       bulletText="•"))
            pending.clear()

        first_entry = True
        for kind, text in blocks:
            if kind == "bullet":
                pending.append(text)
            elif kind == "entry":
                flush()
                if not first_entry:
                    story.append(Spacer(1, 3.4 * spacing_scale))
                first_entry = False
                for f in render_entry(section, text, styles, lw, rw):
                    story.append(f)
            else:  # text
                flush()
                story.append(Paragraph(md_inline(text), styles["body"]))
        flush()

    doc.build(story)


def build_pdf(md_path: str, pdf_path: str):
    md = normalize_ats(Path(md_path).read_text(encoding="utf-8"))
    name, contact, sections = parse_md(md)

    best_font_scale = 1.04
    best_spacing_scale = 1.0
    with tempfile.TemporaryDirectory(prefix="resume-pdf-") as tmp:
        tmp_pdf = str(Path(tmp) / "probe.pdf")

        # Keep fonts readable but restrained, then use whitespace to fill
        # the page. This avoids the "bloated font" look on shorter resumes.
        low, high = 0.94, 1.07
        for _ in range(12):
            mid = (low + high) / 2
            try:
                render_pdf(name, contact, sections, tmp_pdf,
                           font_scale=mid, spacing_scale=1.0)
                pages = count_pages(tmp_pdf)
            except Exception:
                pages = 999
            if pages == 1:
                best_font_scale = mid
                low = mid
            else:
                high = mid

        low, high = 0.9, 2.1
        for _ in range(12):
            mid = (low + high) / 2
            try:
                render_pdf(name, contact, sections, tmp_pdf,
                           font_scale=best_font_scale, spacing_scale=mid)
                pages = count_pages(tmp_pdf)
            except Exception:
                pages = 999
            if pages == 1:
                best_spacing_scale = mid
                low = mid
            else:
                high = mid

    render_pdf(name, contact, sections, pdf_path,
               font_scale=best_font_scale, spacing_scale=best_spacing_scale)

    # one-page guard
    pages = count_pages(pdf_path)
    if pages == 1:
        print("OK  %s -> %s  (1 page, font %.3f, spacing %.3f)" %
              (md_path, pdf_path, best_font_scale, best_spacing_scale))
    else:
        print("WARNING  %s -> %s spans %s pages - TRIM CONTENT to one page."
              % (md_path, pdf_path, pages))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/resume_pdf.py <input.md> <output.pdf>")
        sys.exit(1)
    build_pdf(sys.argv[1], sys.argv[2])
