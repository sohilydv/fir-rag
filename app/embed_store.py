"""Embedding and vector-store persistence using FAISS."""

import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

try:
    from .config import (
        EMBEDDING_MODEL,
        INDEX_PATH,
        IPC_REFERENCE_JSON_PATH,
        IPC_REFERENCE_PDF_PATH,
        META_PATH,
    )
    from .preprocess import build_document
    from .ingest import load_data
    from .dedup import build_case_metadata, find_duplicate_case_ids
    from .ipc_reference import load_reference_sections
    from .ipc_tagger import tag_case_record
except ImportError:
    from config import (
        EMBEDDING_MODEL,
        INDEX_PATH,
        IPC_REFERENCE_JSON_PATH,
        IPC_REFERENCE_PDF_PATH,
        META_PATH,
    )
    from preprocess import build_document
    from ingest import load_data
    from dedup import build_case_metadata, find_duplicate_case_ids
    from ipc_reference import load_reference_sections
    from ipc_tagger import tag_case_record

def create_index():
    df = load_data()
    model = SentenceTransformer(EMBEDDING_MODEL)
    reference_sections = load_reference_sections(
        json_path=IPC_REFERENCE_JSON_PATH,
        pdf_path=IPC_REFERENCE_PDF_PATH,
        auto_build=False,
    )

    documents = []
    metadata = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        doc = build_document(row)
        documents.append(doc)
        meta = build_case_metadata(row, doc)
        tags = tag_case_record(meta, reference_ipc_sections=reference_sections)
        meta["act_tags"] = tags.get("act_tags", [])
        meta["ipc_sections"] = tags.get("ipc_sections", [])
        meta["ipc_sections_raw"] = tags.get("ipc_sections_raw", [])
        meta["bns_sections"] = tags.get("bns_sections", [])
        meta["shortform_hits"] = tags.get("shortform_hits", [])
        meta["sections_line"] = tags.get("sections_line", "")
        metadata.append(meta)

    embeddings = model.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    dup_rows = sum(item["count"] - 1 for item in find_duplicate_case_ids(df))
    print("Index created successfully!")
    print(f"Documents indexed: {len(metadata)}")
    print(f"IPC reference sections loaded: {len(reference_sections)}")
    print(f"Duplicate rows by generated case_id: {dup_rows}")


if __name__ == "__main__":
    create_index()
