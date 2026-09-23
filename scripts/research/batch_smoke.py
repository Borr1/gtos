"""End-to-end smoke test for the Anthropic Batch API wrapper.

Submits 5 trivial Haiku requests through ``src.research_infra.BatchClient``,
waits for the batch to end, and prints per-result content + the cumulative
usage block.

DO NOT run from inside Claude Code agent harness — this is the operator-only
verification script. The CEO runs it manually so the cost is attributed
correctly. Hard-coded model is Haiku (cheapest) so the smoke spend is
trivial; the production trading-decision model (Sonnet 4.6) is NEVER routed
through this script.

Cost
----
5 requests × ~10 input tokens × ~10 output tokens × Haiku 4.5 batch rates ≈
fractions of a cent. Even with retries the smoke is well under $0.01.

Usage
-----
    set ANTHROPIC_API_KEY=sk-...
    python scripts/research/batch_smoke.py

The script exits 0 on success, non-zero on any failure. Output is plain
text intended for human inspection.
"""

from __future__ import annotations

import json
import os
import sys
import time

# Allow running the script from any working directory by ensuring the repo
# root is on sys.path (the script lives two dirs deep).
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from src.research_infra.batch_client import BatchClient, BatchRequest  # noqa: E402

# Hard-coded for the smoke. The production gate uses Sonnet 4.6; the smoke
# uses Haiku 4.5 because we only care about end-to-end batch plumbing here.
SMOKE_MODEL = "claude-haiku-4-5-20251001"
SMOKE_REQUEST_COUNT = 5


def _build_requests() -> list[BatchRequest]:
    return [
        BatchRequest(
            custom_id=f"smoke-{i}",
            model=SMOKE_MODEL,
            messages=[{"role": "user", "content": "reply with the word OK"}],
            max_tokens=10,
            temperature=0.0,
        )
        for i in range(SMOKE_REQUEST_COUNT)
    ]


def _on_progress(status: str, counts: dict) -> None:
    print(f"  [poll] status={status!r} counts={json.dumps(counts, default=str)}")


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY is not set in the environment.", file=sys.stderr)
        return 2

    print(f"Submitting {SMOKE_REQUEST_COUNT} requests via BatchClient (model={SMOKE_MODEL})...")
    client = BatchClient(polling_interval_seconds=15, max_wait_seconds=3600)
    requests = _build_requests()

    submit_start = time.monotonic()
    batch_id = client.submit_batch(requests)
    print(f"Batch submitted: id={batch_id}")

    print("Polling for completion (interval=15s, max_wait=3600s)...")
    results = client.wait_and_fetch(batch_id, progress_callback=_on_progress)
    elapsed = time.monotonic() - submit_start

    print()
    print("=" * 60)
    print(f"Batch {batch_id} ended after {elapsed:.1f}s")
    print(f"Per-result content:")
    print("=" * 60)

    total_in = total_out = total_cache_create = total_cache_read = 0
    for cid in sorted(results):
        r = results[cid]
        if r.error is not None:
            print(f"  {cid}: ERROR {r.error}")
            continue
        print(f"  {cid}: stop={r.stop_reason!r} text={r.content_text!r}")
        u = r.usage or {}
        total_in += int(u.get("input_tokens", 0) or 0)
        total_out += int(u.get("output_tokens", 0) or 0)
        total_cache_create += int(u.get("cache_creation_input_tokens", 0) or 0)
        total_cache_read += int(u.get("cache_read_input_tokens", 0) or 0)

    print()
    print("Cumulative usage:")
    print(f"  input_tokens                = {total_in}")
    print(f"  output_tokens               = {total_out}")
    print(f"  cache_creation_input_tokens = {total_cache_create}")
    print(f"  cache_read_input_tokens     = {total_cache_read}")
    print()

    failures = [cid for cid, r in results.items() if r.error is not None]
    if failures:
        print(f"FAIL: {len(failures)} of {SMOKE_REQUEST_COUNT} results errored: {failures}")
        return 1
    if len(results) != SMOKE_REQUEST_COUNT:
        print(
            f"FAIL: expected {SMOKE_REQUEST_COUNT} results, got {len(results)}"
        )
        return 1
    print(f"OK: {len(results)}/{SMOKE_REQUEST_COUNT} succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
