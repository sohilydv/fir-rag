import pandas as pd

from app.dedup import generate_case_id, find_duplicate_case_ids


def test_generate_case_id_is_stable_for_equivalent_values():
    row_a = pd.Series(
        {
            "district": " Dhanbad ",
            "ps": "Baghmara",
            "reg_year": 2025,
            "fir_srno": "1",
            "reg_dt": "2025-01-07 20:05:00",
        }
    )
    row_b = pd.Series(
        {
            "district": "dhanbad",
            "ps": "baghmara",
            "reg_year": "2025",
            "fir_srno": 1,
            "reg_dt": "2025-01-07",
        }
    )

    assert generate_case_id(row_a) == generate_case_id(row_b)


def test_generate_case_id_changes_when_key_fields_change():
    row_a = pd.Series(
        {
            "district": "dhanbad",
            "ps": "baghmara",
            "reg_year": 2025,
            "fir_srno": "1",
            "reg_dt": "2025-01-07",
        }
    )
    row_b = pd.Series(
        {
            "district": "dhanbad",
            "ps": "baghmara",
            "reg_year": 2025,
            "fir_srno": "2",
            "reg_dt": "2025-01-07",
        }
    )

    assert generate_case_id(row_a) != generate_case_id(row_b)


def test_find_duplicate_case_ids_detects_duplicates():
    df = pd.DataFrame(
        [
            {
                "district": "dhanbad",
                "ps": "baghmara",
                "reg_year": 2025,
                "fir_srno": "1",
                "reg_dt": "2025-01-07",
            },
            {
                "district": "dhanbad",
                "ps": "baghmara",
                "reg_year": 2025,
                "fir_srno": "1",
                "reg_dt": "2025-01-07",
            },
            {
                "district": "dhanbad",
                "ps": "baghmara",
                "reg_year": 2025,
                "fir_srno": "2",
                "reg_dt": "2025-01-07",
            },
        ]
    )

    duplicates = find_duplicate_case_ids(df)

    assert len(duplicates) == 1
    assert duplicates[0]["count"] == 2
