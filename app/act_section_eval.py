"""Act-section prediction prompt and binary accuracy helpers."""

from __future__ import annotations

import re
from typing import Dict, List

try:
    from .ipc_tagger import extract_sections_line, tag_sections_line
except ImportError:
    from ipc_tagger import extract_sections_line, tag_sections_line

ACT_SECTION_QUERY_KEYWORDS = (
    "act section",
    "act sections",
    "ipc section",
    "bns section",
    "which section",
    "which act",
    "कौन सी धारा",
    "धारा",
    "अधिनियम",
    "ipc",
    "bns",
)

_FIR_CONTENT_RE = re.compile(r"^\s*FIR Content:\s*(.*)$", flags=re.IGNORECASE | re.MULTILINE)
_PREDICTED_LINE_RE = re.compile(
    r"Predicted[_\s-]*Act[_\s-]*Section\s*:\s*(.+)",
    flags=re.IGNORECASE,
)

ACT_SECTION_PROMPT_TEMPLATE = """
You are a legal tagging assistant for FIR analysis.

Task:
- Read the user FIR query and retrieved FIR context.
- Predict the most likely act-section value(s).
- Use only retrieved context. Do not invent.

Output format (strict):
Predicted_Act_Section: <comma-separated act-section values OR Unknown>

Retrieved Context:
{context_text}

User Query:
{query}
""".strip()


def is_act_section_query(query: str) -> bool:
    """Detect whether query asks for act-section prediction."""
    normalized = " ".join(str(query or "").lower().split())
    return any(keyword in normalized for keyword in ACT_SECTION_QUERY_KEYWORDS)


def _extract_fir_content(text: str) -> str:
    if not isinstance(text, str):
        return ""
    match = _FIR_CONTENT_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def build_act_section_prompt(query: str, contexts: List[Dict], max_contexts: int = 8) -> str:
    snippets = []
    for item in contexts[:max_contexts]:
        sections_line = item.get("sections_line") or extract_sections_line(item.get("text", ""))
        snippets.append(
            "\n".join(
                [
                    f"CaseID: {item.get('case_id', 'NA')}",
                    f"Sections: {sections_line or 'NA'}",
                    f"FIR Content: {_extract_fir_content(item.get('text', ''))}",
                ]
            )
        )

    context_text = "\n\n".join(snippets)
    return ACT_SECTION_PROMPT_TEMPLATE.format(context_text=context_text, query=query.strip())


def extract_predicted_act_section_text(llm_response: str) -> str:
    """Extract predicted section text from the model output."""
    if not isinstance(llm_response, str):
        return ""

    match = _PREDICTED_LINE_RE.search(llm_response)
    if match:
        return match.group(1).strip()

    for line in llm_response.splitlines():
        cleaned = line.strip(" -*\t")
        if cleaned:
            return cleaned
    return ""


def get_expected_from_context(context_row: Dict) -> Dict:
    """Extract expected act tags and section numbers from metadata context."""
    sections_line = context_row.get("sections_line") or extract_sections_line(context_row.get("text", ""))
    tags = tag_sections_line(sections_line or "")

    expected_act_tags = context_row.get("act_tags") or tags.get("act_tags", [])
    expected_sections = tags.get("all_sections", [])
    if not expected_sections:
        expected_sections = sorted(
            set(context_row.get("ipc_sections", [])) | set(context_row.get("bns_sections", []))
        )

    return {
        "sections_line": sections_line or "",
        "act_tags": sorted(set(expected_act_tags)),
        "all_sections": sorted(set(expected_sections)),
    }


def evaluate_prediction(predicted_text: str, expected_context: Dict) -> Dict:
    """Compute binary accuracy for predicted act-section against metadata."""
    predicted_tags = tag_sections_line(predicted_text or "")
    expected = get_expected_from_context(expected_context)

    predicted_section_set = set(predicted_tags.get("all_sections", []))
    expected_section_set = set(expected.get("all_sections", []))
    predicted_act_tag_set = set(predicted_tags.get("act_tags", []))
    expected_act_tag_set = set(expected.get("act_tags", []))

    section_accuracy = None
    if expected_section_set:
        section_accuracy = int(predicted_section_set == expected_section_set)

    act_tag_accuracy = None
    if expected_act_tag_set:
        act_tag_accuracy = int(predicted_act_tag_set == expected_act_tag_set)

    if section_accuracy is not None:
        accuracy = section_accuracy
    elif act_tag_accuracy is not None:
        accuracy = act_tag_accuracy
    else:
        accuracy = 0

    return {
        "accuracy": int(accuracy),
        "section_accuracy": section_accuracy,
        "act_tag_accuracy": act_tag_accuracy,
        "predicted": {
            "text": predicted_text,
            "act_tags": sorted(predicted_act_tag_set),
            "all_sections": sorted(predicted_section_set),
        },
        "expected": expected,
    }
