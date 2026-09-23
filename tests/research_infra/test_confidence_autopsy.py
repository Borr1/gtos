"""Tests for ``src/research_infra/confidence_autopsy.py``.

Coverage
--------
* ``spearman``: hand-verified for 5-element series with known correlation
  (perfect monotone increasing -> +1; perfect decreasing -> -1; one-tied
  pair shifts the value modestly; constant input -> NaN).
* ``permutation_p_value``: planted-strong-correlation -> low p; planted-null
  (random shuffle) -> high p. Probabilistic; uses a fixed seed.
* ``bonferroni_correct``: 10 raw p-values -> 10 corrected; cap at 1.0;
  NaNs pass through.
* Stratification: 50 synthetic trades across 2 instruments x 2 regimes
  -> 4 strata reported.
* min_n: stratum below threshold gets INSUFFICIENT_N.
* DEGENERATE: stratum where every confidence is identical gets DEGENERATE
  (zero-variance Spearman is undefined).
* Distribution: hist + mean + mode + fraction_at_80 hand-verified.

Discipline
----------
All test data is built in-memory; no production paths touched. The
conftest write-guard would fail the session if we slipped.
"""

from __future__ import annotations

import math
import random
from typing import Any

import pytest

from src.research_infra.confidence_autopsy import (
    DEFAULT_STRATA_AXES,
    VALID_STRATA_AXES,
    AutopsyReport,
    StratumResult,
    bonferroni_correct,
    compute_confidence_distribution,
    permutation_p_value,
    spearman,
    stratify_and_test,
)


# ---------------------------------------------------------------------------
# spearman
# ---------------------------------------------------------------------------


def test_spearman_perfect_positive() -> None:
    """Strictly monotone increasing pairs => Spearman = +1."""
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert spearman(x, y) == pytest.approx(1.0, abs=1e-12)


def test_spearman_perfect_negative() -> None:
    """Strictly monotone decreasing pairs => Spearman = -1."""
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [50.0, 40.0, 30.0, 20.0, 10.0]
    assert spearman(x, y) == pytest.approx(-1.0, abs=1e-12)


def test_spearman_one_swap_5_element() -> None:
    """Swap two adjacent ranks in a 5-element series.

    Reference computation (no ties on either side after the swap):
        x = [1, 2, 3, 4, 5]
        y = [10, 20, 40, 30, 50]
    Ranks of y: [1, 2, 4, 3, 5]
    Pearson on ranks of (x, y_rank):
        mean_x = 3, mean_yr = 3
        cov = (1-3)(1-3) + (2-3)(2-3) + (3-3)(4-3) + (4-3)(3-3) + (5-3)(5-3)
            = 4 + 1 + 0 + 0 + 4 = 9
        var_x = var_yr = 4 + 1 + 0 + 1 + 4 = 10
        rho = 9 / 10 = 0.9
    """
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 20.0, 40.0, 30.0, 50.0]
    assert spearman(x, y) == pytest.approx(0.9, abs=1e-12)


def test_spearman_with_ties_in_y() -> None:
    """One pair tied on the y-side. Average ranks handle ties.

    x = [1, 2, 3, 4, 5]
    y = [10, 20, 30, 30, 50]
    Ranks of y: [1, 2, 3.5, 3.5, 5]  (the two 30s get average of ranks 3,4)
    mean_x = 3, mean_yr = 3
    cov = (1-3)(1-3) + (2-3)(2-3) + (3-3)(3.5-3) + (4-3)(3.5-3) + (5-3)(5-3)
        = 4 + 1 + 0 + 0.5 + 4 = 9.5
    var_x = 10
    var_yr = 4 + 1 + 0.25 + 0.25 + 4 = 9.5
    rho = 9.5 / sqrt(10 * 9.5) = 9.5 / sqrt(95) ≈ 0.97435
    """
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 20.0, 30.0, 30.0, 50.0]
    expected = 9.5 / math.sqrt(10.0 * 9.5)
    assert spearman(x, y) == pytest.approx(expected, abs=1e-12)


def test_spearman_constant_x_is_nan() -> None:
    """Zero variance on either side => Spearman undefined => NaN."""
    x = [80.0, 80.0, 80.0, 80.0, 80.0]
    y = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert math.isnan(spearman(x, y))


def test_spearman_constant_y_is_nan() -> None:
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [0.0, 0.0, 0.0, 0.0, 0.0]
    assert math.isnan(spearman(x, y))


def test_spearman_short_input_is_nan() -> None:
    """n < 2 cannot define correlation."""
    assert math.isnan(spearman([1.0], [2.0]))
    assert math.isnan(spearman([], []))


def test_spearman_length_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        spearman([1.0, 2.0], [1.0])


# ---------------------------------------------------------------------------
# permutation_p_value
# ---------------------------------------------------------------------------


