"""Load FIR records from Excel."""

import pandas as pd
try:
    from .config import DATA_PATH, DATA_SHEET, DATA_HEADER_ROW
except ImportError:
    from config import DATA_PATH, DATA_SHEET, DATA_HEADER_ROW

DATE_COLUMN_CANDIDATES = (
    "reg_dt",
    "reg_date",
    "registration_date",
    "fir_date",
    "date",
)


def _normalize_column(col_name: str) -> str:
    return str(col_name).strip().lower().replace(" ", "_")


def load_data():
    df = pd.read_excel(
        DATA_PATH,
        sheet_name=DATA_SHEET,
        header=DATA_HEADER_ROW,
    )

    df.columns = [_normalize_column(c) for c in df.columns]

    # Drop placeholder empty column that appears as the first column in source files.
    unnamed_cols = [c for c in df.columns if c.startswith("unnamed")]
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    # Remove rows that are fully empty after load.
    df = df.dropna(how="all")

    # Canonicalize FIR text column name.
    if "fir_contents" not in df.columns:
        fir_text_col = next(
            (c for c in ("fir_content", "contents", "content", "fir_text") if c in df.columns),
            None,
        )
        if fir_text_col:
            df["fir_contents"] = df[fir_text_col]
        else:
            df["fir_contents"] = ""

    # Parse the first matching date-like column into a canonical `reg_dt`.
    matched_col = next((c for c in DATE_COLUMN_CANDIDATES if c in df.columns), None)
    if matched_col:
        df["reg_dt"] = pd.to_datetime(df[matched_col], errors="coerce")
    else:
        # Keep pipeline resilient when source schema has no registration date.
        df["reg_dt"] = pd.NaT

    return df

