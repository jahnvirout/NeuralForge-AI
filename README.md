# NeuralForge AI

AI Copilot for Machine Learning Repositories

NeuralForge AI is an AI-powered copilot designed to understand machine learning codebases instead of just reading documents. It combines Retrieval-Augmented Generation (RAG), semantic code retrieval, and Large Language Models (LLMs) to answer repository-specific questions, explain code, and help developers navigate ML repositories. On top of that, it reasons like an ML engineer — auditing repositories for common implementation mistakes like data leakage, missing validation, and unconstrained hyperparameters.

## Motivation

Modern LLMs answer general programming questions well but lack awareness of an entire codebase. Developers often spend significant time understanding unfamiliar repositories before making changes, and generic AI chatbots can't catch ML-specific engineering mistakes that require domain judgment, not just code-reading.

NeuralForge AI bridges this gap in two ways: by indexing a repository and answering questions grounded in the actual code, and by running static analysis checks that flag real ML engineering pitfalls — turning "chat with your repo" into something closer to an automated ML code review.

## Features

### Repository Understanding
- Parses supported source files (`.py`, `.java`, `.cpp`, `.c`, `.js`, and `.ts`)
- Ignores irrelevant directories (`venv`, `node_modules`, `.git`, caches)
- Skips files larger than approximately 500 KB and handles encoding errors safely
- Builds structured repository metadata

### Intelligent Code Chunking
- Python AST-based parsing (not naive text splitting)
- Function-level and class-level chunking
- Preserves complete logical code blocks

### Semantic Search
- Generates embeddings for code chunks using sentence-transformers (all-MiniLM-L6-v2)
- Stores embeddings in an in-memory FAISS vector index for the active session
- Performs similarity search to find relevant code for a given query

### Retrieval-Augmented Generation (RAG)
- Retrieves relevant code context for a user's question
- Builds a grounded prompt (explicitly restricts the LLM to the retrieved context, preventing hallucination)
- Calls Groq (openai/gpt-oss-20b) to generate an answer
- Answers repository-specific questions and explains functions/classes using only retrieved code

### ML Engineer Intelligence (Phase 2)
- **Data leakage detection** — flags `fit_transform()` called before `train_test_split()`
- **Overfitting risk analysis** — flags models trained with `.fit()` but never evaluated against a held-out validation/test set
- **Hyperparameter risk analysis** — flags tree-based models (DecisionTree/RandomForest) initialized without `max_depth`, risking unbounded overfitting
- **Project scoring** — aggregates all checks into a single weighted score (out of 100) with a detailed issue breakdown
- **ML Project Health Report generator** — produces a full Markdown report combining chunk stats and all findings, downloadable from the frontend

### Backend API (FastAPI)
The pipeline is exposed as a REST API, not just terminal scripts:
- `GET /` — backend health check
- `POST /upload-repo` — parses, chunks, embeds, and indexes a repository
- `POST /ask` — answers a question grounded in the indexed repository
- `POST /analyze` — runs Phase 2 checks and returns the score/issue report
- `POST /report` — generates the full Markdown health report
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
├── parser/          # repository parsing, edge-case handling
├── chunking/         # AST-based function/class chunking
├── embeddings/        # embedding generation
├── vector_db/        # FAISS vector store
├── retrieval/         # semantic retrieval logic
├── llm/            # RAG chain, Groq integration
├── evaluation/         # Phase 2 ML intelligence checks
├── backend/          # FastAPI app exposing the pipeline as a REST API
├── frontend/          # Streamlit dashboard
├── rag/            # end-to-end pipeline entry point (terminal)
├── tests/            # pytest unit + integration test suite
├── data/            # sample repositories for testing
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

GitHub repositories are cloned with a shallow clone. The current ingestion
guard rejects a cloned repository larger than 300 MB. The parser also skips
unsupported files and individual source files larger than approximately 500 KB.
These safeguards prevent a single request from exhausting the backend.

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
- Repository indexing is synchronous, so very large repositories can exceed
  request timeouts or available memory.
- The `sentence-transformers` model, PyTorch, and FAISS are memory-intensive;
  small Render instances may restart while indexing larger repositories.
- The current implementation is designed for bounded code repositories, not
  unlimited 1 GB+ ingestion. Background jobs, incremental indexing, and a
  persistent vector database are future scalability work.

## Development Status

**Phase 1 — Working RAG Copilot (complete)**
- Repository parser with edge-case handling
- AST-based code chunker
- Embedding generation
- FAISS vector store
- Semantic retriever
- End-to-end RAG chain with LLM integration

**Phase 2 — ML Engineer Intelligence (complete)**
- Data leakage detector
- Overfitting risk analyzer
- Hyperparameter risk analyzer
- Project scorer
- ML Project Health Report generator

**Phase 3 — Product Layer (complete)**
- FastAPI backend exposing all functionality via REST endpoints
- Streamlit frontend with chat, health dashboard, report viewer, and repo inspector

**Implemented after the initial phases**
- Public GitHub URL ingestion with shallow cloning and cleanup

**Planned**
- Source citations in chat answers (show which file/chunk an answer was grounded in)
- Background indexing jobs and progress reporting for large repositories
- Persistent vector storage across backend restarts

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
