"""Tests for ``src/research_infra/bonferroni_survival.py``.

Methodology:
  - ``binomial_test``: hand-verified canonical case (k=8, n=10, p=0.5),
    plus edge cases (n=0, p=0, p=1, k=0, k=n, observed equal to expected).
  - ``two_sample_wr_test``: hand-verified against a textbook example.
  - ``bonferroni_correct``: 5 raw p-values → 5 corrected with cap at 1.0;
    NaN propagation; empty list.
  - ``evaluate_survival``: synthetic SURVIVES + synthetic FAILS scenarios
    end-to-end, plus INSUFFICIENT_N + NO_DATA.

All tests are pure-Python — no fixtures touch production paths.
"""

from __future__ import annotations

import math

import pytest

from src.research_infra.bonferroni_survival import (
    FAMILY_SIZE,
    SurvivalReport,
    TEST_REGISTRY,
    TestResult,
    TestSpec,
    binomial_test,
    bonferroni_correct,
    evaluate_survival,
    two_sample_wr_test,
)

# Tell pytest not to attempt to collect TestSpec / TestResult as test classes
# (they are dataclasses sharing the Test* prefix).
TestSpec.__test__ = False  # type: ignore[attr-defined]
TestResult.__test__ = False  # type: ignore[attr-defined]


# ────────────────────────────────────────────────────────────────────────────
# binomial_test — hand-verified
# ────────────────────────────────────────────────────────────────────────────

def test_binomial_test_8_of_10_at_half():
    """Canonical hand-verified case.

    Under Binomial(n=10, p=0.5), the PMF at k=8 equals C(10,8)*0.5^10
    = 45/1024 = 0.0439453125. Two-sided exact = sum of all PMFs <= 0.0439...,
    which by symmetry equals 2 * (P(K=8) + P(K=9) + P(K=10))
    = 2 * (45 + 10 + 1) / 1024 = 112 / 1024 = 0.109375.
    """
    p = binomial_test(8, 10, 0.5)
    assert math.isclose(p, 0.109375, rel_tol=1e-9, abs_tol=1e-12)


def test_binomial_test_at_expected_value_returns_one():
    """Observed == expected → no extreme outcome → p = 1.0."""
    # Binomial(n=10, p=0.5): expected wins = 5; PMF(5) = 252/1024 is largest.
    # Sum of all PMFs == 1.0 since every k satisfies pmf(k) <= pmf(5).
    p = binomial_test(5, 10, 0.5)
    assert math.isclose(p, 1.0, rel_tol=1e-9, abs_tol=1e-12)


def test_binomial_test_extremes():
    """k=0 / k=n at p=0.5 → p = 2/1024 = 1/512."""
    p_zero = binomial_test(0, 10, 0.5)
    p_all = binomial_test(10, 10, 0.5)
    expected = 2.0 / 1024.0
    assert math.isclose(p_zero, expected, rel_tol=1e-9, abs_tol=1e-12)
    assert math.isclose(p_all, expected, rel_tol=1e-9, abs_tol=1e-12)


def test_binomial_test_n_zero_returns_nan():
    p = binomial_test(0, 0, 0.5)
    assert math.isnan(p)


def test_binomial_test_validates_inputs():
    with pytest.raises(ValueError):
        binomial_test(-1, 10, 0.5)
    with pytest.raises(ValueError):
        binomial_test(11, 10, 0.5)
    with pytest.raises(ValueError):
        binomial_test(5, 10, 1.5)


def test_binomial_test_xau_full_pop_recovers_corrected_p():
    """Sanity-check the XAU full-batch 65%-WR / n=367 baseline.

    CLAUDE.md "Canonical numbers" lists "Batch population 367 trades,
    Full-pop WR 65%". Two-sided exact binomial of 239/367 (65%) at
    p_null=0.5 lands ~7.2e-09; corrected at family size 5 ≈ 3.6e-08,
    matching the headline 3.42e-08 within rounding. The smaller 80/129
    sub-population (XAUUSD-only batch) produces raw p ≈ 0.008 — a
    different baseline computation underpins the published number.
    The K52 re-test honestly reports both via the live-data WR/n
    inputs; the legend reflects exactly what we put on disk.
    """
    p = binomial_test(239, 367, 0.5)
    # Should be ~ 1e-9 .. 1e-8 territory — strict reject of breakeven.
    assert 0.0 < p < 1e-7


