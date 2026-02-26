# RAG Testing Pipeline (Hindi-Heavy)

This folder contains a ready testing pipeline for retrieval quality and IPC/BNS tagging validation.

## Files

- `build_question_bank.py`: Generates Hindi-heavy question bank (structural first, then semantic).
- `build_ipc_reference.py`: Builds IPC section dictionary JSON from Hindi IPC PDF.
- `question_bank_hi.jsonl`: Generated question set (120 questions).
- `run_rag_eval.py`: Runs retrieval evaluation on the question bank and creates a report.
- `validate_ipc_tagging.py`: Validates IPC/BNS act tagging against section tags already present in metadata.

## 1) Generate question bank (100+)

```bash
python3 tests/rag/build_question_bank.py
```

Output:
- `tests/rag/question_bank_hi.jsonl`

## 2) Run retrieval evaluation

```bash
python3 tests/rag/run_rag_eval.py --k 10
```

Output:
- `tests/rag/reports/rag_eval_report.json`

## 3) Build IPC reference dictionary from PDF

Put your IPC PDF at `tests/rag/references/IPC_hindi.pdf` or pass a custom path.

```bash
python3 tests/rag/build_ipc_reference.py
```

Output:
- `tests/rag/references/ipc_dictionary_hi.json`

After creating dictionary, rebuild vector metadata so each case stores tagged acts/sections:

```bash
python3 -m app.embed_store
```

## 4) Validate IPC/BNS tagging against metadata

```bash
python3 tests/rag/validate_ipc_tagging.py
```

Output:
- `tests/rag/reports/ipc_validation_report.json`

## 5) Optional: auto-build JSON from PDF during validation

```bash
python3 tests/rag/validate_ipc_tagging.py --ipc-pdf /path/to/ipc_reference.pdf --auto-build-reference
```

This checks short-form aware IPC tagging against metadata and validates tagged IPC sections using your official reference.
