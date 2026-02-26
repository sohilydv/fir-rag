"""CLI to report duplicate generated case IDs for the configured dataset."""

try:
    from .ingest import load_data
    from .dedup import find_duplicate_case_ids
except ImportError:
    from ingest import load_data
    from dedup import find_duplicate_case_ids


def main():
    df = load_data()
    duplicates = find_duplicate_case_ids(df)

    print(f"Total rows: {len(df)}")
    print(f"Duplicate case_id groups: {len(duplicates)}")
    print(f"Duplicate rows (extra): {sum(item['count'] - 1 for item in duplicates)}")

    if not duplicates:
        print("No duplicates found by generated case_id.")
        return

    print("Top duplicate case_id entries:")
    for item in duplicates[:20]:
        print(f"- {item['case_id']} -> {item['count']} rows")


if __name__ == "__main__":
    main()
