"""Preprocessing utilities for FIR text documents."""


import re

def mask_pii(text: str) -> str:
    if not isinstance(text, str):
        return ""

    # Aadhaar (12 digit)
    text = re.sub(r"\b\d{12}\b", "[AADHAAR_MASKED]", text)

    # Mobile numbers
    text = re.sub(r"\b\d{10}\b", "[PHONE_MASKED]", text)

    return text


def _safe_value(row, key: str, default: str = "") -> str:
    value = row.get(key, default)
    if value is None:
        return default
    return str(value)


def build_document(row):
    return f"""
    District: {_safe_value(row, 'district')}
    Police Station: {_safe_value(row, 'ps')}
    FIR Number: {_safe_value(row, 'fir_srno')}
    Year: {_safe_value(row, 'reg_year')}
    Date: {_safe_value(row, 'reg_dt')}
    Sections: {_safe_value(row, 'act_section')}
    Complainant: {_safe_value(row, 'complainantname')}
    Victim: {_safe_value(row, 'victimname')}
    Accused: {_safe_value(row, 'fir_accused')}
    IO: {_safe_value(row, 'ioname')}
    FIR Content: {mask_pii(_safe_value(row, 'fir_contents'))}
    """.strip()

