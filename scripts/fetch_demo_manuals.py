"""Download a few public HVAC manuals to data/manuals and ingest them."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

URLS = {
    "carrier_30rb.pdf": "https://www.carrier.com/commercial/en/us/media/30rb-30rbp-om-07a_tcm386-120151.pdf",
    "trane_chiller.pdf": "https://www.trane.com/content/dam/Trane/Commercial/global/products-systems/equipment/chillers/air-cooled-chillers/helical-rotary/rtac/documents/rtac-iom-en.pdf",
}

def download(dest: Path):
    dest.mkdir(parents=True, exist_ok=True)
    for fname, url in URLS.items():
        out = dest / fname
        if out.exists():
            print(f"[skip] {fname} exists")
            continue
        print(f"Downloading {fname}…")
        subprocess.check_call(["curl", "-L", "-o", str(out), url])

    # Ingest downloaded PDFs via DocumentAssistant CLI helper
    try:
        from backend.rag.manager import DocumentAssistant

        assist = DocumentAssistant()
        for path in dest.glob("*.pdf"):
            print(f"Ingesting {path.name}…")
            n = assist.ingest_pdf(str(path))
            print(f"   → {n} chunks added")
    except Exception as e:
        print(f"Warning: could not ingest PDFs automatically: {e}")

if __name__ == "__main__":
    download(Path("data/manuals")) 