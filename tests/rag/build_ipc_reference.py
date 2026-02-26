"""Build IPC section reference JSON from provided Hindi IPC PDF."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ipc_reference import build_reference_json  # noqa: E402

try:
    from app.config import IPC_REFERENCE_JSON_PATH, IPC_REFERENCE_PDF_PATH
except ImportError:
    IPC_REFERENCE_JSON_PATH = str(ROOT / "tests" / "rag" / "references" / "ipc_dictionary_hi.json")
    IPC_REFERENCE_PDF_PATH = str(ROOT / "tests" / "rag" / "references" / "IPC_hindi.pdf")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build IPC reference JSON from PDF")
    parser.add_argument("--ipc-pdf", default=str(IPC_REFERENCE_PDF_PATH), help="Path to IPC Hindi PDF")
    parser.add_argument("--out-json", default=str(IPC_REFERENCE_JSON_PATH), help="Output JSON path")
    args = parser.parse_args()

    try:
        payload = build_reference_json(args.ipc_pdf, args.out_json)
    except RuntimeError as exc:
        print(str(exc))
        return

    print(f"Reference JSON written: {args.out_json}")
    print(f"Source PDF: {args.ipc_pdf}")
    print(f"Sections extracted: {payload.get('section_count', 0)}")

    sample = payload.get("sections", [])[:20]
    print(f"Sample sections: {sample}")


if __name__ == "__main__":
    main()
