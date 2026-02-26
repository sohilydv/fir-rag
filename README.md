# FIR RAG

Minimal Retrieval-Augmented Generation project for querying Jharkhand FIR records from an Excel source.

## Project Structure

```text
fir-rag/
├── data/
│   └── jharkhand_fir.xlsx
├── app/
│   ├── config.py
│   ├── ingest.py
│   ├── preprocess.py
│   ├── embed_store.py
│   ├── retriever.py
│   ├── llm.py
│   └── main.py
├── vector_store/
│   ├── fir.index
│   └── metadata.pkl
├── requirements.txt
└── README.md
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Data Format

- Excel file path: `data/jharkhand_fir.xlsx`
- Active sheet: value from `DATA_SHEET` in `app/config.py`
- Header row: Excel row 2
- Data rows start from Excel row 3

These are configured in `app/config.py` using:
- `DATA_PATH`
- `DATA_SHEET`
- `DATA_HEADER_ROW`

## Usage

1. Put FIR data in `data/jharkhand_fir.xlsx`.
2. Run ingest + preprocessing + vector DB creation:

```bash
python3 -m app.embed_store
```

What this command does:
- Loads FIR records from the configured sheet/header (`app/ingest.py`)
- Normalizes fields and date column
- Applies preprocessing and PII masking (`app/preprocess.py`)
- Generates embeddings and creates FAISS vector DB files:
  - `vector_store/fir.index`
  - `vector_store/metadata.pkl`

3. Start interactive Q&A:

```bash
python3 app/main.py
```

4. Ask questions in Hindi/English, for example:

```text
Ask question: Battery चोरी से संबंधित FIR दिखाओ
```

5. Exit interactive mode:
- Type `exit` or `quit`

## Deduplication Checks

Run dataset-level duplicate check (by generated `case_id`):

```bash
python3 -m app.dedup_check
```

Run automated dedup tests:

```bash
pip install -r requirements.txt
python3 -m pytest -q tests/test_deduplication.py
```

## RAG Testing Pipeline

Hindi-heavy question-bank and validation scripts are available in `tests/rag/`.

Generate 100+ question template (structural first, then semantic):

```bash
python3 tests/rag/build_question_bank.py
```

Run retrieval evaluation:

```bash
python3 tests/rag/run_rag_eval.py --k 10
```

Validate IPC/BNS tagging against metadata sections:

```bash
python3 tests/rag/validate_ipc_tagging.py
```

Build IPC reference dictionary from official Hindi IPC PDF:

```bash
python3 tests/rag/build_ipc_reference.py --ipc-pdf tests/rag/references/IPC_hindi.pdf
```

Then rebuild vector metadata to persist case-level IPC tags:

```bash
python3 -m app.embed_store
```

Optional: validate tagged IPC sections against IPC PDF in one step:

```bash
python3 tests/rag/validate_ipc_tagging.py --ipc-pdf /path/to/ipc_reference.pdf --auto-build-reference
```

## LLM Backend

Current `app/llm.py` uses Ollama at:
- `http://localhost:11434`
- default model: `llama3`

Make sure Ollama is running before querying.
