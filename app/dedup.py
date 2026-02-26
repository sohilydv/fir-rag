"""Case ID generation and duplicate detection utilities."""

from __future__ import annotations

import hashlib
from typing import Dict, List

import pandas as pd


def _clean(value) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def _date_key(value) -> str:
    if value is None or pd.isna(value):
        return ""
    try:
        return pd.to_datetime(value, errors="coerce").strftime("%Y-%m-%d")
    except Exception:
        return _clean(value)


def generate_case_id(row) -> str:
    """Generate a deterministic unique ID from key FIR fields."""
    key_parts = [
        _clean(row.get("district")),
        _clean(row.get("ps")),
        _clean(row.get("reg_year")),
        _clean(row.get("fir_srno")),
        _date_key(row.get("reg_dt")),
    ]
    raw_key = "|".join(key_parts)
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()


def build_case_metadata(row, text: str) -> Dict:
    """Build structured metadata for one FIR vector row."""
    return {
        "case_id": generate_case_id(row),
        "district": row.get("district", ""),
        "ps": row.get("ps", ""),
        "reg_year": row.get("reg_year", ""),
        "fir_srno": row.get("fir_srno", ""),
        "reg_dt": str(row.get("reg_dt", "")),
        "text": text,
    }


def find_duplicate_case_ids(df: pd.DataFrame) -> List[Dict]:
    """Return duplicate case IDs and their counts."""
    if df.empty:
        return []

    ids = df.apply(generate_case_id, axis=1)
    counts = ids.value_counts()
    duplicate_ids = counts[counts > 1]
    return [{"case_id": cid, "count": int(count)} for cid, count in duplicate_ids.items()]
