"""
Centralized configuration for NeuralForge AI.
Defines file limits, supported extensions, ignore patterns, and resource boundaries.
"""

# Maximum individual file size to read (~500 KB)
MAX_FILE_SIZE_BYTES: int = 500_000

# Maximum analyzable source code size for cloned/uploaded repositories (50 MB)
MAX_ANALYZABLE_SOURCE_BYTES: int = 50 * 1024 * 1024

# Maximum number of AST code chunks to vectorize in FAISS index (prevents OOM on Render 512MB)
MAX_INDEX_CHUNKS: int = 500

# Embedding batch size for SentenceTransformer
EMBEDDING_BATCH_SIZE: int = 32

# In-memory session store bounds
MAX_SESSIONS: int = 10
SESSION_TTL_SECONDS: int = 3600  # 1 hour

# Timeout in seconds for git clone operations
DEFAULT_CLONE_TIMEOUT_SECONDS: int = 60

# Timeout in seconds for static repository analysis
MAX_ANALYSIS_SECONDS: int = 60

# Supported code extensions and their language names
SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".ipynb": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".js": "JavaScript",
    ".ts": "TypeScript",
}

# Large dataset and binary extensions skipped during source code analysis
DATA_EXTENSIONS = {
    ".csv", ".tsv", ".parquet", ".pkl", ".pickle", ".h5",
    ".hdf5", ".zip", ".tar", ".gz", ".7z", ".png", ".jpg",
    ".jpeg", ".pt", ".pth", ".bin", ".onnx", ".feather",
}

# Directories excluded from parsing and chunking
IGNORED_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", "fixtures", "site-packages",
    "dist", "build", ".egg-info",
}
