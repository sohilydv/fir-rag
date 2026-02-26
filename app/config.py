"""Central configuration for the FIR RAG project."""

DATA_PATH = "data/jharkhand_fir.xlsx"
DATA_SHEET = "2023"
DATA_HEADER_ROW = 1
INDEX_PATH = "vector_store/fir.index"
META_PATH = "vector_store/metadata.pkl"
IPC_REFERENCE_PDF_PATH = "tests/rag/references/IPC_hindi.pdf"
IPC_REFERENCE_JSON_PATH = "tests/rag/references/ipc_dictionary_hi.json"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2" 
