from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".js": "JavaScript",
    ".ts": "TypeScript"
}

IGNORED_DIRS = {".git", "node_modules", "venv", "__pycache__", ".pytest_cache"}

MAX_FILE_SIZE = 500_000  # ~500KB


def parse_repository(repo_path):

    repo = Path(repo_path)

    repository_data = []

    for file in repo.rglob("*"):

        if any(part in IGNORED_DIRS for part in file.parts):
            continue

        if not file.is_file():
            continue

        if file.suffix not in SUPPORTED_EXTENSIONS:
            continue

        if file.stat().st_size > MAX_FILE_SIZE:
            print(f"Skipping {file}: too large ({file.stat().st_size} bytes)")
            continue

        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()

            repository_data.append(
                {
                    "file_name": file.name,
                    "relative_path": str(file.relative_to(repo)),
                    "language": SUPPORTED_EXTENSIONS[file.suffix],
                    "code": code,
                }
            )

        except UnicodeDecodeError:
            print(f"Skipping {file}: not UTF-8 encoded")
            continue

        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue

    return repository_data


if __name__ == "__main__":

    path = input("Enter repository path: ")

    files = parse_repository(path)

    print(f"\nFound {len(files)} code files.\n")

    for file in files:

        print("=" * 50)