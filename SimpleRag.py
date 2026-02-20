"""
Simple RAG (Retrieval Augmented Generation) Script
Loads a document, chunks it, stores in FAISS, and answers questions using GPT-4.
"""

import os
import numpy as np

# Load environment variables from .env file (must be before using OPENAI_API_KEY)
from dotenv import load_dotenv
load_dotenv()

import faiss
from openai import AsyncOpenAI, OpenAI

# -----------------------------------------------------------------------------
# Lazy initialization: document and FAISS index are created on first query
# -----------------------------------------------------------------------------
CHUNK_SIZE = 200  # Try 1000 for comparison
_rag_initialized = False

# Set by initialize_rag(); used by get_embedding, query_rag, query_rag_async
document_text = None
chunks = None
chunk_embeddings = None
index = None
openai_client = None
async_openai_client = None


def initialize_rag():
    """Initialize the RAG system: load document, create chunks, build FAISS index."""
    global document_text, chunks, chunk_embeddings, index, openai_client, async_openai_client

    # Resolve document path: Modal uses /root, local run uses project directory
    doc_path = "/root/RagDocument.txt" if os.path.exists("/root/RagDocument.txt") else "RagDocument.txt"
    with open(doc_path, "r", encoding="utf-8") as f:
        document_text = f.read()
    print("Document loaded successfully!")

    # Chunk the document
    chunks = []
    for i in range(0, len(document_text), CHUNK_SIZE):
        chunk = document_text[i : i + CHUNK_SIZE]
        if chunk.strip():
            chunks.append(chunk)
    print(f"Chunks created: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}: {len(chunk)} characters")

    # OpenAI clients and FAISS index
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    async_openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_embedding(text: str) -> list[float]:
        """Get embedding vector for text using OpenAI's embedding API."""
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    chunk_embeddings = [get_embedding(chunk) for chunk in chunks]
    embedding_array = np.array(chunk_embeddings).astype("float32")
    embedding_dim = embedding_array.shape[1]
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(embedding_array)
    print("Chunks stored in FAISS!")


def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text using OpenAI's embedding API (requires initialize_rag first)."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding


def query_rag(question: str, max_results: int = 3) -> tuple[str, list[str]]:
    """
    Query the RAG system with a question and return the answer plus source chunks.
    Used by both the interactive script and the FastAPI app.
    """
    global _rag_initialized
    if not _rag_initialized:
        initialize_rag()
        _rag_initialized = True

    # Embed the question and search FAISS for top k similar chunks
    question_embedding = np.array([get_embedding(question)]).astype("float32")
    k = min(max_results, len(chunks))
    distances, indices = index.search(question_embedding, k)

    # Use indices to get the actual chunk texts (sorted by relevance)
    retrieved_chunks = [chunks[i] for i in indices[0]]

    # Build context from retrieved chunks
    context = "\n\n---\n\n".join(retrieved_chunks)

    system_message = """You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context doesn't contain the answer, say so. Be concise and accurate."""

    user_message = f"""Context from the document:

{context}

---

Question: {question}

Answer:"""

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    answer = response.choices[0].message.content
    return answer, retrieved_chunks


async def query_rag_async(question: str, max_results: int = 3) -> tuple[str, list[str]]:
    """
    Async version of query_rag for FastAPI. Uses AsyncOpenAI so API calls
    don't block the event loop—multiple concurrent requests can run in parallel.
    """
    global _rag_initialized
    if not _rag_initialized:
        initialize_rag()
        _rag_initialized = True

    # await: non-blocking embedding call—event loop can handle other requests
    response = await async_openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=question,
    )
    question_embedding = np.array([response.data[0].embedding]).astype("float32")

    k = min(max_results, len(chunks))
    distances, indices = index.search(question_embedding, k)
    retrieved_chunks = [chunks[i] for i in indices[0]]

    context = "\n\n---\n\n".join(retrieved_chunks)
    system_message = """You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context doesn't contain the answer, say so. Be concise and accurate."""
    user_message = f"""Context from the document:

{context}

---

Question: {question}

Answer:"""

    # await: non-blocking chat completion—typically 1–5 seconds of I/O
    response = await async_openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
    )

    answer = response.choices[0].message.content
    return answer, retrieved_chunks


# -----------------------------------------------------------------------------
# INTERACTIVE MODE (run as script)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    user_question = input("\nAsk a question about the document: ")
    answer, retrieved_chunks = query_rag(user_question)

    # Display retrieved chunks
    SEPARATOR = "═" * 60
    question_embedding = np.array([get_embedding(user_question)]).astype("float32")
    k = min(3, len(chunks))
    distances, indices = index.search(question_embedding, k)

    print(f"\n{SEPARATOR}")
    print("  RETRIEVED CHUNKS")
    print(f"{SEPARATOR}\n")

    for rank, idx in enumerate(indices[0], start=1):
        l2_distance = distances[0][rank - 1]
        similarity = 1.0 / (1.0 + l2_distance)
        print(f"  ┌─ Chunk #{rank} (index {idx})")
        print(f"  │  Similarity: {similarity:.2%}  |  L2 distance: {l2_distance:.4f}  |  {len(chunks[idx])} chars")
        print(f"  │")
        print(f"  │  Text:")
        for line in chunks[idx].splitlines():
            print(f"  │    {line}")
        print(f"  └{'─' * 58}\n")

    print(f"{SEPARATOR}\n")
    print(f"{SEPARATOR}")
    print("  AI ANSWER")
    print(f"{SEPARATOR}\n")
    print(answer)
    print(f"\n{SEPARATOR}")