def test_permutation_p_value_strong_correlation_low_p() -> None:
    """A planted strong positive correlation should yield low p (n=20)."""
    n = 20
    x = [float(i) for i in range(n)]
    y = [2.0 * i + 1.0 for i in range(n)]  # exact rho = +1
    p = permutation_p_value(x, y, n_perms=500, seed=1)
    # With perfect correlation no shuffle should beat |rho|=1, so p hits the
    # Phipson-Smyth floor of 1/(n_perms+1) = 1/501 ≈ 0.002.
    assert p == pytest.approx(1.0 / 501.0, abs=1e-9)


def test_permutation_p_value_random_independent_high_p() -> None:
    """Independent random series should yield p comfortably > alpha."""
    rng = random.Random(42)
    n = 50
    x = [rng.random() for _ in range(n)]
    y = [rng.random() for _ in range(n)]
    p = permutation_p_value(x, y, n_perms=500, seed=2)
    # No firm bound, but for independent uniform draws of n=50 the expected
    # |rho| is small and p should be well above 0.05 most of the time. We
    # assert > 0.05 with the fixed seed; if the seed ever produces a fluke
    # it can be re-seeded — this is the standard probabilistic-test pattern.
    assert p > 0.05, f"expected p > 0.05 for null inputs; got {p:.4f}"


def test_permutation_p_value_constant_input_is_one() -> None:
    """Degenerate inputs => null cannot be rejected => p=1.0."""
    x = [80.0] * 10
    y = [1.0, -1.0] * 5
    p = permutation_p_value(x, y, n_perms=200, seed=1)
    assert p == 1.0


def test_permutation_p_value_short_input() -> None:
    """n < 2 => p=1.0."""
    assert permutation_p_value([1.0], [2.0]) == 1.0
    assert permutation_p_value([], []) == 1.0


def test_permutation_p_value_zero_perms() -> None:
    """n_perms <= 0 => p=1.0."""
    assert permutation_p_value([1.0, 2.0, 3.0], [3.0, 2.0, 1.0], n_perms=0) == 1.0


def test_permutation_p_value_seed_determinism() -> None:
    """Same seed + inputs => identical p across calls."""
    x = [float(i) for i in range(15)]
    y = [(i * 1.7 + 0.3) for i in range(15)]
    p1 = permutation_p_value(x, y, n_perms=500, seed=7)
    p2 = permutation_p_value(x, y, n_perms=500, seed=7)
    assert p1 == p2


def test_permutation_p_value_length_mismatch() -> None:
    with pytest.raises(ValueError):
        permutation_p_value([1.0, 2.0], [1.0])


# ---------------------------------------------------------------------------
# bonferroni_correct
# ---------------------------------------------------------------------------


def test_bonferroni_10_p_values_default_family() -> None:
    raw = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]
    corrected = bonferroni_correct(raw)
    assert len(corrected) == 10
    # Each multiplied by 10, capped at 1.0.
    expected = [min(1.0, p * 10) for p in raw]
    for c, e in zip(corrected, expected):
        assert c == pytest.approx(e, abs=1e-12)


def test_bonferroni_explicit_family_size() -> None:
    """When the caller specifies a larger family, correction is harsher."""
    raw = [0.01, 0.02, 0.03]
    corrected = bonferroni_correct(raw, family_size=20)
    assert corrected == pytest.approx([0.20, 0.40, 0.60], abs=1e-12)


def test_bonferroni_caps_at_one() -> None:
    raw = [0.4, 0.7, 0.99]
    corrected = bonferroni_correct(raw, family_size=5)
    # 0.4 * 5 = 2.0 -> cap to 1.0; 0.7 * 5 = 3.5 -> 1.0; 0.99 * 5 = 4.95 -> 1.0
    assert corrected == [1.0, 1.0, 1.0]


def test_bonferroni_nan_passthrough() -> None:
    raw = [0.01, float("nan"), 0.03]
    corrected = bonferroni_correct(raw, family_size=3)
    assert corrected[0] == pytest.approx(0.03)
    assert math.isnan(corrected[1])
    assert corrected[2] == pytest.approx(0.09)


def test_bonferroni_zero_family_size_passes_through() -> None:
    """family_size=0 => no correction (avoid 0-multiplication wipe-out)."""
    raw = [0.1, 0.2, 0.3]
    corrected = bonferroni_correct(raw, family_size=0)
    assert corrected == pytest.approx([0.1, 0.2, 0.3])


def test_bonferroni_negative_family_raises() -> None:
    with pytest.raises(ValueError):
        bonferroni_correct([0.05], family_size=-1)


# ---------------------------------------------------------------------------
# stratify_and_test — synthetic 50-trade fixture
# ---------------------------------------------------------------------------


