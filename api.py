"""
FastAPI application that wraps the RAG system from SimpleRag.py.
Provides a REST API for querying documents with retrieval-augmented generation.
"""

import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# 1. FastAPI app instance
# -----------------------------------------------------------------------------
# Create the FastAPI application. The app handles routing, validation, and
# automatic OpenAPI documentation at /docs.
app = FastAPI(
    title="RAG Query API",
    description="Query documents using Retrieval Augmented Generation",
    version="1.0.0",
)

# -----------------------------------------------------------------------------
# 2. Pydantic request model
# -----------------------------------------------------------------------------
# Defines the expected shape of incoming POST /query requests.
# Pydantic automatically validates the JSON body and returns 422 if invalid.
class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="The question to ask the RAG system",
    )
    max_results: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of document chunks to retrieve (1-10)",
    )


# -----------------------------------------------------------------------------
# 3. Pydantic response model
# -----------------------------------------------------------------------------
# Defines the shape of the API response. Ensures consistent JSON structure.
class QueryResponse(BaseModel):
    answer: str = Field(..., description="The AI-generated answer")
    sources: list[str] = Field(..., description="Retrieved document chunks used as context")
    request_id: str = Field(..., description="Unique identifier for this request")


# -----------------------------------------------------------------------------
# 4. POST /query endpoint (async for concurrency)
# -----------------------------------------------------------------------------
# async def: FastAPI can handle multiple /query requests concurrently. While one
# request awaits OpenAI, others can start—no thread pool or blocking.
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    request_id = str(uuid.uuid4())

    try:
        # Import here to defer RAG initialization until first request
        from SimpleRag import query_rag_async

        # await: yields control during OpenAI I/O; other requests can run
        answer, sources = await query_rag_async(
            question=request.question,
            max_results=request.max_results,
        )

        return QueryResponse(
            answer=answer,
            sources=sources,
            request_id=request_id,
        )

    except Exception as e:
        # OpenAI API failures (rate limits, network, invalid key, etc.)
        raise HTTPException(
            status_code=503,
            detail=f"OpenAI service error: {str(e)}",
        )


# -----------------------------------------------------------------------------
# 5. GET /health endpoint (sync—no I/O, fast env check)
# -----------------------------------------------------------------------------
# def (sync): os.getenv is instant; no benefit from async here.
@app.get("/health")
def health():
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key and api_key.strip():
        return {"status": "healthy"}
    return {"status": "degraded"}


# Custom exception handler: return 400 for validation errors (per requirements)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


# -----------------------------------------------------------------------------
# 6. CORS middleware
# -----------------------------------------------------------------------------
# Allows browser-based clients from any origin to call this API.
# Use allow_origins=["*"] only for development/testing; restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
