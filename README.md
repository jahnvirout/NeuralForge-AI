# NeuralForge AI

AI Copilot for Machine Learning Repositories

NeuralForge AI is an AI-powered copilot designed to understand machine learning codebases instead of just reading documents. It combines Retrieval-Augmented Generation (RAG), semantic code retrieval, and Large Language Models (LLMs) to answer repository-specific questions, explain code, and help developers navigate ML repositories. On top of that, it reasons like an ML engineer — auditing repositories for common implementation mistakes like data leakage, missing validation, and unconstrained hyperparameters.

## Motivation

Modern LLMs answer general programming questions well but lack awareness of an entire codebase. Developers often spend significant time understanding unfamiliar repositories before making changes, and generic AI chatbots can't catch ML-specific engineering mistakes that require domain judgment, not just code-reading.

NeuralForge AI bridges this gap in two ways: by indexing a repository and answering questions grounded in the actual code, and by running static analysis checks that flag real ML engineering pitfalls — turning "chat with your repo" into something closer to an automated ML code review.

## Features

### Repository Understanding
- Parses Python repositories, ignoring irrelevant directories (venv, node_modules, .git)
- Reads source files with encoding and size safeguards
- Builds structured repository metadata

### Intelligent Code Chunking
- Python AST-based parsing (not naive text splitting)
- Function-level and class-level chunking
- Preserves complete logical code blocks

### Semantic Search
- Generates embeddings for code chunks using sentence-transformers (all-MiniLM-L6-v2)
- Stores embeddings in a FAISS vector index
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
The entire pipeline is exposed as a REST API, not just terminal scripts:
- `POST /upload-repo` — parses, chunks, embeds, and indexes a repository
- `POST /ask` — answers a question grounded in the indexed repository
- `POST /analyze` — runs Phase 2 checks and returns the score/issue report
- `POST /report` — generates the full Markdown health report

### Frontend (Streamlit)
A clean, minimal dashboard with four views:
- **Copilot Q&A** — chat interface for asking questions about the codebase
- **ML Health Dashboard** — visual score and itemized issue breakdown
- **Full ML Report** — rendered report with one-click Markdown download
- **Repo Inspector** — pipeline architecture and live session telemetry

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
venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
GROQ_API_KEY=your_key_here
```

**Run the full app (backend + frontend):**

Terminal 1:
```bash
uvicorn backend.main:app --reload --port 8000
```

Terminal 2:
```bash
streamlit run frontend/app.py
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

**Planned**
- GitHub URL ingestion (analyze a repo directly from its URL, not just a local path)
- Source citations in chat answers (show which file/chunk an answer was grounded in)

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
