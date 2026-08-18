import faiss
import numpy as np


class VectorStore:
    """
    Wraps a FAISS index for storing and searching code chunk embeddings.
    """

    def __init__(self, dimension=384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.chunk_metadata = []  # keeps track of which chunk each vector belongs to

    def add_chunks(self, chunks):
        """
        chunks: list of dicts, each with an 'embedding' key (from embedder.py)
        """
        embeddings = np.array([chunk["embedding"] for chunk in chunks]).astype("float32")
        self.index.add(embeddings)
        self.chunk_metadata.extend(chunks)

    def search(self, query_embedding, top_k=5):
        """
        query_embedding: a single embedding vector (from embedding a user's question)
        Returns the top_k most similar chunks.
        """
        query_vector = np.array([query_embedding]).astype("float32")
        distances, indices = self.index.search(query_vector, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx == -1:
                continue
            chunk = self.chunk_metadata[idx]
            results.append({"chunk": chunk, "distance": dist})

        return results


if __name__ == "__main__":
    from chunking.python_chunker import chunk_python_file
    from embeddings.embedder import embed_chunks

    sample_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
"""

    chunks = chunk_python_file(sample_code, "sample.py")
    chunks = embed_chunks(chunks)

    store = VectorStore()
    store.add_chunks(chunks)

    from embeddings.embedder import embed_chunk
    query_embedding = embed_chunk("function that adds two numbers")

    results = store.search(query_embedding, top_k=2)

    for r in results:
        print("Match:", r["chunk"]["name"], "| Distance:", r["distance"])