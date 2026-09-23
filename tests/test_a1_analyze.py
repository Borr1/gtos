"""Unit tests for research/a1_adr005_backtest/analyze.py.

Validates:
1. Wilson CI math matches known reference values.
2. Two-proportion p-value sanity checks (equal props ≈ 1, distant props < 0.01).
3. Aggregator correctly buckets rows by touch / fvg / direction.
4. `decide_touch` + `decide_fvg` respect the pre-registered criteria
   (n>=30 per arm, ratio thresholds, Bonferroni factors).

These tests pin the ANALYSIS logic; the discrimination criteria are NOT
tested here — they are pinned by PREREGISTRATION.md + the script hash
logged in ANALYSIS.md.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "research" / "a1_adr005_backtest" / "analyze.py"
spec = importlib.util.spec_from_file_location("a1_analyze", SPEC_PATH)
a1 = importlib.util.module_from_spec(spec)
sys.modules["a1_analyze"] = a1
spec.loader.exec_module(a1)


# ── Wilson CI ───────────────────────────────────────────────────────────────

def test_wilson_ci_zero_sample():
    assert a1.wilson_ci(0, 0) == (0.0, 0.0)


def test_wilson_ci_simple_case():
    """19/60 success (Track A touch=0 example): 31.7% [21.3, 44.2]."""
    lo, hi = a1.wilson_ci(19, 60)
    # Track A reported 21.3% lower, 44.2% upper.
    assert abs(lo * 100 - 21.3) < 1.5, f"lower off: {lo*100:.2f}"
    assert abs(hi * 100 - 44.2) < 1.5, f"upper off: {hi*100:.2f}"


def test_wilson_ci_100_percent_upper_bound():
    """10/10 success — upper bound must be ≤ 1.0."""
    _, hi = a1.wilson_ci(10, 10)
    assert hi <= 1.0


def test_wilson_ci_0_percent_lower_bound():
    _, hi = a1.wilson_ci(0, 10)
    lo, _ = a1.wilson_ci(0, 10)
    assert lo >= 0.0


# ── Two-proportion p-value ──────────────────────────────────────────────────

def test_two_prop_equal_rates_high_p():
    """Same proportion should give very high p (cannot reject equality)."""
    p = a1.two_prop_pvalue(50, 100, 50, 100)
    assert p > 0.9


def test_two_prop_distant_rates_tiny_p():
    """10/100 vs 90/100 — should be highly significant."""
    p = a1.two_prop_pvalue(10, 100, 90, 100)
    assert p < 1e-10


def test_two_prop_zero_n_returns_one():
    assert a1.two_prop_pvalue(0, 0, 5, 10) == 1.0
    assert a1.two_prop_pvalue(5, 10, 0, 0) == 1.0


def test_two_prop_pooled_is_one_returns_one():
    """Pooled p = 1.0 (both 100%) → can't reject equality; pooled=0 same."""
    # Both 100% → pooled = 1.0 → SE = 0 → can't compute z → return 1.0
    assert a1.two_prop_pvalue(10, 10, 5, 5) == 1.0
    # Both 0% → pooled = 0 → same fallback
    assert a1.two_prop_pvalue(0, 10, 0, 5) == 1.0


# ── Stratification buckets ──────────────────────────────────────────────────

def test_touch_stratum_buckets():
    assert a1.touch_stratum(-1) == "missing"
    assert a1.touch_stratum(0) == "0"
    assert a1.touch_stratum(1) == "1"
    assert a1.touch_stratum(2) == "2"
    assert a1.touch_stratum(3) == ">=3"
    assert a1.touch_stratum(10) == ">=3"
    assert a1.touch_stratum(None) == "missing"


def test_fvg_stratum_buckets():
    assert a1.fvg_stratum(0) == "0"
    assert a1.fvg_stratum(1) == "1-2"
    assert a1.fvg_stratum(2) == "1-2"
    assert a1.fvg_stratum(3) == ">=3"
    assert a1.fvg_stratum(None) == "missing"


# ── Aggregation ─────────────────────────────────────────────────────────────

def _mkrow(decision="CANDIDATE", touch=0, h1_fvg=0, m15_fvg=0, direction="LONG"):
    return {
        "ai_decision": decision,
        "h1_opp_ob_touch": touch,
        "h1_fvg_unfilled_count": h1_fvg,
        "m15_fvg_unfilled_count": m15_fvg,
        "ai_direction_evaluated": direction,
        "pre_ai_gate_skipped": False,
    }


