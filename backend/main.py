from fastapi import FastAPI
from pydantic import BaseModel

from parser.repository_parser import parse_repository
from parser.repo_chunker import chunk_repository
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


@app.post("/upload-repo")
def upload_repo(request: RepoRequest):
    """
    Parses, chunks, embeds, and indexes a repo. Returns a session_id
    to use for asking questions later.
    """
    chunks = chunk_repository(request.repo_path)
    chunks = embed_chunks(chunks)

    store = VectorStore()
    store.add_chunks(chunks)

    retriever = Retriever(store)

    session_id = request.repo_path

    sessions[session_id] = retriever

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
    """
    files = parse_repository(request.repo_path)
    report = score_project(files)
    return report


@app.post("/report")
def report(request: RepoRequest):
    """
    Generates the full ML project health report as Markdown text.
    """
    files = parse_repository(request.repo_path)
    chunks = chunk_repository(request.repo_path)
    score_report = score_project(files)

    report_text = generate_ml_report(files, chunks, score_report)
    return {"report": report_text}


@app.get("/")
def root():
    return {"message": "NeuralForge AI API is running"}