# AI RAG System

A production-ready Retrieval-Augmented Generation (RAG) API built with FastAPI, OpenAI, and FAISS.

## 🚀 Live Demo

**Try it now:** https://somoksenguptaprogrammer--rag-api-fastapi-app.modal.run/docs

### Quick Test:
```bash
curl -X POST "https://somoksenguptaprogrammer--rag-api-fastapi-app.modal.run/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What does ShopifyAudit do?"}'
```

## 📋 Features

- ✅ Production-ready FastAPI application
- ✅ Async/concurrent request handling
- ✅ OpenAI GPT-4o for answer generation
- ✅ FAISS vector search for retrieval
- ✅ Deployed on Modal (serverless, auto-scaling)
- ✅ Automatic API documentation
- ✅ Health monitoring endpoint

## 🏗️ Architecture

See [architecture.md](architecture.md) for detailed system design, cost analysis, and scaling strategy.

## 📊 Performance

- Handles 10 concurrent users with 9.3x speedup (async)
- Response time: ~7 seconds (OpenAI latency)
- Cost: ~$0.002 per query
- See [performanceAnalysis.md](performanceAnalysis.md) for benchmarks

## 🛠️ Tech Stack

- **Backend:** FastAPI (Python)
- **LLM:** OpenAI GPT-4o
- **Vector DB:** FAISS (in-memory)
- **Deployment:** Modal (serverless)
- **API Docs:** Swagger UI (auto-generated)

## 📖 Documentation

- [Architecture Design](architecture.md)
- [Performance Analysis](performanceAnalysis.md)
- [API Documentation](https://somoksenguptaprogrammer--rag-api-fastapi-app.modal.run/docs)

## 🔗 Repository

[GitHub Repository](https://github.com/SomokSenguptaProgrammer/SomokFirstRepo)
