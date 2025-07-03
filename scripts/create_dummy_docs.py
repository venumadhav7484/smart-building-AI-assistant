"""Generate self-contained dummy building documents (PDFs) for local testing.

Creates three PDFs in data/dummy_docs/:
    1. hvac_manual.pdf – operating & maintenance instructions.
    2. energy_guidelines.pdf – energy-efficiency best practices.
    3. safety_procedures.pdf – occupant comfort & safety procedures.

After generation, the script ingests them via DocumentAssistant so they're
immediately searchable.

Requires the `reportlab` package:
    pip install reportlab
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.rag.manager import DocumentAssistant

DOCS = {
    "hvac_manual.pdf": [
        "HVAC-01 OPERATING MANUAL",
        "\nMAINTENANCE SCHEDULE:\n- Filters: Replace every 3 months or when pressure drop exceeds 300 Pa.\n- Coils: Clean annually with non-acidic cleaner.\n- Vibration threshold: 0.5 g peak; shutdown recommended above 0.7 g.",
        "\nENERGY SAVING TIP:\nSet chilled-water supply temperature to 44°F during off-peak hours to save up to 7% energy.",
    ],
    "energy_guidelines.pdf": [
        "BUILDING ENERGY OPTIMISATION GUIDELINES",
        "\nLIGHTING:\n- Replace fluorescent with LED to cut 40% lighting load.\n- Use occupancy sensors in meeting rooms.",
        "\nHVAC:\n- Enable economy mode when outdoor temperature between 55°F and 68°F.\n- Maintain VAV box minimum airflow at 30%.",
        "\nBENCHMARK:\nTarget overall Energy Use Intensity (EUI) < 75 kBtu/ft²·yr.",
    ],
    "safety_procedures.pdf": [
        "OCCUPANT COMFORT AND SAFETY PROCEDURES",
        "\nTHERMAL COMFORT:\nMaintain indoor temperature 72±2°F and RH 40-60%.",
        "\nEMERGENCY VENTILATION:\nIf CO2 > 1000 ppm for 5 minutes, ramp AHU to 100% outdoor air.",
        "\nFIRE SAFETY:\nKeep all fire dampers inspected semi-annually per NFPA 80.",
    ],
}

def make_pdf(path: Path, paragraphs: list[str]):
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    text = c.beginText(40, height - 40)
    text.setFont("Helvetica", 11)
    for para in paragraphs:
        for line in para.split("\n"):
            text.textLine(line)
        text.textLine("")
    c.drawText(text)
    c.showPage()
    c.save()


def generate_docs(dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    for fname, paragraphs in DOCS.items():
        out = dest / fname
        if out.exists():
            print(f"[skip] {fname} already exists")
            continue
        print(f"Creating {fname}…")
        make_pdf(out, paragraphs)

    # Ingest via DocumentAssistant
    assist = DocumentAssistant()
    for pdf in dest.glob("*.pdf"):
        print(f"Ingesting {pdf.name}…")
        n = assist.ingest_pdf(str(pdf))
        print(f"   → {n} chunks added")

if __name__ == "__main__":
    generate_docs(Path("data/dummy_docs")) 