def _synthetic_trades_50(*, seed: int = 1) -> list[dict[str, Any]]:
    """50 synthetic trades across 2 instruments x 2 regimes => 4 strata.

    Trades per stratum: 12 or 13 (12+13+12+13 = 50). With min_n=10 every
    stratum is testable; with min_n=20 every stratum is INSUFFICIENT_N
    (used to test the threshold).
    """
    rng = random.Random(seed)
    instruments = ["XAUUSD", "USDJPY"]
    regimes = ["trending_bull", "range"]
    out: list[dict[str, Any]] = []
    quotas = [13, 13, 12, 12]
    cells = [(s, r) for s in instruments for r in regimes]
    for (s, r), q in zip(cells, quotas):
        for _ in range(q):
            conf = rng.choice([72.0, 75.0, 78.0, 80.0, 82.0])
            r_mult = rng.gauss(0.0, 1.2)
            out.append(
                {
                    "symbol": s,
                    "regime": r,
                    "kill_zone": "ny",
                    "framework": "ob_retest",
                    "setup_grade": "A+",
                    "direction": "LONG",
                    "hour_of_day": 13,
                    "confidence": conf,
                    "r_multiple": r_mult,
                }
            )
    assert len(out) == 50
    return out


def test_stratify_4_strata_at_min_n_10() -> None:
    """50 synthetic trades x 2 instruments x 2 regimes => 4 strata reported."""
    trades = _synthetic_trades_50()
    report = stratify_and_test(
        trades,
        strata_axes=["symbol", "regime"],
        min_n=10,
        rho_threshold=0.2,
        n_perms=200,
        seed=1,
    )
    assert len(report.all_results) == 4
    # All four should be in the family (family_size = 4).
    assert report.family_size == 4
    flags = {r.flag for r in report.all_results}
    # The synthetic data is independent random R, so we expect either
    # PREDICTIVE or NOT_PREDICTIVE — no INSUFFICIENT_N at min_n=10.
    assert "INSUFFICIENT_N" not in flags


def test_stratify_min_n_filter() -> None:
    """At min_n=20, every cell (12 or 13) is INSUFFICIENT_N."""
    trades = _synthetic_trades_50()
    report = stratify_and_test(
        trades,
        strata_axes=["symbol", "regime"],
        min_n=20,
        n_perms=100,
        seed=1,
    )
    assert all(r.flag == "INSUFFICIENT_N" for r in report.all_results)
    # Family is empty when nothing was tested.
    assert report.family_size == 0
    assert report.predictive == []


def test_stratify_predictive_finds_planted_correlation() -> None:
    """Plant a strong positive corr in one stratum; expect it to be flagged."""
    rng = random.Random(7)
    trades: list[dict[str, Any]] = []
    # Stratum A: planted positive correlation between confidence and r_multiple.
    for i in range(40):
        conf = 70.0 + i * 0.5  # 70..89.5
        r = (conf - 79.5) * 0.3  # rho will be close to +1 (rank)
        trades.append(
            {
                "symbol": "XAUUSD",
                "regime": "trending_bull",
                "confidence": conf,
                "r_multiple": r,
            }
        )
    # Stratum B: independent noise.
    for _ in range(40):
        trades.append(
            {
                "symbol": "XAUUSD",
                "regime": "range",
                "confidence": rng.choice([72.0, 75.0, 80.0, 82.0]),
                "r_multiple": rng.gauss(0.0, 1.0),
            }
        )
    report = stratify_and_test(
        trades,
        strata_axes=["symbol", "regime"],
        min_n=20,
        rho_threshold=0.2,
        alpha=0.05,
        n_perms=500,
        seed=1,
    )
    assert report.family_size == 2
    # The planted stratum should be predictive.
    predictive_keys = [
        dict(r.stratum) for r in report.predictive
    ]
    assert any(
        d.get("regime") == "trending_bull" for d in predictive_keys
    ), f"planted stratum not in predictive: {predictive_keys}"


def test_stratify_degenerate_constant_confidence() -> None:
    """A stratum where every confidence is identical => DEGENERATE."""
    trades: list[dict[str, Any]] = []
    for i in range(25):
        trades.append(
            {
                "symbol": "XAUUSD",
                "confidence": 80.0,  # constant
                "r_multiple": float(i) - 12.0,
            }
        )
    report = stratify_and_test(
        trades,
        strata_axes=["symbol"],
        min_n=20,
        n_perms=100,
        seed=1,
    )
    assert len(report.all_results) == 1
    only = report.all_results[0]
    assert only.flag == "DEGENERATE"
    # Degenerate strata are NOT counted in the family.
    assert report.family_size == 0


