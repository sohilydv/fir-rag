"""Generate Hindi-heavy RAG question bank (structural first, then semantic)."""

from __future__ import annotations

import argparse
import json
import pickle
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ipc_tagger import ACT_LABELS_HI, tag_case_record  # noqa: E402


METADATA_PATH = ROOT / "vector_store" / "metadata.pkl"
DEFAULT_OUT = ROOT / "tests" / "rag" / "question_bank_hi.jsonl"

FIELD_LINE_RE = re.compile(r"^\s*([A-Za-z ]+):\s*(.*)$")

FIELD_KEY_MAP = {
    "district": "district",
    "police station": "ps",
    "fir number": "fir_number",
    "year": "year",
    "date": "date",
    "sections": "sections",
    "complainant": "complainant",
    "victim": "victim",
    "accused": "accused",
    "io": "io",
    "fir content": "fir_content",
}


def parse_document_fields(text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    if not isinstance(text, str):
        return fields

    for line in text.splitlines():
        match = FIELD_LINE_RE.match(line)
        if not match:
            continue
        label = " ".join(match.group(1).strip().lower().split())
        key = FIELD_KEY_MAP.get(label)
        if not key:
            continue
        fields[key] = match.group(2).strip()
    return fields


def load_cases() -> List[Dict]:
    with open(METADATA_PATH, "rb") as f:
        data = pickle.load(f)

    cases: List[Dict] = []
    for row in data:
        parsed = parse_document_fields(row.get("text", ""))
        tags = tag_case_record(row)
        merged = {
            **row,
            **parsed,
            "act_tags": tags.get("act_tags", []),
            "all_sections": tags.get("all_sections", []),
            "ipc_sections": tags.get("ipc_sections", []),
            "bns_sections": tags.get("bns_sections", []),
        }
        cases.append(merged)
    return cases


def _clean_value(value: str) -> str:
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value.lower() in {"", "nan", "none", "unknown1"} else value


def build_structural_questions(cases: List[Dict], target_count: int = 70) -> List[Dict]:
    rng = random.Random(42)
    pool = cases[:]
    rng.shuffle(pool)

    templates = [
        {
            "question": "केस आईडी {case_id} में जांच अधिकारी (IO) कौन है?",
            "required": ["case_id", "io"],
            "expected_keys": ["case_id"],
            "intent": "io_lookup",
        },
        {
            "question": "थाना {ps}, FIR नंबर {fir_number}, वर्ष {year} वाले केस में IO कौन है?",
            "required": ["ps", "fir_number", "year", "io"],
            "expected_keys": ["ps", "fir_number", "year"],
            "intent": "io_lookup",
        },
        {
            "question": "केस आईडी {case_id} में शिकायतकर्ता (Complainant) का नाम क्या है?",
            "required": ["case_id", "complainant"],
            "expected_keys": ["case_id"],
            "intent": "complainant_lookup",
        },
        {
            "question": "थाना {ps} के FIR नंबर {fir_number} (वर्ष {year}) में शिकायतकर्ता कौन है?",
            "required": ["ps", "fir_number", "year", "complainant"],
            "expected_keys": ["ps", "fir_number", "year"],
            "intent": "complainant_lookup",
        },
        {
            "question": "केस आईडी {case_id} में आरोपी कौन-कौन हैं?",
            "required": ["case_id", "accused"],
            "expected_keys": ["case_id"],
            "intent": "accused_lookup",
        },
        {
            "question": "केस आईडी {case_id} की घटना/रजिस्ट्रेशन तिथि क्या है?",
            "required": ["case_id", "date"],
            "expected_keys": ["case_id"],
            "intent": "date_lookup",
        },
        {
            "question": "थाना {ps} के FIR नंबर {fir_number}, वर्ष {year} में कौन-कौन सी धाराएं लगी हैं?",
            "required": ["ps", "fir_number", "year", "sections"],
            "expected_keys": ["ps", "fir_number", "year"],
            "intent": "sections_lookup",
        },
        {
            "question": "केस आईडी {case_id} किस थाना और जिले से संबंधित है?",
            "required": ["case_id", "ps", "district"],
            "expected_keys": ["case_id"],
            "intent": "location_lookup",
        },
        {
            "question": "FIR नंबर {fir_number}, वर्ष {year}, थाना {ps} में पीड़ित (Victim) कौन है?",
            "required": ["fir_number", "year", "ps", "victim"],
            "expected_keys": ["ps", "fir_number", "year"],
            "intent": "victim_lookup",
        },
        {
            "question": "केस आईडी {case_id} में FIR का मुख्य विवरण (FIR Content) क्या है?",
            "required": ["case_id", "fir_content"],
            "expected_keys": ["case_id"],
            "intent": "fir_content_lookup",
        },
    ]

    structural: List[Dict] = []
    serial = 1

    for case in pool:
        normalized = {k: _clean_value(v) for k, v in case.items()}

        for template in templates:
            if len(structural) >= target_count:
                break

            if any(not normalized.get(key) for key in template["required"]):
                continue

            question = template["question"].format(**normalized)
            expected = {key: normalized.get(key, "") for key in template["expected_keys"]}

            structural.append(
                {
                    "id": f"S{serial:03d}",
                    "type": "structural",
                    "intent": template["intent"],
                    "question": question,
                    "expected": expected,
                }
            )
            serial += 1

        if len(structural) >= target_count:
            break

    return structural


def build_semantic_questions(cases: List[Dict], target_count: int = 50) -> List[Dict]:
    act_counter: Counter = Counter()
    section_counter: Counter = Counter()
    keyword_counter: Counter = Counter()

    semantic_keywords = [
        "चोरी",
        "मारपीट",
        "हत्या",
        "बलात्कार",
        "अपहरण",
        "दहेज",
        "जालसाजी",
        "धोखाधड़ी",
        "साइबर",
        "विद्युत चोरी",
        "खनन",
        "आयुध",
        "छेड़खानी",
        "गाली गलौज",
        "लूट",
        "डकैती",
        "नाबालिग",
    ]

    for case in cases:
        for tag in case.get("act_tags", []):
            act_counter[tag] += 1
        for section in case.get("all_sections", []):
            section_counter[section] += 1

        text = str(case.get("fir_content", ""))
        lowered = text.lower()
        for kw in semantic_keywords:
            if kw.lower() in lowered:
                keyword_counter[kw] += 1

    semantic: List[Dict] = []
    serial = 1

    act_templates = [
        "{act_label} से संबंधित FIR केस दिखाओ।",
        "ऐसे मामले बताओ जिनमें {act_label} लागू हुआ है।",
        "{act_label} की धाराओं वाले मामलों की सूची दो।",
    ]

    for act_tag, _ in act_counter.most_common(12):
        act_label = ACT_LABELS_HI.get(act_tag, act_tag)
        for template in act_templates:
            if len(semantic) >= target_count:
                break
            semantic.append(
                {
                    "id": f"M{serial:03d}",
                    "type": "semantic",
                    "intent": "act_filter",
                    "question": template.format(act_label=act_label),
                    "expected": {"act_tag": act_tag},
                }
            )
            serial += 1

    section_templates = [
        "धारा {section} वाले FIR मामले दिखाओ।",
        "किन केसों में सेक्शन {section} लगा है?",
    ]

    for section, _ in section_counter.most_common(20):
        for template in section_templates:
            if len(semantic) >= target_count:
                break
            semantic.append(
                {
                    "id": f"M{serial:03d}",
                    "type": "semantic",
                    "intent": "section_filter",
                    "question": template.format(section=section),
                    "expected": {"section": section},
                }
            )
            serial += 1

    keyword_templates = [
        "{keyword} से संबंधित मामले दिखाओ।",
        "ऐसे FIR बताओ जिनमें {keyword} का जिक्र हो।",
    ]

    for keyword, _ in keyword_counter.most_common(20):
        for template in keyword_templates:
            if len(semantic) >= target_count:
                break
            semantic.append(
                {
                    "id": f"M{serial:03d}",
                    "type": "semantic",
                    "intent": "keyword_filter",
                    "question": template.format(keyword=keyword),
                    "expected": {"keyword": keyword},
                }
            )
            serial += 1

    return semantic[:target_count]


def write_jsonl(records: List[Dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Hindi RAG question bank")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSONL path")
    parser.add_argument("--min-count", type=int, default=100, help="Minimum questions")
    args = parser.parse_args()

    cases = load_cases()
    structural = build_structural_questions(cases, target_count=70)
    semantic = build_semantic_questions(cases, target_count=50)

    questions = structural + semantic
    if len(questions) < args.min_count:
        raise ValueError(
            f"Generated only {len(questions)} questions; expected at least {args.min_count}."
        )

    output_path = Path(args.out)
    write_jsonl(questions, output_path)

    print(f"Question bank generated: {output_path}")
    print(f"Structural questions: {len(structural)}")
    print(f"Semantic questions: {len(semantic)}")
    print(f"Total questions: {len(questions)}")


if __name__ == "__main__":
    main()
