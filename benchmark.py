"""
Benchmark script for the RAG Query API.
Sends 10 concurrent POST /query requests and measures performance.
"""

import asyncio
import time

import aiohttp

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
API_ENDPOINT = "http://127.0.0.1:8000/query"
NUM_REQUESTS = 10
QUESTION = "What does ShopifyAudit do?"
PAYLOAD = {"question": QUESTION, "max_results": 3}


async def fetch_one(session: aiohttp.ClientSession) -> tuple[float | None, str | None]:
    """Send one POST request. Returns (time, None) on success, (None, error_msg) on failure."""
    start = time.perf_counter()
    try:
        async with session.post(API_ENDPOINT, json=PAYLOAD) as resp:
            await resp.json()
            if resp.status != 200:
                return None, f"HTTP {resp.status}"
        return time.perf_counter() - start, None
    except aiohttp.ClientError as e:
        return None, str(e)
    except asyncio.TimeoutError:
        return None, "timeout"


async def run_benchmark() -> list[tuple[float | None, str | None]]:
    """Run 10 concurrent requests and return individual timings (seconds)."""
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_one(session) for _ in range(NUM_REQUESTS)]
        return await asyncio.gather(*tasks)


def main():
    print("=" * 60)
    print("  RAG API Benchmark - 10 Concurrent Requests")
    print("=" * 60)
    print(f"  Endpoint: POST {API_ENDPOINT}")
    print(f"  Question: {QUESTION}")
    print(f"  Requests: {NUM_REQUESTS} (simultaneous)")
    print("=" * 60)

    total_start = time.perf_counter()
    results = asyncio.run(run_benchmark())
    total_elapsed = time.perf_counter() - total_start

    timings = [r[0] for r in results if r[0] is not None]
    failures = [(i + 1, r[1]) for i, r in enumerate(results) if r[0] is None]

    if failures:
        print()
        print("  FAILED REQUESTS")
        print("-" * 60)
        for req_num, err in failures:
            print(f"    Request {req_num:2d}: {err}")
        print("-" * 60)

    if not timings:
        print()
        print("  No successful requests.")
        print("=" * 60)
        raise SystemExit(1)

    total_time = total_elapsed
    avg_time = total_time / len(timings)
    min_time = min(timings)
    max_time = max(timings)

    print()
    print("  RESULTS")
    print("-" * 60)
    print(f"  Successful: {len(timings)}/{NUM_REQUESTS}")
    print(f"  Total time (all complete):  {total_time:.2f}s")
    print(f"  Average time per request:   {avg_time:.2f}s")
    print(f"  Min time per request:       {min_time:.2f}s")
    print(f"  Max time per request:       {max_time:.2f}s")
    print("-" * 60)
    print()
    print("  Per-request times (s):")
    for i, r in enumerate(results, 1):
        t, err = r
        if t is not None:
            print(f"    Request {i:2d}: {t:.2f}s")
        else:
            print(f"    Request {i:2d}: FAILED ({err})")
    print("=" * 60)


if __name__ == "__main__":
    main()
