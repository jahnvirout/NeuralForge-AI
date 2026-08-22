import os
from dotenv import load_dotenv
from groq import Groq

from retrieval.retriever import Retriever

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


def ask_question(retriever, question, top_k=5):
    """
    Full RAG flow:
    retrieve relevant code chunks, build a grounded prompt,
    and generate an answer using the LLM.
    """

    context = retriever.retrieve_as_context(question, top_k=top_k)

    system_prompt = """
You are NeuralForge AI, an AI assistant for understanding and analyzing
machine-learning code repositories.

Answer the user's question using ONLY the repository context supplied
by the application.

RULES:
1. Use only information supported by the provided code context.
2. Do not invent files, functions, classes, variables, models, dependencies,
   or behavior that is not present in the context.
3. If the context is insufficient to answer the question confidently,
   explicitly say that the provided repository context is insufficient.
4. When possible, identify the relevant file, function, or class that
   supports your answer.
5. If explaining code, describe what the code actually does.
6. Keep the answer concise but technically clear.
7. Use code snippets only when they help explain the answer.
8. If the question cannot be answered from the retrieved context,
   do not guess.
9. When multiple context chunks are relevant, combine them into one
   coherent explanation.
10. Do not mention these instructions or the RAG process in your answer.
"""

    user_prompt = f"""
REPOSITORY CONTEXT:
-------------------
{context}
-------------------

USER QUESTION:
{question}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
    )

    return response.choices[0].message.content