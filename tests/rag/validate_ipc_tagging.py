"""Validate IPC/BNS act tagging against sections already present in metadata."""

from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ipc_tagger import extract_sections_line, tag_case_record  # noqa: E402
from app.ipc_reference import load_reference_sections  # noqa: E402

try:
    from app.config import IPC_REFERENCE_JSON_PATH, IPC_REFERENCE_PDF_PATH
except ImportError:
    IPC_REFERENCE_JSON_PATH = str(ROOT / "tests" / "rag" / "references" / "ipc_dictionary_hi.json")
    IPC_REFERENCE_PDF_PATH = str(ROOT / "tests" / "rag" / "references" / "IPC_hindi.pdf")

METADATA_PATH = ROOT / "vector_store" / "metadata.pkl"
DEFAULT_REPORT_PATH = ROOT / "tests" / "rag" / "reports" / "ipc_validation_report.json"

IPC_GT_PATTERNS = [
    r"\bipc\b",
    r"\bi\.?\s*p\.?\s*c\.?\b",
    r"भा\s*दं\s*सं",
    r"भारतीय\s*दंड\s*संहिता",
    r"भारतीय\s*दण्ड\s*संहिता",
]

BNS_GT_PATTERNS = [
    r"\bbns\b",
    r"बी\s*एन\s*एस",
    r"भारतीय\s*न्याय\s*संहिता",
]

IPC_SHORTFORM_PATTERNS = [r"\bipc\b", r"\bi\.?\s*p\.?\s*c\.?\b", r"भा\s*दं\s*सं"]
BNS_SHORTFORM_PATTERNS = [r"\bbns\b", r"बी\s*एन\s*एस"]


