from collections import OrderedDict
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from config import (
    EMBEDDING_BATCH_SIZE,
    MAX_ANALYSIS_SECONDS,
    MAX_INDEX_CHUNKS,
    MAX_SESSIONS,
    SESSION_TTL_SECONDS,
)
from parser.repository_parser import parse_repository
from parser.repo_chunker import chunk_repository
from parser.github_ingestion import clone_github_repo, cleanup_repo, is_valid_github_url
from embeddings.embedder import embed_chunks
from vector_db.vector_store import VectorStore
from retrieval.retriever import Retriever
from llm.rag_chain import ask_question
from evaluation.project_scorer import score_project
from evaluation.readme_generator import generate_ml_report
from evaluation.pipeline_reconstructor import reconstruct_repository_pipelines
from evaluation.verified_autofix import generate_all_verified_fixes

app = FastAPI(
    title="NeuralForge AI API",
    description="Grounded RAG copilot, static ML auditor, and verified auto-fix engine.",
    version="2.0.0",
)


# -------------------------------------------------------------------------
# Bounded Session Store (LRU + TTL to stay under 512MB on Render)
# -------------------------------------------------------------------------

class BoundedSessionStore:
    """In-memory session cache bounded by maximum entries and TTL."""

    def __init__(self, max_size: int = MAX_SESSIONS, ttl_seconds: int = SESSION_TTL_SECONDS):
        self._store: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl_seconds

    def _cleanup_expired(self) -> None:
        now = time.time()
        expired = [k for k, (_, ts) in self._store.items() if now - ts >= self.ttl]
        for k in expired:
            del self._store[k]

    def get(self, key: str) -> Optional[Any]:
        self._cleanup_expired()
        if key in self._store:
            data, ts = self._store[key]
            if time.time() - ts < self.ttl:
                self._store.move_to_end(key)
                return data
            del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        self._cleanup_expired()
        if len(self._store) >= self.max_size:
            self._store.popitem(last=False)
        self._store[key] = (value, time.time())


sessions = BoundedSessionStore()


# -------------------------------------------------------------------------
# Request Models
# -------------------------------------------------------------------------

class RepoRequest(BaseModel):
    repo_path: str


class QuestionRequest(BaseModel):
    session_id: str
    question: str


# -------------------------------------------------------------------------
# Source Resolver Helper
# -------------------------------------------------------------------------

def resolve_repo_source(source: str) -> Tuple[str, Optional[str]]:
    """
    Validates and resolves a repository source (local path or GitHub URL).
    Returns (actual_path, temp_dir_to_clean).
    """
    cleaned = source.strip()
    if is_valid_github_url(cleaned):
        try:
            temp_dir = clone_github_repo(cleaned)
            return temp_dir, temp_dir
        except TimeoutError as e:
            raise HTTPException(status_code=status.HTTP_408_REQUEST_TIMEOUT, detail=str(e))
        except ValueError as e:
            if "exceeds limit" in str(e).lower():
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(e))
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Clone failed: {e}")
    else:
        path_obj = Path(cleaned)
        if not path_obj.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Local repository path does not exist: {cleaned}",
            )
        return cleaned, None


def is_indexable_chunk(chunk: Dict[str, Any]) -> bool:
    """Filters out unit tests, vendor code, and migrations to keep chat indexing compact."""
    file_path = chunk.get("file_path", "").lower().replace("\\", "/")
    skip_tokens = [
        "/tests/", "/test/", "/test_", "test_", "_test.py",
        "/vendor/", "/third_party/", "/node_modules/", "/migrations/",
    ]
    return not any(token in file_path for token in skip_tokens)


# -------------------------------------------------------------------------
# API Endpoints (All Existing Signatures Strictly Maintained)
# -------------------------------------------------------------------------

