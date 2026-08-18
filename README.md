# NeuralForge AI

AI Copilot for Machine Learning Repositories

NeuralForge AI is an AI-powered copilot designed to understand machine learning codebases instead of just reading documents. It combines Retrieval-Augmented Generation (RAG), semantic code retrieval, and Large Language Models (LLMs) to answer repository-specific questions, explain code, and help developers navigate ML repositories.

The long-term vision is an intelligent ML Engineer copilot capable of reviewing machine learning pipelines, detecting common implementation issues, and providing engineering-level recommendations grounded in the actual source code.

## Motivation

Modern LLMs answer general programming questions well but lack awareness of an entire codebase. Developers often spend significant time understanding unfamiliar repositories before making changes.

NeuralForge AI bridges this gap by indexing a repository, understanding its structure, retrieving the most relevant code, and generating context-aware responses grounded in the actual project — rather than acting as a generic chatbot.

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
- Builds a grounded prompt (explicitly restricts the LLM to the retrieved context)
- Calls Groq (openai/gpt-oss-20b) to generate an answer
- Answers repository-specific questions, explains functions/classes, and reasons over the retrieved code

### ML Engineer Intelligence (Phase 2, in progress)
- Data leakage detection — flags scaling/encoding applied before train-test split
- Overfitting risk analysis — flags models trained without evaluation against a held-out set
- Project scoring — aggregates checks into a single weighted score with a detailed issue breakdown

Planned: hyperparameter analysis, auto-generated ML-specific documentation, repository health reports.

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
LLM (Groq)
    |
Context-Aware Response
```

## Tech Stack

**Core:** Python, AST, pathlib

**ML/AI:** sentence-transformers, Hugging Face, FAISS

**RAG/LLM:** LangChain, Groq API

**Testing:** pytest

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
├── rag/            # end-to-end pipeline entry point
├── tests/            # pytest test suite
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

Run the end-to-end pipeline:
```bash
python -m rag.test_end_to_end
```

Run the test suite:
```bash
pytest
```

## Development Status

**Phase 1 — Working RAG Copilot (complete)**
- Repository parser with edge-case handling
- AST-based code chunker
- Embedding generation
- FAISS vector store
- Semantic retriever
- End-to-end RAG chain with LLM integration

**Phase 2 — ML Engineer Intelligence (in progress)**
- Data leakage detector
- Overfitting risk analyzer
- Project scorer
- Hyperparameter analysis (planned)
- ML-specific README generation (planned)

**Phase 3 — Polish & Deployment (upcoming)**
- Frontend dashboard
- Deployment

## Learning Objectives

This project explores practical implementation of:
- Retrieval-Augmented Generation (RAG)
- Abstract Syntax Trees (AST) for code understanding
- Semantic code chunking
- Embedding models and vector search
- Prompt engineering for grounded, non-hallucinated responses
- ML-specific static analysis (data leakage, overfitting risk detection)
