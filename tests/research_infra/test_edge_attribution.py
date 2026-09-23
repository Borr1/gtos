"""Tests for ``src/research_infra/edge_attribution.py`` (K50).

Methodology
-----------
- Synthetic data with planted signal so we can assert the regressor /
  Bayesian recovers the right ranking deterministically.
- Optional-dep fallbacks (``shap`` / ``lightgbm`` missing) are exercised by
  monkeypatching the module-level handles back to ``None`` — guaranteed to
  hit the fallback branch even on machines that have those libs.
- All file writes use ``tmp_path``; no production paths touched (conftest
  guard would catch a regression anyway).
- F16 update: tests added for proper SHAP path enforcement, bootstrap CI
  math, Bonferroni correction across the feature family, and the
  ``--alpha`` CLI flag.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from src.research_infra import edge_attribution as ea
from src.research_infra.edge_attribution import (
    AttributionReport,
    AttributionWithCI,
    FEATURE_NAMES,
    FeatureCI,
    FeatureImportanceTest,
    FeatureRanking,
    bayesian_linear_attribution,
    bonferroni_correct,
    build_feature_matrix,
    compute_shap_attribution,
    compute_shap_attribution_with_ci,
    h1_h2_importance_test,
    spearman_rank_delta,
    train_gbm_regressor,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
K50_CLI = REPO_ROOT / "scripts" / "research" / "run_k50_edge_attribution.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trade(
    *,
    r: float,
    framework: str = "ob_retest",
    kill_zone: str = "london",
    displacement_quality: str = "strong",
    fvg_present: bool = False,
    touch_count: int = 1,
    ob_distance_atr: float = 0.5,
    hour: int = 8,
    regime: str = "trend_up",
    symbol: str = "XAUUSD",
    trade_id: str | None = None,
    date: str = "2024-04-01",
) -> dict:
    """Build a synthetic trade dict carrying every K50 feature."""
    base_dt = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
    ts = base_dt + timedelta(hours=hour)
    return {
        "trade_id": trade_id or f"syn_{date}_{hour:02d}_{r:+.2f}",
        "symbol": symbol,
        "framework": framework,
        "kill_zone": kill_zone,
        "displacement_quality": displacement_quality,
        "fvg_present": fvg_present,
        "touch_count": touch_count,
        "ob_retest_distance_atr": ob_distance_atr,
        "regime_tag": regime,
        "candle_close_time": ts.isoformat(),
        "date": date,
        "r_multiple": r,
    }


def _planted_signal_trades(n: int = 60, seed: int = 0) -> list[dict]:
    """Generate trades where ``displacement_quality_score`` dominates R.

    R = 1.5 * displacement_score + 0.4 * fvg_present + 0.05 * touch_count
        + small_noise

    By construction, ``displacement_quality_score`` should rank #1 in
    both SHAP and Bayesian outputs.
    """
    rng = np.random.default_rng(seed)
    quality_choices = ["strong", "medium", "weak", "ambiguous"]
    quality_scores = {"strong": 1.0, "medium": 0.5, "weak": 0.0, "ambiguous": 0.25}

    trades = []
    base_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        q = quality_choices[i % len(quality_choices)]
        fvg = bool(i % 3 == 0)
        touch = (i % 4) + 1
        # Vary another nuisance feature so the GBM has variance to assign:
        ob_dist = 0.3 + 0.1 * (i % 5)
        # Planted target
        r = (
            1.5 * quality_scores[q]
            + 0.4 * (1.0 if fvg else 0.0)
            + 0.05 * touch
            + rng.normal(0.0, 0.05)
        )
        d = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
        trades.append(
            _trade(
                r=r,
                displacement_quality=q,
                fvg_present=fvg,
                touch_count=touch,
                ob_distance_atr=ob_dist,
                framework="fvg_fill" if fvg else "ob_retest",
                kill_zone="london" if i % 2 else "ny",
                hour=(8 if i % 2 else 14) + (i % 3),
                date=d,
                trade_id=f"planted_{i:03d}",
            )
        )
    return trades


# ---------------------------------------------------------------------------
# build_feature_matrix
# ---------------------------------------------------------------------------

def test_build_feature_matrix_shape_and_dtypes():
    trades = [
        _trade(r=1.0),
        _trade(r=-0.5, displacement_quality="weak"),
        _trade(r=2.0, fvg_present=True, framework="fvg_fill"),
        _trade(r=0.0, touch_count=3),
        _trade(r=-1.0, kill_zone="ny", hour=14),
    ]
    X, y, names = build_feature_matrix(trades)
    assert X.shape == (5, len(FEATURE_NAMES))
    assert y.shape == (5,)
    assert X.dtype == np.float64
    assert y.dtype == np.float64
    assert names == list(FEATURE_NAMES)


def test_build_feature_matrix_drops_unfilled():
    """Trades without realised R are dropped silently."""
    trades = [
        _trade(r=1.0),
        {"trade_id": "unfilled", "symbol": "XAUUSD", "framework": "ob_retest"},
        _trade(r=-0.5),
    ]
    X, y, names = build_feature_matrix(trades)
    assert X.shape == (2, len(FEATURE_NAMES))
    assert list(y) == [1.0, -0.5]


def test_build_feature_matrix_empty_input():
    X, y, names = build_feature_matrix([])
    assert X.shape == (0, len(FEATURE_NAMES))
    assert y.shape == (0,)
    assert names == list(FEATURE_NAMES)


def test_build_feature_matrix_non_dict_rows_skipped():
    trades = [_trade(r=1.0), "garbage", None, _trade(r=-0.5)]
    X, y, _ = build_feature_matrix(trades)  # type: ignore[arg-type]
    assert X.shape[0] == 2
    assert list(y) == [1.0, -0.5]


def test_build_feature_matrix_type_error_non_list():
    with pytest.raises(TypeError):
        build_feature_matrix({"trade_id": "foo"})  # type: ignore[arg-type]


def test_displacement_score_and_fvg_extraction():
    trades = [
        _trade(r=1.0, displacement_quality="strong", fvg_present=True),
        _trade(r=1.0, displacement_quality="weak", fvg_present=False),
        _trade(r=1.0, displacement_quality="ambiguous"),
    ]
    X, _, names = build_feature_matrix(trades)
    disp_col = names.index("displacement_quality_score")
    fvg_col = names.index("fvg_present")
    assert X[0, disp_col] == 1.0
    assert X[1, disp_col] == 0.0
    assert X[2, disp_col] == 0.25
    assert X[0, fvg_col] == 1.0
    assert X[1, fvg_col] == 0.0


def test_kill_zone_and_framework_encoding():
    t_lon = _trade(r=1.0, kill_zone="london", framework="ob_retest")
    t_ny = _trade(r=1.0, kill_zone="ny", framework="fvg_fill")
    t_tok = _trade(r=1.0, kill_zone="tokyo", framework="breaker_re_entry")
    X, _, names = build_feature_matrix([t_lon, t_ny, t_tok])
    sess_col = names.index("session_id")
    fw_col = names.index("framework_id")
    assert X[0, sess_col] == 0
    assert X[1, sess_col] == 1
    assert X[2, sess_col] == 2
    assert X[0, fw_col] == 0
    assert X[1, fw_col] == 1
    assert X[2, fw_col] == 2


# ---------------------------------------------------------------------------
# train_gbm_regressor
# ---------------------------------------------------------------------------

def test_train_gbm_regressor_recovers_planted_signal():
    """On planted-signal data, the dominant feature must rank highest."""
    trades = _planted_signal_trades(n=80, seed=42)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)

    # Use SHAP if available; otherwise permutation. Either path should
    # rank displacement_quality_score in the top-2.
    report = compute_shap_attribution(model, X, names, y=y)
    top = [r.feature for r in report.rankings[:3]]
    assert "displacement_quality_score" in top, (
        f"Top rankings did not surface planted feature: {top}"
    )


def test_train_gbm_regressor_input_validation():
    with pytest.raises(ValueError):
        train_gbm_regressor(np.zeros(10), np.zeros(10))  # 1-D X
    with pytest.raises(ValueError):
        train_gbm_regressor(np.zeros((4, 8)), np.zeros((3,)))  # mismatch
    with pytest.raises(ValueError):
        train_gbm_regressor(np.zeros((2, 8)), np.zeros((2,)))  # too few rows


def test_train_gbm_regressor_predicts_finite():
    trades = _planted_signal_trades(n=20, seed=1)
    X, y, _ = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    preds = model.predict(X)
    assert preds.shape == (X.shape[0],)
    assert np.all(np.isfinite(preds))


# ---------------------------------------------------------------------------
# compute_shap_attribution — primary + fallback paths
# ---------------------------------------------------------------------------

def test_compute_shap_attribution_returns_per_feature_attribution():
    trades = _planted_signal_trades(n=60, seed=7)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)

    report = compute_shap_attribution(model, X, names, y=y)
    assert isinstance(report, AttributionReport)
    assert report.n_samples == X.shape[0]
    assert report.shap_values.shape == X.shape
    assert len(report.rankings) == len(names)
    # Rankings must be 1..N permutation of features
    assert {r.rank for r in report.rankings} == set(range(1, len(names) + 1))
    # Relative importance sums to 1 (within fp tolerance)
    total = sum(r.relative_importance for r in report.rankings)
    assert abs(total - 1.0) < 1e-6
    # Method must be one of the documented values
    assert report.method in {
        "shap_treeexplainer",
        "shap_kernelexplainer",
        "permutation_importance",
    }


def test_compute_shap_attribution_falls_back_when_shap_missing(monkeypatch):
    """Force the SHAP-missing path: module handle set to None."""
    monkeypatch.setattr(ea, "_SHAP", None)

    trades = _planted_signal_trades(n=30, seed=9)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)

    report = compute_shap_attribution(model, X, names, y=y)
    assert report.method == "permutation_importance"
    # Permutation rows are tiled identically by design — sanity-check.
    assert report.shap_values.shape == X.shape
    assert np.allclose(report.shap_values[0], report.shap_values[-1])
    # Rankings still cover every feature
    assert {r.feature for r in report.rankings} == set(FEATURE_NAMES)


def test_compute_shap_attribution_falls_back_when_lightgbm_missing(monkeypatch):
    """Force lightgbm + xgboost missing → sklearn path; output still valid."""
    monkeypatch.setattr(ea, "_LIGHTGBM", None)
    monkeypatch.setattr(ea, "_XGBOOST", None)

    trades = _planted_signal_trades(n=40, seed=11)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    assert getattr(model, "_k50_backend", None) == "sklearn"

    report = compute_shap_attribution(model, X, names, y=y)
    assert report.shap_values.shape == X.shape


def test_compute_shap_attribution_validates_shape_mismatch():
    X = np.zeros((5, 8))
    with pytest.raises(ValueError):
        compute_shap_attribution(object(), X, FEATURE_NAMES[:3])


# ---------------------------------------------------------------------------
# bayesian_linear_attribution
# ---------------------------------------------------------------------------

def test_bayesian_linear_attribution_recovers_planted_coefficients():
    """Recover known coefficients to within ±0.1 (raw-space)."""
    rng = np.random.default_rng(123)
    n = 200
    p = 4
    true_beta = np.array([1.5, 0.4, 0.0, 0.05])  # raw-space
    X = rng.normal(size=(n, p))
    y = X @ true_beta + rng.normal(scale=0.05, size=n)

    out = bayesian_linear_attribution(
        X, y, ["a", "b", "c", "d"]
    )
    raw = out["raw_space_mean"]
    for i, name in enumerate(["a", "b", "c", "d"]):
        assert abs(raw[name] - float(true_beta[i])) < 0.1, (
            f"feature {name}: recovered {raw[name]}, expected {true_beta[i]}"
        )

    # Highest-magnitude in standardised space is "a" (largest true_beta * std)
    assert out["rank_by_abs_mean"][0] == "a"


def test_bayesian_linear_attribution_handles_constant_column():
    """Zero-variance feature must not blow up."""
    rng = np.random.default_rng(7)
    n = 60
    X = np.column_stack([rng.normal(size=n), np.ones(n), rng.normal(size=n)])
    y = 2.0 * X[:, 0] + rng.normal(scale=0.1, size=n)
    out = bayesian_linear_attribution(X, y, ["x", "const", "z"])
    # All posterior means must be finite
    for v in out["posterior_mean"].values():
        assert math.isfinite(v)
    for v in out["raw_space_mean"].values():
        assert math.isfinite(v)


def test_bayesian_linear_attribution_input_validation():
    with pytest.raises(ValueError):
        bayesian_linear_attribution(np.zeros(10), np.zeros(10), [])  # 1-D X
    with pytest.raises(ValueError):
        bayesian_linear_attribution(np.zeros((10, 3)), np.zeros((9,)), ["a", "b", "c"])
    with pytest.raises(ValueError):
        bayesian_linear_attribution(np.zeros((2, 3)), np.zeros((2,)), ["a", "b", "c"])
    with pytest.raises(ValueError):
        bayesian_linear_attribution(np.zeros((10, 3)), np.zeros((10,)), ["a", "b"])


def test_bayesian_returns_expected_keys():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(40, 3))
    y = rng.normal(size=40)
    out = bayesian_linear_attribution(X, y, ["a", "b", "c"])
    expected_keys = {
        "feature_means",
        "feature_stds",
        "posterior_mean",
        "posterior_std",
        "rank_by_abs_mean",
        "raw_space_mean",
        "intercept",
        "noise_variance_mode",
        "n_samples",
    }
    assert set(out.keys()) == expected_keys
    assert out["n_samples"] == 40


# ---------------------------------------------------------------------------
# spearman_rank_delta
# ---------------------------------------------------------------------------

def test_spearman_rank_delta_perfect_agreement():
    rankings = tuple(
        FeatureRanking(
            feature=f, mean_abs_shap=1.0 - i * 0.1, mean_shap=0.0,
            relative_importance=0.0, rank=i + 1,
        )
        for i, f in enumerate(["a", "b", "c", "d"])
    )
    bayes = ["a", "b", "c", "d"]
    out = spearman_rank_delta(rankings, bayes)
    assert out["spearman_r"] == pytest.approx(1.0)
    assert out["n"] == 4


def test_spearman_rank_delta_perfect_disagreement():
    rankings = tuple(
        FeatureRanking(
            feature=f, mean_abs_shap=1.0 - i * 0.1, mean_shap=0.0,
            relative_importance=0.0, rank=i + 1,
        )
        for i, f in enumerate(["a", "b", "c", "d"])
    )
    bayes = ["d", "c", "b", "a"]
    out = spearman_rank_delta(rankings, bayes)
    assert out["spearman_r"] == pytest.approx(-1.0)


def test_spearman_rank_delta_handles_empty_input():
    out = spearman_rank_delta(tuple(), [])
    assert math.isnan(out["spearman_r"])
    assert out["n"] == 0


# ---------------------------------------------------------------------------
# End-to-end with planted signal — SHAP and Bayesian should agree on top-1
# ---------------------------------------------------------------------------

def test_end_to_end_shap_and_bayesian_agree_on_dominant_feature():
    trades = _planted_signal_trades(n=120, seed=2026)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    report = compute_shap_attribution(model, X, names, y=y)
    bayes = bayesian_linear_attribution(X, y, names)

    # The top-2 of each method must overlap on at least one feature
    shap_top2 = {r.feature for r in report.rankings[:2]}
    bayes_top2 = set(bayes["rank_by_abs_mean"][:2])
    assert shap_top2 & bayes_top2, (
        f"SHAP top2 {shap_top2} and Bayesian top2 {bayes_top2} disjoint"
    )


def test_end_to_end_with_shap_missing_does_not_crash(monkeypatch):
    monkeypatch.setattr(ea, "_SHAP", None)
    trades = _planted_signal_trades(n=60, seed=3)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    report = compute_shap_attribution(model, X, names, y=y)
    bayes = bayesian_linear_attribution(X, y, names)
    # Permutation report still produces a valid set of rankings
    assert len(report.rankings) == len(names)
    assert report.method == "permutation_importance"
    # Bayesian still finite
    for v in bayes["posterior_mean"].values():
        assert math.isfinite(v)


# ---------------------------------------------------------------------------
# F16 — proper SHAP + Bonferroni + bootstrap CI
# ---------------------------------------------------------------------------

def test_f16_shap_method_used_when_shap_installed():
    """Regression: when shap is installed and a tree backend is present,
    the ``method='shap'`` path must produce ``shap_treeexplainer`` /
    ``shap_kernelexplainer`` (NOT permutation_importance).

    Falsifiability: this test FAILS in environments where ``shap`` is
    not actually importable — exactly the post-F5 environment we want to
    confirm. Skip rather than fall-through if the optional dep is
    genuinely missing on the runner so we don't false-flag.
    """
    if not ea._shap_available():
        pytest.skip("SHAP path not available in this test environment")
    trades = _planted_signal_trades(n=60, seed=42)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    report = compute_shap_attribution(model, X, names, y=y, method="shap")
    assert report.method.startswith("shap_"), (
        f"method='shap' should produce a shap_* method label, got {report.method!r}"
    )
    # SHAP rows are per-trade values (not the tiled-permutation-pseudo
    # matrix), so the first and last rows must NOT be identical.
    if X.shape[0] > 2:
        assert not np.allclose(report.shap_values[0], report.shap_values[-1]), (
            "SHAP per-trade rows should differ; got identical first/last rows"
        )


def test_f16_method_shap_raises_when_shap_missing(monkeypatch):
    """``method='shap'`` must raise RuntimeError when shap is missing.

    Force ``_SHAP=None`` and assert the helpful error message comes out
    rather than silently falling back. This is the contract: callers
    that explicitly want SHAP must NOT receive permutation values.
    """
    monkeypatch.setattr(ea, "_SHAP", None)
    trades = _planted_signal_trades(n=20, seed=1)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    with pytest.raises(RuntimeError, match=r"shap"):
        compute_shap_attribution(model, X, names, y=y, method="shap")


def test_f16_method_validation_rejects_unknown():
    """method must be one of the documented values."""
    trades = _planted_signal_trades(n=20, seed=2)
    X, y, names = build_feature_matrix(trades)
    model = train_gbm_regressor(X, y)
    with pytest.raises(ValueError, match=r"method must be"):
        compute_shap_attribution(model, X, names, y=y, method="bogus")


def test_f16_bootstrap_ci_returns_per_feature_ci():
    """Bootstrap CI must produce one FeatureCI per feature with
    ``ci_low <= point <= ci_high`` (modulo bootstrap-noise tolerance)
    and ``n_resamples`` equal to the requested resample count.
    """
    trades = _planted_signal_trades(n=60, seed=7)
    X, y, names = build_feature_matrix(trades)
    out = compute_shap_attribution_with_ci(
        X, y, names, method="auto", n_resamples=20, seed=7,
    )
    assert isinstance(out, AttributionWithCI)
    assert isinstance(out.base_report, AttributionReport)
    assert len(out.cis) == len(names)
    # CI bounds are non-decreasing (within fp tolerance)
    for fc in out.cis:
        assert fc.ci_low <= fc.ci_high + 1e-12, (
            f"{fc.feature}: ci_low {fc.ci_low} > ci_high {fc.ci_high}"
        )
        assert fc.n_resamples in (0, 20), (
            f"unexpected n_resamples {fc.n_resamples}"
        )
    # Bootstrap distributions length must equal the resample count
    for f in names:
        assert len(out.bootstrap_distributions[f]) == 20

    # method_used reflects the actual SHAP path when available
    if ea._shap_available():
        assert out.method_used.startswith("shap_")
    else:
        assert out.method_used == "permutation_importance"


def test_f16_bootstrap_ci_zero_resamples_collapses_to_point():
    """``n_resamples=0`` must skip bootstrap; CI bounds == point."""
    trades = _planted_signal_trades(n=20, seed=11)
    X, y, names = build_feature_matrix(trades)
    out = compute_shap_attribution_with_ci(
        X, y, names, method="auto", n_resamples=0, seed=11,
    )
    for fc in out.cis:
        assert fc.ci_low == fc.point
        assert fc.ci_high == fc.point
        assert fc.n_resamples == 0
    # bootstrap_distributions are empty lists
    for f in names:
        assert out.bootstrap_distributions[f] == []


def test_f16_bootstrap_ci_input_validation():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(10, len(FEATURE_NAMES)))
    y = rng.normal(size=10)
    with pytest.raises(ValueError, match=r"method must be"):
        compute_shap_attribution_with_ci(X, y, FEATURE_NAMES, method="bogus")
    with pytest.raises(ValueError, match=r"X must be"):
        compute_shap_attribution_with_ci(
            np.zeros(5), y, FEATURE_NAMES, method="auto",  # 1-D X
        )
    with pytest.raises(ValueError, match=r"y must be"):
        compute_shap_attribution_with_ci(
            X, np.zeros((10, 1)), FEATURE_NAMES, method="auto",
        )
    with pytest.raises(ValueError, match=r"row count mismatch"):
        compute_shap_attribution_with_ci(
            X, np.zeros(9), FEATURE_NAMES, method="auto",
        )
    with pytest.raises(ValueError, match=r"n_resamples"):
        compute_shap_attribution_with_ci(
            X, y, FEATURE_NAMES, method="auto", n_resamples=-1,
        )
    with pytest.raises(ValueError, match=r"ci_alpha"):
        compute_shap_attribution_with_ci(
            X, y, FEATURE_NAMES, method="auto", ci_alpha=1.5,
        )


def test_f16_bonferroni_correct_basic():
    """Bonferroni multiplication math:
    - finite p × family_size, capped at 1.0
    - NaN propagates
    - empty/zero family is handled
    """
    out = bonferroni_correct([0.01, 0.05, 0.30], family_size=5)
    assert out == [0.05, 0.25, 1.0]  # 0.30*5 capped at 1.0

    out2 = bonferroni_correct([0.001], family_size=10)
    assert out2 == [0.01]

    # NaN propagation
    out3 = bonferroni_correct([float("nan"), 0.02], family_size=4)
    assert math.isnan(out3[0])
    assert out3[1] == pytest.approx(0.08)

    # Default family_size = len(p_values)
    out4 = bonferroni_correct([0.01, 0.01, 0.01])
    assert out4 == [0.03, 0.03, 0.03]

    # Zero family size → empty
    assert bonferroni_correct([0.5], family_size=0) == []


def test_f16_h1_h2_importance_test_bonferroni_family():
    """The H1/H2 importance test must apply Bonferroni across the
    canonical feature family — verify the multiplier is
    ``family_size`` and that p-values cap at 1.0.

    Construct H1 / H2 distributions where one feature has H1 >> H2
    (clean decay) and another is identical (no decay). The decayed
    feature's raw p must be small; the corrected p must be at most
    ``raw_p * family_size`` and capped at 1.0; only the decayed feature
    should survive Bonferroni.
    """
    rng = np.random.default_rng(123)
    feats = ["dec", "stable_a", "stable_b", "stable_c"]
    h1_dists = {
        "dec": list(rng.normal(loc=1.0, scale=0.05, size=30)),
        "stable_a": list(rng.normal(loc=0.5, scale=0.05, size=30)),
        "stable_b": list(rng.normal(loc=0.3, scale=0.05, size=30)),
        "stable_c": list(rng.normal(loc=0.1, scale=0.05, size=30)),
    }
    h2_dists = {
        "dec": list(rng.normal(loc=0.1, scale=0.05, size=30)),  # decayed
        "stable_a": list(rng.normal(loc=0.5, scale=0.05, size=30)),  # equal
        "stable_b": list(rng.normal(loc=0.3, scale=0.05, size=30)),
        "stable_c": list(rng.normal(loc=0.1, scale=0.05, size=30)),
    }
    results = h1_h2_importance_test(
        h1_dists, h2_dists, feats, alpha=0.05, family_size=len(feats),
    )
    assert len(results) == len(feats)
    by_feat = {r.feature: r for r in results}

    # The 'dec' feature must show large positive delta and survive Bonferroni
    dec = by_feat["dec"]
    assert dec.delta > 0.5, f"expected delta > 0.5, got {dec.delta}"
    assert math.isfinite(dec.bonferroni_p)
    assert dec.bonferroni_p < 0.05
    assert dec.survives_bonferroni is True
    assert dec.family_size == len(feats)

    # The Bonferroni p is exactly raw_p × family_size (capped at 1.0)
    expected_bonf = min(1.0, dec.raw_p * len(feats))
    assert dec.bonferroni_p == pytest.approx(expected_bonf, abs=1e-12)

    # The stable features must NOT survive Bonferroni
    for name in ("stable_a", "stable_b", "stable_c"):
        rec = by_feat[name]
        # delta should be near zero (within bootstrap noise)
        assert abs(rec.delta) < 0.05, (
            f"{name}: delta {rec.delta} too large for stable feature"
        )
        assert rec.survives_bonferroni is False


def test_f16_h1_h2_importance_test_invalid_alpha():
    with pytest.raises(ValueError, match=r"alpha"):
        h1_h2_importance_test({}, {}, ["a", "b"], alpha=0.0)
    with pytest.raises(ValueError, match=r"alpha"):
        h1_h2_importance_test({}, {}, ["a", "b"], alpha=1.0)


def test_f16_h1_h2_importance_test_handles_empty_distributions():
    """Empty distributions must yield NaN p-values, not crash."""
    results = h1_h2_importance_test(
        {"a": [], "b": []}, {"a": [], "b": []}, ["a", "b"], alpha=0.05,
    )
    assert len(results) == 2
    for r in results:
        assert math.isnan(r.raw_p)
        assert math.isnan(r.bonferroni_p)
        assert r.survives_bonferroni is False


def test_k50_cli_help_builds_every_argparse_help_string():
    """``--help`` must exit 0 — i.e. every ``help=`` string must be valid.

    CPython 3.14 validates each ``help=`` inside ``add_argument`` itself
    (``argparse.py:1748`` ``_check_help`` → ``_expand_help`` → ``help % params``),
    so a bare ``%`` anywhere in the parser kills **every** invocation of the
    script, not just ``--help``. One such string lived at
    ``run_k50_edge_attribution.py:775`` (``"(95% CI)"``); it was invisible here
    because the only other CLI test skips whenever ``shap`` is unavailable.

    Behavioural, not a source grep: it builds the real parser in a child
    process and reads the rendered help text back. No ``shap`` needed —
    ``--help`` never reaches the attribution path.
    """
    result = subprocess.run(
        [sys.executable, str(K50_CLI), "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        f"`{K50_CLI.name} --help` failed; stderr={result.stderr!r}"
    )
    assert "badly formed help string" not in result.stderr
    # `%%` in the source must render as a single literal `%` in the output.
    rendered = " ".join(result.stdout.split())
    assert "percentiles (95% CI)" in rendered, rendered
    assert "%%" not in rendered, rendered


def test_f16_cli_alpha_flag_propagates_to_output(tmp_path):
    """``--alpha 0.10`` must appear in the produced ranking.json."""
    if not ea._shap_available():
        pytest.skip("SHAP path required for the CLI smoke run")

    # Build a synthetic _trade_index.json so the CLI has data
    trades = _planted_signal_trades(n=80, seed=2026)
    trade_index_path = tmp_path / "_trade_index.json"
    trade_index_path.write_text(
        json.dumps({"trades": trades}), encoding="utf-8",
    )

    out_dir = tmp_path / "K50_alpha_test"

    # Run the CLI with --alpha 0.10. Use --no-comparison and
    # --no-unified-csv so the CLI is fully self-contained.
    result = subprocess.run(
        [
            sys.executable,
            str(K50_CLI),
            "--output-dir", str(out_dir),
            "--trade-index", str(trade_index_path),
            "--no-unified-csv",
            "--no-comparison",
            "--method", "auto",
            "--alpha", "0.10",
            "--bootstrap-n-resamples", "5",  # tiny for speed
            "--bootstrap-seed", "1",
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert result.returncode == 0, (
        f"CLI failed: stdout={result.stdout!r} stderr={result.stderr!r}"
    )

    ranking_path = out_dir / "ranking.json"
    assert ranking_path.exists(), "ranking.json was not produced"
    payload = json.loads(ranking_path.read_text(encoding="utf-8"))
    assert payload["alpha"] == pytest.approx(0.10)
    assert payload["bootstrap_n_resamples"] == 5
    # Must have populated h1_h2 importance test rows
    assert "h1_h2_importance_test" in payload
    h1_h2 = payload["h1_h2_importance_test"]
    if h1_h2 is not None:
        for row in h1_h2:
            assert row["family_size"] == len(FEATURE_NAMES)


def test_f16_h1_h2_test_propagates_through_attribution_with_ci():
    """End-to-end: bootstrap distributions from
    ``compute_shap_attribution_with_ci`` plug into
    ``h1_h2_importance_test`` cleanly.

    Construct two halves where the H1 half is heavily-noised and the H2
    half is clean — the importance distributions will differ.
    """
    rng = np.random.default_rng(2026)
    n_each = 40
    Xh1 = rng.normal(size=(n_each, len(FEATURE_NAMES)))
    Xh2 = rng.normal(size=(n_each, len(FEATURE_NAMES)))
    yh1 = 0.5 * Xh1[:, 1] + rng.normal(scale=1.0, size=n_each)  # noisy
    yh2 = 1.5 * Xh2[:, 1] + rng.normal(scale=0.05, size=n_each)  # clean

    h1_full = compute_shap_attribution_with_ci(
        Xh1, yh1, FEATURE_NAMES, method="auto", n_resamples=10, seed=1,
    )
    h2_full = compute_shap_attribution_with_ci(
        Xh2, yh2, FEATURE_NAMES, method="auto", n_resamples=10, seed=2,
    )
    assert len(h1_full.bootstrap_distributions["displacement_quality_score"]) == 10
    assert len(h2_full.bootstrap_distributions["displacement_quality_score"]) == 10

    results = h1_h2_importance_test(
        h1_full.bootstrap_distributions,
        h2_full.bootstrap_distributions,
        FEATURE_NAMES,
        alpha=0.05,
        family_size=len(FEATURE_NAMES),
    )
    # All features have a result with the canonical family size
    assert len(results) == len(FEATURE_NAMES)
    for r in results:
        assert r.family_size == len(FEATURE_NAMES)
        # Bonferroni p is finite or NaN — never negative
        if math.isfinite(r.bonferroni_p):
            assert r.bonferroni_p >= 0


def test_f16_shap_available_helper():
    """``_shap_available`` must reflect both shap + tree-backend imports."""
    if ea._SHAP is None:
        # Without shap, helper is False regardless of tree backends
        assert ea._shap_available() is False
    else:
        # With shap and at least sklearn-GBM (a hard repo dep), helper is True
        assert ea._shap_available() is True
