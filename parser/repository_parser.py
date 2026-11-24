import fnmatch
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union


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


def parse_repository(
    repo_path: str,
    byte_budget: Optional[int] = None,
    time_budget: Optional[float] = None,
    return_stats: bool = False,
    progress_callback: Optional[Any] = None,
) -> Union[List[Dict[str, Any]], Tuple[List[Dict[str, Any]], Dict[str, Any]]]:
    """
    Parses source code files from a repository in a deterministic order (smallest first),
    skipping ignored directories, deliberate fixtures, and .neuralforgeignore patterns.
    Stops scanning when byte_budget or time_budget is exceeded and returns partial results.
    """
    repo = Path(repo_path)
    repository_data: List[Dict[str, Any]] = []
    ignore_patterns = _load_ignore_patterns(repo)

    if not repo.exists():
        stats = {
            "truncated": False,
            "reason": None,
            "files_scanned": 0,
            "files_skipped": 0,
            "total_files": 0,
            "scanned_bytes": 0,
        }
        return (repository_data, stats) if return_stats else repository_data

    # Collect candidate files
    candidates: List[Tuple[int, str, Path]] = []
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

        size = file.stat().st_size
        if size > MAX_FILE_SIZE:
            continue

        candidates.append((size, rel_path, file))

    # Deterministic order: smallest first, tie-break by relative path
    candidates.sort(key=lambda item: (item[0], item[1]))
    total_files = len(candidates)

    if progress_callback and total_files == 0:
        progress_callback(0, 0)

    start_time = time.time()
    scanned_bytes = 0
    files_scanned = 0
    truncated = False
    reason = None

    for size, rel_path, file in candidates:
        if byte_budget is not None and (scanned_bytes + size > byte_budget):
            truncated = True
            reason = f"Source code size exceeded {byte_budget // (1024 * 1024)}MB limit"
            break

        if time_budget is not None and (time.time() - start_time > time_budget):
            truncated = True
            reason = f"Audit time exceeded {int(time_budget)}s limit"
            break

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
                    "size_bytes": size,
                }
            )
            scanned_bytes += size
            files_scanned += 1
            if progress_callback:
                progress_callback(files_scanned, total_files)

        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

    files_skipped = total_files - files_scanned
    if files_skipped > 0 and (byte_budget is not None or time_budget is not None):
        truncated = True
        if not reason:
            reason = "File processing limits exceeded"

    stats = {
        "truncated": truncated,
        "reason": reason,
        "files_scanned": files_scanned,
        "files_skipped": files_skipped,
        "total_files": total_files,
        "scanned_bytes": scanned_bytes,
    }

    if return_stats:
        return repository_data, stats
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