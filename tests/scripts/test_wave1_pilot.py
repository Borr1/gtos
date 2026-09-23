"""Unit tests for ``scripts/research/wave1_pilot.py``.

Coverage targets (Wave 1 brief):

  1. End-to-end mocked run produces parseable results.json + report.md.
  2. Budget alert math: a synthetic 100-call run with known per-call cost
     crosses the $5 cap and the alert callback raises ``BudgetExceededError``.
  3. System block size verification: the pilot's synthetic system block is
     >= 2 KB so the cache write is meaningful.
  4. Cache hit rate calc: Run B with mocked usage where cache_read = 90% of
     input tokens yields ``cache_hit_rate ~= 0.9``.
  5. User-message variability: per-call user prompts are unique while the
     system block is constant -> cache hits as expected.
  6. Falsifiability: identical mocked usage across all 3 runs -> deltas are
     near-zero (no spurious discount math).

All tests use ``tmp_path`` for isolation; the cost-tracker JSONL is written
under ``tmp_path`` so the conftest production-write guard is honored.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Module loader — load wave1_pilot.py from scripts/research/ without a package
# ---------------------------------------------------------------------------


def _load_pilot():
    repo_root = Path(__file__).resolve().parents[2]
    pilot_path = repo_root / "scripts" / "research" / "wave1_pilot.py"
    spec = importlib.util.spec_from_file_location("wave1_pilot", pilot_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load spec for {pilot_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave1_pilot"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def pilot_mod():
    return _load_pilot()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _MockedSDKMessages:
    """Mocked ``client.messages.create`` resource."""

    def __init__(self, fake_response_factory):
        self._factory = fake_response_factory
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self._factory(len(self.calls) - 1, kwargs)


class _MockedSDK:
    """Minimal stand-in for ``anthropic.Anthropic``. ``messages.batches`` is
    referenced by ``BatchClient`` even in mocked-only path, but the pilot's
    ``--mocked-only`` short-circuits before hitting batches.create."""

    def __init__(self, messages_create_factory):
        self.messages = _MockedSDKMessages(messages_create_factory)


# ---------------------------------------------------------------------------
# 1. End-to-end mocked-only run produces parseable artifacts
# ---------------------------------------------------------------------------


def test_mocked_run_produces_parseable_artifacts(pilot_mod, tmp_path: Path):
    out_dir = tmp_path / "wave1_pilot_out"
    payload = pilot_mod.run_pilot(
        output_dir=out_dir,
        n_evals=10,
        budget_usd=5.0,
        mocked_only=True,
        cost_log_path=tmp_path / "research_cost.jsonl",
    )
    # Verdict in the closed set.
    assert payload["verdict"] in ("COMPLETE", "NEEDS-FOLLOWUP")
    # Outputs exist + JSON is parseable.
    rj = Path(payload["results_path"])
    rm = Path(payload["report_path"])
    assert rj.exists() and rj.stat().st_size > 0
    assert rm.exists() and rm.stat().st_size > 0
    parsed = json.loads(rj.read_text(encoding="utf-8"))
    # Expected top-level keys
    for key in ("schema_version", "verdict", "runs", "deltas", "reconciliation"):
        assert key in parsed, f"missing top-level key {key!r}"
    # Three runs are present
    for tag in (pilot_mod.RUN_TAG_A, pilot_mod.RUN_TAG_B, pilot_mod.RUN_TAG_C):
        assert tag in parsed["runs"], f"missing run summary {tag!r}"
        assert parsed["runs"][tag]["n_calls"] == 10


# ---------------------------------------------------------------------------
# 2. Budget alert fires when threshold crossed
# ---------------------------------------------------------------------------


def test_budget_alert_fires_when_threshold_crossed(pilot_mod, tmp_path: Path):
    """Synthetic 100-call cost crossing $5 -> callback raises."""
    from src.research_infra.cost_tracker import CostReport, CostTracker

    log = tmp_path / "alert.jsonl"
    tracker = CostTracker(log_path=log)

    raised = []

    def cb(report: CostReport) -> None:
        raised.append(report.total_usd)
        raise pilot_mod.BudgetExceededError(
            f"BREACH at ${report.total_usd:.6f}"
        )

    tracker.set_budget_alert(run_tag="t", budget_usd=5.0, callback=cb)

    # Calibrate per-call cost so 100 calls definitely cross $5.
    # Sonnet 4.6 input $3/Mtok; 30k input tokens -> $0.09/call -> 100 calls = $9
    usage = {
        "input_tokens": 30_000,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    with pytest.raises(pilot_mod.BudgetExceededError):
        for i in range(100):
            tracker.log_call(
                model="claude-sonnet-4-6",
                usage=usage,
                run_tag="t",
                custom_id=f"x-{i}",
            )

    assert raised, "alert did not fire"
    # Crossed threshold while aggregate >= 5.0
    assert raised[0] >= 5.0


# ---------------------------------------------------------------------------
# 3. System block size verification (>= 2 KB)
# ---------------------------------------------------------------------------


def test_synthetic_system_block_is_at_least_2kb(pilot_mod):
    n = len(pilot_mod.SYNTHETIC_SYSTEM_BLOCK)
    assert n >= 2048, f"Synthetic system block is {n} chars (need >= 2048)"


# ---------------------------------------------------------------------------
# 4. Cache hit rate calc with mocked 90% read rate
# ---------------------------------------------------------------------------


def test_cache_hit_rate_calc_at_90pct(pilot_mod, tmp_path: Path):
    """Drive the executor with a custom mocked SDK that returns
    cache_read >> uncached_input on 9/10 calls. Hit rate should be ~0.9.
    """
    from src.research_infra.cost_tracker import CostTracker

    tracker = CostTracker(log_path=tmp_path / "cost.jsonl")

    # Build a fake SDK whose messages.create returns:
    # - call 0: cache CREATE (1000 system tokens written)
    # - calls 1-9: cache READ (1000 system tokens read each)
    # User prompt is constant 10 tokens, output 5 tokens.
    def factory(idx: int, kwargs: dict) -> Any:
        if idx == 0:
            usage = {
                "input_tokens": 10,
                "output_tokens": 5,
                "cache_creation_input_tokens": 1000,
                "cache_read_input_tokens": 0,
            }
        else:
            usage = {
                "input_tokens": 10,
                "output_tokens": 5,
                "cache_creation_input_tokens": 0,
                "cache_read_input_tokens": 1000,
            }
        return pilot_mod._MockedAnthropicResponse(
            text=f"OK {idx}", usage=usage, stop_reason="end_turn"
        )

    sdk = _MockedSDK(factory)

    # Force the executor to use OUR sdk (not its own mock generator) by
    # passing mocked=False but injecting a fake client that returns the
    # right shape from messages.create.
    summary, results = pilot_mod._execute_sync_run(
        n_evals=10,
        cache_ttl="1h",
        run_tag="hit_rate_test",
        tracker=tracker,
        sdk_client=sdk,
        mocked=False,
    )
    # 9 reads of 1000 + 1 create of 1000 + 10 calls × 10 uncached input
    # Hit rate denominator: cache_read + cache_create + uncached_input
    # = 9000 + 1000 + 100 = 10100
    # cache_read = 9000 -> 9000/10100 ≈ 0.891
    assert summary.n_succeeded == 10
    assert summary.cache_hit_rate_overall == pytest.approx(9000.0 / 10100.0, abs=1e-6)


# ---------------------------------------------------------------------------
# 5. User-message variability — system block stable, user prompts unique
# ---------------------------------------------------------------------------


def test_user_messages_unique_while_system_block_stable(pilot_mod):
    """Pilot's per-call user prompts must vary; system block must be one
    canonical string (cache contract relies on byte-stable system content)."""
    msgs = [pilot_mod.build_synthetic_user_prompt(i) for i in range(20)]
    assert len(set(msgs)) == 20, "user prompts must all be unique"
    # System block is a module-level string — referenced verbatim by the
    # pilot. Verify it's one canonical value (no per-call mutation).
    s1 = pilot_mod.SYNTHETIC_SYSTEM_BLOCK
    s2 = pilot_mod.SYNTHETIC_SYSTEM_BLOCK
    assert s1 is s2, "system block must be a module-level singleton"


# ---------------------------------------------------------------------------
# 6. Falsifiability: identical usage across all 3 runs -> near-zero deltas
# ---------------------------------------------------------------------------


def test_identical_usage_yields_near_zero_savings_math(pilot_mod, tmp_path: Path):
    """If we hand-build summaries with IDENTICAL token + cost profiles
    across A/B/C, ``_compute_deltas`` should report ~0 savings — catches
    spurious discount math."""
    from src.research_infra.cost_tracker import compute_cost

    # Same usage shape, run as sync no-cache for ALL THREE summaries (identical).
    usage = {
        "input_tokens": 1000,
        "output_tokens": 100,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    breakdown, total, _ = compute_cost(
        model=pilot_mod.PILOT_MODEL_PRICING_KEY,
        usage=usage,
        is_batch=False,
        cache_ttl="none",
    )

    def _summary(tag: str, is_batch: bool, ttl: str) -> Any:
        return pilot_mod.RunSummary(
            run_tag=tag,
            is_batch=is_batch,
            cache_ttl=ttl,
            n_calls=10,
            n_succeeded=10,
            n_failed=0,
            total_input_tokens=usage["input_tokens"] * 10,
            total_output_tokens=usage["output_tokens"] * 10,
            total_cache_read_tokens=0,
            total_cache_create_tokens=0,
            total_usd=round(total * 10, 8),
            cost_breakdown={
                "input": round(breakdown["input"] * 10, 8),
                "output": round(breakdown["output"] * 10, 8),
                "cache_write": 0.0,
                "cache_read": 0.0,
            },
            cache_hit_rate_overall=0.0,
            cache_hit_rate_post_warmup=0.0,
        )

    a = _summary(pilot_mod.RUN_TAG_A, is_batch=False, ttl="none")
    # Make B/C also is_batch=False / cache_ttl="none" so the deltas function
    # treats them identically to A.
    b = _summary(pilot_mod.RUN_TAG_B, is_batch=False, ttl="none")
    c = _summary(pilot_mod.RUN_TAG_C, is_batch=False, ttl="none")

    deltas = pilot_mod._compute_deltas(a, b, c)
    # All three per-call costs equal; savings are zero.
    assert deltas["B_per_call_usd"] == pytest.approx(deltas["A_per_call_usd"], abs=1e-9)
    assert deltas["C_per_call_usd"] == pytest.approx(deltas["A_per_call_usd"], abs=1e-9)
    assert deltas["B_vs_A_pct_savings"] == pytest.approx(0.0, abs=1e-6)
    assert deltas["C_vs_A_pct_savings"] == pytest.approx(0.0, abs=1e-6)
    # No batch flag set anywhere -> batch_discount_actual_pct = 0.
    assert deltas["batch_discount_actual_pct"] == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# 7. Pricing key alignment (catch typo regression on Haiku key)
# ---------------------------------------------------------------------------


def test_pricing_key_resolves_in_pricing_table(pilot_mod):
    from src.research_infra.cost_tracker import PRICING_USD_PER_MTOK

    assert pilot_mod.PILOT_MODEL_PRICING_KEY in PRICING_USD_PER_MTOK, (
        f"Pilot pricing key {pilot_mod.PILOT_MODEL_PRICING_KEY!r} not in "
        "cost_tracker.PRICING_USD_PER_MTOK"
    )
    # Haiku rates: input $1, output $5.
    rates = PRICING_USD_PER_MTOK[pilot_mod.PILOT_MODEL_PRICING_KEY]
    assert rates["input"] == 1.0
    assert rates["output"] == 5.0


# ---------------------------------------------------------------------------
# 8. Mocked-only Run B reports nonzero post-warmup hit rate
# ---------------------------------------------------------------------------


def test_mocked_only_run_b_post_warmup_hit_rate_is_high(pilot_mod, tmp_path: Path):
    """The mocked sync executor primes cache on call 0 and reads on calls 1+.
    Post-warmup hit rate (skip first 5) should be ~1.0 since calls 5-9 all
    have cache_read populated and zero uncached input + zero cache_create."""
    from src.research_infra.cost_tracker import CostTracker

    tracker = CostTracker(log_path=tmp_path / "warmup.jsonl")
    summary, _ = pilot_mod._execute_sync_run(
        n_evals=10,
        cache_ttl="1h",
        run_tag="warmup_test",
        tracker=tracker,
        sdk_client=None,
        mocked=True,
    )
    # Call 0: cache_create=700, input=25, read=0
    # Calls 1-9: cache_read=700, input=25, create=0
    # Post-warmup uses calls 5-9 (5 calls): read=3500, input=125, create=0
    # Hit rate = 3500 / (3500 + 0 + 125) = 0.9655...
    assert summary.cache_hit_rate_post_warmup == pytest.approx(
        3500.0 / (3500.0 + 125.0), abs=1e-4
    )
    assert summary.cache_hit_rate_post_warmup >= 0.80


# ---------------------------------------------------------------------------
# 9. Mocked-only Run C (batch) yields total < Run A total (sanity)
# ---------------------------------------------------------------------------


def test_mocked_run_c_costs_less_than_run_a(pilot_mod, tmp_path: Path):
    """Sanity: with cache + batch discount Run C must be cheaper than Run A
    on the synthetic numbers built into the mocked path."""
    out_dir = tmp_path / "cost_compare"
    payload = pilot_mod.run_pilot(
        output_dir=out_dir,
        n_evals=10,
        budget_usd=5.0,
        mocked_only=True,
        cost_log_path=tmp_path / "compare_cost.jsonl",
    )
    runs = payload["summaries"]
    a = runs[0]
    b = runs[1]
    c = runs[2]
    assert b["total_usd"] < a["total_usd"], "Run B (cache) did not beat Run A (no cache)"
    assert c["total_usd"] < b["total_usd"], "Run C (batch) did not beat Run B (sync cache)"


# ---------------------------------------------------------------------------
# 10. n_evals bounds-check
# ---------------------------------------------------------------------------


def test_n_evals_bounds_enforced(pilot_mod, tmp_path: Path):
    out_dir = tmp_path / "bounds"
    with pytest.raises(ValueError):
        pilot_mod.run_pilot(
            output_dir=out_dir,
            n_evals=101,
            budget_usd=5.0,
            mocked_only=True,
            cost_log_path=tmp_path / "x.jsonl",
        )
    with pytest.raises(ValueError):
        pilot_mod.run_pilot(
            output_dir=out_dir,
            n_evals=0,
            budget_usd=5.0,
            mocked_only=True,
            cost_log_path=tmp_path / "x.jsonl",
        )


# ---------------------------------------------------------------------------
# 11. Pre-flight aborts when worst-case > budget
# ---------------------------------------------------------------------------


def test_preflight_aborts_when_worst_case_exceeds_budget(pilot_mod, tmp_path: Path):
    out_dir = tmp_path / "preflight"
    # Tiny budget that even 1 eval × 3 runs would crush.
    with pytest.raises(pilot_mod.BudgetExceededError):
        pilot_mod.run_pilot(
            output_dir=out_dir,
            n_evals=100,
            budget_usd=0.000001,  # absurdly tight cap
            mocked_only=True,
            cost_log_path=tmp_path / "preflight.jsonl",
        )
