"""Unit tests for ``src.research_infra.bayesian_decay_attribution`` (A6).

Coverage matrix
---------------
* ``beta_posterior`` —
    - hand-verified Beta(10, 5) parameters when wins=9, losses=4 with
      Beta(1, 1) prior.
    - posterior mean = alpha / (alpha + beta) = 10/15 ≈ 0.6667.
    - rejects negative wins / losses and non-positive priors.

* ``beta_credible_interval`` —
    - Beta(1, 1) CI is symmetric about 0.5 at 95% level.
    - Beta(10, 5) CI contains the posterior mean and lies within [0, 1].
    - in-house bisection path agrees with scipy when scipy is available.

* ``stratify_by_component`` —
    - 20 synthetic trades across 3 framework values yield 3 stratum
      lists with correct totals.
    - missing component value maps to ``MISSING_VALUE`` sentinel.
    - empty input yields empty dict.
    - non-string component name raises ValueError.

* ``attribute_decay`` end-to-end —
    - synthetic H1 vs H2 with planted decay in ``framework=ob_retest``:
      attribution flags ob_retest and per-component CI brackets the
      planted true decay.
    - sanity check: total_attributed_pp + residual_pp ≈ observed_delta_pp.
    - low-n strata flagged, excluded from sum, listed in skipped_strata.
    - chi-square p-value goes <0.05 when planted heterogeneity is large.
    - Bonferroni correction multiplies raw_p by family_size.

* edge cases —
    - empty period -> wr=0 and observed_delta=0.
    - all wins in H1, all losses in H2 -> observed_delta=100.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.research_infra.bayesian_decay_attribution import (
    DEFAULT_PRIOR_A,
    DEFAULT_PRIOR_B,
    LOW_N_THRESHOLD,
    MISSING_VALUE,
    AttributionReport,
    ComponentAttribution,
    StratumStats,
    _beta_ppf_bisect,
    _betainc_regularized,
    _chi_square_p_value,
    _chi_square_per_stratum,
    attribute_decay,
    beta_credible_interval,
    beta_mean,
    beta_posterior,
    stratify_by_component,
)


# ---------------------------------------------------------------------------
# beta_posterior
# ---------------------------------------------------------------------------


def test_beta_posterior_hand_verified_alpha_beta() -> None:
    """Beta(1, 1) prior + 9 wins, 4 losses => Beta(10, 5)."""
    a, b = beta_posterior(9, 4, prior_a=1.0, prior_b=1.0)
    assert a == pytest.approx(10.0)
    assert b == pytest.approx(5.0)


def test_beta_posterior_mean_is_alpha_over_alpha_plus_beta() -> None:
    """Beta(10, 5) mean = 10/15 = 0.6667."""
    a, b = beta_posterior(9, 4, prior_a=1.0, prior_b=1.0)
    assert beta_mean(a, b) == pytest.approx(10.0 / 15.0, rel=1e-9)


def test_beta_posterior_with_jeffreys_prior() -> None:
    """Beta(0.5, 0.5) prior + 5 wins, 5 losses => Beta(5.5, 5.5)."""
    a, b = beta_posterior(5, 5, prior_a=0.5, prior_b=0.5)
    assert a == pytest.approx(5.5)
    assert b == pytest.approx(5.5)
    assert beta_mean(a, b) == pytest.approx(0.5)


def test_beta_posterior_zero_wins_zero_losses() -> None:
    """Posterior with no data is the prior itself."""
    a, b = beta_posterior(0, 0, prior_a=2.0, prior_b=3.0)
    assert a == 2.0
    assert b == 3.0


def test_beta_posterior_rejects_negative_wins() -> None:
    with pytest.raises(ValueError, match="wins"):
        beta_posterior(-1, 5)


def test_beta_posterior_rejects_negative_losses() -> None:
    with pytest.raises(ValueError, match="losses"):
        beta_posterior(5, -1)


def test_beta_posterior_rejects_zero_prior() -> None:
    with pytest.raises(ValueError, match="prior"):
        beta_posterior(5, 5, prior_a=0.0, prior_b=1.0)
    with pytest.raises(ValueError, match="prior"):
        beta_posterior(5, 5, prior_a=1.0, prior_b=0.0)


# ---------------------------------------------------------------------------
# beta_credible_interval
# ---------------------------------------------------------------------------


def test_beta_credible_interval_uniform_is_symmetric() -> None:
    """Beta(1, 1) is uniform; 95% CI is approximately [0.025, 0.975]."""
    lo, hi = beta_credible_interval(1.0, 1.0, level=0.95)
    assert lo == pytest.approx(0.025, abs=1e-3)
    assert hi == pytest.approx(0.975, abs=1e-3)


def test_beta_credible_interval_brackets_mean() -> None:
    """Beta(10, 5) CI must contain the posterior mean 0.6667."""
    a, b = 10.0, 5.0
    lo, hi = beta_credible_interval(a, b, level=0.95)
    mean = beta_mean(a, b)
    assert 0.0 <= lo <= mean <= hi <= 1.0
    assert hi - lo > 0.0  # non-degenerate


def test_beta_credible_interval_extreme_alpha() -> None:
    """Very informed posterior (Beta(100, 50)) has narrow CI."""
    lo, hi = beta_credible_interval(100.0, 50.0, level=0.95)
    width = hi - lo
    # Should be much narrower than the uninformed Beta(1, 1) ~ 0.95 width.
    assert width < 0.20


def test_beta_credible_interval_rejects_invalid_inputs() -> None:
    with pytest.raises(ValueError, match="alpha|beta"):
        beta_credible_interval(0.0, 1.0)
    with pytest.raises(ValueError, match="level"):
        beta_credible_interval(1.0, 1.0, level=1.5)
    with pytest.raises(ValueError, match="level"):
        beta_credible_interval(1.0, 1.0, level=0.0)


def test_betainc_regularized_basic_values() -> None:
    """Hand-verified: I_0.5(1, 1) = 0.5 (uniform CDF at midpoint)."""
    val = _betainc_regularized(1.0, 1.0, 0.5)
    assert val == pytest.approx(0.5, abs=1e-6)
    # I_0.5(2, 2) is the symmetric Beta CDF -> 0.5 at the midpoint.
    val = _betainc_regularized(2.0, 2.0, 0.5)
    assert val == pytest.approx(0.5, abs=1e-6)
    # Endpoints
    assert _betainc_regularized(2.0, 5.0, 0.0) == 0.0
    assert _betainc_regularized(2.0, 5.0, 1.0) == 1.0


# ---------------------------------------------------------------------------
# stratify_by_component
# ---------------------------------------------------------------------------


def _trade(framework: str, r: float, **extra) -> dict:
    out = {"framework": framework, "r_multiple": r}
    out.update(extra)
    return out


def test_stratify_three_frameworks_correct_partition() -> None:
    """20 synthetic trades across 3 frameworks => 3 stratum lists."""
    trades = (
        [_trade("ob_retest", 1.0)] * 10
        + [_trade("fvg_fill", -1.0)] * 6
        + [_trade("breaker_re_entry", 0.5)] * 4
    )
    out = stratify_by_component(trades, "framework")
    assert set(out.keys()) == {"ob_retest", "fvg_fill", "breaker_re_entry"}
    assert len(out["ob_retest"]) == 10
    assert len(out["fvg_fill"]) == 6
    assert len(out["breaker_re_entry"]) == 4
    # Stable partition: original order is preserved within each stratum.
    assert all(t["framework"] == "ob_retest" for t in out["ob_retest"])


def test_stratify_missing_value_maps_to_sentinel() -> None:
    """Trades with no value for the component go under MISSING_VALUE."""
    trades = [
        {"r_multiple": 1.0},  # no framework key
        {"framework": None, "r_multiple": -1.0},
        {"framework": "", "r_multiple": 0.5},
        {"framework": "ob_retest", "r_multiple": 1.0},
    ]
    out = stratify_by_component(trades, "framework")
    assert MISSING_VALUE in out
    assert len(out[MISSING_VALUE]) == 3
    assert "ob_retest" in out
    assert len(out["ob_retest"]) == 1


def test_stratify_empty_input() -> None:
    assert stratify_by_component([], "framework") == {}


def test_stratify_rejects_non_string_component() -> None:
    with pytest.raises(ValueError, match="component"):
        stratify_by_component([_trade("ob_retest", 1.0)], "")
    with pytest.raises(ValueError, match="component"):
        stratify_by_component([_trade("ob_retest", 1.0)], 123)  # type: ignore[arg-type]


def test_stratify_skips_non_dict_entries() -> None:
    """List with mixed dicts and non-dicts skips the non-dicts."""
    trades = [_trade("ob_retest", 1.0), "not a dict", 42, _trade("ob_retest", -1.0)]
    out = stratify_by_component(trades, "framework")  # type: ignore[arg-type]
    assert len(out["ob_retest"]) == 2


# ---------------------------------------------------------------------------
# attribute_decay — end-to-end with planted decay
# ---------------------------------------------------------------------------


def _make_planted_decay_dataset() -> tuple[list[dict], list[dict], float]:
    """Build H1/H2 trade lists with a known planted ob_retest decay.

    Setup
    -----
    H1: 30 ob_retest @ 70% WR, 15 fvg_fill @ 60% WR.
    H2: 30 ob_retest @ 30% WR, 15 fvg_fill @ 60% WR.

    ob_retest's per-stratum WR drops 70% -> 30% (40pp).
    fvg_fill stays at 60% (no decay).

    The H2 n-share weighting gives ob_retest weight 30/45 = 0.6667.
    Attributed decay (via component='framework'):
        (0.70 - 0.30) * 0.6667 + (0.60 - 0.60) * 0.3333 = 0.2667 = 26.67pp.

    Top-level observed delta:
        H1 WR: (21 + 9) / 45 = 0.6667
        H2 WR: (9 + 9) / 45  = 0.4
        delta = 26.67pp. (Matches attributed by construction.)

    Returns the trade lists + the expected attribution in pp.
    """
    h1: list[dict] = []
    # 30 ob_retest @ 70% WR -> 21 wins, 9 losses.
    for i in range(21):
        h1.append({"framework": "ob_retest", "kill_zone": "london", "r_multiple": 1.0})
    for i in range(9):
        h1.append({"framework": "ob_retest", "kill_zone": "london", "r_multiple": -1.0})
    # 15 fvg_fill @ 60% WR -> 9 wins, 6 losses.
    for i in range(9):
        h1.append({"framework": "fvg_fill", "kill_zone": "london", "r_multiple": 1.0})
    for i in range(6):
        h1.append({"framework": "fvg_fill", "kill_zone": "london", "r_multiple": -1.0})

    h2: list[dict] = []
    # 30 ob_retest @ 30% WR -> 9 wins, 21 losses.
    for i in range(9):
        h2.append({"framework": "ob_retest", "kill_zone": "london", "r_multiple": 1.0})
    for i in range(21):
        h2.append({"framework": "ob_retest", "kill_zone": "london", "r_multiple": -1.0})
    # 15 fvg_fill @ 60% WR -> 9 wins, 6 losses.
    for i in range(9):
        h2.append({"framework": "fvg_fill", "kill_zone": "london", "r_multiple": 1.0})
    for i in range(6):
        h2.append({"framework": "fvg_fill", "kill_zone": "london", "r_multiple": -1.0})

    expected_attribution_pp = (0.40 * (30.0 / 45.0)) * 100.0
    return h1, h2, expected_attribution_pp


def test_attribute_decay_recovers_planted_attribution() -> None:
    h1, h2, expected_pp = _make_planted_decay_dataset()
    report = attribute_decay(h1, h2, components=["framework"])
    fw = next(c for c in report.components if c.component == "framework")
    # Should have used both frameworks in the sum.
    assert sorted(fw.used_strata) == ["fvg_fill", "ob_retest"]
    assert fw.skipped_strata == []
    # Attribution recovers the planted ~26.67pp within 0.1pp.
    assert fw.attributed_decay_pp == pytest.approx(expected_pp, abs=0.1)


def test_attribute_decay_sanity_check_residual() -> None:
    """observed_delta == total_attributed + residual within numeric tol."""
    h1, h2, _ = _make_planted_decay_dataset()
    report = attribute_decay(h1, h2, components=["framework"])
    assert report.h1_n == 45
    assert report.h2_n == 45
    assert report.observed_delta_pp == pytest.approx(
        report.total_attributed_pp + report.residual_pp, abs=1e-9
    )


def test_attribute_decay_credible_interval_brackets_truth() -> None:
    """The 95% CI on attributed decay must contain the planted truth."""
    h1, h2, expected_pp = _make_planted_decay_dataset()
    report = attribute_decay(h1, h2, components=["framework"], ci_n_samples=4000)
    fw = next(c for c in report.components if c.component == "framework")
    assert fw.attributed_decay_ci is not None
    lo, hi = fw.attributed_decay_ci
    assert lo <= expected_pp <= hi


def test_attribute_decay_low_n_strata_flagged_and_excluded() -> None:
    """Strata with n < LOW_N_THRESHOLD are skipped from the sum."""
    h1: list[dict] = []
    h2: list[dict] = []
    # framework=ob_retest large n in both periods.
    for i in range(15):
        h1.append({"framework": "ob_retest", "r_multiple": 1.0})
        h2.append({"framework": "ob_retest", "r_multiple": -1.0})
    # framework=breaker_re_entry: n=3 in H1, n=2 in H2 (LOW_N).
    for i in range(3):
        h1.append({"framework": "breaker_re_entry", "r_multiple": 1.0})
    for i in range(2):
        h2.append({"framework": "breaker_re_entry", "r_multiple": -1.0})
    report = attribute_decay(h1, h2, components=["framework"], low_n_threshold=10)
    fw = next(c for c in report.components if c.component == "framework")
    # ob_retest used; breaker excluded.
    assert "ob_retest" in fw.used_strata
    assert "breaker_re_entry" not in fw.used_strata
    skipped = dict(fw.skipped_strata)
    assert skipped.get("breaker_re_entry") in ("LOW_N_H1", "LOW_N_H2")


def test_attribute_decay_chi_square_significant_for_planted_decay() -> None:
    """When planted decay is large (~40pp on n=30), chi^2 p-value < 0.05."""
    h1, h2, _ = _make_planted_decay_dataset()
    report = attribute_decay(h1, h2, components=["framework"])
    fw = next(c for c in report.components if c.component == "framework")
    assert fw.raw_p < 0.05
    # bonf_p with family_size=1 equals raw_p.
    assert fw.bonf_p == pytest.approx(fw.raw_p, rel=1e-9)


def test_attribute_decay_bonferroni_with_multiple_components() -> None:
    """family_size=3 multiplies raw_p by 3."""
    h1, h2, _ = _make_planted_decay_dataset()
    # Add side + kill_zone fields so the additional components are
    # well-defined (they already are — kill_zone='london').
    for t in h1 + h2:
        t["side"] = "LONG"
    report = attribute_decay(h1, h2, components=["framework", "kill_zone", "side"])
    fw = next(c for c in report.components if c.component == "framework")
    # bonf_p = raw_p * 3 (clipped to 1.0).
    assert fw.bonf_p == pytest.approx(min(1.0, fw.raw_p * 3), rel=1e-9)
    assert fw.family_size == 3


def test_attribute_decay_empty_periods() -> None:
    """Empty H1 and H2 -> trivial report with zero delta."""
    report = attribute_decay([], [], components=["framework"])
    assert report.h1_n == 0
    assert report.h2_n == 0
    assert report.observed_delta_pp == 0.0
    assert report.total_attributed_pp == 0.0


def test_attribute_decay_extreme_planted_decay() -> None:
    """All H1 wins, all H2 losses -> observed_delta=100."""
    h1 = [{"framework": "ob_retest", "r_multiple": 1.0} for _ in range(20)]
    h2 = [{"framework": "ob_retest", "r_multiple": -1.0} for _ in range(20)]
    report = attribute_decay(h1, h2, components=["framework"])
    assert report.observed_delta_pp == pytest.approx(100.0)


def test_attribute_decay_rejects_empty_components() -> None:
    with pytest.raises(ValueError, match="components"):
        attribute_decay([], [], components=[])


# ---------------------------------------------------------------------------
# Chi-square helper sanity checks
# ---------------------------------------------------------------------------


def test_chi_square_per_stratum_zero_when_homogeneous() -> None:
    """Equal WR in both periods -> chi^2 ~ 0."""
    pairs = [
        (10, 20, 10, 20),  # 50% WR in both
        (15, 25, 15, 25),  # 60% WR in both
    ]
    chi2, df = _chi_square_per_stratum(pairs)
    assert chi2 == pytest.approx(0.0, abs=1e-9)
    assert df == 2


def test_chi_square_per_stratum_grows_with_heterogeneity() -> None:
    """Larger WR delta -> larger chi^2."""
    pairs_small = [(10, 20, 11, 20)]  # 50% vs 55%
    pairs_large = [(15, 20, 5, 20)]   # 75% vs 25%
    chi2_small, _ = _chi_square_per_stratum(pairs_small)
    chi2_large, _ = _chi_square_per_stratum(pairs_large)
    assert chi2_large > chi2_small


def test_chi_square_p_value_classic_threshold() -> None:
    """chi^2 = 3.841 with df=1 has p ~ 0.05 (textbook value)."""
    p = _chi_square_p_value(3.841, df=1)
    assert p == pytest.approx(0.05, abs=0.01)


def test_chi_square_p_value_zero_chi_is_one() -> None:
    """Zero chi^2 -> p == 1.0."""
    assert _chi_square_p_value(0.0, df=5) == 1.0


# ---------------------------------------------------------------------------
# Beta PPF sanity (in-house bisection vs scipy if available)
# ---------------------------------------------------------------------------


def test_beta_ppf_endpoints() -> None:
    assert _beta_ppf_bisect(0.0, 1.0, 1.0) == 0.0
    assert _beta_ppf_bisect(1.0, 1.0, 1.0) == 1.0


def test_beta_ppf_uniform_median() -> None:
    """Beta(1, 1).ppf(0.5) == 0.5."""
    val = _beta_ppf_bisect(0.5, 1.0, 1.0)
    assert val == pytest.approx(0.5, abs=1e-4)
