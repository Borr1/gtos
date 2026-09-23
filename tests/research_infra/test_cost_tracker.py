"""Unit tests for ``src/research_infra/cost_tracker.py``.

Coverage targets (T0.2 brief):

  1. Pricing math — hand-calc cost for known usage; assert ≤ $0.0001 delta.
  2. Batch discount — is_batch=True ⇒ 0.50× input+output; cache rates unchanged.
  3. Cache 1h vs 5m — write rate differs per pricing table.
  4. JSONL persistence + reload roundtrip.
  5. aggregate() filters by run_tag.
  6. aggregate() filters by ``since`` (and ``until``).
  7. Budget alert fires when threshold crossed; not before.
  8. Concurrent log_call calls do not corrupt JSONL (file-lock atomicity).
  9. Unknown model raises a clear error (no silent fallback).

All tests use ``tmp_path`` for log isolation — the conftest production-write
guard blocks writes to ``shadow_logs/`` from the pytest process, so the
tracker's default sink must be redirected to ``tmp_path`` per test.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from src.research_infra.cost_tracker import (
    BATCH_DISCOUNT_INPUT_OUTPUT,
    PRICING_USD_PER_MTOK,
    CostEntry,
    CostReport,
    CostTracker,
    UnknownModelError,
    compute_cost,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _usage(
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_read: int = 0,
    cache_create: int = 0,
) -> Dict[str, int]:
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_create,
    }


def _tracker(tmp_path: Path) -> CostTracker:
    return CostTracker(log_path=tmp_path / "research_cost.jsonl")


# ---------------------------------------------------------------------------
# 1. Pricing math (hand-calc against published rates)
# ---------------------------------------------------------------------------


def test_compute_cost_sonnet_simple_input_output_only():
    # Sonnet 4.6: input $3.00 / Mtok, output $15.00 / Mtok
    # 1_000_000 input tokens = $3.00; 100_000 output tokens = $1.50
    # Total = $4.50; no cache, no batch.
    breakdown, total, _ = compute_cost(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000, output_tokens=100_000),
        is_batch=False,
        cache_ttl="none",
    )
    assert breakdown["input"] == pytest.approx(3.0, abs=0.0001)
    assert breakdown["output"] == pytest.approx(1.5, abs=0.0001)
    assert breakdown["cache_write"] == 0.0
    assert breakdown["cache_read"] == 0.0
    assert total == pytest.approx(4.5, abs=0.0001)


def test_compute_cost_opus_with_cache_5m():
    # Opus 4.7: input $15, output $75, cache_write_5m $18.75, cache_read $1.50
    # 200_000 input → $3.00
    # 50_000 output → $3.75
    # 100_000 cache_creation @ 5m → 100_000 * 18.75 / 1e6 = $1.875
    # 500_000 cache_read → 500_000 * 1.50 / 1e6 = $0.75
    # Total = 9.375
    breakdown, total, _ = compute_cost(
        model="claude-opus-4-7",
        usage=_usage(
            input_tokens=200_000,
            output_tokens=50_000,
            cache_create=100_000,
            cache_read=500_000,
        ),
        is_batch=False,
        cache_ttl="5m",
    )
    assert breakdown["input"] == pytest.approx(3.00, abs=0.0001)
    assert breakdown["output"] == pytest.approx(3.75, abs=0.0001)
    assert breakdown["cache_write"] == pytest.approx(1.875, abs=0.0001)
    assert breakdown["cache_read"] == pytest.approx(0.75, abs=0.0001)
    assert total == pytest.approx(9.375, abs=0.0001)


def test_compute_cost_haiku_simple():
    # Haiku 4.5: input $1.00, output $5.00
    # 500_000 input → $0.50; 200_000 output → $1.00
    breakdown, total, _ = compute_cost(
        model="claude-haiku-4-5",
        usage=_usage(input_tokens=500_000, output_tokens=200_000),
        is_batch=False,
        cache_ttl="none",
    )
    assert breakdown["input"] == pytest.approx(0.50, abs=0.0001)
    assert breakdown["output"] == pytest.approx(1.00, abs=0.0001)
    assert total == pytest.approx(1.50, abs=0.0001)


# ---------------------------------------------------------------------------
# 2. Batch discount (0.50× on input+output, NOT on cache)
# ---------------------------------------------------------------------------


def test_batch_discount_halves_input_output_only():
    usage = _usage(
        input_tokens=1_000_000,
        output_tokens=100_000,
        cache_create=100_000,
        cache_read=500_000,
    )

    full_breakdown, full_total, _ = compute_cost(
        model="claude-sonnet-4-6", usage=usage, is_batch=False, cache_ttl="5m"
    )
    batch_breakdown, batch_total, _ = compute_cost(
        model="claude-sonnet-4-6", usage=usage, is_batch=True, cache_ttl="5m"
    )

    # Input + output halved.
    assert batch_breakdown["input"] == pytest.approx(
        full_breakdown["input"] * BATCH_DISCOUNT_INPUT_OUTPUT, abs=0.0001
    )
    assert batch_breakdown["output"] == pytest.approx(
        full_breakdown["output"] * BATCH_DISCOUNT_INPUT_OUTPUT, abs=0.0001
    )
    # Cache untouched.
    assert batch_breakdown["cache_write"] == pytest.approx(
        full_breakdown["cache_write"], abs=0.0001
    )
    assert batch_breakdown["cache_read"] == pytest.approx(
        full_breakdown["cache_read"], abs=0.0001
    )
    # Total = full_total - 0.5*(input+output)
    expected_delta = (full_breakdown["input"] + full_breakdown["output"]) * (
        1.0 - BATCH_DISCOUNT_INPUT_OUTPUT
    )
    assert batch_total == pytest.approx(full_total - expected_delta, abs=0.0001)


# ---------------------------------------------------------------------------
# 3. Cache 1h vs 5m
# ---------------------------------------------------------------------------


def test_cache_write_5m_vs_1h_rate_difference():
    # Sonnet 4.6: cache_write_5m=$3.75, cache_write_1h=$6.00 per Mtok.
    # 1_000_000 cache_creation tokens → $3.75 (5m) vs $6.00 (1h).
    bd_5m, _, _ = compute_cost(
        model="claude-sonnet-4-6",
        usage=_usage(cache_create=1_000_000),
        is_batch=False,
        cache_ttl="5m",
    )
    bd_1h, _, _ = compute_cost(
        model="claude-sonnet-4-6",
        usage=_usage(cache_create=1_000_000),
        is_batch=False,
        cache_ttl="1h",
    )
    assert bd_5m["cache_write"] == pytest.approx(3.75, abs=0.0001)
    assert bd_1h["cache_write"] == pytest.approx(6.00, abs=0.0001)
    assert bd_1h["cache_write"] > bd_5m["cache_write"]


def test_cache_ttl_none_yields_zero_cache_write():
    bd, _, _ = compute_cost(
        model="claude-sonnet-4-6",
        usage=_usage(cache_create=1_000_000),  # nonzero, but TTL says "none"
        is_batch=False,
        cache_ttl="none",
    )
    assert bd["cache_write"] == 0.0


def test_invalid_cache_ttl_raises():
    with pytest.raises(ValueError, match="cache_ttl"):
        compute_cost(
            model="claude-sonnet-4-6",
            usage=_usage(input_tokens=100),
            is_batch=False,
            cache_ttl="bogus",
        )


# ---------------------------------------------------------------------------
# 4. JSONL persistence + reload roundtrip
# ---------------------------------------------------------------------------


def test_log_call_writes_jsonl_row(tmp_path):
    tracker = _tracker(tmp_path)
    entry = tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1000, output_tokens=200),
        run_tag="phase1_test",
        custom_id="cand_001",
    )

    p = tmp_path / "research_cost.jsonl"
    assert p.exists()
    with open(p, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]
    assert len(lines) == 1

    parsed = json.loads(lines[0])
    assert parsed["model"] == "claude-sonnet-4-6"
    assert parsed["run_tag"] == "phase1_test"
    assert parsed["custom_id"] == "cand_001"
    assert parsed["is_batch"] is False
    assert parsed["cache_ttl"] == "none"
    assert parsed["usage"]["input_tokens"] == 1000
    assert parsed["usage"]["output_tokens"] == 200
    assert parsed["cost_usd_total"] == entry.cost_usd_total
    assert "input" in parsed["cost_usd_breakdown"]
    assert "timestamp_iso" in parsed


def test_jsonl_roundtrip_via_from_jsonl_row(tmp_path):
    tracker = _tracker(tmp_path)
    written = tracker.log_call(
        model="claude-opus-4-7",
        usage=_usage(input_tokens=500, output_tokens=100, cache_create=200, cache_read=1000),
        run_tag="phase1_roundtrip",
        custom_id="x",
        is_batch=True,
        cache_ttl="1h",
    )
    raw = (tmp_path / "research_cost.jsonl").read_text(encoding="utf-8").strip()
    decoded = CostEntry.from_jsonl_row(raw)
    assert decoded.run_tag == written.run_tag
    assert decoded.model == written.model
    assert decoded.is_batch is True
    assert decoded.cache_ttl == "1h"
    assert decoded.usage == written.usage
    assert decoded.cost_usd_breakdown == written.cost_usd_breakdown
    assert decoded.cost_usd_total == pytest.approx(written.cost_usd_total, abs=1e-8)


def test_log_call_appends_does_not_overwrite(tmp_path):
    tracker = _tracker(tmp_path)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=100),
        run_tag="phase1_a",
    )
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=200),
        run_tag="phase1_a",
    )
    tracker.log_call(
        model="claude-haiku-4-5",
        usage=_usage(input_tokens=300),
        run_tag="phase1_b",
    )
    raw = (tmp_path / "research_cost.jsonl").read_text(encoding="utf-8")
    assert raw.count("\n") == 3
    assert raw.count("phase1_a") == 2
    assert raw.count("phase1_b") == 1


def test_log_call_creates_parent_dir(tmp_path):
    nested = tmp_path / "deeply" / "nested" / "dir" / "cost.jsonl"
    tracker = CostTracker(log_path=nested)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1),
        run_tag="phase1_dirs",
    )
    assert nested.exists()


# ---------------------------------------------------------------------------
# 5. aggregate() filters by run_tag
# ---------------------------------------------------------------------------


def test_aggregate_filters_by_run_tag(tmp_path):
    tracker = _tracker(tmp_path)
    # Two calls under "a", one under "b"
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000, output_tokens=100_000),
        run_tag="phase1_a",
    )
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=2_000_000, output_tokens=50_000),
        run_tag="phase1_a",
    )
    tracker.log_call(
        model="claude-haiku-4-5",
        usage=_usage(input_tokens=500_000, output_tokens=10_000),
        run_tag="phase1_b",
    )

    rep_a = tracker.aggregate(run_tag="phase1_a")
    rep_b = tracker.aggregate(run_tag="phase1_b")

    assert rep_a.n_calls == 2
    assert rep_a.total_input_tokens == 3_000_000
    assert rep_a.total_output_tokens == 150_000
    # input: (1M*3 + 2M*3) = $9; output: (100k*15 + 50k*15)/1M = $2.25 → total $11.25
    assert rep_a.total_usd == pytest.approx(11.25, abs=0.0001)
    assert "claude-sonnet-4-6" in rep_a.per_model
    assert rep_a.per_model["claude-sonnet-4-6"]["n_calls"] == 2

    assert rep_b.n_calls == 1
    assert rep_b.total_input_tokens == 500_000
    # 500k*1.00/1M=0.50 + 10k*5.00/1M=0.05 = 0.55
    assert rep_b.total_usd == pytest.approx(0.55, abs=0.0001)


def test_aggregate_empty_log_returns_zero_report(tmp_path):
    tracker = _tracker(tmp_path)
    rep = tracker.aggregate(run_tag="phase1_nothing")
    assert rep.n_calls == 0
    assert rep.total_usd == 0.0
    assert rep.per_model == {}
    assert rep.start_iso is None
    assert rep.end_iso is None


def test_aggregate_unknown_tag_returns_zero(tmp_path):
    tracker = _tracker(tmp_path)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1000),
        run_tag="phase1_present",
    )
    rep = tracker.aggregate(run_tag="phase1_absent")
    assert rep.n_calls == 0
    assert rep.total_usd == 0.0


# ---------------------------------------------------------------------------
# 6. aggregate() filters by `since` (and `until`)
# ---------------------------------------------------------------------------


def test_aggregate_since_filter(tmp_path, monkeypatch):
    """Write three rows with controlled timestamps; aggregate from the middle."""
    tracker = _tracker(tmp_path)

    timestamps = [
        "2026-04-26T08:00:00+00:00",
        "2026-04-26T10:00:00+00:00",
        "2026-04-26T12:00:00+00:00",
    ]
    iter_ts = iter(timestamps)

    class _FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(next(iter_ts))

    # Patch the symbol the tracker actually uses.
    import src.research_infra.cost_tracker as _ct

    monkeypatch.setattr(_ct, "datetime", _FakeDateTime)

    for _ in range(3):
        tracker.log_call(
            model="claude-sonnet-4-6",
            usage=_usage(input_tokens=1_000_000),  # $3.00 each
            run_tag="phase1_since",
        )

    # No filter — all three.
    rep_all = tracker.aggregate(run_tag="phase1_since")
    assert rep_all.n_calls == 3

    # since=09:00 → drops first row → 2 calls / $6.00.
    since = datetime(2026, 4, 26, 9, 0, 0, tzinfo=timezone.utc)
    rep_since = tracker.aggregate(run_tag="phase1_since", since=since)
    assert rep_since.n_calls == 2
    assert rep_since.total_usd == pytest.approx(6.00, abs=0.0001)

    # until=11:00 → only row at 10:00 (until is exclusive on the upper bound) → 2 if since=8 else 1.
    until = datetime(2026, 4, 26, 11, 0, 0, tzinfo=timezone.utc)
    rep_until = tracker.aggregate(run_tag="phase1_since", until=until)
    assert rep_until.n_calls == 2  # 08:00 + 10:00


def test_aggregate_since_naive_datetime_treated_as_utc(tmp_path, monkeypatch):
    """Naive datetimes in `since` must be coerced to UTC, not raise."""
    tracker = _tracker(tmp_path)

    class _FixedDt(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime(2026, 4, 26, 12, 0, 0, tzinfo=timezone.utc)

    import src.research_infra.cost_tracker as _ct

    monkeypatch.setattr(_ct, "datetime", _FixedDt)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1000),
        run_tag="phase1_naive",
    )

    naive_since = datetime(2026, 4, 26, 11, 0, 0)  # naive, before write
    rep = tracker.aggregate(run_tag="phase1_naive", since=naive_since)
    assert rep.n_calls == 1


# ---------------------------------------------------------------------------
# 7. Budget alert behaviour
# ---------------------------------------------------------------------------


def test_budget_alert_fires_when_threshold_crossed(tmp_path):
    tracker = _tracker(tmp_path)
    fired: List[CostReport] = []

    def cb(report):
        fired.append(report)

    # $5 budget. One Sonnet call with 1M input = $3 (under), then another = $6 (over).
    tracker.set_budget_alert("phase1_budget", budget_usd=5.0, callback=cb)

    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000),
        run_tag="phase1_budget",
    )
    assert fired == []

    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000),
        run_tag="phase1_budget",
    )
    assert len(fired) == 1
    assert fired[0].run_tag == "phase1_budget"
    assert fired[0].total_usd >= 5.0


def test_budget_alert_fires_only_once(tmp_path):
    tracker = _tracker(tmp_path)
    fired: List[CostReport] = []
    tracker.set_budget_alert("phase1_one", budget_usd=1.0, callback=fired.append)

    # Cross the budget on call 1, then keep going — callback must not re-fire.
    for _ in range(5):
        tracker.log_call(
            model="claude-sonnet-4-6",
            usage=_usage(input_tokens=1_000_000),
            run_tag="phase1_one",
        )
    assert len(fired) == 1


def test_budget_alert_does_not_fire_when_below(tmp_path):
    tracker = _tracker(tmp_path)
    fired: List[CostReport] = []
    tracker.set_budget_alert("phase1_low", budget_usd=100.0, callback=fired.append)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000),
        run_tag="phase1_low",
    )
    assert fired == []


def test_budget_alert_isolated_per_run_tag(tmp_path):
    """A breach on tag A must not trigger a callback registered on tag B."""
    tracker = _tracker(tmp_path)
    fired_a: List[CostReport] = []
    fired_b: List[CostReport] = []
    tracker.set_budget_alert("phase1_A", budget_usd=1.0, callback=fired_a.append)
    tracker.set_budget_alert("phase1_B", budget_usd=1.0, callback=fired_b.append)

    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000),
        run_tag="phase1_A",
    )
    assert len(fired_a) == 1
    assert fired_b == []


def test_clear_budget_alert(tmp_path):
    tracker = _tracker(tmp_path)
    fired: List[CostReport] = []
    tracker.set_budget_alert("phase1_clear", budget_usd=1.0, callback=fired.append)
    tracker.clear_budget_alert("phase1_clear")
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000),
        run_tag="phase1_clear",
    )
    assert fired == []


def test_budget_negative_or_zero_rejected(tmp_path):
    tracker = _tracker(tmp_path)
    with pytest.raises(ValueError):
        tracker.set_budget_alert("x", 0.0, lambda r: None)
    with pytest.raises(ValueError):
        tracker.set_budget_alert("x", -1.0, lambda r: None)


# ---------------------------------------------------------------------------
# 8. Concurrent log_call doesn't corrupt JSONL
# ---------------------------------------------------------------------------


def test_concurrent_log_call_jsonl_integrity(tmp_path):
    """Spawn N threads each calling log_call M times; expect exactly N*M well-formed lines."""
    tracker = _tracker(tmp_path)
    N_THREADS = 8
    M_PER_THREAD = 25

    def worker(idx):
        for k in range(M_PER_THREAD):
            tracker.log_call(
                model="claude-sonnet-4-6",
                usage=_usage(input_tokens=10, output_tokens=2),
                run_tag="phase1_concurrent",
                custom_id=f"t{idx}_n{k}",
            )

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N_THREADS)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    raw = (tmp_path / "research_cost.jsonl").read_text(encoding="utf-8")
    lines = [ln for ln in raw.split("\n") if ln.strip()]
    assert len(lines) == N_THREADS * M_PER_THREAD

    # Every line must parse as JSON and have all required keys.
    seen_ids = set()
    for ln in lines:
        d = json.loads(ln)
        assert d["run_tag"] == "phase1_concurrent"
        assert d["model"] == "claude-sonnet-4-6"
        assert "cost_usd_total" in d
        seen_ids.add(d["custom_id"])
    # All custom_ids unique → no two writers overwrote each other's data.
    assert len(seen_ids) == N_THREADS * M_PER_THREAD


# ---------------------------------------------------------------------------
# 9. Unknown model raises a clear error
# ---------------------------------------------------------------------------


def test_unknown_model_raises_unknown_model_error(tmp_path):
    tracker = _tracker(tmp_path)
    with pytest.raises(UnknownModelError) as exc_info:
        tracker.log_call(
            model="claude-fictional-9-9",
            usage=_usage(input_tokens=100),
            run_tag="phase1_x",
        )
    msg = str(exc_info.value)
    assert "claude-fictional-9-9" in msg
    assert "Known" in msg or "PRICING" in msg


def test_unknown_model_does_not_write_row(tmp_path):
    """A failed log_call must not leave a partial row on disk."""
    tracker = _tracker(tmp_path)
    with pytest.raises(UnknownModelError):
        tracker.log_call(
            model="claude-not-real",
            usage=_usage(input_tokens=100),
            run_tag="phase1_x",
        )
    # Either the file doesn't exist, or it's empty.
    p = tmp_path / "research_cost.jsonl"
    if p.exists():
        assert p.read_text(encoding="utf-8").strip() == ""


def test_unknown_model_in_compute_cost_directly():
    with pytest.raises(UnknownModelError):
        compute_cost(
            model="garbage",
            usage=_usage(input_tokens=1),
            is_batch=False,
            cache_ttl="none",
        )


# ---------------------------------------------------------------------------
# Sanity / edge cases
# ---------------------------------------------------------------------------


def test_pricing_table_has_all_required_models():
    for m in ("claude-sonnet-4-6", "claude-opus-4-7", "claude-haiku-4-5"):
        assert m in PRICING_USD_PER_MTOK
        for k in ("input", "output", "cache_write_5m", "cache_write_1h", "cache_read"):
            assert k in PRICING_USD_PER_MTOK[m], f"{m} missing {k}"


def test_per_model_breakdown_aggregates_multiple_models(tmp_path):
    tracker = _tracker(tmp_path)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1_000_000),
        run_tag="phase1_mix",
    )
    tracker.log_call(
        model="claude-opus-4-7",
        usage=_usage(input_tokens=100_000),
        run_tag="phase1_mix",
    )
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=500_000),
        run_tag="phase1_mix",
    )
    rep = tracker.aggregate("phase1_mix")
    assert rep.n_calls == 3
    assert rep.per_model["claude-sonnet-4-6"]["n_calls"] == 2
    assert rep.per_model["claude-opus-4-7"]["n_calls"] == 1
    # Sonnet: (1M + 0.5M) * 3 / 1M = $4.50
    assert rep.per_model["claude-sonnet-4-6"]["total_usd"] == pytest.approx(4.50, abs=0.0001)
    # Opus: 100k * 15 / 1M = $1.50
    assert rep.per_model["claude-opus-4-7"]["total_usd"] == pytest.approx(1.50, abs=0.0001)


def test_aggregate_records_start_and_end_iso(tmp_path, monkeypatch):
    tracker = _tracker(tmp_path)
    timestamps = [
        "2026-04-26T08:00:00+00:00",
        "2026-04-26T09:00:00+00:00",
        "2026-04-26T07:30:00+00:00",  # earlier than the first write — tests min()
    ]
    iter_ts = iter(timestamps)

    class _FakeDt(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.fromisoformat(next(iter_ts))

    import src.research_infra.cost_tracker as _ct

    monkeypatch.setattr(_ct, "datetime", _FakeDt)
    for _ in range(3):
        tracker.log_call(
            model="claude-sonnet-4-6",
            usage=_usage(input_tokens=100),
            run_tag="phase1_window",
        )
    rep = tracker.aggregate("phase1_window")
    assert rep.start_iso == "2026-04-26T07:30:00+00:00"
    assert rep.end_iso == "2026-04-26T09:00:00+00:00"


def test_malformed_jsonl_row_is_skipped_not_fatal(tmp_path):
    """Aggregation must tolerate a corrupted line and warn, not crash."""
    tracker = _tracker(tmp_path)
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1000),
        run_tag="phase1_malformed",
    )
    p = tmp_path / "research_cost.jsonl"
    with open(p, "a", encoding="utf-8") as f:
        f.write("{not valid json\n")
        f.write("\n")  # blank line
    tracker.log_call(
        model="claude-sonnet-4-6",
        usage=_usage(input_tokens=1000),
        run_tag="phase1_malformed",
    )
    rep = tracker.aggregate("phase1_malformed")
    # Both valid rows aggregated; malformed row + blank skipped.
    assert rep.n_calls == 2


def test_usage_block_with_missing_fields_treated_as_zero(tmp_path):
    """Real Anthropic SDK responses sometimes omit cache_* fields entirely."""
    tracker = _tracker(tmp_path)
    entry = tracker.log_call(
        model="claude-sonnet-4-6",
        usage={"input_tokens": 100, "output_tokens": 50},  # no cache fields at all
        run_tag="phase1_partial",
    )
    assert entry.usage["cache_read_input_tokens"] == 0
    assert entry.usage["cache_creation_input_tokens"] == 0
    assert entry.cost_usd_breakdown["cache_read"] == 0.0
    assert entry.cost_usd_breakdown["cache_write"] == 0.0
