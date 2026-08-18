from parser.repository_parser import parse_repository
from chunking.python_chunker import chunk_python_file


def chunk_repository(repo_path):
    """
    Runs the repository parser first (gets all files),
    then chunks each Python file into function/class-level pieces.
    Returns one flat list of all chunks across the whole repo.
    """
    files = parse_repository(repo_path)

    all_chunks = []

    for file in files:

        if file["language"] != "Python":
            continue

        file_chunks = chunk_python_file(file["code"], file["relative_path"])
        all_chunks.extend(file_chunks)

    return all_chunks


if __name__ == "__main__":

    path = input("Enter repository path: ")

    chunks = chunk_repository(path)

    print(f"\nFound {len(chunks)} chunks.\n")

    for chunk in chunks:
        print("=" * 50)
        print("File:", chunk["file_path"])
        print("Name:", chunk["name"], "-", chunk["chunk_type"])
        print("Lines:", chunk["start_line"], "-", chunk["end_line"])