"""Run retrieval validation on a Hindi RAG question bank."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ipc_tagger import tag_case_record  # noqa: E402
from app.retriever import retrieve  # noqa: E402

DEFAULT_QUESTION_BANK = ROOT / "tests" / "rag" / "question_bank_hi.jsonl"
DEFAULT_REPORT_PATH = ROOT / "tests" / "rag" / "reports" / "rag_eval_report.json"


def load_jsonl(path: Path) -> List[Dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _match_structural(expected: Dict, hits: List[Dict]) -> bool:
    if not expected:
        return False

    for hit in hits:
        if expected.get("case_id") and str(hit.get("case_id")) != str(expected["case_id"]):
            continue

        if expected.get("ps") and str(hit.get("ps", "")).strip() != str(expected["ps"]).strip():
            continue

        if expected.get("fir_number") and str(hit.get("fir_srno", "")).strip() != str(expected["fir_number"]).strip():
            continue

        if expected.get("year") and str(hit.get("reg_year", "")).strip() != str(expected["year"]).strip():
            continue

        return True

    return False


def _match_semantic(expected: Dict, hits: List[Dict]) -> bool:
    if not expected:
        return False

    act_tag = expected.get("act_tag")
    section = str(expected.get("section", "")).strip()
    keyword = str(expected.get("keyword", "")).strip().lower()

    for hit in hits:
        tags = tag_case_record(hit)
        if act_tag and act_tag in tags.get("act_tags", []):
            return True
        if section and section in tags.get("all_sections", []):
            return True
        if keyword and keyword in str(hit.get("text", "")).lower():
            return True

    return False


def evaluate_questions(questions: List[Dict], k: int) -> Tuple[Dict, List[Dict]]:
    results: List[Dict] = []
    by_type = {"structural": {"total": 0, "passed": 0}, "semantic": {"total": 0, "passed": 0}}

    for row in questions:
        qid = row.get("id", "")
        qtype = row.get("type", "unknown")
        question = row.get("question", "")
        expected = row.get("expected", {})

        hits = retrieve(question, k=k)

        if qtype == "structural":
            passed = _match_structural(expected, hits)
        else:
            passed = _match_semantic(expected, hits)

        if qtype in by_type:
            by_type[qtype]["total"] += 1
            by_type[qtype]["passed"] += int(passed)

        results.append(
            {
                "id": qid,
                "type": qtype,
                "intent": row.get("intent", ""),
                "question": question,
                "expected": expected,
                "passed": passed,
                "top_hit_case_id": hits[0].get("case_id", "") if hits else "",
                "retrieved_count": len(hits),
            }
        )

    total = len(questions)
    passed_total = sum(1 for r in results if r["passed"])

    summary = {
        "total_questions": total,
        "passed": passed_total,
        "accuracy": (passed_total / total) if total else 0.0,
        "by_type": {
            t: {
                "total": stats["total"],
                "passed": stats["passed"],
                "accuracy": (stats["passed"] / stats["total"]) if stats["total"] else 0.0,
            }
            for t, stats in by_type.items()
        },
    }
    return summary, results


def main() -> None:
    parser = argparse.ArgumentParser(description="Run RAG retrieval evaluation")
    parser.add_argument("--question-bank", default=str(DEFAULT_QUESTION_BANK), help="Question bank JSONL")
    parser.add_argument("--k", type=int, default=10, help="Top-k retrieval depth")
    parser.add_argument("--max-questions", type=int, default=0, help="Limit question count")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_PATH), help="Output report JSON")
    args = parser.parse_args()

    question_bank = Path(args.question_bank)
    questions = load_jsonl(question_bank)
    if args.max_questions > 0:
        questions = questions[: args.max_questions]

    summary, results = evaluate_questions(questions, k=args.k)

    out_path = Path(args.report_out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "results": results}, f, ensure_ascii=False, indent=2)

    print(f"Report written: {out_path}")
    print(f"Total: {summary['total_questions']}")
    print(f"Passed: {summary['passed']}")
    print(f"Accuracy: {summary['accuracy']:.4f}")
    for qtype, stats in summary["by_type"].items():
        print(f"{qtype}: {stats['passed']}/{stats['total']} ({stats['accuracy']:.4f})")


if __name__ == "__main__":
    main()
