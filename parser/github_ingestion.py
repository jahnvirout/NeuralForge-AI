import re
import shutil
import tempfile
from pathlib import Path

import git

MAX_REPO_SIZE_MB = 300  # reject repos larger than this after cloning


def is_valid_github_url(url):
    """
    Checks that the URL matches a real github.com/user/repo pattern.
    Prevents random/malicious URLs from being passed to git clone.
    """
    pattern = r"^https://github\.com/[\w\-]+/[\w\-\.]+/?$"
    return re.match(pattern, url) is not None


def get_folder_size_mb(folder_path):
    """
    Calculates total size of a folder in megabytes.
    """
    total_size = 0
    for file in Path(folder_path).rglob("*"):
        if file.is_file():
            total_size += file.stat().st_size
    return total_size / (1024 * 1024)


def clone_github_repo(github_url):
    """
    Clones a public GitHub repo into a temporary directory.
    Returns the local path to the cloned repo.
    Raises ValueError if the URL is invalid or the repo is too large.
    """
    if not is_valid_github_url(github_url):
        raise ValueError(f"Invalid GitHub URL: {github_url}")

    temp_dir = tempfile.mkdtemp(prefix="neuralforge_")

    try:
        git.Repo.clone_from(github_url, temp_dir, depth=1)
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError(f"Failed to clone repository: {e}")

    size_mb = get_folder_size_mb(temp_dir)

    if size_mb > MAX_REPO_SIZE_MB:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise ValueError(f"Repository too large ({size_mb:.1f}MB). Limit is {MAX_REPO_SIZE_MB}MB.")

    return temp_dir


def cleanup_repo(temp_dir):
    """
    Deletes the temporary cloned repo folder.
    """
    shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    test_url = "https://github.com/karpathy/micrograd"

    print(f"Cloning {test_url}...")
    repo_path = clone_github_repo(test_url)
    print(f"Cloned to: {repo_path}")

    from parser.repository_parser import parse_repository
    files = parse_repository(repo_path)
    print(f"Parsed {len(files)} code files.")

    cleanup_repo(repo_path)
    print("Cleaned up temp directory.")