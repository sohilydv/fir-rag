"""Similarity search over FIR vector store."""


import os
import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from .config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
    from .utils.retrieval_debug import print_top_k_debug
except ImportError:
    from config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
    from utils.retrieval_debug import print_top_k_debug

model = SentenceTransformer(EMBEDDING_MODEL)
index = faiss.read_index(INDEX_PATH)

with open(META_PATH, "rb") as f:
    metadata = pickle.load(f)


def retrieve(query, k=50):
    q_emb = model.encode([query]).astype("float32")
    D, I = index.search(q_emb, k)
    results = []
    for rank, idx in enumerate(I[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        row = metadata[idx]
        row = dict(row)
        row["score"] = float(D[0][rank])
        results.append(row)

    if os.getenv("RETRIEVAL_DEBUG", "0") in {"1", "true", "True"}:
        print_top_k_debug(query=query, results=results, top_k=k)

    return results
