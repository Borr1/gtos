"""Known-answer / behavioural tests for the assembled Validation-Integrity Gauntlet.

The gauntlet wires the six components into one verdict. These tests build two small,
deterministic synthetic books and assert the SHAPE and DIRECTION of the merged verdict:

  (1) CLEAN book   -- a stationary multi-sleeve book with distinct, persistent positive
                      per-sleeve edges and constant per-year means. The directional edge is
                      real (DSR significant at a small n_trials, low PBO, tiny permutation p)
                      and the selection window is representative (no regime inflation).
                      EXPECT: integrity_verdict == 'PASS', contamination_flag False.

  (2) CONTAMINATED book -- the same structure but the final year's mean is blown up ~5x, so
                      the forward window is a best-regime surface and is the literal top year.
                      EXPECT: contamination_flag True and integrity_verdict in
                      {'CONDITIONAL','FAIL'} (a real edge with an inflated MAGNITUDE is never
                      a clean PASS).

Both cases also assert that every documented sub-key is present.

Determinism: synthetic returns use a seeded numpy Generator, so the verdict is reproducible.
Run directly:  /opt/homebrew/bin/python3 tests/research_infra/test_validation_integrity_gauntlet.py
or via pytest.
"""
from __future__ import annotations

import datetime as _dt
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from research_infra.validation_integrity.gauntlet import (  # noqa: E402
    run_gauntlet,
    estimate_sr_variance_from_sleeves,
)


# ----------------------------------------------------------------------------------------------
# deterministic synthetic builders
# ----------------------------------------------------------------------------------------------
def _build_book(n_years: int, n_sleeves: int, seed: int, last_year_boost: float = 1.0):
    """Build a deterministic (T, N) book of ``n_years`` calendar years.

    Each sleeve j has a DISTINCT, persistent positive mean (so the IS-best sleeve stays best
    OOS -> low PBO), unit-ish noise, and a constant mean across years -- except the final
    year, whose mean is multiplied by ``last_year_boost`` (== 1.0 for a clean book).

    Returns (all_days, sleeves, sleeve_matrix, combined, dated_series, last_year_start).
    """
    rng = np.random.default_rng(seed)
    # distinct, persistent per-sleeve means (all positive, well-separated) so the IS-best
    # sleeve stays best OOS (low PBO). A tight noise keeps per-YEAR means clustered so a
    # clean book's forward window is representative (ratio ~1.0, no spurious regime flag).
    mu = np.array([0.09 + 0.02 * j for j in range(n_sleeves)], dtype=float)
    sigma = 0.3

    days_per_year = 252  # < 365, so each block stays inside its calendar year
    all_days = []
    rows = []
    last_year_index = n_years - 1
    for y in range(n_years):
        boost = last_year_boost if y == last_year_index else 1.0
        year_mu = mu * boost
        year_base = _dt.date(2020 + y, 1, 1)
        for k in range(days_per_year):
            all_days.append(year_base + _dt.timedelta(days=k))
            row = year_mu + rng.normal(0.0, sigma, size=n_sleeves)
            rows.append([float(v) for v in row])

    sleeve_matrix = rows
    sleeves = [f"sleeve_{j}" for j in range(n_sleeves)]
    combined = [float(sum(r)) for r in sleeve_matrix]
    dated_series = list(zip([str(d) for d in all_days], combined))
    last_year_start = str(_dt.date(2020 + last_year_index, 1, 1))
    return all_days, sleeves, sleeve_matrix, combined, dated_series, last_year_start


_SUBKEYS_COMPONENTS = ("dsr", "pbo", "permutation", "regime_inflation", "walk_forward")
_SUBKEYS_HONEST = (
    "honest_n1_sharpe_daily_all_history",
    "honest_basis_note",
    "contamination_flag",
    "recommended_magnitude_haircut",
)
_TOP_KEYS = (
    "schema", "n_obs", "n_sleeves", "sleeves", "selection_window_start", "n_trials",
    "sr_variance_used", "sr_variance_source", "ground_truth", "components", "gates",
    "integrity_verdict", "integrity_reasons", "honest_summary", "honest_headline",
)


def _assert_shape(res):
    for k in _TOP_KEYS:
        assert k in res, f"missing top-level key {k!r}"
    for k in _SUBKEYS_COMPONENTS:
        assert k in res["components"], f"missing component {k!r}"
    for k in _SUBKEYS_HONEST:
        assert k in res["honest_summary"], f"missing honest_summary key {k!r}"
    # each gate carries a boolean 'pass'
    for gname, g in res["gates"].items():
        assert "pass" in g and isinstance(g["pass"], bool), f"gate {gname} missing bool pass"
    assert res["integrity_verdict"] in ("PASS", "CONDITIONAL", "FAIL")
    # ground-truth reproduction block
    for k in ("sd_book", "mean_all", "mean_fwd", "fwd_all_ratio", "n_obs", "n_in_window"):
        assert k in res["ground_truth"], f"missing ground_truth.{k}"


