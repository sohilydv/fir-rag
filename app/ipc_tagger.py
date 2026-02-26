"""Act/section tagging utilities with IPC/BNS short-form support."""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Set

try:
    from .ipc_reference import normalize_section_token
except ImportError:
    from ipc_reference import normalize_section_token

ACT_ALIAS_PATTERNS = {
    "IPC_1860": [
        r"\bipc\b",
        r"\bi\.?\s*p\.?\s*c\.?\b",
        r"भा\s*दं\s*सं",
        r"भारतीय\s*दंड\s*संहिता",
        r"भारतीय\s*दण्ड\s*संहिता",
        r"indian\s*penal\s*code",
    ],
    "BNS_2023": [
        r"\bbns\b",
        r"बी\s*एन\s*एस",
        r"भारतीय\s*न्याय\s*संहिता",
        r"bharatiya\s*nyaya\s*sanhita",
    ],
    "ELECTRICITY_ACT_2003": [
        r"विद्युत\s*अधिनियम",
        r"electricity\s*act",
    ],
    "MMDR_ACT_1957": [
        r"खान\s*एवं\s*खनिज",
        r"खान\s*और\s*खनिज",
        r"खनिज\s*\(विनियमन",
        r"mmdr",
        r"mines?\s*and\s*minerals",
    ],
    "ARMS_ACT_1959": [
        r"आयुध\s*अधिनियम",
        r"arms\s*act",
    ],
    "DOWRY_PROHIBITION_ACT_1961": [
        r"दहेज\s*प्रतिषेध\s*अधिनियम",
        r"dowry\s*prohibition",
    ],
    "POCSO_2012": [
        r"लैंगिक\s*अपराधों?\s*से\s*बालकों?\s*का\s*सरं?क्षण\s*अधिनियम",
        r"pocso",
    ],
    "IT_ACT_2000": [
        r"सूचना\s*प्रौद्?योगिकी",
        r"information\s*technology",
        r"\bit\s*act\b",
    ],
    "SCST_ACT_1989": [
        r"अनुसूचित\s*जाति\s*एवं\s*अनुसूचित\s*जनजाति",
        r"\bsc\s*/?\s*st\b",
    ],
    "PCA_1960": [
        r"पशुओं?\s*के\s*प्रति\s*क्रूरता",
        r"prevention\s*of\s*cruelty\s*to\s*animals",
    ],
}

ACT_LABELS_HI = {
    "IPC_1860": "भारतीय दंड संहिता (IPC 1860)",
    "BNS_2023": "भारतीय न्याय संहिता (BNS 2023)",
    "ELECTRICITY_ACT_2003": "विद्युत अधिनियम 2003",
    "MMDR_ACT_1957": "खान एवं खनिज अधिनियम 1957",
    "ARMS_ACT_1959": "आयुध अधिनियम 1959",
    "DOWRY_PROHIBITION_ACT_1961": "दहेज प्रतिषेध अधिनियम 1961",
    "POCSO_2012": "पॉक्सो अधिनियम 2012",
    "IT_ACT_2000": "सूचना प्रौद्योगिकी अधिनियम 2000",
    "SCST_ACT_1989": "SC/ST अत्याचार निवारण अधिनियम 1989",
    "PCA_1960": "पशु क्रूरता निवारण अधिनियम 1960",
}

SHORTFORM_PATTERNS = {
    "IPC_1860": [r"\bipc\b", r"\bi\.?\s*p\.?\s*c\.?\b", r"भा\s*दं\s*सं"],
    "BNS_2023": [r"\bbns\b", r"बी\s*एन\s*एस"],
}

_SECTION_CODE_RE = re.compile(r"(\d{1,4}(?:\(\d+\))?)")
_SECTIONS_LINE_RE = re.compile(r"^\s*Sections:\s*(.*)$", flags=re.MULTILINE)


def extract_sections_line(document_text: str) -> str:
    """Extract the `Sections:` line from a preprocessed FIR document blob."""
    if not isinstance(document_text, str):
        return ""
    match = _SECTIONS_LINE_RE.search(document_text)
    return match.group(1).strip() if match else ""


