# NeuralForge AI

Repository intelligence and static auditing for machine learning projects.

NeuralForge AI does two things for an ML repository:

1. **Deterministic audit.** An AST-based analyzer finds data leakage, missing validation, and risky hyperparameters. Every finding has file, function, line range, evidence, and a suggested fix. No LLM is involved in the audit.
2. **Repository copilot.** A retrieval-augmented chat answers questions about the code, grounded in AST chunks, with citations (file, function, line range). When retrieval is weak, it says "insufficient evidence" instead of guessing.

## Features

### Audit (no LLM, no tokens)

- **Scope-aware data leakage detection.** Matches real `ast.Call` nodes only, so strings, comments, docstrings, and imports can never trigger a rule. Tracks how data flows through variables inside each function and module scope, and flags preprocessors (scalers, encoders, imputers, PCA, selectors) that are fitted before a train/test split. Pipelines and fits on the training split only are not flagged.
- **Overfitting and validation checks.** Detects models trained without any held-out evaluation.
- **Hyperparameter checks.** Detects tree models created without depth or leaf constraints.
- **Explainable health score.** The score is a visible list of rule, points deducted, and maximum deduction. There are no hidden weights.
- **Pipeline reconstruction.** Rebuilds each training script's pipeline (data load, preprocessing, split, fit, evaluate) from the AST, with file and line evidence per stage. Stages with no evidence are shown as "insufficient evidence". Rendered as a graph in the UI.
- **Verified auto-fix.** For each leakage finding, generates a minimal unified diff deterministically (split first, then fit on the training split and transform the test split). The patched code is re-analyzed in memory, and the fix is shown only if the finding disappears and the code still parses. Repository code is never executed.
- **Committed dataset detection.** Reports data and binary files committed to the repository (csv, parquet, pkl, h5, zip, images) with their sizes.
- **Notebook support.** Extracts code cells from `.ipynb` files.
- **Ignore rules.** Skips `tests/fixtures` and honors an optional `.neuralforgeignore` file.

### Copilot

- AST-aware chunking: function chunks, module-level chunks for top-level logic, and method chunks tagged with their parent class.
- Dense retrieval with sentence-transformers embeddings and a FAISS index.
- Citations from chunk metadata, and an explicit "insufficient evidence" answer when retrieval is weak.
- Bounded in-memory sessions (LRU eviction and TTL).

## Architecture

```
Streamlit UI (frontend/app.py)
        |
        v
FastAPI backend (backend/main.py)
        |
        +-- parser/        clone (shallow, sparse), ignore rules, file parsing
        +-- chunking/      AST chunker
        +-- embeddings/    sentence-transformers
        +-- llm/           RAG chain, citations, weak-retrieval check
        +-- evaluation/    detectors, scorer, pipeline reconstructor, verified autofix
        +-- config.py      limits, ignored directories, supported extensions
```

## API

| Endpoint | Purpose |
|---|---|
| `POST /upload-repo` | Index a repository for chat (embeddings and FAISS). Returns 413 if the repository is too large to index. |
| `POST /ask` | Ask a question about an indexed repository. Returns an answer with citations. |
| `POST /analyze` | Run the deterministic audit. Works on large repositories and may return partial results. |
| `POST /report` | Generate the full project report. |
| `POST /pipeline` | Return reconstructed ML pipelines and graph definitions. |
| `POST /autofix` | Return verified leakage fixes. |

Errors use proper HTTP status codes (400, 404, 408, 413, 422) with a `detail` message.

Audit responses include `truncated`, `files_scanned`, `files_skipped`, `total_files`, and a `timing` breakdown, so partial results are always labeled.

## Setup

Requirements: Python 3.11 or newer.

```
git clone https://github.com/jahnvirout/NeuralForge-AI.git
cd NeuralForge-AI
python -m pip install -r requirements.txt
```

Create a `.env` file in the project root with your Groq API key. Never commit this file.

```
GROQ_API_KEY=your_key_here
```

## Run

Start the backend:

```
python -m uvicorn backend.main:app --port 8000
```

In a second terminal, start the frontend:

```
python -m streamlit run frontend/app.py
```

The frontend reads the backend address from the `BACKEND_API_URL` environment variable and defaults to `http://127.0.0.1:8000`.

## Tests

```
python -m pytest tests/ --ignore=tests/test_live_system.py
```

`tests/test_live_system.py` needs running servers and is skipped by default.

The suite covers each detector (true positive, true negative, string and comment false positive, cross-function scope), a regression test that the repository's own `evaluation/` folder produces zero findings, pipeline reconstruction, verified auto-fix, and the large-repository response behavior. Deliberately bad sample code lives in `tests/fixtures/`.

## Large repositories

- Cloning is shallow and sparse, so large blobs such as committed virtual environments are not downloaded.
- The audit runs file by file under a time and size budget. If a limit is hit, the response sets `truncated: true` and reports how many files were scanned and skipped.
- Chat indexing has a lower limit than the audit. For repositories above it, `/upload-repo` returns 413, and the audit endpoints still work.

## Limitations

- Analysis is per file and per scope. Data flows across modules are not traced.
- On very large repositories the audit can be partial. This is reported, never hidden.
- Repository chat is unavailable when a repository is too large for in-memory embedding on a 512 MB host.
- The validation-gap rule treats `.fit()` calls broadly, so it can flag non-sklearn objects such as cloud training estimators.
- Verified fixes confirm that the flagged pattern is gone and the code still parses. They do not guarantee identical behavior.
- Chat answers come from an LLM and depend on what retrieval returns. The audit does not use an LLM.

## Tech stack

Python, FastAPI, Streamlit, sentence-transformers (all-MiniLM-L6-v2), FAISS, LangChain, Groq API, pytest.
