"""Render a work order to a trilingual (EN/FR/AR) PDF with Arabic RTL shaping."""

from pathlib import Path

from fpdf import FPDF

from torq.agent.schemas import WorkOrder
from torq.config import settings

# label, work-order language key, text alignment
_SECTIONS = [
    ("English", "en", "L"),
    ("Francais", "fr", "L"),
    ("العربية", "ar", "R"),
]


def render_pdf(wo: WorkOrder, out_path: Path | None = None) -> Path:
    """Write the work order to a PDF and return its path."""
    out_path = out_path or (settings.workorder_dir / f"work_order_{wo.id}.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.add_font("amiri", "", str(settings.font_path))
    pdf.set_text_shaping(True)  # harfbuzz: Arabic shaping + bidi
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("amiri", size=18)
    pdf.cell(0, 12, f"TORQ Work Order  {wo.id}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("amiri", size=11)
    pdf.cell(0, 8, f"{wo.machine}   fault {wo.fault_code}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    for label, lang, align in _SECTIONS:
        text = wo.content.get(lang)
        if not text:
            continue
        pdf.set_font("amiri", size=14)
        pdf.multi_cell(0, 9, label, align=align, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("amiri", size=11)
        pdf.multi_cell(0, 7, text, align=align, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    pdf.output(str(out_path))
    return out_path