@app.post("/upload-repo")
def upload_repo(request: RepoRequest):
    """
    Indexes repository chunks into FAISS vector store for grounded RAG chat.
    Caps chunk count and embeds in batches to stay within Render's 512MB RAM limit.
    """
    temp_dir = None
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)

        raw_chunks = chunk_repository(actual_path)
        # Filter test/vendor code to focus on core logic
        candidate_chunks = [c for c in raw_chunks if is_indexable_chunk(c)]
        if not candidate_chunks:
            candidate_chunks = raw_chunks  # fallback if all files were filtered

        total_found = len(candidate_chunks)
        is_capped = total_found > MAX_INDEX_CHUNKS
        chunks_to_index = candidate_chunks[:MAX_INDEX_CHUNKS]

        # Batch embed to prevent RAM spikes
        for i in range(0, len(chunks_to_index), EMBEDDING_BATCH_SIZE):
            batch = chunks_to_index[i : i + EMBEDDING_BATCH_SIZE]
            embed_chunks(batch)

        store = VectorStore()
        store.add_chunks(chunks_to_index)

        retriever = Retriever(store)
        session_id = request.repo_path
        sessions.set(session_id, retriever)

        msg = (
            f"Indexed {len(chunks_to_index)} chunks."
            if not is_capped
            else f"Capped at {MAX_INDEX_CHUNKS} chunks (out of {total_found}) to preserve memory."
        )

        return {
            "session_id": session_id,
            "chunks_found": len(chunks_to_index),
            "chunks_total_detected": total_found,
            "capped": is_capped,
            "message": msg,
        }

    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.post("/ask")
def ask(request: QuestionRequest):
    """Answers a question using grounded AST context from the indexed session."""
    retriever = sessions.get(request.session_id)
    if retriever is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or expired. Upload/analyze repository first.",
        )

    answer = ask_question(retriever, request.question)
    return {"answer": answer}


@app.post("/analyze")
def analyze(request: RepoRequest):
    """
    Executes cheap static AST audit:
      - Scope-aware data leakage detection
      - Validation and overfitting checks
      - Tree complexity bounding checks
      - Committed dataset file scanning
      - Reconstructed ML pipeline graphs
      - Verified auto-fixes
    Never runs expensive vector embedding.
    """
    temp_dir = None
    start_time = time.time()
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)

        files = parse_repository(actual_path)
        report = score_project(files, repo_path=actual_path)

        # Phase 3: Pipeline reconstruction and verified auto-fixes
        pipelines = reconstruct_repository_pipelines(files)
        verified_fixes = generate_all_verified_fixes(files)

        report["pipelines"] = pipelines
        report["verified_fixes"] = verified_fixes
        report["truncated"] = (time.time() - start_time) > MAX_ANALYSIS_SECONDS

        return report

    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.post("/report")
def report(request: RepoRequest):
    """Generates comprehensive Markdown ML project health report without embedding."""
    temp_dir = None
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)

        files = parse_repository(actual_path)
        chunks = chunk_repository(actual_path)
        score_report = score_project(files, repo_path=actual_path)

        report_text = generate_ml_report(files, chunks, score_report)
        return {"report": report_text}

    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


# -------------------------------------------------------------------------
# Phase 3 Additive Endpoints
# -------------------------------------------------------------------------

@app.post("/pipeline")
def get_pipeline(request: RepoRequest):
    """Additive endpoint returning deterministic reconstructed ML pipelines and DOT graphs."""
    temp_dir = None
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
        files = parse_repository(actual_path)
        pipelines = reconstruct_repository_pipelines(files)
        return {"pipelines": pipelines}
    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.post("/autofix")
def get_autofix(request: RepoRequest):
    """Additive endpoint returning in-memory verified auto-fix diffs for detected leakage."""
    temp_dir = None
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
        files = parse_repository(actual_path)
        verified_fixes = generate_all_verified_fixes(files)
        return {"verified_fixes": verified_fixes}
    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "NeuralForge AI API is running"}