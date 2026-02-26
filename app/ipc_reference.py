"""IPC reference dictionary loaders/builders from PDF and JSON cache."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Set, Tuple


SECTION_TOKEN_RE = re.compile(r"^(\d{1,4}[A-Za-z]?)$")


def normalize_section_token(token: str) -> str:
    """Normalize section token for robust comparisons."""
    if token is None:
        return ""
    cleaned = str(token).strip().upper()
    cleaned = cleaned.replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    if SECTION_TOKEN_RE.match(cleaned):
        return cleaned
    return ""


def extract_reference_from_pdf(pdf_path: str) -> Tuple[Set[str], Dict[str, str]]:
    """Extract IPC section identifiers and optional labels from a PDF."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "pypdf is required to parse IPC PDF. Install with: pip install pypdf"
        ) from exc

    reader = PdfReader(pdf_path)
    text_lines = []
    for page in reader.pages:
        text = page.extract_text() or ""
        text_lines.extend(text.splitlines())

    section_title_map: Dict[str, str] = {}
    for raw_line in text_lines:
        line = " ".join(str(raw_line).split())
        if not line:
            continue

        match = re.match(
            r"^(?:धारा|Section)\s*([0-9]{1,4}[A-Za-z]?)\s*[:.\-]?\s*(.*)$",
            line,
            flags=re.IGNORECASE,
        )
        if not match:
            continue

        section = normalize_section_token(match.group(1))
        if not section:
            continue

        title = match.group(2).strip()
        section_title_map.setdefault(section, title)

    # Fallback: capture any section tokens if strict line match was sparse.
    if not section_title_map:
        full_text = "\n".join(text_lines)
        tokens = re.findall(
            r"(?:धारा|Section)\s*([0-9]{1,4}[A-Za-z]?)",
            full_text,
            flags=re.IGNORECASE,
        )
        for token in tokens:
            section = normalize_section_token(token)
            if section:
                section_title_map.setdefault(section, "")

    return set(section_title_map.keys()), section_title_map


def build_reference_json(pdf_path: str, output_json_path: str) -> Dict:
    """Build JSON cache from IPC PDF."""
    sections, section_title_map = extract_reference_from_pdf(pdf_path)

    payload = {
        "source_pdf": str(pdf_path),
        "section_count": len(sections),
        "sections": sorted(sections),
        "section_title_map": section_title_map,
    }

    out_path = Path(output_json_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return payload


def load_reference_sections(
    json_path: str,
    pdf_path: str = "",
    auto_build: bool = False,
) -> Set[str]:
    """Load normalized section set from cache JSON or optional PDF build."""
    json_file = Path(json_path)
    if json_file.exists():
        with open(json_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
        raw_sections = payload.get("sections", [])
        return {normalize_section_token(s) for s in raw_sections if normalize_section_token(s)}

    if auto_build and pdf_path and Path(pdf_path).exists():
        payload = build_reference_json(pdf_path, json_path)
        raw_sections = payload.get("sections", [])
        return {normalize_section_token(s) for s in raw_sections if normalize_section_token(s)}

    return set()
