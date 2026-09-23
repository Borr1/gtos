"""Known-answer tests for ``src/research_infra/validation_integrity/dsr.py``.

The Deflated Sharpe Ratio is a *gate*: it decides whether an apparent edge is
real or a multiple-testing artifact, and that decision sizes real money.  So
every component is pinned to a known answer:

* the inverse standard-normal ``Z`` is validated at the canonical 97.5%
  quantile (``Z(0.975) = 1.95996...``) and by a Phi round-trip;
* the PSR is recomputed from raw arithmetic (independent of the module's
  internal moment code) on a deterministic asymmetric series;
* the DSR is exercised on three scenarios with a hard qualitative answer:
    1. pure Gaussian noise, many trials  -> NOT significant (deflated to ~0);
    2. a strong genuine edge, one trial   -> significant;
    3. the SAME edge, 5000 trials         -> meaningfully deflated vs (2).
"""

from __future__ import annotations

import math
import random

import pytest

from src.research_infra.validation_integrity.dsr import (
    EULER_MASCHERONI,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    inv_phi,
    phi,
    probabilistic_sharpe_ratio,
)


# ---------------------------------------------------------------------------
# Phi / inverse-Phi
# ---------------------------------------------------------------------------
def test_phi_known_points():
    assert phi(0.0) == pytest.approx(0.5, abs=1e-15)
    # symmetry: phi(-x) = 1 - phi(x)
    for x in (0.3, 1.0, 1.95996, 3.0):
        assert phi(-x) == pytest.approx(1.0 - phi(x), abs=1e-15)
    # canonical: phi(1.959963985) == 0.975
    assert phi(1.959963984540054) == pytest.approx(0.975, abs=1e-12)


def test_inverse_normal_canonical_quantile():
    """The load-bearing validation: Z(0.975) ~= 1.95996."""
    z = inv_phi(0.975)
    assert z == pytest.approx(1.95996, abs=1e-5)
    # tighter: full-precision reference value
    assert z == pytest.approx(1.9599639845400538, abs=1e-12)


def test_inverse_normal_other_quantiles_and_roundtrip():
    assert inv_phi(0.5) == pytest.approx(0.0, abs=1e-12)
    assert inv_phi(0.99) == pytest.approx(2.326347874040841, abs=1e-9)
    assert inv_phi(0.025) == pytest.approx(-1.9599639845400538, abs=1e-12)
    # round-trip phi(inv_phi(p)) == p to machine precision across the range
    for p in (1e-6, 0.001, 0.02425, 0.1, 0.3, 0.5, 0.7, 0.9, 0.97559, 0.999, 1 - 1e-6):
        assert phi(inv_phi(p)) == pytest.approx(p, abs=1e-12)
    # degenerate tails
    assert inv_phi(0.0) == float("-inf")
    assert inv_phi(1.0) == float("inf")


# ---------------------------------------------------------------------------
# PSR — independent arithmetic known-answer
# ---------------------------------------------------------------------------
def test_psr_independent_recompute_on_asymmetric_series():
    """Recompute PSR from raw moments + erf, independent of module internals."""
    # Deterministic, deliberately skewed/fat-tailed series.
    xs = [0.5, -0.3, 1.2, -0.1, 0.4, -0.8, 2.5, 0.1, -0.2, 0.3,
          0.6, -0.4, 0.2, 1.1, -0.9, 0.7, -0.05, 0.15, 3.0, -0.6]
    n = len(xs)
    mean = sum(xs) / n
    m2 = sum((v - mean) ** 2 for v in xs) / n
    m3 = sum((v - mean) ** 3 for v in xs) / n
    m4 = sum((v - mean) ** 4 for v in xs) / n
    std = math.sqrt(m2)
    skew = m3 / m2 ** 1.5
    kurt = m4 / m2 ** 2  # non-excess
    sr = mean / std
    benchmark = 0.0
    var_term = 1.0 - skew * sr + ((kurt - 1.0) / 4.0) * sr * sr
    z = (sr - benchmark) * math.sqrt(n - 1) / math.sqrt(var_term)
    psr_expected = 0.5 * math.erfc(-z / math.sqrt(2.0))

    out = probabilistic_sharpe_ratio(xs, sr_benchmark=benchmark)
    assert out["sr_per_period"] == pytest.approx(sr, abs=1e-15)
    assert out["skew"] == pytest.approx(skew, abs=1e-15)
    assert out["kurtosis"] == pytest.approx(kurt, abs=1e-15)
    assert out["n"] == n
    assert out["psr"] == pytest.approx(psr_expected, abs=1e-15)
    assert out["p_value"] == pytest.approx(1.0 - psr_expected, abs=1e-15)


