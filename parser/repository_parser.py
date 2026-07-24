from pathlib import Path

SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".js": "JavaScript",
    ".ts": "TypeScript"
}


def parse_repository(repo_path):

    repo = Path(repo_path)

    repository_data = []

    for file in repo.rglob("*"):

        if not file.is_file():
            continue

        if file.suffix not in SUPPORTED_EXTENSIONS:
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

        except Exception as e:
            print(f"Error reading {file}: {e}")

    return repository_data


if __name__ == "__main__":

    path = input("Enter repository path: ")

    files = parse_repository(path)

    print(f"\nFound {len(files)} code files.\n")

    for file in files:

        print("=" * 50)
        print("File:", file["relative_path"])
        print("Language:", file["language"])
        print("Characters:", len(file["code"]))