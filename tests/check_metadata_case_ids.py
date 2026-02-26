"""Quick check: verify every metadata row has case_id."""

import pickle


def main() -> None:
    with open("vector_store/metadata.pkl", "rb") as f:
        data = pickle.load(f)

    total = len(data)
    with_case_id = sum(1 for row in data if isinstance(row, dict) and "case_id" in row)
    missing_case_id = total - with_case_id

    print(f"total_rows={total}")
    print(f"rows_with_case_id={with_case_id}")
    print(f"rows_missing_case_id={missing_case_id}")


if __name__ == "__main__":
    main()