def test_psr_gaussian_denominator_identity():
    """For (near-)Gaussian returns the denominator collapses to sqrt(1+SR^2/2)."""
    random.seed(99)
    g = [random.gauss(0.05, 1.0) for _ in range(20000)]
    out = probabilistic_sharpe_ratio(g, 0.0)
    # skew ~ 0, kurt ~ 3 for a large Gaussian sample
    assert abs(out["skew"]) < 0.1
    assert abs(out["kurtosis"] - 3.0) < 0.15
    sr = out["sr_per_period"]
    n = out["n"]
    z_gauss = sr * math.sqrt(n - 1) / math.sqrt(1.0 + 0.5 * sr * sr)
    assert out["psr"] == pytest.approx(phi(z_gauss), abs=2e-3)


# ---------------------------------------------------------------------------
# expected_max_sharpe
# ---------------------------------------------------------------------------
def test_expected_max_sharpe_properties_and_value():
    # N=1 -> no selection -> 0
    assert expected_max_sharpe(1, 0.25) == 0.0
    # zero variance -> 0
    assert expected_max_sharpe(1000, 0.0) == 0.0
    # strictly increasing in N (more trials -> larger expected max)
    vals = [expected_max_sharpe(nt, 1.0) for nt in (2, 5, 10, 100, 1000, 10000)]
    assert all(b > a for a, b in zip(vals, vals[1:]))
    # scales with sqrt(variance)
    assert expected_max_sharpe(500, 4.0) == pytest.approx(
        2.0 * expected_max_sharpe(500, 1.0), abs=1e-12
    )
    # independent recompute for a specific N
    nt, V = 1000, 1.0
    g = EULER_MASCHERONI
    expect = math.sqrt(V) * (
        (1 - g) * inv_phi(1 - 1.0 / nt) + g * inv_phi(1 - 1.0 / (nt * math.e))
    )
    assert expected_max_sharpe(nt, V) == pytest.approx(expect, abs=1e-15)


# ---------------------------------------------------------------------------
# DSR — three known-answer scenarios
# ---------------------------------------------------------------------------
def test_dsr_case1_gaussian_noise_many_trials_not_significant():
    """Pure mean-0 Gaussian noise, deflated by 1000 trials -> NOT significant."""
    random.seed(12345)
    noise = [random.gauss(0.0, 1.0) for _ in range(1500)]
    out = deflated_sharpe_ratio(noise, n_trials=1000, sr_variance=0.0004)
    assert out["significant"] is False
    assert out["dsr"] < 0.5            # deflated well below significance
    assert out["sr_benchmark"] > 0.0   # selection benchmark is positive
    assert out["p_value"] == pytest.approx(1.0 - out["dsr"], abs=1e-15)


def test_dsr_case2_strong_edge_single_trial_significant():
    """A genuine edge (mean 0.1, sd 1, n=1500), one trial -> significant."""
    random.seed(777)
    edge = [random.gauss(0.1, 1.0) for _ in range(1500)]
    out = deflated_sharpe_ratio(edge, n_trials=1, sr_variance=0.0009)
    assert out["sr_benchmark"] == 0.0  # one trial -> no deflation
    assert out["significant"] is True
    assert out["dsr"] > 0.95
    assert out["psr"] > 0.95


def test_dsr_case3_same_edge_many_trials_meaningfully_deflated():
    """The SAME edge under 5000 trials deflates materially vs a single trial."""
    random.seed(777)
    edge = [random.gauss(0.1, 1.0) for _ in range(1500)]
    one = deflated_sharpe_ratio(edge, n_trials=1, sr_variance=0.0009)
    many = deflated_sharpe_ratio(edge, n_trials=5000, sr_variance=0.0009)
    assert many["sr_benchmark"] > one["sr_benchmark"]
    assert many["dsr"] < one["dsr"]
    # "meaningfully" deflated: a large, decision-changing drop
    assert (one["dsr"] - many["dsr"]) > 0.1
    assert many["significant"] is False


def test_dsr_requires_variance_or_benchmark():
    edge = [0.1, -0.2, 0.3, 0.0, 0.15, -0.05, 0.2, 0.1] * 10
    with pytest.raises(ValueError):
        deflated_sharpe_ratio(edge, n_trials=100)  # both None -> error
    # explicit benchmark path works
    out = deflated_sharpe_ratio(edge, n_trials=100, sr_benchmark=0.05)
    assert out["sr_benchmark"] == 0.05


def test_moments_guard_zero_variance():
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([0.3, 0.3, 0.3, 0.3])
    with pytest.raises(ValueError):
        probabilistic_sharpe_ratio([0.3])  # too few obs
