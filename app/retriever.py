"""Similarity search over FIR vector store."""


import pickle
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    from .config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
except ImportError:
    from config import EMBEDDING_MODEL, INDEX_PATH, META_PATH

model = SentenceTransformer(EMBEDDING_MODEL)
index = faiss.read_index(INDEX_PATH)

with open(META_PATH, "rb") as f:
    documents = pickle.load(f)


def retrieve(query, k=5):
    q_emb = model.encode([query]).astype("float32")
    D, I = index.search(q_emb, k)
    return [documents[i] for i in I[0]]

