"""Render a work order to a trilingual (EN/FR/AR) PDF with Arabic RTL shaping."""

from pathlib import Path

from fpdf import FPDF

from torq.agent.schemas import WorkOrder
from torq.config import settings

GREEN = (63, 185, 80)
DARK = (17, 28, 40)
RED = (215, 58, 73)
MUTE = (120, 130, 140)
BLACK = (20, 20, 20)

# label, language key, alignment (Arabic right-to-left)
_TRANSLATIONS = [("Francais (FR)", "fr", "L"), ("العربية (AR)", "ar", "R")]


def _heading(pdf: FPDF, text: str, align: str = "L") -> None:
    pdf.ln(3)
    pdf.set_font("amiri", size=13)
    pdf.set_text_color(*GREEN)
    pdf.multi_cell(0, 8, text, align=align, new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*BLACK)


def _bullets(pdf: FPDF, title: str, items: list[str]) -> None:
    if not items:
        return
    _heading(pdf, title)
    pdf.set_font("amiri", size=11)
    for it in items:
        pdf.multi_cell(0, 6, f"  -  {it}", new_x="LMARGIN", new_y="NEXT")


def _numbered(pdf: FPDF, title: str, items: list[str]) -> None:
    if not items:
        return
    _heading(pdf, title)
    pdf.set_font("amiri", size=11)
    for i, it in enumerate(items, start=1):
        pdf.multi_cell(0, 6, f"  {i}.  {it}", new_x="LMARGIN", new_y="NEXT")


def render_pdf(wo: WorkOrder, out_path: Path | None = None) -> Path:
    """Write the work order to a PDF and return its path."""
    out_path = out_path or (settings.workorder_dir / f"work_order_{wo.id}.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.add_font("amiri", "", str(settings.font_path))
    pdf.set_text_shaping(True)  # harfbuzz: Arabic shaping + bidi
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # Header bar
    pdf.set_fill_color(*DARK)
    pdf.rect(0, 0, 210, 24, "F")
    pdf.set_xy(12, 6)
    pdf.set_font("amiri", size=20)
    pdf.set_text_color(*GREEN)
    pdf.cell(28, 10, "TORQ")
    pdf.set_font("amiri", size=13)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, f"Work Order  {wo.id}")
    pdf.set_text_color(*BLACK)

    # Info line
    pdf.set_xy(12, 28)
    pdf.set_font("amiri", size=11)
    pdf.set_text_color(*MUTE)
    pdf.multi_cell(0, 6, f"{wo.machine}   |   fault {wo.fault_code}   |   status: {wo.status}",
                   new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(*BLACK)

    # Root cause
    _heading(pdf, "Root cause")
    pdf.set_font("amiri", size=11)
    pdf.multi_cell(0, 6, wo.root_cause, new_x="LMARGIN", new_y="NEXT")

    # Structured English body
    _numbered(pdf, "Repair steps", wo.repair_steps)
    _bullets(pdf, "Parts", wo.parts)
    _bullets(pdf, "Tools", wo.tools)

    # Safety callout
    if wo.safety_warnings:
        pdf.ln(3)
        pdf.set_font("amiri", size=12)
        pdf.set_text_color(*RED)
        pdf.multi_cell(0, 7, "Safety", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)
        pdf.set_font("amiri", size=11)
        for w in wo.safety_warnings:
            pdf.multi_cell(0, 6, f"  !  {w}", new_x="LMARGIN", new_y="NEXT")

    # Translations (full text block per language; Arabic right-to-left)
    for label, lang, align in _TRANSLATIONS:
        text = wo.content.get(lang)
        if not text:
            continue
        _heading(pdf, label, align)
        pdf.set_font("amiri", size=10)
        pdf.multi_cell(0, 6, text, align=align, new_x="LMARGIN", new_y="NEXT")

    if wo.sources:
        _heading(pdf, "Grounded in")
        pdf.set_font("amiri", size=9)
        pdf.set_text_color(*MUTE)
        pdf.multi_cell(0, 5, "  -  " + "\n  -  ".join(wo.sources), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(*BLACK)

    pdf.output(str(out_path))
    return out_path
