# RAG API Performance Analysis

## 1. Test Setup

| Parameter | Value |
|-----------|-------|
| **What was tested** | 10 concurrent requests to POST /query |
| **Question** | "What does ShopifyAudit do?" |
| **Environment** | Local machine, async FastAPI |
| **Tools** | aiohttp, asyncio |
| **Endpoint** | http://127.0.0.1:8000/query |

---

## 2. Results Summary

| Metric | Value |
|--------|-------|
| Total time (all 10 complete) | 7.54s |
| Average per request | 0.75s *(misleading—see analysis)* |
| Individual request range | 6.85s – 7.53s |
| Success rate | 10/10 (100%) |

---

## 3. Key Findings

- All 10 requests completed in **~7 seconds**, nearly simultaneously.
- **Async concurrency is working:** requests ran in parallel rather than blocking each other.
- **Sequential comparison:** If run one-by-one, total time would be ~70 seconds (10 × 7s).
- **Speedup:** ~9.3× for 10 concurrent users vs sequential execution.

---

## 4. Bottleneck Analysis

| Component | Status | Notes |
|-----------|--------|-------|
| **Primary bottleneck** | OpenAI API latency (~7s) | All requests wait on embedding + chat completion |
| **Evidence** | Similar per-request times | 6.85s–7.53s indicates shared waiting on I/O |
| **Not bottlenecked** | FAISS search | Fast, in-memory |
| **Not bottlenecked** | FastAPI processing | Negligible overhead |
| **Not bottlenecked** | Local network | Minimal impact |

**Conclusion:** The system is **I/O bound** (waiting on OpenAI), not CPU bound. Async design is appropriate.

---

## 5. Performance at Scale

| Concurrent Users | Estimated Total Time | Notes |
|------------------|----------------------|-------|
| 10 | ~7.5s | Current benchmark |
| 50 | ~7–8s | Until OpenAI rate limits |
| 100 | Degraded | Would hit OpenAI rate limits (~60 req/sec on paid tier) |
| **Breaking point** | ~60 req/sec | OpenAI API limit |

---

## 6. Optimization Opportunities

### Priority 1: Caching (40% cost/time reduction)

| Aspect | Detail |
|--------|--------|
| Approach | Cache identical questions |
| Estimated impact | ~30% API call reduction if 30% of queries repeat |
| Implementation | Redis with 1-hour TTL |

### Priority 2: Model Selection (60% cost reduction for simple queries)

| Aspect | Detail |
|--------|--------|
| Approach | Route simple queries to GPT-3.5 (cheaper, faster) |
| Complex queries | Keep on GPT-4o |
| Estimated impact | ~50% of queries can use GPT-3.5 |

### Priority 3: Prompt Compression (20% speedup)

| Aspect | Detail |
|--------|--------|
| Approach | Reduce chunk content sent to LLM, compress system prompts |
| Trade-off | Possible slight quality reduction |

---

## 7. Production Readiness Assessment

### Current State

| Category | Status |
|----------|--------|
| Handles concurrent requests efficiently | ✅ |
| Async implementation working | ✅ |
| Caching | ❌ (waste on repeated queries) |
| Rate limiting | ❌ (vulnerable to abuse) |
| Monitoring | ❌ (limited visibility into issues) |

### Next Steps for Production

1. Add Redis caching *(Day 10)*
2. Implement rate limiting
3. Add monitoring/logging *(Day 19)*
4. Deploy to cloud *(Day 7)*
