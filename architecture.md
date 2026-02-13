# RAG System Architecture

## System Overview

A Retrieval-Augmented Generation system that answers questions based on document content using OpenAI's GPT-4o.

---

## System Flow

### Indexing Phase (When SimpleRag.py runs):

**Step 1: Document Loading**
- Loads `document.txt` from local filesystem

**Step 2: Text Chunking**
- Splits document into 200-character chunks
- Uses RecursiveCharacterTextSplitter (preserves sentence boundaries)

**Step 3: Embedding Generation**
- Converts each chunk to vector embeddings
- Model: OpenAI text-embedding-3-small
- Dimensions: 1536

**Step 4: Vector Storage**
- Stores embeddings in FAISS (in-memory index)
- Enables fast similarity search

---

### Query Phase (When user asks a question):

**Step 1: Question Embedding**
- User's question is converted to a vector
- Uses same embedding model (text-embedding-3-small)

**Step 2: Similarity Search**
- FAISS compares question vector against all chunk vectors
- Retrieves top 3 most similar chunks
- Similarity metric: Cosine distance

**Step 3: Context Building**
- Combines the 3 retrieved chunks
- Adds user's question

**Step 4: LLM Generation**
- Sends context + question to GPT-4o
- Model generates answer based on retrieved chunks
- If answer not in chunks: GPT-4o says "not found in context"

**Step 5: Return Answer**
- User receives final answer

---

## Components

### **Document Loader**
- **Technology:** Python file I/O
- **Current:** Reads .txt files only
- **Limitation:** Can't handle PDFs, DOCX, or multiple files

### **Text Chunker**
- **Technology:** LangChain RecursiveCharacterTextSplitter
- **Chunk size:** 200 characters
- **Why 200:** [From your Day 3 experiments - balance between context and precision]
- **Trade-off:** Smaller chunks = more precise but less context

### **Embeddings**
- **Model:** text-embedding-3-small
- **Cost:** $0.00002 per 1K tokens (~$0.000004 per chunk)
- **Why this model:** Cheap, fast, good quality for general use
- **Alternative:** text-embedding-3-large (better quality, 3x cost)

### **Vector Store**
- **Technology:** FAISS (Facebook AI Similarity Search)
- **Type:** In-memory, CPU-based
- **Cost:** Free (open source)
- **Why FAISS:** 
  - Zero cost
  - Fast for <10K documents
  - No external dependencies
- **Limitation:** Data lost on restart (not persistent)
- **When to switch:** Move to Pinecone/Weaviate when need persistence or >10K documents

### **LLM**
- **Model:** GPT-4o
- **Cost:** $0.005 per 1K input tokens, $0.015 per 1K output tokens
- **Why GPT-4o:** Latest model, good quality
- **Alternative:** GPT-3.5-turbo (20x cheaper, lower quality)

---

## Current Limitations

### **1. Data Loss on Restart**
- **Problem:** FAISS index is in-memory only
- **Impact:** Must re-index documents every time script runs
- **When this matters:** If indexing takes >30 seconds or documents change frequently
- **Solution:** Switch to persistent vector DB (Pinecone, Weaviate)

### **2. No Caching**
- **Problem:** Same question asked twice = two OpenAI API calls
- **Cost impact:** If 30% of queries are duplicates, wasting 30% of API costs
- **Solution:** Add Redis cache for common queries (would reduce costs ~40%)

### **3. Single Document Only**
- **Problem:** Can only load one .txt file
- **Impact:** Can't scale to multiple knowledge sources
- **Solution:** Add document loader that handles multiple files/formats

### **4. Fixed Chunk Size**
- **Problem:** 200 chars might be too small for some content, too large for others
- **Impact:** May fragment important information or include irrelevant content
- **Solution:** Adaptive chunking based on content type

### **5. No Error Handling**
- **Problem:** If OpenAI API is down, system crashes
- **Impact:** Poor user experience
- **Solution:** Add try/catch, retry logic, fallback responses

---

## What Breaks at 10x Scale?

### **Current: ~10 queries/day**
- Works perfectly
- Cost: ~$0.50/month
- No performance issues

### **At 100 queries/day (10x):**

**What breaks FIRST: Cost becomes noticeable**

**Analysis:**
- Current cost per query: ~$0.005 (mostly GPT-4o)
- At 100 queries/day: 100 × $0.005 = $0.50/day = $15/month
- Not broken yet, but now worth optimizing

**Solutions:**
1. Add caching (reduce to $9/month - 40% savings)
2. Switch to GPT-3.5 for simple queries (reduce to $3/month)
3. Compress prompts (reduce to $12/month)

**Chosen solution:** Add caching first (biggest ROI, least effort)

---

### **At 1,000 queries/day (100x):**

**What breaks FIRST: Need persistent storage**

**Analysis:**
- FAISS re-indexing on every restart becomes annoying
- Cost: $150/month (caching helps but still high)
- Need better monitoring

**Solutions:**
1. Switch to Pinecone ($70/month, persistent)
2. Add monitoring/logging (LangSmith)
3. Implement query categorization (simple questions → GPT-3.5, complex → GPT-4o)

**Total cost at 1K queries/day:** ~$100/month (acceptable)

---

### **At 10,000 queries/day (1000x):**

**What breaks FIRST: Vector search becomes bottleneck**

**Analysis:**
- FAISS in-memory may hit memory limits
- Latency increases (search takes >500ms)
- Cost: $1,500/month without optimization

