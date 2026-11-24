from collections import OrderedDict
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from config import (
    EMBEDDING_BATCH_SIZE,
    MAX_ANALYSIS_SECONDS,
    MAX_ANALYZABLE_SOURCE_BYTES,
    MAX_INDEX_CHUNKS,
    MAX_SESSIONS,
    SESSION_TTL_SECONDS,
)
from parser.repository_parser import parse_repository
from parser.repo_chunker import chunk_repository
from parser.github_ingestion import (
    clone_github_repo,
    cleanup_repo,
    is_valid_github_url,
    calculate_analyzable_source_bytes,
)
from chunking.python_chunker import chunk_python_file
from embeddings.embedder import embed_chunks
from vector_db.vector_store import VectorStore
from retrieval.retriever import Retriever
from llm.rag_chain import ask_question
from evaluation.project_scorer import score_project
from evaluation.readme_generator import generate_ml_report
from evaluation.pipeline_reconstructor import reconstruct_repository_pipelines, is_training_script
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
    Enforces 50MB limit for chat indexing (returns 413).
    Caps chunk count and embeds in batches to stay within Render's 512MB RAM limit.
    """
    temp_dir = None
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)

        # Enforce 50MB limit only for /upload-repo (chat indexing)
        analyzable_bytes = calculate_analyzable_source_bytes(actual_path)
        if analyzable_bytes > MAX_ANALYZABLE_SOURCE_BYTES:
            size_mb = analyzable_bytes / (1024 * 1024)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Repository analyzable source size ({size_mb:.1f}MB) exceeds 50MB limit for chat indexing. Audit results are still available.",
            )

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
      - Reconstructed ML pipeline graphs (capped at 10 on training scripts only)
      - Verified auto-fixes (on training scripts only)
    Governed by an overall request deadline with granular timing metrics.
    """
    req_start = time.time()
    deadline = req_start + MAX_ANALYSIS_SECONDS
    temp_dir = None
    try:
        t0 = time.time()
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
        clone_s = round(time.time() - t0, 3)

        rem_for_scan = max(0.0, deadline - time.time())
        t1 = time.time()
        files, stats = parse_repository(
            actual_path,
            byte_budget=MAX_ANALYZABLE_SOURCE_BYTES,
            time_budget=rem_for_scan,
            return_stats=True,
        )
        scan_s = round(time.time() - t1, 3)

        report = score_project(files, repo_path=actual_path)

        # Run pipeline reconstruction and autofix ONLY on training scripts (split + fit)
        t2 = time.time()
        pipelines = []
        verified_fixes = []
        truncated = stats["truncated"]

        if time.time() < deadline:
            training_files = [f for f in files if is_training_script(f.get("code", ""))]
            pipelines = reconstruct_repository_pipelines(training_files)[:10]
            if time.time() < deadline:
                verified_fixes = generate_all_verified_fixes(training_files)
            else:
                truncated = True
        else:
            truncated = True

        pipeline_s = round(time.time() - t2, 3)

        report["pipelines"] = pipelines
        report["verified_fixes"] = verified_fixes
        report["truncated"] = truncated or (time.time() > deadline)
        report["files_scanned"] = stats["files_scanned"]
        report["files_skipped"] = stats["files_skipped"]
        report["total_files"] = stats["total_files"]
        report["timing"] = {
            "clone_s": clone_s,
            "scan_s": scan_s,
            "pipeline_s": pipeline_s,
        }

        return report

    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.post("/report")
def report(request: RepoRequest):
    """Generates comprehensive Markdown ML project health report without embedding."""
    req_start = time.time()
    deadline = req_start + MAX_ANALYSIS_SECONDS
    temp_dir = None
    try:
        t0 = time.time()
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
        clone_s = round(time.time() - t0, 3)

        rem_for_scan = max(0.0, deadline - time.time())
        t1 = time.time()
        files, stats = parse_repository(
            actual_path,
            byte_budget=MAX_ANALYZABLE_SOURCE_BYTES,
            time_budget=rem_for_scan,
            return_stats=True,
        )
        scan_s = round(time.time() - t1, 3)

        t2 = time.time()
        chunks = []
        for file in files:
            if file.get("language") == "Python":
                chunks.extend(chunk_python_file(file["code"], file["relative_path"]))

        score_report = score_project(files, repo_path=actual_path)
        report_text = generate_ml_report(files, chunks, score_report)
        pipeline_s = round(time.time() - t2, 3)

        return {
            "report": report_text,
            "truncated": stats["truncated"] or (time.time() > deadline),
            "files_scanned": stats["files_scanned"],
            "files_skipped": stats["files_skipped"],
            "total_files": stats["total_files"],
            "timing": {
                "clone_s": clone_s,
                "scan_s": scan_s,
                "pipeline_s": pipeline_s,
            },
        }

    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


# -------------------------------------------------------------------------
# Phase 3 Additive Endpoints
# -------------------------------------------------------------------------

@app.post("/pipeline")
def get_pipeline(request: RepoRequest):
    """Additive endpoint returning deterministic reconstructed ML pipelines and DOT graphs."""
    req_start = time.time()
    deadline = req_start + MAX_ANALYSIS_SECONDS
    temp_dir = None
    try:
        t0 = time.time()
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
        clone_s = round(time.time() - t0, 3)

        rem_for_scan = max(0.0, deadline - time.time())
        t1 = time.time()
        files, stats = parse_repository(
            actual_path,
            byte_budget=MAX_ANALYZABLE_SOURCE_BYTES,
            time_budget=rem_for_scan,
            return_stats=True,
        )
        scan_s = round(time.time() - t1, 3)

        t2 = time.time()
        pipelines = reconstruct_repository_pipelines(files)
        pipeline_s = round(time.time() - t2, 3)

        return {
            "pipelines": pipelines,
            "truncated": stats["truncated"] or (time.time() > deadline),
            "files_scanned": stats["files_scanned"],
            "files_skipped": stats["files_skipped"],
            "total_files": stats["total_files"],
            "timing": {
                "clone_s": clone_s,
                "scan_s": scan_s,
                "pipeline_s": pipeline_s,
            },
        }
    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.post("/autofix")
def get_autofix(request: RepoRequest):
    """Additive endpoint returning in-memory verified auto-fix diffs for detected leakage."""
    req_start = time.time()
    deadline = req_start + MAX_ANALYSIS_SECONDS
    temp_dir = None
    try:
        t0 = time.time()
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
        clone_s = round(time.time() - t0, 3)

        rem_for_scan = max(0.0, deadline - time.time())
        t1 = time.time()
        files, stats = parse_repository(
            actual_path,
            byte_budget=MAX_ANALYZABLE_SOURCE_BYTES,
            time_budget=rem_for_scan,
            return_stats=True,
        )
        scan_s = round(time.time() - t1, 3)

        t2 = time.time()
        verified_fixes = generate_all_verified_fixes(files)
        pipeline_s = round(time.time() - t2, 3)

        return {
            "verified_fixes": verified_fixes,
            "truncated": stats["truncated"] or (time.time() > deadline),
            "files_scanned": stats["files_scanned"],
            "files_skipped": stats["files_skipped"],
            "total_files": stats["total_files"],
            "timing": {
                "clone_s": clone_s,
                "scan_s": scan_s,
                "pipeline_s": pipeline_s,
            },
        }
    finally:
        if temp_dir:
            cleanup_repo(temp_dir)


@app.get("/")
def root():
    """Health check endpoint."""
    return {"message": "NeuralForge AI API is running"}