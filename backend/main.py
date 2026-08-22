from fastapi import FastAPI
from pydantic import BaseModel

from parser.repository_parser import parse_repository
from parser.repo_chunker import chunk_repository
from parser.github_ingestion import clone_github_repo, cleanup_repo, is_valid_github_url
from embeddings.embedder import embed_chunks
from vector_db.vector_store import VectorStore
from retrieval.retriever import Retriever
from llm.rag_chain import ask_question
from evaluation.project_scorer import score_project
from evaluation.readme_generator import generate_ml_report

app = FastAPI(title="NeuralForge AI API")

# In-memory storage for now — sessions reset if the server restarts
sessions = {}


class RepoRequest(BaseModel):
    repo_path: str


class QuestionRequest(BaseModel):
    session_id: str
    question: str


def resolve_repo_source(source):
    """
    Takes either a local folder path or a GitHub URL.
    If it's a GitHub URL, clones it to a temp folder and returns that path
    plus the temp folder (so the caller can clean it up afterward).
    If it's a local path, returns it unchanged with no temp folder to clean.
    """
    if is_valid_github_url(source):
        temp_dir = clone_github_repo(source)
        return temp_dir, temp_dir
    else:
        return source, None


@app.post("/upload-repo")
def upload_repo(request: RepoRequest):
    """
    Parses, chunks, embeds, and indexes a repo. Accepts either a local
    folder path or a GitHub URL. Returns a session_id to use for asking
    questions later.
    """
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
    except ValueError as e:
        return {"error": str(e)}

    chunks = chunk_repository(actual_path)
    chunks = embed_chunks(chunks)

    store = VectorStore()
    store.add_chunks(chunks)

    retriever = Retriever(store)

    session_id = request.repo_path  # use the original input (URL or path) as the session key

    sessions[session_id] = retriever

    if temp_dir:
        cleanup_repo(temp_dir)

    return {"session_id": session_id, "chunks_found": len(chunks)}


@app.post("/ask")
def ask(request: QuestionRequest):
    """
    Answers a question using the retriever from a previously uploaded repo.
    """
    retriever = sessions.get(request.session_id)

    if retriever is None:
        return {"error": "Session not found. Upload a repo first."}

    answer = ask_question(retriever, request.question)
    return {"answer": answer}


@app.post("/analyze")
def analyze(request: RepoRequest):
    """
    Runs Phase 2 ML intelligence checks and returns a score + issue report.
    Accepts either a local folder path or a GitHub URL.
    """
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
    except ValueError as e:
        return {"error": str(e)}

    files = parse_repository(actual_path)
    report = score_project(files)

    if temp_dir:
        cleanup_repo(temp_dir)

    return report


@app.post("/report")
def report(request: RepoRequest):
    """
    Generates the full ML project health report as Markdown text.
    Accepts either a local folder path or a GitHub URL.
    """
    try:
        actual_path, temp_dir = resolve_repo_source(request.repo_path)
    except ValueError as e:
        return {"error": str(e)}

    files = parse_repository(actual_path)
    chunks = chunk_repository(actual_path)
    score_report = score_project(files)

    report_text = generate_ml_report(files, chunks, score_report)

    if temp_dir:
        cleanup_repo(temp_dir)

    return {"report": report_text}


@app.get("/")
def root():
    return {"message": "NeuralForge AI API is running"}