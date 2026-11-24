# NeuralForge AI

AI Copilot for Machine Learning Repositories

NeuralForge AI is an AI-powered copilot designed to understand machine learning codebases instead of just reading documents. It combines Retrieval-Augmented Generation (RAG), semantic code retrieval, and Large Language Models (LLMs) to answer repository-specific questions, explain code, and help developers navigate ML repositories. On top of that, it reasons like an ML engineer — auditing repositories for common implementation mistakes like data leakage, missing validation, and unconstrained hyperparameters.

## Motivation

Modern LLMs answer general programming questions well but lack awareness of an entire codebase. Developers often spend significant time understanding unfamiliar repositories before making changes, and generic AI chatbots can't catch ML-specific engineering mistakes that require domain judgment, not just code-reading.

NeuralForge AI bridges this gap in two ways: by indexing a repository and answering questions grounded in the actual code, and by running static analysis checks that flag real ML engineering pitfalls — turning "chat with your repo" into something closer to an automated ML code review.

## Features

### Repository Understanding
- Recursively walks the repository and recognizes `.py`, `.ipynb`, `.java`, `.cpp`, `.c`, `.js`, and `.ts` files
- Extracts and analyzes code cells from Jupyter Notebooks (`.ipynb`)
- Honors repository ignore patterns via `.neuralforgeignore` alongside default exclusions (`venv`, `node_modules`, `.git`, caches)
- Detects committed data files and model checkpoints (`.csv`, `.parquet`, `.pkl`, `.pt`, `.h5`), warning developers and applying health score deductions
- Caps individual source file analysis at 500 KB and total analyzable source size at 25 MB

### Intelligent Code Chunking
- Python AST-based parsing preserving function-level, class-level, and top-level module blocks
- Tags class methods with class hierarchy metadata (`parent=ClassName`)
- Caps total indexed chunks at 500 to keep memory bounded on resource-constrained environments

### Semantic Search
- Generates embeddings in batches using sentence-transformers (all-MiniLM-L6-v2)
- Stores embeddings in an in-memory FAISS vector index per session
- Bounded session store with LRU eviction (max 10 sessions) and 1-hour TTL

### Retrieval-Augmented Generation (RAG)
- Retrieves relevant code context for a user's question
- Formats explicit citations (file path, function name, and line numbers) for retrieved chunks
- Guarded retrieval: returns "Insufficient evidence in repository" when similarity falls below confidence threshold
- Builds a grounded prompt restricting the LLM to retrieved context to prevent hallucination
- Calls Groq (openai/gpt-oss-20b) to generate answers

### Verified ML Audit and Static Analysis
- **AST scope-aware data leakage detection** — tracks variable taint across `fit_transform` and `train_test_split` within local scopes, immune to string and comment false positives
- **AST overfitting risk analysis** — inspects AST `Call` nodes to match estimator `.fit()` invocations against validation/test evaluations or score calls
- **AST hyperparameter risk analysis** — validates tree-based models (DecisionTree, RandomForest, ExtraTrees, GradientBoosting) for `max_depth`, `min_samples_leaf`, or `max_leaf_nodes` constraints
- **Explainable project scoring** — transparent score breakdown detailing deductions for leakage (-35), unconstrained trees (-20), unvalidated models (-15), and committed datasets (-10)
- **ML Pipeline Reconstruction** — analyzes repository ASTs to trace pipeline stages (Data Ingestion -> Preprocessing -> Data Splitting -> Model Training -> Evaluation) and generates Graphviz DOT DAGs
- **Verified Auto-Fix** — produces deterministic unified diffs to fix detected issues and validates fixes in-memory with AST re-analysis confirming zero remaining issues
- **ML Project Health Report generator** — generates complete Markdown audit reports combining chunk stats and all findings

### Backend API (FastAPI)
The pipeline is exposed as a REST API with standardized HTTP status codes (400, 404, 408, 413, 422):
- `GET /` — backend health check
- `POST /upload-repo` — parses, chunks, batch-embeds, and indexes a repository
- `POST /ask` — answers questions with citations and weak retrieval detection
- `POST /analyze` — runs lightweight AST static analysis without vector indexing
- `POST /report` — generates the full Markdown health report
- `POST /pipeline` — reconstructs ML pipeline stages and returns Graphviz DOT graph
- `POST /autofix` — generates verified unified diffs to resolve detected audit issues
- `GET /docs` — interactive FastAPI documentation

### Frontend (Streamlit)
A clean, minimal dashboard with five tabs:
- **Overview** — repository health and executive summary
- **Copilot Q&A** — chat interface for asking questions about the codebase
- **ML Health Dashboard** — visual score and itemized issue breakdown
- **Full ML Report** — rendered report with one-click Markdown download
- **Architecture** — pipeline architecture and live session telemetry

## Architecture

```
Repository
    |
Repository Parser
    |
AST-Based Chunking
    |
Embedding Generation
    |
FAISS Vector Database
    |
Retriever
    |
LLM (Groq) ---- ML Intelligence Checks (Phase 2)
    |                    |
Context-Aware Response   Score + Issue Report
    |                    |
     +--------------------+
             |
      FastAPI Backend
      (in-memory sessions)
             |
      Streamlit Frontend
```

## Tech Stack

**Core:** Python, AST, pathlib

**ML/AI:** sentence-transformers, Hugging Face, FAISS

**RAG/LLM:** LangChain, Groq API

**Backend:** FastAPI, uvicorn

**Frontend:** Streamlit

**Testing:** pytest (unit tests for parser/chunker, integration tests for live API endpoints)

## Project Structure

