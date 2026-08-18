from parser.repo_chunker import chunk_repository
from embeddings.embedder import embed_chunks
from vector_db.vector_store import VectorStore
from retrieval.retriever import Retriever
from llm.rag_chain import ask_question


def main():
    repo_path = input("Enter repository path: ")

    print("\nParsing and chunking repository...")
    chunks = chunk_repository(repo_path)
    print(f"Found {len(chunks)} chunks.")

    print("\nGenerating embeddings...")
    chunks = embed_chunks(chunks)

    print("\nBuilding vector store...")
    store = VectorStore()
    store.add_chunks(chunks)

    retriever = Retriever(store)

    print("\nReady! Ask a question about the codebase (or type 'exit' to quit).\n")

    while True:
        question = input("Question: ")
        if question.lower() == "exit":
            break

        answer = ask_question(retriever, question)
        print("\nAnswer:", answer, "\n")


if __name__ == "__main__":
    main()