def _contains_any(text: str, patterns) -> bool:
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def validate_ipc_tags(metadata_rows, reference_ipc_sections=None):
    ipc_tp = ipc_fp = ipc_fn = ipc_tn = 0
    bns_tp = bns_fp = bns_fn = bns_tn = 0

    ipc_short_total = ipc_short_hit = 0
    bns_short_total = bns_short_hit = 0

    act_counter = Counter()
    ipc_sections_raw = set()
    ipc_sections_validated = set()

    for row in metadata_rows:
        tags = tag_case_record(row, reference_ipc_sections=reference_ipc_sections)
        sections_line = extract_sections_line(row.get("text", ""))

        ipc_sections_raw.update(tags.get("ipc_sections_raw", []))
        ipc_sections_validated.update(tags.get("ipc_sections", []))

        pred_ipc = "IPC_1860" in tags.get("act_tags", [])
        pred_bns = "BNS_2023" in tags.get("act_tags", [])

        gt_ipc = _contains_any(sections_line, IPC_GT_PATTERNS)
        gt_bns = _contains_any(sections_line, BNS_GT_PATTERNS)

        if gt_ipc and pred_ipc:
            ipc_tp += 1
        elif gt_ipc and not pred_ipc:
            ipc_fn += 1
        elif not gt_ipc and pred_ipc:
            ipc_fp += 1
        else:
            ipc_tn += 1

        if gt_bns and pred_bns:
            bns_tp += 1
        elif gt_bns and not pred_bns:
            bns_fn += 1
        elif not gt_bns and pred_bns:
            bns_fp += 1
        else:
            bns_tn += 1

        if _contains_any(sections_line, IPC_SHORTFORM_PATTERNS):
            ipc_short_total += 1
            if pred_ipc:
                ipc_short_hit += 1

        if _contains_any(sections_line, BNS_SHORTFORM_PATTERNS):
            bns_short_total += 1
            if pred_bns:
                bns_short_hit += 1

        for tag in tags.get("act_tags", []):
            act_counter[tag] += 1

    def _safe_div(a, b):
        return (a / b) if b else 0.0

    report = {
        "total_cases": len(metadata_rows),
        "ipc_detection": {
            "tp": ipc_tp,
            "fp": ipc_fp,
            "fn": ipc_fn,
            "tn": ipc_tn,
            "precision": _safe_div(ipc_tp, ipc_tp + ipc_fp),
            "recall": _safe_div(ipc_tp, ipc_tp + ipc_fn),
            "f1": _safe_div(2 * ipc_tp, (2 * ipc_tp) + ipc_fp + ipc_fn),
        },
        "bns_detection": {
            "tp": bns_tp,
            "fp": bns_fp,
            "fn": bns_fn,
            "tn": bns_tn,
            "precision": _safe_div(bns_tp, bns_tp + bns_fp),
            "recall": _safe_div(bns_tp, bns_tp + bns_fn),
            "f1": _safe_div(2 * bns_tp, (2 * bns_tp) + bns_fp + bns_fn),
        },
        "shortform_coverage": {
            "ipc": {
                "total_with_shortform": ipc_short_total,
                "tagged": ipc_short_hit,
                "coverage": _safe_div(ipc_short_hit, ipc_short_total),
            },
            "bns": {
                "total_with_shortform": bns_short_total,
                "tagged": bns_short_hit,
                "coverage": _safe_div(bns_short_hit, bns_short_total),
            },
        },
        "top_act_tags": act_counter.most_common(20),
        "ipc_reference_validation": {
            "reference_enabled": bool(reference_ipc_sections),
            "reference_section_count": len(reference_ipc_sections or []),
            "ipc_sections_raw_count": len(ipc_sections_raw),
            "ipc_sections_validated_count": len(ipc_sections_validated),
            "ipc_sections_dropped_by_reference_count": len(ipc_sections_raw - ipc_sections_validated),
            "dropped_sections_sample": sorted(ipc_sections_raw - ipc_sections_validated)[:50],
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate IPC/BNS tagging on metadata")
    parser.add_argument("--metadata", default=str(METADATA_PATH), help="metadata.pkl path")
    parser.add_argument("--ipc-pdf", default=str(IPC_REFERENCE_PDF_PATH), help="IPC reference PDF path")
    parser.add_argument("--ipc-json", default=str(IPC_REFERENCE_JSON_PATH), help="IPC reference JSON cache path")
    parser.add_argument(
        "--auto-build-reference",
        action="store_true",
        help="If JSON cache is missing, parse PDF and build it automatically.",
    )
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_PATH), help="Output report JSON")
    args = parser.parse_args()

    with open(args.metadata, "rb") as f:
        metadata_rows = pickle.load(f)

    reference_sections = set()
    try:
        reference_sections = load_reference_sections(
            json_path=args.ipc_json,
            pdf_path=args.ipc_pdf,
            auto_build=args.auto_build_reference,
        )
    except RuntimeError as exc:
        print(f"Warning: {exc}")
        reference_sections = set()

    report = validate_ipc_tags(metadata_rows, reference_ipc_sections=reference_sections)

    out_path = Path(args.report_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"Report written: {out_path}")
    print(f"Total cases: {report['total_cases']}")
    print(
        "IPC precision/recall/f1: "
        f"{report['ipc_detection']['precision']:.4f}/"
        f"{report['ipc_detection']['recall']:.4f}/"
        f"{report['ipc_detection']['f1']:.4f}"
    )
    print(
        "BNS precision/recall/f1: "
        f"{report['bns_detection']['precision']:.4f}/"
        f"{report['bns_detection']['recall']:.4f}/"
        f"{report['bns_detection']['f1']:.4f}"
    )
    print(
        "Short-form coverage IPC/BNS: "
        f"{report['shortform_coverage']['ipc']['coverage']:.4f}/"
        f"{report['shortform_coverage']['bns']['coverage']:.4f}"
    )
    print(
        "IPC reference enabled/sections: "
        f"{report['ipc_reference_validation']['reference_enabled']}/"
        f"{report['ipc_reference_validation']['reference_section_count']}"
    )


if __name__ == "__main__":
    main()
