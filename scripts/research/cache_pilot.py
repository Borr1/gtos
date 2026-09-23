"""Cache helper pilot — demonstrates 1h-TTL annotation + hit-rate measurement.

This script is a **documentation/demo runner**. It does NOT call the Anthropic
API. Usage data is mocked to mirror the response shape Anthropic returns from
``messages.create()`` so you can see how :class:`CacheMetrics` accumulates and
what :func:`annotate_system_blocks` produces on the wire.

Run::

    python scripts/research/cache_pilot.py

Expected output:
    1. The annotated request body (system blocks + cache_control)
    2. Per-call usage trace for a 50-evaluation simulated batch
    3. Final summary with hit-rate + savings estimate

Why no real API call? T0.3 is infrastructure for Phase 2-4 backtests; spending
on the demo would defeat the purpose. Real runs happen via
``scripts/simulate_t7_live_period.py`` once T0.1 (batch API) and T0.2 (cost
tracker) are merged.

Cross-references
----------------
- Helper module: ``src/research_infra/cache_helper.py``
- Production cache pin (5m default, do NOT change here):
  ``src/components/primary_analyzer.py:215-221``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running this script directly without `pip install -e .`.
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research_infra.cache_helper import (  # noqa: E402
    CacheMetrics,
    annotate_system_blocks,
)


# ---------------------------------------------------------------------------
# Mock helpers — simulate what Anthropic returns. Numbers are realistic for
# the GTOS XAUUSD primary analyzer prompt (system ~8000 tokens, user ~1500
# tokens, output ~500 tokens).
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TOKENS = 8_000
USER_PROMPT_TOKENS = 1_500
OUTPUT_TOKENS = 500


def mock_first_call_usage() -> dict:
    """Usage block for the FIRST call of a batch — populates the cache."""
    return {
        "input_tokens": USER_PROMPT_TOKENS,
        "cache_creation_input_tokens": SYSTEM_PROMPT_TOKENS,
        "cache_read_input_tokens": 0,
        "output_tokens": OUTPUT_TOKENS,
    }


def mock_cached_call_usage() -> dict:
    """Usage block for subsequent calls — system prompt served from cache."""
    return {
        "input_tokens": USER_PROMPT_TOKENS,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": SYSTEM_PROMPT_TOKENS,
        "output_tokens": OUTPUT_TOKENS,
    }


# ---------------------------------------------------------------------------
# Demo flow
# ---------------------------------------------------------------------------


def demo_annotate() -> list[dict]:
    """Show the request-body shape after 1h annotation."""
    print("=" * 72)
    print("STEP 1 -- Annotating the system blocks for 1h TTL")
    print("=" * 72)

    # Mirrors the production block shape from primary_analyzer.py:215-221.
    production_blocks = [
        {
            "type": "text",
            "text": (
                "<system prompt body, ~8000 tokens of MSO-gate instructions, "
                "static D1/H4 context, framework rules, etc>"
            ),
            # Production keeps 5m default (cache_control: {"type": "ephemeral"}).
            "cache_control": {"type": "ephemeral"},
        }
    ]

    annotated = annotate_system_blocks(production_blocks, ttl="1h")
    print("\nProduction (5m) shape -> input:")
    print(json.dumps(production_blocks, indent=2))
    print("\nResearch (1h) shape -> output:")
    print(json.dumps(annotated, indent=2))

    return annotated


def demo_cache_metrics(num_evals: int = 50) -> CacheMetrics:
    """Run a simulated batch of ``num_evals`` calls and report metrics."""
    print("\n" + "=" * 72)
    print(f"STEP 2 -- Simulating a {num_evals}-evaluation batch with 1h TTL")
    print("=" * 72)

    metrics = CacheMetrics()
    metrics.record(mock_first_call_usage())
    print(
        f"  Call 1/{num_evals}: cache CREATE -- "
        f"{SYSTEM_PROMPT_TOKENS} system tokens written to cache"
    )

    for i in range(2, num_evals + 1):
        metrics.record(mock_cached_call_usage())
    print(
        f"  Calls 2-{num_evals}/{num_evals}: cache READ -- "
        f"{SYSTEM_PROMPT_TOKENS} system tokens served from cache (each)"
    )

    return metrics


def demo_summary(metrics: CacheMetrics, ttl: str = "1h") -> None:
    """Pretty-print the final summary."""
    print("\n" + "=" * 72)
    print("STEP 3 -- Cache hit-rate + savings summary")
    print("=" * 72)

    summary = metrics.summary(ttl_used=ttl)
    print(json.dumps(summary, indent=2))

    print("\nKey takeaways:")
    print(
        f"  - {summary['calls']} calls -> hit_rate = "
        f"{summary['hit_rate'] * 100:.2f}%"
    )
    print(
        f"  - Cost (token-equivalents): with-cache = "
        f"{summary['estimated_cost_with_cache']:.0f}, "
        f"no-cache = {summary['estimated_cost_no_cache']:.0f}"
    )
    print(
        f"  - Savings: {summary['estimated_savings']:.0f} tokens "
        f"({summary['estimated_savings_pct'] * 100:.2f}% of no-cache cost)"
    )
    print(
        "\nNB: 'cost' is in base-input-token-equivalents. Multiply by your "
        "model's per-token base-input price (USD) for a $$ figure."
    )


def main() -> int:
    demo_annotate()
    metrics = demo_cache_metrics(num_evals=50)
    demo_summary(metrics, ttl="1h")
    print(
        "\n[OK] cache_pilot complete -- no API calls were made. "
        "See src/research_infra/README.md for usage notes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
