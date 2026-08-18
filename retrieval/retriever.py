from embeddings.embedder import embed_chunk


class Retriever:
    """
    Takes a user's question, embeds it, and finds the most relevant
    code chunks from the vector store.
    """

    def __init__(self, vector_store):
        self.vector_store = vector_store

    def retrieve(self, query, top_k=5):
        """
        query: a plain English question, e.g. "how does the sorting work?"
        Returns the top_k most relevant chunks (with their code, not just names).
        """
        query_embedding = embed_chunk(query)
        results = self.vector_store.search(query_embedding, top_k=top_k)
        return results

    def retrieve_as_context(self, query, top_k=5):
        """
        Same as retrieve(), but formats the results as a single text block
        ready to be inserted into an LLM prompt.
        """
        results = self.retrieve(query, top_k=top_k)

        context_parts = []
        for r in results:
            chunk = r["chunk"]
            context_parts.append(
                f"File: {chunk['file_path']}\n"
                f"Name: {chunk['name']} ({chunk['chunk_type']})\n"
                f"Code:\n{chunk['code']}\n"
            )

        return "\n---\n".join(context_parts)


if __name__ == "__main__":
    from chunking.python_chunker import chunk_python_file
    from embeddings.embedder import embed_chunks
    from vector_db.vector_store import VectorStore

    sample_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

class Calculator:
    def divide(self, a, b):
        return a / b
"""

    chunks = chunk_python_file(sample_code, "sample.py")
    chunks = embed_chunks(chunks)

    store = VectorStore()
    store.add_chunks(chunks)

    retriever = Retriever(store)

    query = "how do I divide two numbers?"
    context = retriever.retrieve_as_context(query, top_k=2)

    print("Query:", query)
    print("\nRetrieved Context:\n")
    print(context)