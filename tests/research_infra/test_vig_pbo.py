"""Known-answer tests for ``src/research_infra/validation_integrity/pbo.py``.

Method: CSCV PBO (Bailey, Borwein, Lopez de Prado, Zhu 2017).

Known-answer design
-------------------
1. PURE NOISE -> PBO == 0.5 in expectation.
   A single CSCV realisation is high-variance (the IS-best column's OOS luck is
   shared across 12870 highly-overlapping combinations, so a lone matrix can
   land anywhere ~0.35-0.65). The *robust* known-answer is therefore the mean
   PBO over many independent iid noise matrices, which converges tightly to 0.5
   (here ~0.48 over 24 fixed-seed draws). The logit distribution is symmetric
   about 0 for noise, so mean(mean_logit) ~ 0.

2. ONE GENUINE EDGE among noise -> PBO LOW (< 0.2).
   A single column carries a persistent positive mean-shift across ALL blocks.
   It is the IS-best in nearly every split AND stays top OOS, so its logit is
   large-positive almost always -> very few combinations have lambda <= 0.

Plus: degenerate all-equal matrix (graceful, no nan/inf), the subsample branch
for S > 20, structural invariants, and input validation. All synthetic and
deterministic; nothing touches a production path.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from src.research_infra.validation_integrity.pbo import (
    DEFAULT_MAX_COMBINATIONS,
    pbo_cscv,
)


# ---------------------------------------------------------------------------
# Known-answer 1: pure noise -> mean PBO ~ 0.5
# ---------------------------------------------------------------------------

def test_pure_noise_pbo_is_half_on_average():
    """Mean PBO over 24 iid-noise matrices converges to ~0.5 (no real edge)."""
    pbos = []
    mean_logits = []
    for seed in range(1000, 1024):
        M = np.random.default_rng(seed).standard_normal((1200, 20))
        res = pbo_cscv(M, n_partitions=16, metric="sharpe")
        pbos.append(res["pbo"])
        mean_logits.append(res["mean_logit"])
    mean_pbo = float(np.mean(pbos))
    # Deterministic value for this seed set is ~0.4803; band is wide enough to
    # be robust yet still unambiguously "around 0.5" (far from the edge/degen
    # regimes which sit near 0.04 and 1.0 respectively).
    assert 0.40 < mean_pbo < 0.60, mean_pbo
    # logit distribution is symmetric about 0 under the null.
    assert abs(float(np.mean(mean_logits))) < 0.20


def test_pure_noise_single_matrix_structure():
    """Structural invariants on one S=16 noise run."""
    M = np.random.default_rng(0).standard_normal((1600, 20))
    res = pbo_cscv(M, n_partitions=16, metric="sharpe")
    assert res["total_combinations"] == math.comb(16, 8) == 12870
    assert res["n_combinations"] == 12870
    assert res["subsampled"] is False
    assert len(res["logits"]) == res["n_combinations"]
    assert np.all(np.isfinite(res["logits"]))
    assert 0.0 <= res["pbo"] <= 1.0
    assert res["n_strategies"] == 20
    assert res["n_partitions"] == 16


# ---------------------------------------------------------------------------
# Known-answer 2: one genuine persistent edge -> PBO low
# ---------------------------------------------------------------------------

def test_genuine_edge_gives_low_pbo_sharpe():
    """One column with a persistent mean-shift across ALL blocks -> PBO < 0.2."""
    M = np.random.default_rng(7).standard_normal((1200, 20))
    M[:, 7] += 0.12  # genuine, time-stable edge in column 7
    res = pbo_cscv(M, n_partitions=16, metric="sharpe")
    assert res["pbo"] < 0.2, res["pbo"]
    # Real edge -> the IS-best stays well above the OOS median -> positive drift.
    assert res["mean_logit"] > 0.5


def test_genuine_edge_gives_low_pbo_mean_metric():
    """Same edge detected under metric='mean'."""
    M = np.random.default_rng(7).standard_normal((1200, 20))
    M[:, 7] += 0.12
    res = pbo_cscv(M, n_partitions=16, metric="mean")
    assert res["pbo"] < 0.2, res["pbo"]


def test_edge_pbo_below_noise_pbo():
    """Ordering sanity: the edge matrix has lower PBO than its noise twin."""
    base = np.random.default_rng(11).standard_normal((1200, 20))
    noise_pbo = pbo_cscv(base, n_partitions=16, metric="sharpe")["pbo"]
    edged = base.copy()
    edged[:, 3] += 0.15
    edge_pbo = pbo_cscv(edged, n_partitions=16, metric="sharpe")["pbo"]
    assert edge_pbo < noise_pbo


# ---------------------------------------------------------------------------
# Degenerate / tie handling
# ---------------------------------------------------------------------------

def test_all_equal_columns_graceful():
    """All-constant matrix must not crash; logits finite; PBO well-defined."""
    M = np.full((400, 5), 3.0)
    res = pbo_cscv(M, n_partitions=8, metric="sharpe")
    assert np.all(np.isfinite(res["logits"]))
    assert 0.0 <= res["pbo"] <= 1.0
    # All columns tie at the OOS median (w=0.5, lambda=0 <= 0) -> PBO == 1.0.
    assert res["pbo"] == 1.0
    assert all(abs(l) < 1e-12 for l in res["logits"])


def test_tied_columns_do_not_crash():
    """Duplicate columns (exact ties) handled by average-rank without error."""
    rng = np.random.default_rng(5)
    col = rng.standard_normal((800, 1))
    M = np.hstack([col, col, rng.standard_normal((800, 3))])  # two identical cols
    res = pbo_cscv(M, n_partitions=10, metric="sharpe")
    assert np.all(np.isfinite(res["logits"]))
    assert 0.0 <= res["pbo"] <= 1.0


# ---------------------------------------------------------------------------
# Subsample branch (S > 20)
# ---------------------------------------------------------------------------

def test_subsample_branch_caps_and_is_deterministic():
    M = np.random.default_rng(3).standard_normal((330, 5))
    res = pbo_cscv(M, n_partitions=22, metric="sharpe",
                   max_combinations=20000, random_state=0)
    assert res["total_combinations"] == math.comb(22, 11) == 705432
    assert res["subsampled"] is True
    assert res["n_combinations"] == 20000
    assert len(res["logits"]) == 20000
    # Same seed -> identical result.
    res2 = pbo_cscv(M, n_partitions=22, metric="sharpe",
                    max_combinations=20000, random_state=0)
    assert res2["pbo"] == res["pbo"]
    assert res2["logits"] == res["logits"]


def test_default_max_combinations_constant():
    assert DEFAULT_MAX_COMBINATIONS == 20000


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_rejects_single_column():
    with pytest.raises(ValueError):
        pbo_cscv(np.random.default_rng(0).standard_normal((100, 1)), n_partitions=4)


def test_rejects_odd_partitions():
    with pytest.raises(ValueError):
        pbo_cscv(np.random.default_rng(0).standard_normal((100, 5)), n_partitions=7)


def test_rejects_partitions_exceeding_rows():
    with pytest.raises(ValueError):
        pbo_cscv(np.random.default_rng(0).standard_normal((6, 5)), n_partitions=8)


def test_rejects_non_finite():
    M = np.random.default_rng(0).standard_normal((100, 5))
    M[0, 0] = np.nan
    with pytest.raises(ValueError):
        pbo_cscv(M, n_partitions=4)


def test_rejects_bad_metric():
    with pytest.raises(ValueError):
        pbo_cscv(np.random.default_rng(0).standard_normal((100, 5)),
                 n_partitions=4, metric="omega")


def test_rejects_non_2d():
    with pytest.raises(ValueError):
        pbo_cscv(np.arange(10.0), n_partitions=4)