def _match_act_tags(text: str) -> Set[str]:
    lowered = text.lower()
    matched = set()
    for act_tag, patterns in ACT_ALIAS_PATTERNS.items():
        if any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in patterns):
            matched.add(act_tag)
    return matched


def _extract_section_codes(text: str) -> List[str]:
    # Prefer tokens attached to hyphens in act-section strings.
    hyphen_codes = re.findall(r"-\s*(\d{1,4}(?:\(\d+\))?)", text)
    if hyphen_codes:
        return sorted(set(hyphen_codes))

    # Fallback: generic numeric section tokens, excluding likely years.
    all_codes = []
    for token in _SECTION_CODE_RE.findall(text):
        try:
            number = int(token.split("(")[0])
        except ValueError:
            continue
        if 1800 <= number <= 2099:
            continue
        all_codes.append(token)
    return sorted(set(all_codes))


def _validate_ipc_sections(ipc_sections: List[str], reference_sections: Set[str]) -> List[str]:
    if not reference_sections:
        return ipc_sections

    validated = []
    for section in ipc_sections:
        normalized = normalize_section_token(section)
        if normalized and normalized in reference_sections:
            validated.append(section)
    return sorted(set(validated))


def tag_sections_line(sections_line: str, reference_ipc_sections: Optional[Set[str]] = None) -> Dict:
    """Tag act families and section codes from a raw act_section string."""
    if not sections_line:
        return {
            "act_tags": [],
            "act_labels_hi": [],
            "all_sections": [],
            "ipc_sections": [],
            "ipc_sections_raw": [],
            "bns_sections": [],
            "shortform_hits": [],
        }

    act_tags = _match_act_tags(sections_line)
    all_sections = _extract_section_codes(sections_line)

    # Token pass to assign section codes to the most recent detected act tag.
    act_to_sections = {tag: set() for tag in act_tags}
    current_tags: Set[str] = set()
    for part in [p.strip() for p in sections_line.split(",") if p.strip()]:
        matched = _match_act_tags(part)
        if matched:
            current_tags = matched
        section_codes = _extract_section_codes(part)
        if not section_codes:
            continue

        target_tags = matched or current_tags or act_tags
        for tag in target_tags:
            act_to_sections.setdefault(tag, set()).update(section_codes)

    # If no assignment happened but we do have sections + acts, assign globally.
    if all_sections and act_tags and not any(act_to_sections.values()):
        for tag in act_tags:
            act_to_sections[tag] = set(all_sections)

    shortform_hits = []
    for act_tag, patterns in SHORTFORM_PATTERNS.items():
        if any(re.search(p, sections_line, flags=re.IGNORECASE) for p in patterns):
            shortform_hits.append(act_tag)

    ipc_sections_raw = sorted(act_to_sections.get("IPC_1860", set()))
    ipc_sections = _validate_ipc_sections(ipc_sections_raw, reference_ipc_sections or set())
    bns_sections = sorted(act_to_sections.get("BNS_2023", set()))

    ordered_tags = sorted(act_tags)
    return {
        "act_tags": ordered_tags,
        "act_labels_hi": [ACT_LABELS_HI.get(tag, tag) for tag in ordered_tags],
        "all_sections": sorted(set(all_sections)),
        "ipc_sections": ipc_sections,
        "ipc_sections_raw": ipc_sections_raw,
        "bns_sections": bns_sections,
        "shortform_hits": sorted(set(shortform_hits)),
    }


def tag_case_record(case_record: Dict, reference_ipc_sections: Optional[Set[str]] = None) -> Dict:
    """Tag one metadata row containing `text` and optional IDs."""
    sections_line = extract_sections_line(case_record.get("text", ""))
    tags = tag_sections_line(sections_line, reference_ipc_sections=reference_ipc_sections)
    tags["case_id"] = case_record.get("case_id", "")
    tags["sections_line"] = sections_line
    return tags
