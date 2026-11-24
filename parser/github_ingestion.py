import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

from parser.repository_parser import SUPPORTED_EXTENSIONS, _is_ignored, _load_ignore_patterns

# Maximum total analyzable source bytes after ignore filtering (50 MB of source code)
MAX_ANALYZABLE_SOURCE_BYTES = 50 * 1024 * 1024
DEFAULT_CLONE_TIMEOUT = 60  # seconds


def is_valid_github_url(url: str) -> bool:
    """
    Validates that the input is a valid github.com repository URL.
    Prevents command injection or invalid URL schemes.
    """
    if not isinstance(url, str):
        return False
    pattern = r"^https://github\.com/[\w\-]+/[\w\-\.]+/?$"
    return re.match(pattern, url.strip()) is not None


def calculate_analyzable_source_bytes(folder_path: str) -> int:
    """
    Computes total size in bytes of all supported source and notebook files,
    honoring default ignored directories and .neuralforgeignore.
    """
    folder = Path(folder_path)
    if not folder.exists():
        return 0

    ignore_patterns = _load_ignore_patterns(folder)
    total_bytes = 0

    for file in folder.rglob("*"):
        if not file.is_file():
            continue

        try:
            rel_path = str(file.relative_to(folder))
        except ValueError:
            rel_path = file.name

        if _is_ignored(rel_path, file.parts, ignore_patterns):
            continue

        if file.suffix in SUPPORTED_EXTENSIONS:
            total_bytes += file.stat().st_size

    return total_bytes


def clone_github_repo(github_url: str, timeout_seconds: int = DEFAULT_CLONE_TIMEOUT) -> str:
    """
    Performs smart, resource-efficient shallow cloning of a public GitHub repository.
    Uses blobless filter (--filter=blob:none) and sparse-checkout to exclude heavy
    venv, node_modules, and binaries before downloading files.
    Always cleans up temporary directory on failure.
    Raises ValueError on invalid URL or size limit breach, or TimeoutError on clone timeout.
    """
    if not is_valid_github_url(github_url):
        raise ValueError(f"Invalid GitHub repository URL: {github_url}")

    temp_dir = tempfile.mkdtemp(prefix="neuralforge_")

    try:
        # Step 1: Shallow blobless clone without initial checkout
        subprocess.run(
            [
                "git", "clone",
                "--depth", "1",
                "--filter=blob:none",
                "--no-checkout",
                github_url,
                temp_dir,
            ],
            check=True,
            capture_output=True,
            timeout=timeout_seconds,
            text=True,
        )

        # Step 2: Configure sparse-checkout without cone mode to filter files
        subprocess.run(
            ["git", "sparse-checkout", "init", "--no-cone"],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            timeout=15,
            text=True,
        )

        sparse_patterns = [
            "*.py",
            "*.ipynb",
            "*.java",
            "*.cpp",
            "*.c",
            "*.js",
            "*.ts",
            ".neuralforgeignore",
            "!venv/",
            "!.venv/",
            "!node_modules/",
            "!site-packages/",
        ]
        subprocess.run(
            ["git", "sparse-checkout", "set"] + sparse_patterns,
            cwd=temp_dir,
            check=True,
            capture_output=True,
            timeout=15,
            text=True,
        )

        # Step 3: Checkout filtered files
        subprocess.run(
            ["git", "checkout"],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            timeout=timeout_seconds,
            text=True,
        )

    except subprocess.TimeoutExpired:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise TimeoutError(f"Cloning {github_url} exceeded {timeout_seconds}s timeout limit.")
    except Exception:
        # Fallback to standard shallow depth=1 clone if sparse-checkout is unsupported
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir = tempfile.mkdtemp(prefix="neuralforge_")
            subprocess.run(
                ["git", "clone", "--depth", "1", github_url, temp_dir],
                check=True,
                capture_output=True,
                timeout=timeout_seconds,
                text=True,
            )
        except subprocess.TimeoutExpired:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise TimeoutError(f"Cloning {github_url} timed out after {timeout_seconds}s.")
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise ValueError(f"Failed to clone repository: {e}")

    return temp_dir


def cleanup_repo(temp_dir: str) -> None:
    """Deletes temporary cloned repository directory."""
    if temp_dir and Path(temp_dir).exists():
        shutil.rmtree(temp_dir, ignore_errors=True)