**Solutions:**
1. Shard FAISS by topic
2. Move to managed vector DB with replicas (Pinecone/Weaviate)
3. Add CDN for caching common queries
4. Implement query queue (async processing)

**Architecture changes needed:**
- Load balancer
- Multiple API instances
- Separate vector DB server
- Redis cluster

**Estimated cost at 10K queries/day:** $500/month (with optimizations)

---

## Design Decisions

### **Why FAISS over Pinecone?**

**Decision:** FAISS (in-memory, local)

**Alternative:** Pinecone (managed, cloud)

**Reasoning:**
- Current scale: <100 documents, <100 queries/day
- FAISS cost: $0
- Pinecone cost: $70/month
- For MVP/learning: Free wins

**Trade-offs:**
- **FAISS Pro:** Free, fast, simple
- **FAISS Con:** Not persistent, manual scaling
- **Pinecone Pro:** Persistent, auto-scales, managed
- **Pinecone Con:** $70/month, vendor lock-in

**When I'd switch:**
- Need persistence (production app)
- >10K documents
- >1K queries/day
- Team collaboration (shared index)

---

### **Why 200-character chunks?**

**Decision:** 200 characters per chunk

**Alternatives tested:** 100, 500, 1000

**Reasoning:**
- 100: Too small, context fragmented
- 200: Good balance
- 500: Too much irrelevant info
- 1000: Very unfocused results

**Trade-off:**
- Smaller chunks: More precise retrieval, less context
- Larger chunks: More context, less precise

**When I'd reconsider:**
- Different content types (legal docs = larger, tweets = smaller)
- Different use cases (Q&A = smaller, summarization = larger)

---

### **Why GPT-4o over GPT-3.5?**

**Decision:** GPT-4o

**Alternative:** GPT-3.5-turbo (20x cheaper)

**Reasoning:**
- At <100 queries/day, cost difference is ~$12/month
- Quality matters more than cost at this scale
- GPT-4o better at following "answer only from context" instruction

**Trade-off:**
- GPT-4o: Better quality, expensive
- GPT-3.5: Cheaper, more hallucination risk

**When I'd switch:**
- At 10K+ queries/day (cost = $1500/mo → need to optimize)
- Would implement smart routing: simple queries → 3.5, complex → 4o
- Could reduce costs 60% with minimal quality loss

---

## Cost Analysis

### **Per-Query Cost Breakdown**

**Assumptions:**
- Question: 20 words (~27 tokens)
- Retrieved chunks: 3 × 200 chars = 600 chars (~150 tokens)
- Answer: 50 words (~67 tokens)

**Costs:**
| Component | Usage | Cost per Query |
|-----------|-------|----------------|
| Question embedding | 27 tokens | $0.0000005 |
| Chunk embeddings (one-time) | 150 tokens × 3 | $0.000009 |
| GPT-4o input | 177 tokens | $0.00089 |
| GPT-4o output | 67 tokens | $0.001 |
| **Total** | | **~$0.002/query** |

### **Monthly Projections**

| Scale | Queries/Month | Monthly Cost | Notes |
|-------|---------------|--------------|-------|
| Current | 300 | $0.60 | Learning/testing |
| 10x | 3,000 | $6 | Add caching → $3.60 |
| 100x | 30,000 | $60 | Need monitoring |
| 1000x | 300,000 | $600 | Need architecture changes |

### **Cost Optimization Opportunities**

**1. Caching (40% savings)**
- Cache identical queries
- Cache embeddings for chunks
- Estimated hit rate: 30-40%
- Savings at 3K queries/month: ~$2.40

**2. Model Selection (60% savings on some queries)**
- Route simple queries to GPT-3.5
- Keep GPT-4o for complex queries
- Estimated: 50% of queries can use GPT-3.5
- Savings: ~$30/month at 30K queries

**3. Prompt Compression (20% savings)**
- Reduce chunk content sent to LLM
- More aggressive chunk filtering
- Savings: ~$12/month at 30K queries

---

## Future Enhancements

**Priority 1: Caching**
- Add Redis for query results
- Cache embeddings
- Target: 40% cost reduction

**Priority 2: Monitoring**
- Add LangSmith tracing
- Track: latency, cost, quality
- Set up alerts

**Priority 3: Multi-document Support**
- Load multiple files
- Support PDF, DOCX
- Better for real use cases

**Priority 4: Persistent Storage**
- Switch to Pinecone or Weaviate
- No data loss on restart
- Easier to update documents

---

## Interview-Ready Talking Points

**"Walk me through your architecture"**
→ [Point to this doc, explain flow diagram]

**"Why did you choose FAISS?"**
→ "At current scale (<100 queries/day, <100 docs), cost optimization matters more than features. FAISS is free and fast. I'd switch to Pinecone at 1K+ queries/day when persistence and auto-scaling justify the $70/month cost."

**"What happens at 10x scale?"**
→ "At 10x (100 queries/day), cost becomes noticeable ($15/month). I'd add Redis caching first - 40% cost reduction for minimal effort. At 100x, I'd need persistent storage. At 1000x, I'd need to rearchitect with load balancing and query queues."

**"How much does this cost?"**
→ "Currently ~$0.002 per query. At 1K queries/day that's $60/month. With caching and smart model routing (GPT-3.5 for simple queries, GPT-4o for complex), I can keep it under $30/month."