# ────────────────────────────────────────────────────────────────────────────
# two_sample_wr_test — hand-verified
# ────────────────────────────────────────────────────────────────────────────

def test_two_sample_wr_identical_proportions_returns_one():
    p = two_sample_wr_test(50, 100, 50, 100)
    assert math.isclose(p, 1.0, rel_tol=1e-9, abs_tol=1e-12)


def test_two_sample_wr_textbook_example():
    """Hand-verified via pooled-z formula.

    Inputs: 70/100 vs 50/100 → p_a=0.7, p_b=0.5, p_pool=0.6.
    var = 0.6 * 0.4 * (1/100 + 1/100) = 0.24 * 0.02 = 0.0048
    z = (0.7 - 0.5) / sqrt(0.0048) ≈ 0.2 / 0.069282 ≈ 2.88675
    Two-sided p ≈ 2 * (1 - Phi(2.88675)) ≈ 0.003892
    """
    p = two_sample_wr_test(70, 100, 50, 100)
    assert math.isclose(p, 0.003892, rel_tol=5e-3, abs_tol=1e-5)


def test_two_sample_wr_zero_n_returns_nan():
    assert math.isnan(two_sample_wr_test(0, 0, 5, 10))
    assert math.isnan(two_sample_wr_test(5, 10, 0, 0))


def test_two_sample_wr_no_variance_returns_one():
    """All wins in both groups → p_pool=1, var=0 → 1.0 (cannot reject)."""
    p = two_sample_wr_test(10, 10, 5, 5)
    assert math.isclose(p, 1.0, rel_tol=1e-9, abs_tol=1e-12)


def test_two_sample_wr_validates_inputs():
    with pytest.raises(ValueError):
        two_sample_wr_test(-1, 10, 5, 10)
    with pytest.raises(ValueError):
        two_sample_wr_test(11, 10, 5, 10)


def test_two_sample_wr_ob_baseline_recovers_signal():
    """Test A rerun: 122/173 vs 73/136 ≈ 70.5% vs 53.7%, p≈0.003.

    From .context/03_analysis/test_a_rerun_real_bos_results.md.
    """
    p = two_sample_wr_test(122, 173, 73, 136)
    # Should be on the order of 1e-3 .. 1e-2 (published Fisher p was 0.0029)
    assert 1e-4 < p < 5e-2


# ────────────────────────────────────────────────────────────────────────────
# bonferroni_correct — 5 raw → 5 corrected with cap
# ────────────────────────────────────────────────────────────────────────────

def test_bonferroni_correct_five_pvalues_with_cap():
    raws = [0.001, 0.01, 0.05, 0.5, 0.7]
    out = bonferroni_correct(raws)
    assert len(out) == 5
    # 0.001 * 5 = 0.005, 0.01 * 5 = 0.05, 0.05 * 5 = 0.25,
    # 0.5 * 5 = 2.5 → capped 1.0, 0.7 * 5 = 3.5 → capped 1.0
    assert math.isclose(out[0], 0.005, rel_tol=1e-12)
    assert math.isclose(out[1], 0.05, rel_tol=1e-12)
    assert math.isclose(out[2], 0.25, rel_tol=1e-12)
    assert out[3] == 1.0
    assert out[4] == 1.0


def test_bonferroni_correct_empty_returns_empty():
    assert bonferroni_correct([]) == []


def test_bonferroni_correct_propagates_nan():
    out = bonferroni_correct([float("nan"), 0.05, float("nan")])
    assert math.isnan(out[0])
    assert math.isclose(out[1], 0.15, rel_tol=1e-12)  # 0.05 * 3
    assert math.isnan(out[2])


def test_bonferroni_correct_caps_at_one():
    """Even raw p of 1.0 stays at 1.0; raw p > 1/N still caps at 1.0."""
    out = bonferroni_correct([1.0, 0.5, 0.5, 0.5, 0.5])
    for p in out:
        assert 0.0 <= p <= 1.0
    assert out[0] == 1.0


def test_bonferroni_correct_zero_unchanged():
    out = bonferroni_correct([0.0, 0.0])
    assert out == [0.0, 0.0]


# ────────────────────────────────────────────────────────────────────────────
# evaluate_survival — end-to-end
# ────────────────────────────────────────────────────────────────────────────