def test_aggregate_counts_per_touch():
    rows = [
        _mkrow(decision="CANDIDATE", touch=0),
        _mkrow(decision="NO_TRADE", touch=0),
        _mkrow(decision="CANDIDATE", touch=2),
        _mkrow(decision="NO_TRADE", touch=2),
        _mkrow(decision="NO_TRADE", touch=2),
    ]
    agg = a1.aggregate(rows)
    assert agg["by_touch"]["0"]["cand"] == 1
    assert agg["by_touch"]["0"]["total"] == 2
    assert agg["by_touch"]["2"]["cand"] == 1
    assert agg["by_touch"]["2"]["total"] == 3


def test_aggregate_excludes_pre_ai_gate_skipped():
    rows = [
        _mkrow(decision="CANDIDATE", touch=0),
        {
            "ai_decision": None, "pre_ai_gate_skipped": True,
            "h1_opp_ob_touch": 0, "h1_fvg_unfilled_count": 0,
            "m15_fvg_unfilled_count": 0, "ai_direction_evaluated": "LONG",
        },
    ]
    agg = a1.aggregate(rows)
    assert agg["n_total_rows"] == 2
    assert agg["n_ai_rows"] == 1


def test_aggregate_fvg_total_sums_h1_and_m15():
    rows = [
        _mkrow(decision="CANDIDATE", h1_fvg=2, m15_fvg=2),  # total=4 → '>=3'
        _mkrow(decision="NO_TRADE", h1_fvg=0, m15_fvg=1),   # total=1 → '1-2'
    ]
    agg = a1.aggregate(rows)
    assert agg["by_fvg"][">=3"]["cand"] == 1
    assert agg["by_fvg"][">=3"]["total"] == 1
    assert agg["by_fvg"]["1-2"]["cand"] == 0
    assert agg["by_fvg"]["1-2"]["total"] == 1


# ── Discrimination verdict ──────────────────────────────────────────────────

def test_decide_touch_fails_below_min_n():
    by_touch = {"0": {"cand": 10, "total": 20}, "2": {"cand": 1, "total": 20},
                ">=3": {"cand": 0, "total": 10}}
    v = a1.decide_touch(by_touch)
    assert v["criteria"]["n_touch0_ge_30"] is False
    assert v["discriminates"] is False


def test_decide_touch_passes_when_all_criteria_met():
    # touch=0: 30/60 = 50%; touch>=2: 10/100 = 10%. Ratio = 5x; p < 1e-6.
    by_touch = {"0": {"cand": 30, "total": 60},
                "2": {"cand": 5, "total": 50},
                ">=3": {"cand": 5, "total": 50}}
    v = a1.decide_touch(by_touch)
    assert v["ratio"] >= 1.5
    assert v["bonf_p"] < 0.05
    assert v["t0_n"] >= 30
    assert v["t2plus_n"] >= 30
    assert v["discriminates"] is True


def test_decide_touch_fails_on_ratio_with_significant_p():
    """High-n same rates → p ≈ 1, fails ratio criterion even if n plenty."""
    by_touch = {"0": {"cand": 15, "total": 100},   # 15%
                "2": {"cand": 14, "total": 100},   # 14%
                ">=3": {"cand": 14, "total": 100}}  # 14%
    v = a1.decide_touch(by_touch)
    assert v["ratio"] < 1.5  # 15/14 ≈ 1.07
    assert v["discriminates"] is False


def test_decide_fvg_passes_when_all_criteria_met():
    by_fvg = {"0": {"cand": 5, "total": 50},         # 10%
              "1-2": {"cand": 10, "total": 50},       # 20%
              ">=3": {"cand": 30, "total": 100}}     # 30%
    v = a1.decide_fvg(by_fvg)
    assert v["ratio"] >= 1.3
    assert v["discriminates"] is True


def test_decide_fvg_fails_when_ratio_low():
    by_fvg = {"0": {"cand": 20, "total": 100},       # 20%
              ">=3": {"cand": 22, "total": 100}}     # 22% → ratio 1.1
    v = a1.decide_fvg(by_fvg)
    assert v["ratio"] < 1.3
    assert v["discriminates"] is False
