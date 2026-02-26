"""Debug-only helpers for retrieval inspection."""

from typing import Dict, List


def print_top_k_debug(query: str, results: List[Dict], top_k: int) -> None:
    """Print a concise view of top-k retrieved documents."""
    print("\n[DEBUG] Retrieval output")
    print(f"[DEBUG] Query: {query}")
    print(f"[DEBUG] Retrieved: {len(results)} documents (requested k={top_k})")

    for idx, item in enumerate(results, start=1):
        case_id = item.get("case_id", "NA")
        fir_no = item.get("fir_srno", "NA")
        ps = item.get("ps", "NA")
        score = item.get("score", "NA")
        text = str(item.get("text", "")).replace("\n", " ").strip()
        snippet = text[:240] + ("..." if len(text) > 240 else "")

        print(
            f"[DEBUG] {idx}. case_id={case_id} fir_srno={fir_no} "
            f"ps={ps} score={score}"
        )
        print(f"[DEBUG]    {snippet}")