def _build_synthetic_data(
    *,
    # Synthetic SURVIVES baseline: WRs strong enough to clear Bonferroni at
    # family size 5 with realistic n. Tuned so each one-sample test corrected
    # p < 0.05 and the two-sample tests have explicit signal.
    xau_wins: int = 200,
    xau_n: int = 300,        # 66.7% — corrected p ≈ 1e-8 at n=300
    us30_wins: int = 60,
    us30_n: int = 90,        # 66.7% × 5 still survives
    usdjpy_wins: int = 50,
    usdjpy_n: int = 75,      # 66.7%
    ob_wins: int = 122,
    ob_n: int = 173,
    base_wins: int = 73,
    base_n: int = 136,
    fvg_blocks: dict | None = None,
) -> dict:
    """Build a complete synthetic data dict matching the registry's expected layout."""
    if fvg_blocks is None:
        # 6 instruments all with positive FVG-in-impulse delta (matches
        # the original 6/6 sign-test claim).
        fvg_blocks = {
            "XAUUSD": {"fvg_wins": 60, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "US30": {"fvg_wins": 65, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "USDJPY": {"fvg_wins": 70, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "GBPJPY": {"fvg_wins": 60, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "GBPUSD": {"fvg_wins": 58, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "XAGUSD": {"fvg_wins": 62, "fvg_n": 100, "non_wins": 50, "non_n": 100},
        }
    return {
        "xau_ob_retest": {"wins": xau_wins, "n": xau_n},
        "us30_ob_retest": {"wins": us30_wins, "n": us30_n},
        "usdjpy_ob_retest": {"wins": usdjpy_wins, "n": usdjpy_n},
        "ob_zone_vs_baseline_80pct": {
            "ob_wins": ob_wins, "ob_n": ob_n,
            "base_wins": base_wins, "base_n": base_n,
        },
        "fvg_in_impulse_per_instrument": fvg_blocks,
    }


def test_evaluate_survival_synthetic_survives_scenario():
    """All 5 baseline wins/n echoed → all 5 survive."""
    data = _build_synthetic_data()
    report = evaluate_survival(TEST_REGISTRY, data)
    assert isinstance(report, SurvivalReport)
    assert report.family_size == 5
    # All 5 specs should produce a SURVIVES verdict
    statuses = {r.spec_key: r.status for r in report.results}
    assert statuses["xau_wr_vs_be"] == "SURVIVES"
    assert statuses["us30_wr_vs_be"] == "SURVIVES"
    assert statuses["usdjpy_wr_vs_be"] == "SURVIVES"
    assert statuses["ob_zone_advantage"] == "SURVIVES"
    assert statuses["fvg_in_impulse"] == "SURVIVES"
    assert len(report.surviving) == 5
    assert len(report.failed) == 0
    assert len(report.insufficient) == 0


def test_evaluate_survival_synthetic_fails_scenario():
    """Drive WRs back to ~50% and FVG delta to ~0 → all five fail."""
    data = _build_synthetic_data(
        xau_wins=65, xau_n=129,        # ~50.4%
        us30_wins=21, us30_n=41,       # ~51.2%
        usdjpy_wins=17, usdjpy_n=33,   # ~51.5%
        ob_wins=87, ob_n=173,          # 50.3%
        base_wins=68, base_n=136,      # 50.0%
        fvg_blocks={
            # Each instrument has near-zero delta
            "A": {"fvg_wins": 51, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "B": {"fvg_wins": 50, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "C": {"fvg_wins": 49, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "D": {"fvg_wins": 51, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "E": {"fvg_wins": 50, "fvg_n": 100, "non_wins": 50, "non_n": 100},
            "F": {"fvg_wins": 49, "fvg_n": 100, "non_wins": 50, "non_n": 100},
        },
    )
    report = evaluate_survival(TEST_REGISTRY, data)
    statuses = {r.spec_key: r.status for r in report.results}
    # All five are well above the n_min floor here, so all should resolve
    # to FAILS rather than INSUFFICIENT_N.
    assert statuses["xau_wr_vs_be"] == "FAILS"
    assert statuses["us30_wr_vs_be"] == "FAILS"
    assert statuses["usdjpy_wr_vs_be"] == "FAILS"
    assert statuses["ob_zone_advantage"] == "FAILS"
    assert statuses["fvg_in_impulse"] == "FAILS"
    assert len(report.surviving) == 0
    assert len(report.failed) == 5


def test_evaluate_survival_insufficient_n_below_floor():
    """If a single test has n < n_min, mark it INSUFFICIENT_N — not FAILS."""
    data = _build_synthetic_data(us30_wins=10, us30_n=15)  # n=15 < n_min=20
    report = evaluate_survival(TEST_REGISTRY, data)
    statuses = {r.spec_key: r.status for r in report.results}
    assert statuses["us30_wr_vs_be"] == "INSUFFICIENT_N"
    # Other 4 still survive on the synthetic baseline numbers
    assert statuses["xau_wr_vs_be"] == "SURVIVES"


def test_evaluate_survival_no_data():
    """Missing block → NO_DATA, not crash."""
    data = _build_synthetic_data()
    # Remove the USDJPY block entirely
    del data["usdjpy_ob_retest"]
    report = evaluate_survival(TEST_REGISTRY, data)
    statuses = {r.spec_key: r.status for r in report.results}
    assert statuses["usdjpy_wr_vs_be"] == "NO_DATA"
    # The other four are unaffected
    assert statuses["xau_wr_vs_be"] == "SURVIVES"


def test_evaluate_survival_family_size_is_five():
    """Bonferroni divisor stays 5 even when only 1 test is runnable."""
    data = {"xau_ob_retest": {"wins": 80, "n": 129}}  # only 1 of 5 specs runnable
    report = evaluate_survival(TEST_REGISTRY, data)
    assert report.family_size == 5
    # The runnable test's corrected p must be raw_p × 5
    xau_result = next(r for r in report.results if r.spec_key == "xau_wr_vs_be")
    if math.isfinite(xau_result.current_raw_p):
        assert math.isclose(
            xau_result.current_corrected_p,
            min(1.0, xau_result.current_raw_p * 5),
            rel_tol=1e-12,
        )
    # All other tests are NO_DATA, not surviving.
    other_keys = [r.spec_key for r in report.results if r.spec_key != "xau_wr_vs_be"]
    for k in other_keys:
        result = next(r for r in report.results if r.spec_key == k)
        assert result.status == "NO_DATA"


def test_evaluate_survival_overrides_family_size():
    """Caller can override family_size for sensitivity analysis."""
    data = _build_synthetic_data()
    report = evaluate_survival(TEST_REGISTRY, data, family_size=10)
    assert report.family_size == 10
    # corrected_p must be 10 × raw_p (capped at 1.0) for runnable tests
    for r in report.results:
        if math.isfinite(r.current_raw_p):
            assert math.isclose(
                r.current_corrected_p,
                min(1.0, r.current_raw_p * 10),
                rel_tol=1e-12,
            )


def test_test_registry_has_five_entries():
    """Pre-registered family size is hard-coded at 5."""
    assert FAMILY_SIZE == 5
    assert len(TEST_REGISTRY) == 5
    keys = {s.key for s in TEST_REGISTRY}
    assert keys == {
        "xau_wr_vs_be",
        "ob_zone_advantage",
        "us30_wr_vs_be",
        "usdjpy_wr_vs_be",
        "fvg_in_impulse",
    }


def test_evaluate_survival_filled_trades_input():
    """Populator accepts ``filled_trades=[{"r": ...}, ...]`` form too."""
    data = _build_synthetic_data()
    # Replace XAU pre-aggregated wins/n with raw filled-trades list at
    # ~67% WR n=300 (a strong-survives shape consistent with the rest
    # of the synthetic builder).
    data["xau_ob_retest"] = {
        "filled_trades": [{"r": 1.5}] * 200 + [{"r": -1.0}] * 100
    }
    report = evaluate_survival(TEST_REGISTRY, data)
    xau = next(r for r in report.results if r.spec_key == "xau_wr_vs_be")
    assert xau.current_n == 300
    assert xau.current_summary["wins"] == 200
    assert xau.status == "SURVIVES"


def test_evaluate_survival_summary_carries_per_instrument_signtest():
    """FVG result includes per-instrument deltas + 6/6 sign-test result."""
    data = _build_synthetic_data()
    report = evaluate_survival(TEST_REGISTRY, data)
    fvg = next(r for r in report.results if r.spec_key == "fvg_in_impulse")
    assert "per_instrument" in fvg.current_summary
    assert fvg.current_summary["sign_test_n_total"] == 6
    # Synthetic data has all 6 positive
    assert fvg.current_summary["sign_test_n_positive"] == 6
