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
from openai import OpenAI

# -----------------------------------------------------------------------------
# 1. LOAD THE DOCUMENT
# -----------------------------------------------------------------------------
# Read the text file that contains the content we want to query
with open("RagDocument.txt", "r", encoding="utf-8") as f:
    document_text = f.read()

print("Document loaded successfully!")

# -----------------------------------------------------------------------------
# 2. CHUNK THE DOCUMENT
# -----------------------------------------------------------------------------
# Change this to compare results: 200 = smaller, more precise chunks; 1000 = larger context
CHUNK_SIZE = 200  # Try 1000 for comparison
chunks = []

for i in range(0, len(document_text), CHUNK_SIZE):
    chunk = document_text[i : i + CHUNK_SIZE]
    if chunk.strip():  # Skip empty chunks
        chunks.append(chunk)

# 1. Show how many chunks were created
print(f"Chunks created: {len(chunks)}")

# 2. Show the size (character count) of each chunk
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i}: {len(chunk)} characters")

# -----------------------------------------------------------------------------
# 3. STORE CHUNKS IN FAISS
# -----------------------------------------------------------------------------
# FAISS is a vector similarity search library - it stores embeddings for fast lookup
# We use OpenAI to create embeddings (numerical representations that capture meaning)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_embedding(text: str) -> list[float]:
    """Get embedding vector for text using OpenAI's embedding API."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

# Create embeddings for all chunks
chunk_embeddings = [get_embedding(chunk) for chunk in chunks]
embedding_array = np.array(chunk_embeddings).astype("float32")

# Create FAISS index (flat index for exact search - good for small datasets)
embedding_dim = embedding_array.shape[1]
index = faiss.IndexFlatL2(embedding_dim)
index.add(embedding_array)

print("Chunks stored in FAISS!")

# -----------------------------------------------------------------------------
# 4 & 5. GET USER QUESTION AND RETRIEVE RELEVANT CHUNKS
# -----------------------------------------------------------------------------
user_question = input("\nAsk a question about the document: ")

# Embed the question and search FAISS for top 3 similar chunks
question_embedding = np.array([get_embedding(user_question)]).astype("float32")
k = min(3, len(chunks))
distances, indices = index.search(question_embedding, k)

# Use indices to get the actual chunk texts (sorted by relevance)
retrieved_chunks = [chunks[i] for i in indices[0]]

# -----------------------------------------------------------------------------
# DISPLAY RETRIEVED CHUNKS (with actual text and similarity scores)
# -----------------------------------------------------------------------------
SEPARATOR = "═" * 60
print(f"\n{SEPARATOR}")
print("  RETRIEVED CHUNKS")
print(f"{SEPARATOR}\n")

for rank, idx in enumerate(indices[0], start=1):
    l2_distance = distances[0][rank - 1]
    # Convert L2 distance to similarity: 1/(1+distance) → 0-1 scale (higher = more similar)
    similarity = 1.0 / (1.0 + l2_distance)

    print(f"  ┌─ Chunk #{rank} (index {idx})")
    print(f"  │  Similarity: {similarity:.2%}  |  L2 distance: {l2_distance:.4f}  |  {len(chunks[idx])} chars")
    print(f"  │")
    print(f"  │  Text:")
    for line in chunks[idx].splitlines():
        print(f"  │    {line}")
    print(f"  └{'─' * 58}\n")

print(f"{SEPARATOR}\n")

# -----------------------------------------------------------------------------
# 6. SEND TO GPT-4 FOR ANSWER
# -----------------------------------------------------------------------------
# Build context from retrieved chunks
context = "\n\n---\n\n".join(retrieved_chunks)

# Create the prompt with context and question
system_message = """You are a helpful assistant. Answer the user's question based ONLY on the provided context.
If the context doesn't contain the answer, say so. Be concise and accurate."""

user_message = f"""Context from the document:

{context}

---

Question: {user_question}

Answer:"""

# Call OpenAI GPT-4 API
response = openai_client.chat.completions.create(
    model="gpt-4o",  # GPT-4 model (use gpt-4o-mini for lower cost)
    messages=[
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]
)

# -----------------------------------------------------------------------------
# 7. PRINT THE ANSWER
# -----------------------------------------------------------------------------
answer = response.choices[0].message.content

print(f"{SEPARATOR}")
print("  AI ANSWER")
print(f"{SEPARATOR}\n")
print(answer)
print(f"\n{SEPARATOR}")