# ----------------------------------------------------------------------------------------------
# tests
# ----------------------------------------------------------------------------------------------
def test_sr_variance_estimator_is_population_variance():
    """The estimator returns the ddof=0 variance of per-sleeve Sharpes (matches DSR self-check)."""
    _, _, M, _, _, _ = _build_book(n_years=4, n_sleeves=6, seed=7)
    sv = estimate_sr_variance_from_sleeves(M)
    assert sv["sr_variance"] >= 0.0
    assert len(sv["per_sleeve_sharpe"]) == 6
    # hand-recompute population variance of the per-sleeve Sharpes
    srs = sv["per_sleeve_sharpe"]
    mu = sum(srs) / len(srs)
    pop_var = sum((s - mu) ** 2 for s in srs) / len(srs)
    assert math.isclose(sv["sr_variance"], pop_var, rel_tol=1e-12, abs_tol=1e-15)


def test_gauntlet_clean_book_passes():
    """A stationary, representative book passes structure AND magnitude -> PASS, no contamination."""
    _, sleeves, M, combined, dated, last_year_start = _build_book(
        n_years=4, n_sleeves=6, seed=11, last_year_boost=1.0
    )
    res = run_gauntlet(
        combined_daily=combined,
        dated_series=dated,
        sleeve_matrix=M,
        sleeves=sleeves,
        selection_window_start=last_year_start,
        n_trials=2,  # small search -> light DSR deflation on a genuinely strong edge
    )
    _assert_shape(res)

    # structure gates pass
    assert res["gates"]["dsr_significant"]["pass"], res["components"]["dsr"]
    assert res["gates"]["pbo_not_overfit"]["pass"], res["components"]["pbo"]["pbo"]
    assert res["gates"]["permutation_directional_edge"]["pass"], res["components"]["permutation"]
    # magnitude clean
    assert res["honest_summary"]["contamination_flag"] is False
    assert res["gates"]["magnitude_not_contaminated"]["pass"]
    # representative window -> haircut close to 1.0
    assert res["honest_summary"]["recommended_magnitude_haircut"] > 0.8
    # overall
    assert res["integrity_verdict"] == "PASS", res["integrity_reasons"]


def test_gauntlet_contaminated_book_flags_magnitude():
    """A book whose final year is blown up ~5x is flagged contaminated and is NOT a clean PASS."""
    _, sleeves, M, combined, dated, last_year_start = _build_book(
        n_years=4, n_sleeves=6, seed=11, last_year_boost=5.0
    )
    res = run_gauntlet(
        combined_daily=combined,
        dated_series=dated,
        sleeve_matrix=M,
        sleeves=sleeves,
        selection_window_start=last_year_start,
        n_trials=128,
    )
    _assert_shape(res)

    # the magnitude gate must catch the regime inflation
    assert res["honest_summary"]["contamination_flag"] is True, res["components"]["regime_inflation"]
    assert res["gates"]["magnitude_not_contaminated"]["pass"] is False
    # forward window is materially inflated and recommends a real haircut
    fwd_ratio = res["components"]["regime_inflation"]["fwd_all_mean_ratio"]
    assert fwd_ratio is not None and fwd_ratio >= 1.5, fwd_ratio
    assert res["honest_summary"]["recommended_magnitude_haircut"] < 1.0
    # a real edge with an inflated magnitude is CONDITIONAL (or FAIL) -- never a clean PASS
    assert res["integrity_verdict"] in ("CONDITIONAL", "FAIL"), res["integrity_reasons"]


def test_gauntlet_rejects_mismatched_sleeve_names():
    """Defensive: sleeve-name count must match the matrix columns."""
    _, _, M, combined, dated, last_year_start = _build_book(n_years=3, n_sleeves=5, seed=3)
    raised = False
    try:
        run_gauntlet(combined, dated, M, ["only", "three", "names"], last_year_start, 4)
    except ValueError:
        raised = True
    assert raised, "expected ValueError on sleeve/column count mismatch"


def _run_all():
    fns = [
        test_sr_variance_estimator_is_population_variance,
        test_gauntlet_clean_book_passes,
        test_gauntlet_contaminated_book_flags_magnitude,
        test_gauntlet_rejects_mismatched_sleeve_names,
    ]
    for fn in fns:
        fn()
        print(f"PASS {fn.__name__}")
    print(f"\nALL {len(fns)} gauntlet tests passed.")


if __name__ == "__main__":
    _run_all()
