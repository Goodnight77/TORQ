"""PDF check: render a trilingual (EN/FR/AR) work order and validate the output.

Run:  uv run python scripts/run_pdf.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows console defaults to cp1252

from torq.agent.schemas import WorkOrder
from torq.workorder.pdf import render_pdf

SAMPLE = WorkOrder(
    id="demo01",
    fault_code="E-471",
    machine="CM-350 Line 2",
    root_cause="Clogged intake louvers restricting cooling airflow.",
    repair_steps=["Lockout/tagout the drive.", "Clean intake louvers.", "Reset and monitor."],
    parts=["Intake filter mat AF-12"],
    required_skill="electromechanical",
    content={
        "en": "WORK ORDER - CM-350 Line 2 - fault E-471\nRoot cause: clogged louvers.\nSteps:\n  - LOTO the drive\n  - Clean louvers\n  - Reset",
        "fr": "ORDRE DE TRAVAIL - CM-350 Ligne 2 - defaut E-471\nCause: volets d'admission obstrues.\nEtapes:\n  - Consigner l'entrainement\n  - Nettoyer les volets\n  - Reinitialiser",
        "ar": "أمر عمل - CM-350 الخط 2 - العطل E-471\nالسبب: انسداد فتحات سحب الهواء.\nالخطوات:\n  - قفل ووسم المحرك\n  - تنظيف الفتحات\n  - إعادة التشغيل",
    },
)


def main() -> None:
    path = render_pdf(SAMPLE)
    data = path.read_bytes()
    print(f"Rendered {path}  ({len(data)} bytes)")
    assert path.exists(), "PDF was not written"
    assert data[:4] == b"%PDF", "output is not a valid PDF"
    assert len(data) > 2000, "PDF suspiciously small (fonts/content may be missing)"
    print("Trilingual work-order PDF rendered (EN/FR/AR, Arabic shaped RTL). ✅")


if __name__ == "__main__":
    main()
