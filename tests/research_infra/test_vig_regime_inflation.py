"""Known-answer tests for the regime-inflation / window-contamination diagnostic.

Two synthetic cases with hand-derivable answers:
  (1) CLEAN: every year has the SAME mean and the selection window is representative
      -> fwd_all_mean_ratio == 1.0, contamination_flag False, recommended haircut == 1.0.
  (2) CONTAMINATED: the last window's mean is 3x the all-history mean AND that window year is the
      single top year -> fwd_all_mean_ratio == 3.0, flag True, recommended haircut ~= 1/3.

Synthetic returns use a deterministic zero-mean alternating pattern (value = mean +/- c) so each
year's sample mean equals its target EXACTLY and its population std equals c EXACTLY -- the answers
are closed-form, not Monte-Carlo. Run:  /opt/homebrew/bin/python3 <thisfile>
"""
from __future__ import annotations

import datetime as _dt
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.abspath(os.path.join(_HERE, "..", "..", "src"))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from research_infra.validation_integrity.regime_inflation import (  # noqa: E402
    regime_inflation_diagnostic,
    expected_max_sharpe,
    expected_max_z,
    norm_cdf,
    norm_ppf,
)


# ----------------------------------------------------------------------------------------------
# deterministic synthetic builder
# ----------------------------------------------------------------------------------------------
def _year_block(year: int, mean: float, c: float, n: int):
    """n (even) dated obs inside `year` with EXACT sample mean=`mean` and EXACT pop-std=`c`."""
    assert n % 2 == 0, "use an even day count for an exact zero-mean alternating pattern"
    base = _dt.date(year, 1, 1)
    out = []
    for i in range(n):
        d = base + _dt.timedelta(days=i)  # n<=120 stays inside the calendar year
        out.append((d, mean + c if i % 2 == 0 else mean - c))
    return out


def _build(years, means, c=0.2, n=120):
    series = []
    for y, m in zip(years, means):
        series.extend(_year_block(y, m, c, n))
    return series


# ----------------------------------------------------------------------------------------------
# (0) normal-helper sanity (these underpin the selection-surface penalty)
# ----------------------------------------------------------------------------------------------
def test_normal_helpers():
    # inverse-CDF known values
    assert abs(norm_ppf(0.975) - 1.959963985) < 1e-6
    assert abs(norm_ppf(0.5) - 0.0) < 1e-9
    assert abs(norm_ppf(0.025) + 1.959963985) < 1e-6
    # round-trip
    for p in (0.001, 0.05, 0.3, 0.5, 0.84, 0.999):
        assert abs(norm_cdf(norm_ppf(p)) - p) < 1e-9
    # expected-max of N normals: 0 at N<=1, monotone increasing, ~2.5-2.8 around N=128
    assert expected_max_z(1) == 0.0
    assert expected_max_z(2) < expected_max_z(10) < expected_max_z(128) < expected_max_z(1000)
    assert 2.4 < expected_max_z(128) < 2.8
    # expected_max_sharpe scales with sqrt(variance) and is 0 at N<=1
    assert expected_max_sharpe(1, 0.04) == 0.0
    assert abs(expected_max_sharpe(128, 0.04)
               - expected_max_z(128) * math.sqrt(0.04)) < 1e-12
    print("[ok] normal helpers: norm_ppf(.975)=%.6f  E_maxZ(128)=%.4f"
          % (norm_ppf(0.975), expected_max_z(128)))


# ----------------------------------------------------------------------------------------------
# (1) CLEAN known-answer
# ----------------------------------------------------------------------------------------------
def test_clean_window_is_representative():
    years = list(range(2014, 2026))             # 12 years
    series = _build(years, means=[0.10] * 12, c=0.20, n=120)
    out = regime_inflation_diagnostic(series, selection_window_start="2025-01-01",
                                      n_trials=128)
    print("[clean] ratio=%.4f flag=%s haircut=%.4f selpen=%.4f topk=%s"
          % (out["fwd_all_mean_ratio"], out["contamination_flag"],
             out["recommended_magnitude_haircut"], out["selection_surface_penalty"], out["holdout_are_topk"]))
    assert abs(out["fwd_all_mean_ratio"] - 1.0) < 1e-9
    assert out["contamination_flag"] is False
    assert abs(out["recommended_magnitude_haircut"] - 1.0) < 1e-6
    assert out["holdout_are_topk"] is False
    # every year identical -> per-year SR variance deconvolves to 0 -> no selection haircut
    assert abs(out["selection_surface_penalty"] - 1.0) < 1e-6
    assert out["holdout_years"] == [2025]
    assert "CLEAN" in out["verdict"]


# ----------------------------------------------------------------------------------------------
# (2) CONTAMINATED known-answer:  fwd/all == 3.0 exactly, window year is the single top year
# ----------------------------------------------------------------------------------------------
def test_contaminated_3x_window():
    years = list(range(2014, 2026))             # 12 years
    # 11 rest years at mean 0.10; last (window) year at 0.3666667 so window/all == 3 exactly:
    #   mean_all = (11*0.10 + 0.3666667)/12 = 0.1222222 ; 0.3666667 / 0.1222222 = 3.0
    means = [0.10] * 11 + [11.0 / 30.0]         # 0.36666... gives an exact 3x
    series = _build(years, means=means, c=0.20, n=120)
    out = regime_inflation_diagnostic(series, selection_window_start="2025-01-01",
                                      n_trials=128)
    print("[contam] ratio=%.4f flag=%s haircut=%.4f selpen=%.4f regime_basis=%.4f topk=%s rank=%s"
          % (out["fwd_all_mean_ratio"], out["contamination_flag"],
             out["recommended_magnitude_haircut"], out["selection_surface_penalty"],
             out["regime_basis_haircut"], out["holdout_are_topk"], out["holdout_years_rank"]))
    assert abs(out["fwd_all_mean_ratio"] - 3.0) < 1e-6
    assert out["contamination_flag"] is True
    assert out["holdout_are_topk"] is True
    assert out["holdout_years_rank"] == {2025: 1}          # window year is the single best
    # recommended haircut ~ 1/3 (regime basis dominates; selection penalty is the over-and-above)
    assert abs(out["recommended_magnitude_haircut"] - (1.0 / 3.0)) < 0.06
    assert 0.0 < out["selection_surface_penalty"] <= 1.0
    assert "CONTAMINATED" in out["verdict"]
    # the regime basis is EXACTLY 1/3 here (3x window); module rounds to 5dp
    assert abs(out["regime_basis_haircut"] - (1.0 / 3.0)) < 1e-4


def _run_all():
    test_normal_helpers()
    test_clean_window_is_representative()
    test_contaminated_3x_window()
    print("\nALL KNOWN-ANSWER TESTS PASSED")


if __name__ == "__main__":
    _run_all()
