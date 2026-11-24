import fnmatch
import json
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".ipynb": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".js": "JavaScript",
    ".ts": "TypeScript",
}

DATA_EXTENSIONS = {
    ".csv", ".tsv", ".parquet", ".pkl", ".pickle", ".h5",
    ".hdf5", ".zip", ".tar", ".gz", ".7z", ".png", ".jpg",
    ".jpeg", ".pt", ".pth", ".bin", ".onnx", ".feather",
}

IGNORED_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", "fixtures", "site-packages",
}

MAX_FILE_SIZE = 500_000  # ~500KB


def _load_ignore_patterns(repo: Path) -> List[str]:
    """Loads ignore patterns from an optional .neuralforgeignore file."""
    ignore_file = repo / ".neuralforgeignore"
    patterns: List[str] = []
    if ignore_file.is_file():
        try:
            with open(ignore_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#"):
                        patterns.append(stripped)
        except Exception:
            pass
    return patterns


def _is_ignored(rel_path: str, parts: Tuple[str, ...], patterns: List[str]) -> bool:
    """Checks if a file path matches default ignored directories or .neuralforgeignore patterns."""
    if any(part in IGNORED_DIRS for part in parts):
        return True

    rel_posix = rel_path.replace("\\", "/")
    for pattern in patterns:
        clean_pat = pattern.rstrip("/")
        if fnmatch.fnmatch(rel_posix, pattern) or fnmatch.fnmatch(rel_posix, f"*{pattern}*"):
            return True
        if any(fnmatch.fnmatch(part, clean_pat) for part in parts):
            return True
    return False


def _extract_ipynb_code(raw_json: str) -> str:
    """Extracts executable Python code cells from a Jupyter notebook JSON."""
    try:
        nb_data = json.loads(raw_json)
        code_lines: List[str] = []
        for cell in nb_data.get("cells", []):
            if cell.get("cell_type") == "code":
                source = cell.get("source", [])
                if isinstance(source, list):
                    code_lines.append("".join(source))
                elif isinstance(source, str):
                    code_lines.append(source)
                code_lines.append("\n")
        return "".join(code_lines)
    except Exception:
        return ""


def parse_repository(repo_path: str) -> List[Dict[str, Any]]:
    """
    Parses source code files from a repository, skipping ignored directories,
    deliberate fixtures, and patterns defined in an optional .neuralforgeignore.
    Supports Python, Jupyter Notebooks (.ipynb code cells), and common source formats.
    """
    repo = Path(repo_path)
    repository_data: List[Dict[str, Any]] = []
    ignore_patterns = _load_ignore_patterns(repo)

    if not repo.exists():
        return repository_data

    for file in repo.rglob("*"):
        if not file.is_file():
            continue

        try:
            rel_path = str(file.relative_to(repo))
        except ValueError:
            rel_path = file.name

        if _is_ignored(rel_path, file.parts, ignore_patterns):
            continue

        if file.suffix not in SUPPORTED_EXTENSIONS:
            continue

        if file.stat().st_size > MAX_FILE_SIZE:
            continue

        try:
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                raw_content = f.read()

            if file.suffix == ".ipynb":
                code = _extract_ipynb_code(raw_content)
                if not code.strip():
                    continue
            else:
                code = raw_content

            repository_data.append(
                {
                    "file_name": file.name,
                    "relative_path": rel_path,
                    "language": SUPPORTED_EXTENSIONS[file.suffix],
                    "code": code,
                    "size_bytes": file.stat().st_size,
                }
            )

        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

    return repository_data


def scan_committed_data_files(repo_path: str) -> List[Dict[str, Any]]:
    """
    Finds binary and large dataset files committed to the repository
    (e.g. CSVs, weights, images, archives) and returns their metadata.
    """
    repo = Path(repo_path)
    data_files: List[Dict[str, Any]] = []
    ignore_patterns = _load_ignore_patterns(repo)

    if not repo.exists():
        return data_files

    for file in repo.rglob("*"):
        if not file.is_file():
            continue

        try:
            rel_path = str(file.relative_to(repo))
        except ValueError:
            rel_path = file.name

        if _is_ignored(rel_path, file.parts, ignore_patterns):
            continue

        if file.suffix.lower() in DATA_EXTENSIONS:
            size_bytes = file.stat().st_size
            data_files.append({
                "file": rel_path,
                "size_bytes": size_bytes,
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "extension": file.suffix.lower(),
            })

    return data_files