def test_stratify_drops_rows_missing_confidence_or_r() -> None:
    """Rows without confidence OR without r_multiple are silently dropped."""
    trades: list[dict[str, Any]] = []
    for _ in range(25):
        trades.append(
            {"symbol": "XAUUSD", "confidence": 78.0, "r_multiple": 1.0}
        )
    # Pollute with rows missing fields; should not enter the stratifier.
    trades.append({"symbol": "XAUUSD", "confidence": None, "r_multiple": 1.0})
    trades.append({"symbol": "XAUUSD", "confidence": 80.0, "r_multiple": None})
    trades.append({"symbol": "XAUUSD"})
    report = stratify_and_test(
        trades,
        strata_axes=["symbol"],
        min_n=20,
        n_perms=100,
        seed=1,
    )
    # Only 25 valid trades.
    assert report.distribution["n"] == 25


def test_stratify_axis_validation() -> None:
    """An unknown axis name raises ValueError."""
    trades = [{"symbol": "XAUUSD", "confidence": 80.0, "r_multiple": 1.0}]
    with pytest.raises(ValueError):
        stratify_and_test(
            trades,
            strata_axes=["bogus_axis"],
            min_n=1,
        )


def test_stratify_empty_axes_raises() -> None:
    trades = [{"symbol": "XAUUSD", "confidence": 80.0, "r_multiple": 1.0}]
    with pytest.raises(ValueError):
        stratify_and_test(trades, strata_axes=[], min_n=1)


def test_stratify_default_axes_used_when_none() -> None:
    """Passing ``strata_axes=None`` uses ``DEFAULT_STRATA_AXES``."""
    trades = []
    # Three strata: vary symbol, others constant.
    for sym in ("XAUUSD", "USDJPY", "GBPUSD"):
        for i in range(25):
            trades.append(
                {
                    "symbol": sym,
                    "regime": "trending_bull",
                    "kill_zone": "ny",
                    "framework": "ob_retest",
                    "setup_grade": "A+",
                    "confidence": 75.0 + (i % 5),
                    "r_multiple": (i - 12) * 0.1,
                }
            )
    report = stratify_and_test(trades, strata_axes=None, min_n=20, n_perms=100)
    assert report.strata_axes == list(DEFAULT_STRATA_AXES)
    # 3 strata (one per symbol; everything else is constant across rows).
    assert len(report.all_results) == 3


# ---------------------------------------------------------------------------
# Distribution
# ---------------------------------------------------------------------------


def test_compute_distribution_empty() -> None:
    d = compute_confidence_distribution([])
    assert d["n"] == 0
    assert d["mean"] is None
    assert d["mode"] is None
    assert d["fraction_at_80"] is None
    assert d["histogram"] == {}


def test_compute_distribution_dominated_by_80() -> None:
    """98 trades at 80 + 2 trades at 75 -> fraction_at_80 = 0.98 (CLAUDE.md scenario)."""
    trades: list[dict[str, Any]] = []
    for _ in range(98):
        trades.append({"confidence": 80.0, "r_multiple": 0.0})
    for _ in range(2):
        trades.append({"confidence": 75.0, "r_multiple": 0.0})
    d = compute_confidence_distribution(trades)
    assert d["n"] == 100
    assert d["mode"] == 80
    assert d["fraction_at_80"] == pytest.approx(0.98)
    assert d["mode_fraction"] == pytest.approx(0.98)
    assert d["mean"] == pytest.approx(0.98 * 80.0 + 0.02 * 75.0)


def test_compute_distribution_rounds_floats_to_int() -> None:
    """Confidence values like 79.6 round to 80 for histogram bucketing."""
    trades = [
        {"confidence": 79.6, "r_multiple": 0.0},
        {"confidence": 80.4, "r_multiple": 0.0},
        {"confidence": 75.0, "r_multiple": 0.0},
    ]
    d = compute_confidence_distribution(trades)
    assert d["histogram"] == {75: 1, 80: 2}
    assert d["fraction_at_80"] == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# Report serialization
# ---------------------------------------------------------------------------


def test_report_to_dict_round_trip() -> None:
    """to_dict() should be JSON-serializable (no exceptions)."""
    import json

    trades = _synthetic_trades_50()
    report = stratify_and_test(
        trades,
        strata_axes=["symbol"],
        min_n=20,
        n_perms=100,
    )
    d = report.to_dict()
    s = json.dumps(d)  # raises if non-serializable
    parsed = json.loads(s)
    assert parsed["family_size"] == report.family_size
    assert parsed["min_n"] == 20
    assert "distribution" in parsed
    assert "all_results" in parsed
    assert "predictive" in parsed


def test_valid_strata_axes_constants_exposed() -> None:
    """Public surface keeps the axes set + default axes addressable."""
    assert "symbol" in VALID_STRATA_AXES
    assert "hour_of_day" in VALID_STRATA_AXES
    assert "bogus" not in VALID_STRATA_AXES
    # Every default axis is in the valid set.
    for a in DEFAULT_STRATA_AXES:
        assert a in VALID_STRATA_AXES
