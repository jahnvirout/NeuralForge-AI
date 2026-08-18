import os
from dotenv import load_dotenv
from groq import Groq

from retrieval.retriever import Retriever

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


def ask_question(retriever, question, top_k=5):
    """
    Full RAG flow: retrieve relevant chunks, build a prompt, call the LLM.
    """
    context = retriever.retrieve_as_context(question, top_k=top_k)

    prompt = f"""You are a helpful assistant that answers questions about a codebase.
Use ONLY the following code context to answer the question. If the context doesn't contain enough information, say so.

Context:
{context}

Question: {question}

Answer:"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )

    return response.choices[0].message.content