```
NeuralForge-AI/
├── parser/          # repository parsing, edge-case handling, .ipynb & .neuralforgeignore support
├── chunking/        # AST-based function, class, and module chunking
├── embeddings/      # batch embedding generation
├── vector_db/       # FAISS vector store
├── retrieval/       # semantic retrieval logic
├── llm/             # RAG chain, Groq integration, citation formatting
├── evaluation/      # AST static audit, pipeline reconstructor, verified auto-fix
├── backend/         # FastAPI REST API with bounded session cache and proper status codes
├── frontend/        # Streamlit dashboard with DAG pipeline and auto-fix diffs
├── tests/           # pytest suite (unit tests, AST detectors, feature tests)
├── data/            # sample repositories for testing
├── config.py        # centralized configuration constants
└── docs/
```

## Setup

```bash
git clone https://github.com/<your-username>/NeuralForge-AI.git
cd NeuralForge-AI
python -m venv venv
.\venv\Scripts\Activate.ps1       # Windows PowerShell
python -m pip install -r requirements.txt
```

The project is developed and tested with Python 3.13.6. If PowerShell blocks
the activation script, run the project with the Python executable from your
virtual environment instead.

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

**Run the full app (backend + frontend):**

Terminal 1:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2:
```bash
python -m streamlit run frontend/app.py
```

Open `http://localhost:8501` in your browser.

**Or run the terminal-only end-to-end pipeline:**
```bash
python -m rag.test_end_to_end
```

**Run the test suite:**
```bash
pytest tests/
```

When running locally, the frontend uses `http://127.0.0.1:8000` by default.
For a deployed frontend, set `BACKEND_API_URL` to the public backend URL.

## GitHub Repositories

`/upload-repo`, `/analyze`, and `/report` accept either a local repository path
or a public GitHub HTTPS URL, for example:

```text
https://github.com/karpathy/micrograd
```

GitHub repositories are cloned using shallow blobless cloning with a 60-second
timeout and guaranteed directory cleanup. The ingestion guard enforces a 25 MB
analyzable source limit, rejecting repositories whose meaningful code exceeds
safe processing bounds. The parser respects `.neuralforgeignore` files to ignore
project-specific non-code paths and warns on committed data files.

## Deployment

The application is deployed as two Render Web Services: a FastAPI backend and
a Streamlit frontend.

### Backend service

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Health check path:** `/`
- **Environment variables:** `GROQ_API_KEY`, `PYTHON_VERSION=3.13.6`

### Frontend service

- **Root directory:** `frontend`
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `streamlit run app.py --server.address 0.0.0.0 --server.port $PORT`
- **Environment variable:** `BACKEND_API_URL=<public-backend-url>`

Keep `GROQ_API_KEY` on the backend only; it must not be exposed to the
frontend. The frontend URL is the user-facing website, while the backend URL
is used for the API and `/docs`.

## Current Limitations

- FAISS indexes and retriever sessions are stored in memory; they reset when
  the backend restarts or sleeps.
- Repository indexing is synchronous, so large repositories can exceed request
  timeouts or available memory.
- The repository-size check happens before parsing and currently counts
  redundant files too, so a repository can be rejected even when its useful
  source code would be much smaller.
- Filtering is basic, not relevance-aware: datasets, checkpoints, build
  outputs, and other project-specific noise are not automatically excluded
  unless they fall under the existing hard-coded rules.
- The `sentence-transformers` model, PyTorch, and FAISS are memory-intensive;
  small Render instances may restart while indexing larger repositories.
- The current implementation is designed for bounded code repositories, not
  unlimited 1 GB+ ingestion. Intelligent file filtering, background jobs,
  incremental indexing, and persistent vector storage are future work.

## Development Status

**Phase 1 — Working RAG Copilot (complete)**
- Repository parser with edge-case handling and `.ipynb` notebook support
- AST-based function, class, and module code chunker
- Batch embedding generation
- FAISS vector store
- Semantic retriever with weak-retrieval guard
- End-to-end RAG chain with formatted citations and LLM integration

**Phase 2 — AST ML Static Analysis and Auditor (complete)**
- Scope-aware AST data leakage detector (variable taint tracking)
- Call-node AST overfitting risk analyzer
- AST hyperparameter risk analyzer with tree constraints
- Transparent, explainable project scoring rules and score breakdown
- Committed dataset detection and warning
- ML Project Health Report generator

**Phase 3 — Verified Audit and Pipeline Reconstruction (complete)**
- AST ML pipeline reconstructor (ingest, preprocess, split, train, eval)
- Pipeline DAG visualization with Graphviz DOT export
- Verified auto-fix engine generating unified diffs verified by in-memory AST re-analysis
- Additive REST endpoints: `POST /pipeline` and `POST /autofix`

**Phase 4 — Robustness and Resource Guardrails (complete)**
- Smart shallow blobless cloning with 60s timeout and guaranteed cleanup
- Analyzable source byte budget enforcement (25 MB limit)
- Bounded in-memory session store (max 10 sessions, 1-hour TTL)
- Standardized HTTP status codes (400, 404, 408, 413, 422)
- Centralized `config.py` configuration constants

## Learning Objectives

This project explores practical implementation of:
- Retrieval-Augmented Generation (RAG)
- Abstract Syntax Trees (AST) for code understanding
- Semantic code chunking
- Embedding models and vector search
- Prompt engineering for grounded, non-hallucinated responses
- ML-specific static analysis (data leakage, overfitting risk, hyperparameter risk detection)
- Building and exposing an ML pipeline as a REST API
- Building a usable frontend on top of a multi-stage AI pipeline
