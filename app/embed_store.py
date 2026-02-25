"""Embedding and vector-store persistence using FAISS."""

import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

try:
    from .config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
    from .preprocess import build_document
    from .ingest import load_data
except ImportError:
    from config import EMBEDDING_MODEL, INDEX_PATH, META_PATH
    from preprocess import build_document
    from ingest import load_data

def create_index():
    df = load_data()
    model = SentenceTransformer(EMBEDDING_MODEL)

    documents = []
    for _, row in tqdm(df.iterrows(), total=len(df)):
        documents.append(build_document(row))

    embeddings = model.encode(documents, show_progress_bar=True)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    with open(META_PATH, "wb") as f:
        pickle.dump(documents, f)

    print("Index created successfully!")


if __name__ == "__main__":
    create_index()

