from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model():
    """
    Loads the embedding model once and reuses it.
    Loading a model is slow, so we don't want to reload it every time we embed something.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_chunk(code_text):
    """
    Takes a single chunk of code (string) and returns its embedding (a vector).
    """
    model = get_model()
    embedding = model.encode(code_text)
    return embedding


def embed_chunks(chunks):
    """
    Takes a list of chunk dicts (from the chunker) and adds an 'embedding' field to each.
    """
    model = get_model()

    texts = [chunk["code"] for chunk in chunks]
    embeddings = model.encode(texts)

    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    return chunks


if __name__ == "__main__":
    sample_texts = [
        "def add(a, b): return a + b",
        "def subtract(a, b): return a - b",
    ]

    model = get_model()
    embeddings = model.encode(sample_texts)

    for text, emb in zip(sample_texts, embeddings):
        print("Text:", text)
        print("Embedding shape:", emb.shape)
        print("First 5 values:", emb[:5])
        print()