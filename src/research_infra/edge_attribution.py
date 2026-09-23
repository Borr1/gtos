"""K50 — Causal Edge Attribution (SHAP / Bayesian).

Pure-Python research infra that quantifies how much realised R per filled
trade attributes to each engineered edge feature.

Strategic question
------------------
Of the realised R per trade, what fraction attributes to OB-zone advantage,
displacement quality, FVG presence, touch_count, framework choice, kill-zone
session, time-of-day, and regime? The output feeds K54's ML classifier
feature engineering.

Design notes
------------
*Realised R only* — every supervised target is per-trade realised R. We do
not feed walk-level proxies (per ``feedback_walk_level_evidence_not_predictive``).

*Optional deps tolerated* — the module degrades gracefully:

   - ``lightgbm`` → ``xgboost`` → ``sklearn.GradientBoostingRegressor``
     (sklearn is a hard dep already used elsewhere; the previous two
     accelerate fitting + ship native SHAP support).
   - ``shap`` → if absent, fall back to permutation importance (already
     in ``sklearn.inspection``).
   - Bayesian linear regression is **pure NumPy** (conjugate normal-inverse-
     gamma posterior); it never needs ``pymc`` / ``arviz``.

*No production code touched*. ``src.research_infra`` is additive only and
must not be imported from ``src/components/`` or ``src/safety/``.

*No API calls*. K50 is offline analysis.

F16 update — proper SHAP + Bonferroni + bootstrap CI
----------------------------------------------------
Mirrors the F5 update to K51 (``decayed_component_identifier.py``):

1. **SHAP path enforcement** — ``compute_shap_attribution`` accepts a
   ``method`` argument: ``"auto"`` (default; SHAP when available,
   permutation otherwise), ``"shap"`` (forces SHAP, raises if missing),
   ``"permutation"`` (forces the deterministic fallback).
2. **Bootstrap 95% CI** per feature — ``compute_shap_attribution_with_ci``
   resamples filled trades within the population and re-fits + re-explains,
   producing a 2.5/97.5 percentile band on each feature's mean |SHAP|.
3. **Bonferroni-corrected H1/H2 importance-delta test** —
   ``h1_h2_importance_test`` runs a one-sided Welch's t-test on the
   bootstrap distributions of H1 vs H2 mean |SHAP| per feature, then
   applies Bonferroni correction across the canonical-feature family.
   This is the same pattern used in
   ``decayed_component_identifier.identify_decay`` (K51 / F5).

References
----------
- Lundberg, S. M., & Lee, S.-I. (2017). A Unified Approach to Interpreting
  Model Predictions. NeurIPS.
- Murphy, K. P. (2012). Machine Learning: A Probabilistic Perspective.
  §7.6 Bayesian Linear Regression (conjugate normal-inverse-gamma prior).
- Press, W. H., Teukolsky, S. A., Vetterling, W. T., & Flannery, B. P.
  (1992). Numerical Recipes in C, §6.4 (incomplete beta function /
  Lentz's algorithm — used for Welch's t-test p-values without scipy).
"""

from __future__ import annotations

import math
import random
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Sequence

import numpy as np


# ---------------------------------------------------------------------------
# Optional dependency probing
# ---------------------------------------------------------------------------

def _try_import(name: str) -> Any | None:
    """Best-effort optional import returning the module or None."""
    try:
        return __import__(name)
    except Exception:  # ImportError, plus any odd loader-side failures
        return None


_LIGHTGBM = _try_import("lightgbm")
_XGBOOST = _try_import("xgboost")
_SHAP = _try_import("shap")


def _import_sklearn_gbm():
    """Hard requirement: sklearn must be available (used elsewhere in repo)."""
    from sklearn.ensemble import GradientBoostingRegressor  # noqa: WPS433

    return GradientBoostingRegressor


def _import_permutation_importance():
    from sklearn.inspection import permutation_importance  # noqa: WPS433

    return permutation_importance


def _has_sklearn_gbm() -> bool:
    """True iff sklearn's GradientBoostingRegressor importable."""
    try:
        _import_sklearn_gbm()
        return True
    except Exception:
        return False


def _shap_available() -> bool:
    """True iff the SHAP path can run (needs SHAP + a tree backend).

    Mirrors the K51 helper of the same name. The SHAP path needs both
    ``shap`` AND a tree backend (``lightgbm`` / ``xgboost`` / sklearn-GBM).
    """
    if _SHAP is None:
        return False
    return _LIGHTGBM is not None or _XGBOOST is not None or _has_sklearn_gbm()


# ---------------------------------------------------------------------------
# Public dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureRanking:
    """Per-feature aggregated attribution.

    Attributes
    ----------
    feature : str
        Feature name (matches column in feature matrix).
    mean_abs_shap : float
        Mean absolute SHAP value across all trades. Treated as the
        canonical "relative importance" magnitude.
    mean_shap : float
        Mean signed SHAP value. Sign indicates whether the feature on
        average raises (+) or lowers (-) realised R.
    relative_importance : float
        ``mean_abs_shap`` divided by the sum of all features'
        ``mean_abs_shap``. Always in [0, 1]; sums to 1 across features.
    rank : int
        1-based rank by ``mean_abs_shap`` descending.
    """

    feature: str
    mean_abs_shap: float
    mean_shap: float
    relative_importance: float
    rank: int


@dataclass(frozen=True)
class AttributionReport:
    """Output of :func:`compute_shap_attribution`.

    Attributes
    ----------
    feature_names : tuple[str, ...]
        In the same order as the feature matrix columns.
    shap_values : np.ndarray
        Shape ``(n_samples, n_features)``. SHAP values per trade per feature.
        If SHAP is unavailable, holds permutation-importance "pseudo-shap"
        rows (each row equals the permutation delta — coarse but the
        rankings are still valid).
    rankings : tuple[FeatureRanking, ...]
        Sorted descending by ``mean_abs_shap``.
    method : str
        One of ``"shap_treeexplainer"``, ``"shap_kernelexplainer"``,
        ``"permutation_importance"``.
    base_value : float
        Expected model output (used for SHAP additivity check). For the
        permutation fallback, the trained-set mean R.
    n_samples : int
        Rows in ``shap_values``.
    """

    feature_names: tuple[str, ...]
    shap_values: np.ndarray
    rankings: tuple[FeatureRanking, ...]
    method: str
    base_value: float
    n_samples: int


# ---------------------------------------------------------------------------
# Feature definitions
# ---------------------------------------------------------------------------

# Categorical encodings — kept stable so downstream artifacts are reproducible.
_FRAMEWORK_INDEX = {
    "ob_retest": 0,
    "fvg_fill": 1,
    "breaker_re_entry": 2,
    "none": -1,
}

_KILL_ZONE_INDEX = {
    "london": 0,
    "ny": 1,
    "tokyo": 2,
    "asia": 2,  # alias
    "asian": 2,  # alias
    "off": -1,
    "": -1,
}

_REGIME_INDEX = {
    "trend_up": 0,
    "trend_down": 1,
    "range_high_vol": 2,
    "range_low_vol": 3,
    "unknown": -1,
    "": -1,
}

# Realised-R extraction probes (mirrors decay_velocity)
_REALIZED_R_FIELDS = (
    "realized_r",
    "realized_R",
    "actual_r",
    "actual_R",
    "r_multiple",
    "rR",
)

_DISPLACEMENT_QUALITY_MAP = {
    "strong": 1.0,
    "medium": 0.5,
    "weak": 0.0,
    "ambiguous": 0.25,
    "": 0.0,
    None: 0.0,
}

# Canonical feature column order
FEATURE_NAMES: tuple[str, ...] = (
    "ob_retest_distance_atr",
    "displacement_quality_score",
    "fvg_present",
    "touch_count",
    "framework_id",
    "session_id",
    "hour_of_day_utc",
    "regime_tag",
)


# ---------------------------------------------------------------------------
# Pure helpers — feature extraction per trade
# ---------------------------------------------------------------------------

def _coerce_float(value: Any, default: float = 0.0) -> float:
    """Coerce to float; return default on failure / non-finite."""
    if value is None:
        return default
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(f):
        return default
    return f


def _coerce_int(value: Any, default: int = 0) -> int:
    """Coerce to int; return default on failure."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _extract_realized_r(trade: dict) -> float | None:
    """Find realised R on a trade dict; return None if absent."""
    for key in _REALIZED_R_FIELDS:
        if key in trade and trade[key] is not None:
            try:
                value = float(trade[key])
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                return value
    nested = trade.get("exit") if isinstance(trade.get("exit"), dict) else None
    if nested:
        for key in _REALIZED_R_FIELDS:
            if key in nested and nested[key] is not None:
                try:
                    value = float(nested[key])
                except (TypeError, ValueError):
                    continue
                if math.isfinite(value):
                    return value
    return None


def _extract_hour(trade: dict) -> int:
    """Best-effort UTC hour-of-day extraction.

    Tries (in order): ``candle_close_time``, ``candle_time``, ``timestamp``,
    nested under ``metadata``. Falls back to a kill-zone-implied hour if
    nothing else parses (london→8, ny→14, tokyo→1).
    """
    candidates = [
        trade.get("candle_close_time"),
        trade.get("candle_time"),
        trade.get("timestamp"),
        trade.get("entry_time"),
    ]
    if isinstance(trade.get("metadata"), dict):
        meta = trade["metadata"]
        candidates.extend([meta.get("candle_close_time"), meta.get("entry_time")])

    for raw in candidates:
        if not isinstance(raw, str) or not raw.strip():
            continue
        s = raw.strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).hour

    # Kill-zone implied fallback (centre of typical XAUUSD windows)
    kz = str(trade.get("kill_zone", "") or "").strip().lower()
    if kz == "london":
        return 8
    if kz == "ny":
        return 14
    if kz in ("tokyo", "asia", "asian"):
        return 1
    return -1


def _normalize_kill_zone(raw: Any) -> int:
    return _KILL_ZONE_INDEX.get(str(raw or "").strip().lower(), -1)


def _normalize_framework(raw: Any) -> int:
    return _FRAMEWORK_INDEX.get(str(raw or "").strip().lower(), -1)


def _normalize_regime(raw: Any) -> int:
    return _REGIME_INDEX.get(str(raw or "").strip().lower(), -1)


def _displacement_score(raw: Any) -> float:
    if raw is None:
        return 0.0
    key = str(raw).strip().lower()
    return _DISPLACEMENT_QUALITY_MAP.get(key, 0.0)


def _extract_ob_distance_atr(trade: dict) -> float:
    """Extract OB-retest distance normalised by ATR.

    Looks for ``ob_retest_distance_atr`` (preferred), then
    ``proximity_atr``, else derives from ``entry_price`` - ``ob_top``
    over ``atr``. Returns 0.0 when nothing is available.
    """
    for key in ("ob_retest_distance_atr", "proximity_atr", "distance_atr"):
        if key in trade and trade[key] is not None:
            return _coerce_float(trade[key], 0.0)

    entry = trade.get("entry_price")
    ob_top = trade.get("ob_top") or trade.get("ob_high")
    ob_bottom = trade.get("ob_bottom") or trade.get("ob_low")
    atr = trade.get("atr") or trade.get("atr_h1")
    if entry is None or atr in (None, 0):
        return 0.0
    try:
        e = float(entry)
        a = float(atr)
        if a <= 0 or not math.isfinite(a):
            return 0.0
        if ob_top is not None and ob_bottom is not None:
            mid = (float(ob_top) + float(ob_bottom)) / 2.0
            return (e - mid) / a
    except (TypeError, ValueError):
        return 0.0
    return 0.0


def _extract_fvg_present(trade: dict) -> int:
    """Boolean FVG-present flag (0/1)."""
    for key in ("fvg_present", "fvg_in_impulse", "has_fvg"):
        if key in trade and trade[key] is not None:
            try:
                return 1 if bool(trade[key]) else 0
            except Exception:
                continue
    if str(trade.get("framework", "")).strip().lower() == "fvg_fill":
        return 1
    return 0


def _extract_touch_count(trade: dict) -> int:
    """Touch count of the entered OB."""
    for key in ("touch_count", "ob_touch_count", "touches"):
        if key in trade and trade[key] is not None:
            return _coerce_int(trade[key], 0)
    return 0


def _trade_to_features(trade: dict) -> np.ndarray:
    """Deterministic feature vector for one trade.

    Returns a length-len(FEATURE_NAMES) ``np.float64`` array in
    ``FEATURE_NAMES`` order. Missing values become 0.0 / -1 for
    categoricals (handled as a separate "unknown" bucket by the GBM).
    """
    return np.asarray(
        [
            _extract_ob_distance_atr(trade),
            _displacement_score(trade.get("displacement_quality")),
            float(_extract_fvg_present(trade)),
            float(_extract_touch_count(trade)),
            float(_normalize_framework(trade.get("framework"))),
            float(_normalize_kill_zone(trade.get("kill_zone"))),
            float(_extract_hour(trade)),
            float(_normalize_regime(trade.get("regime_tag") or trade.get("regime"))),
        ],
        dtype=np.float64,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_feature_matrix(
    trades: list[dict],
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Build (X, y, feature_names) from a list of filled trade dicts.

    Drops trades that have no realised R (unfilled CANDIDATEs).

    Parameters
    ----------
    trades : list of dict
        Heterogeneous trade dicts from ``_trade_index.json`` /
        ``trades_unified.csv`` rows / ``v1.1`` instrumentation records.

    Returns
    -------
    X : np.ndarray, shape (n, n_features), float64
    y : np.ndarray, shape (n,), float64 — realised R per trade
    feature_names : list[str] — copy of ``FEATURE_NAMES``
    """
    if not isinstance(trades, list):
        raise TypeError(f"trades must be a list, got {type(trades).__name__}")

    rows: list[np.ndarray] = []
    targets: list[float] = []
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        r = _extract_realized_r(trade)
        if r is None:
            continue
        rows.append(_trade_to_features(trade))
        targets.append(float(r))

    if not rows:
        # Empty matrix with the canonical schema preserved.
        return (
            np.zeros((0, len(FEATURE_NAMES)), dtype=np.float64),
            np.zeros((0,), dtype=np.float64),
            list(FEATURE_NAMES),
        )

    return (
        np.vstack(rows),
        np.asarray(targets, dtype=np.float64),
        list(FEATURE_NAMES),
    )


def train_gbm_regressor(X: np.ndarray, y: np.ndarray, *, random_state: int = 0) -> Any:
    """Fit a gradient-boosting regressor with realised R as the target.

    Backend preference: ``lightgbm`` → ``xgboost`` →
    ``sklearn.GradientBoostingRegressor``. Hyperparameters are conservative
    (small, shallow ensemble) — K50's job is feature attribution, not
    state-of-the-art prediction; over-fitting blows up SHAP magnitudes.

    The returned object is duck-typed: any backend supports ``predict(X)``.
    """
    if not isinstance(X, np.ndarray) or X.ndim != 2:
        raise ValueError("X must be a 2-D numpy array")
    if not isinstance(y, np.ndarray) or y.ndim != 1:
        raise ValueError("y must be a 1-D numpy array")
    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"row count mismatch: X has {X.shape[0]}, y has {y.shape[0]}",
        )
    if X.shape[0] < 4:
        raise ValueError(
            f"need at least 4 samples to fit a GBM, got {X.shape[0]}",
        )

    if _LIGHTGBM is not None:
        # LightGBM with conservative defaults
        model = _LIGHTGBM.LGBMRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            min_child_samples=2,
            random_state=random_state,
            verbosity=-1,
        )
        model.fit(X, y)
        # Tag backend so downstream code can branch.
        model._k50_backend = "lightgbm"
        return model

    if _XGBOOST is not None:
        model = _XGBOOST.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.05,
            random_state=random_state,
            verbosity=0,
            objective="reg:squarederror",
        )
        model.fit(X, y)
        model._k50_backend = "xgboost"
        return model

    GradientBoostingRegressor = _import_sklearn_gbm()
    model = GradientBoostingRegressor(
        n_estimators=100,
        max_depth=3,
        learning_rate=0.05,
        random_state=random_state,
    )
    model.fit(X, y)
    model._k50_backend = "sklearn"
    return model


def _shap_values_for_model(model: Any, X: np.ndarray) -> tuple[np.ndarray, float, str]:
    """Best-effort SHAP value computation. Returns (values, base_value, method).

    Falls through gracefully if SHAP is unavailable or the explainer fails.
    """
    if _SHAP is None:
        raise RuntimeError("shap not installed")

    backend = getattr(model, "_k50_backend", "sklearn")
    # TreeExplainer supports lightgbm / xgboost / sklearn-GBM (Booster)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            explainer = _SHAP.TreeExplainer(model)
            shap_vals = explainer.shap_values(X)
        if isinstance(shap_vals, list):  # binary classification edge case
            shap_vals = shap_vals[0]
        base = explainer.expected_value
        if isinstance(base, (list, tuple, np.ndarray)):
            base_val = float(np.asarray(base).flatten()[0])
        else:
            base_val = float(base)
        return np.asarray(shap_vals, dtype=np.float64), base_val, "shap_treeexplainer"
    except Exception:
        # Fall back to KernelExplainer with a small background sample.
        try:
            background = X[: min(50, len(X))]

            def predict_fn(z: np.ndarray) -> np.ndarray:
                return np.asarray(model.predict(z))

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                explainer = _SHAP.KernelExplainer(predict_fn, background)
                shap_vals = explainer.shap_values(X, nsamples=50, silent=True)
            if isinstance(shap_vals, list):
                shap_vals = shap_vals[0]
            base = explainer.expected_value
            base_val = (
                float(np.asarray(base).flatten()[0])
                if isinstance(base, (list, tuple, np.ndarray))
                else float(base)
            )
            return np.asarray(shap_vals, dtype=np.float64), base_val, "shap_kernelexplainer"
        except Exception as exc:
            raise RuntimeError(f"SHAP fallback also failed: {exc}") from exc


def _permutation_attribution(
    model: Any,
    X: np.ndarray,
    y: np.ndarray | None,
    feature_names: Sequence[str],
) -> tuple[np.ndarray, float, str]:
    """Permutation-importance fallback when SHAP is unavailable.

    Returns a pseudo-SHAP matrix of shape (n, n_features) where every row
    is identical and equal to the per-feature permutation importance (mean
    R-squared decrease). This preserves the public matrix shape without
    fabricating per-trade variation. ``mean_abs_shap`` aggregates from
    these rows correctly (== abs of the permutation importance).
    """
    permutation_importance = _import_permutation_importance()
    base_pred = float(np.mean(model.predict(X)))

    if y is None or len(y) != len(X):
        # Without targets we cannot run R^2 permutation; return a zero
        # matrix and warn. Callers should always pass y.
        warnings.warn(
            "permutation fallback received no y — returning zeros",
            stacklevel=2,
        )
        return (
            np.zeros((len(X), len(feature_names)), dtype=np.float64),
            base_pred,
            "permutation_importance",
        )

    result = permutation_importance(
        model,
        X,
        y,
        n_repeats=10,
        random_state=0,
        scoring="r2",
    )
    importances = np.asarray(result.importances_mean, dtype=np.float64)

    # Stamp every row with the same permutation vector so the public
    # matrix shape (n_samples, n_features) is preserved.
    n = X.shape[0]
    pseudo = np.tile(importances, (n, 1))
    return pseudo, base_pred, "permutation_importance"


def compute_shap_attribution(
    model: Any,
    X: np.ndarray,
    feature_names: Sequence[str],
    *,
    y: np.ndarray | None = None,
    method: str = "auto",
) -> AttributionReport:
    """Compute per-feature attribution for a fitted GBM.

    Uses SHAP TreeExplainer / KernelExplainer when ``shap`` is importable;
    otherwise falls back to scikit-learn permutation importance. The
    fallback path needs ``y`` to score; SHAP path does not.

    Parameters
    ----------
    model : duck-typed
        Output of :func:`train_gbm_regressor`.
    X : np.ndarray
        Same matrix the model was fitted on (or a held-out slice).
    feature_names : sequence of str
    y : np.ndarray, optional
        Realised R targets — required only for the permutation fallback.
    method : {"auto", "shap", "permutation"}, default "auto"
        ``"auto"`` (default) → SHAP when available, permutation
        otherwise. ``"shap"`` forces SHAP and raises ``RuntimeError`` if
        ``shap`` is missing. ``"permutation"`` forces the deterministic
        fallback (used in tests + low-dep environments).

    Returns
    -------
    AttributionReport
    """
    if method not in {"auto", "shap", "permutation"}:
        raise ValueError(
            f"method must be one of 'auto', 'shap', 'permutation'; got {method!r}",
        )
    if not isinstance(X, np.ndarray) or X.ndim != 2:
        raise ValueError("X must be a 2-D numpy array")
    feat_names = tuple(feature_names)
    if X.shape[1] != len(feat_names):
        raise ValueError(
            f"feature count mismatch: X has {X.shape[1]}, names has {len(feat_names)}",
        )

    if method == "shap":
        if _SHAP is None:
            raise RuntimeError(
                "method='shap' requested but the shap library is not "
                "installed. Install with `pip install \"shap>=0.42\" "
                "\"lightgbm>=4.0\"` or use method='auto' / 'permutation'.",
            )
        shap_vals, base_val, method_used = _shap_values_for_model(model, X)
    elif method == "permutation":
        shap_vals, base_val, method_used = _permutation_attribution(
            model, X, y, feat_names,
        )
    elif _SHAP is not None:
        try:
            shap_vals, base_val, method_used = _shap_values_for_model(model, X)
        except RuntimeError:
            shap_vals, base_val, method_used = _permutation_attribution(
                model, X, y, feat_names,
            )
    else:
        shap_vals, base_val, method_used = _permutation_attribution(
            model, X, y, feat_names,
        )

    # Aggregate
    mean_abs = np.mean(np.abs(shap_vals), axis=0)
    mean_signed = np.mean(shap_vals, axis=0)
    total_abs = float(np.sum(mean_abs)) if np.sum(mean_abs) > 0 else 1.0

    pairs = list(enumerate(zip(mean_abs, mean_signed)))
    # Sort descending by mean_abs
    pairs.sort(key=lambda kv: -float(kv[1][0]))
    rankings: list[FeatureRanking] = []
    for rank_idx, (col, (abs_v, signed_v)) in enumerate(pairs, start=1):
        rankings.append(
            FeatureRanking(
                feature=feat_names[col],
                mean_abs_shap=float(abs_v),
                mean_shap=float(signed_v),
                relative_importance=float(abs_v) / total_abs,
                rank=rank_idx,
            )
        )

    return AttributionReport(
        feature_names=feat_names,
        shap_values=shap_vals,
        rankings=tuple(rankings),
        method=method_used,
        base_value=float(base_val),
        n_samples=int(X.shape[0]),
    )


# ---------------------------------------------------------------------------
# Bonferroni correction (mirror of decayed_component_identifier.bonferroni_correct)
# ---------------------------------------------------------------------------

def bonferroni_correct(
    p_values: list[float], family_size: int | None = None,
) -> list[float]:
    """Apply Bonferroni correction across a family of raw p-values.

    Returns ``[min(1.0, p * family_size)]`` with ``NaN`` propagated
    unchanged. ``family_size`` defaults to ``len(p_values)`` (consistent
    with the K52 ``bonferroni_survival.bonferroni_correct`` and the
    K51 ``decayed_component_identifier.bonferroni_correct``).

    Parameters
    ----------
    p_values : list of float
        Raw uncorrected p-values. ``NaN`` entries propagate.
    family_size : int, optional
        Bonferroni denominator. ``None`` ⇒ ``len(p_values)``.

    Returns
    -------
    list[float]
        Corrected p-values, same length and order as input. Each entry
        is ``min(1.0, p_raw × family_size)`` (or ``NaN`` if input was).
    """
    n = family_size if family_size is not None else len(p_values)
    if n <= 0:
        return []
    out: list[float] = []
    for p in p_values:
        if p is None or (isinstance(p, float) and math.isnan(p)):
            out.append(float("nan"))
            continue
        adj = min(1.0, float(p) * n)
        out.append(adj)
    return out


# ---------------------------------------------------------------------------
# Welch's t-test p-values (pure-Python; same closed form as K51)
# ---------------------------------------------------------------------------

def _welch_t_p_one_sided(h1: list[float], h2: list[float]) -> float:
    """One-sided Welch's t-test p-value for ``H0: mean(H1) ≤ mean(H2)``.

    A small p-value means the mean of ``h1`` is significantly LARGER
    than the mean of ``h2`` (i.e. evidence the H1 attribution exceeds
    the H2 attribution — used for the K50 H1/H2 importance-delta test).

    Returns ``NaN`` when the test is undefined (n < 2 in either half,
    zero variance in both halves with equal means).

    Mirrors the implementation in
    ``decayed_component_identifier._welch_t_p_one_sided`` so K50 and
    K51 share the same numerical conventions.
    """
    n1 = len(h1)
    n2 = len(h2)
    if n1 < 2 or n2 < 2:
        return float("nan")
    m1 = sum(h1) / n1
    m2 = sum(h2) / n2
    v1 = sum((x - m1) ** 2 for x in h1) / (n1 - 1)
    v2 = sum((x - m2) ** 2 for x in h2) / (n2 - 1)
    if v1 == 0.0 and v2 == 0.0:
        if m1 > m2:
            return 0.0
        if m1 < m2:
            return 1.0
        return float("nan")
    se = math.sqrt(v1 / n1 + v2 / n2)
    if se == 0.0:
        return float("nan")
    t = (m1 - m2) / se
    num = (v1 / n1 + v2 / n2) ** 2
    denom = (v1 ** 2) / ((n1 ** 2) * (n1 - 1)) + (v2 ** 2) / ((n2 ** 2) * (n2 - 1))
    if denom == 0.0:
        return float("nan")
    df = num / denom
    return _student_t_sf(t, df)


def _student_t_sf(t: float, df: float) -> float:
    """One-sided Student-t survival function ``P(T > t)``.

    Pure-Python via the regularised incomplete beta function (same
    expansion as ``decayed_component_identifier._student_t_sf``).
    """
    if not math.isfinite(t) or not math.isfinite(df) or df <= 0:
        return float("nan")
    if t == 0:
        return 0.5
    if t > 0:
        x = df / (df + t * t)
        return 0.5 * _betainc_regularised(df / 2.0, 0.5, x)
    return 1.0 - _student_t_sf(-t, df)


def _betainc_regularised(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function ``I_x(a, b)``.

    Lentz continued-fraction expansion (Press et al. 1992 §6.4).
    Sufficient accuracy for p-values down to ~1e-10. Mirror of K51's
    helper so the two modules cannot drift.
    """
    if not (0.0 <= x <= 1.0):
        return float("nan")
    if x == 0.0:
        return 0.0
    if x == 1.0:
        return 1.0
    log_bt = (
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log(1.0 - x)
    )
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(log_bt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(log_bt) * _betacf(b, a, 1.0 - x) / b


def _betacf(
    a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-16,
) -> float:
    """Continued-fraction component of the incomplete beta function."""
    qab = a + b
    qap = a + 1.0
    qam = a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-300:
        d = 1e-300
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-300:
            d = 1e-300
        c = 1.0 + aa / c
        if abs(c) < 1e-300:
            c = 1e-300
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    return h


def _percentile(sorted_values: list[float], q: float) -> float:
    """Linear-interpolated percentile (q in [0, 1]). Input pre-sorted."""
    if not sorted_values:
        return 0.0
    if q <= 0:
        return sorted_values[0]
    if q >= 1:
        return sorted_values[-1]
    n = len(sorted_values)
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return sorted_values[lo]
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


# ---------------------------------------------------------------------------
# Bootstrap CI on per-feature mean |SHAP| importance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureCI:
    """Bootstrap percentile CI on a single feature's mean |SHAP|.

    Attributes
    ----------
    feature : str
    point : float
        Point estimate (mean |SHAP| from the original fit).
    ci_low, ci_high : float
        Lower/upper percentiles of the bootstrap distribution.
    n_resamples : int
        Bootstrap resamples used; ``0`` means CI bounds are equal to the
        point estimate (bootstrap was skipped).
    """

    feature: str
    point: float
    ci_low: float
    ci_high: float
    n_resamples: int


@dataclass(frozen=True)
class AttributionWithCI:
    """``compute_shap_attribution_with_ci`` output.

    Attributes
    ----------
    base_report : AttributionReport
        The point-estimate attribution (same shape as the F5-pre output).
    cis : tuple[FeatureCI, ...]
        One bootstrap CI per feature, in ``feature_names`` order.
    bootstrap_distributions : dict[str, list[float]]
        Per-feature bootstrap distribution of mean |SHAP| (length =
        ``n_resamples``). Empty when ``n_resamples == 0``.
    method_used : str
        ``"shap_treeexplainer"`` / ``"shap_kernelexplainer"`` /
        ``"permutation_importance"`` (matches ``base_report.method``).
    """

    base_report: AttributionReport
    cis: tuple["FeatureCI", ...]
    bootstrap_distributions: dict[str, list[float]]
    method_used: str


def compute_shap_attribution_with_ci(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: Sequence[str],
    *,
    method: str = "auto",
    n_resamples: int = 100,
    seed: int = 0,
    ci_alpha: float = 0.05,
) -> AttributionWithCI:
    """Mean |SHAP| per feature + bootstrap percentile CI.

    Resamples ``(X_row, y_row)`` pairs with replacement, refits a
    gradient-boosting regressor, re-explains, and aggregates per-feature
    mean |SHAP|. The 2.5/97.5 percentiles of the resulting per-feature
    distribution become the CI bounds.

    The fit/explain backend obeys the same ``method`` contract as
    :func:`compute_shap_attribution`. F16 ships with default
    ``n_resamples=100`` to match K51 (F5).

    Parameters
    ----------
    X : np.ndarray, shape (n, p)
    y : np.ndarray, shape (n,)
    feature_names : sequence of str
        Length p.
    method : {"auto", "shap", "permutation"}
        See :func:`compute_shap_attribution`.
    n_resamples : int, default 100
        Number of bootstrap resamples. ``0`` skips the bootstrap; CI
        bounds equal the point estimate.
    seed : int, default 0
        Reproducibility seed.
    ci_alpha : float, default 0.05
        Two-sided CI level. ``0.05`` → 2.5/97.5 percentiles (95% CI).

    Returns
    -------
    AttributionWithCI
    """
    if method not in {"auto", "shap", "permutation"}:
        raise ValueError(
            f"method must be one of 'auto', 'shap', 'permutation'; got {method!r}",
        )
    if not isinstance(X, np.ndarray) or X.ndim != 2:
        raise ValueError("X must be a 2-D numpy array")
    if not isinstance(y, np.ndarray) or y.ndim != 1:
        raise ValueError("y must be a 1-D numpy array")
    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"row count mismatch: X has {X.shape[0]}, y has {y.shape[0]}",
        )
    if n_resamples < 0:
        raise ValueError(f"n_resamples must be >= 0, got {n_resamples}")
    if not 0 < ci_alpha < 1:
        raise ValueError(f"ci_alpha must be in (0, 1), got {ci_alpha}")

    feat_names = tuple(feature_names)

    # Point estimate
    point_model = train_gbm_regressor(X, y, random_state=seed)
    base_report = compute_shap_attribution(
        point_model, X, feat_names, y=y, method=method,
    )
    point_imps = {r.feature: r.mean_abs_shap for r in base_report.rankings}

    if n_resamples == 0 or X.shape[0] < 4:
        cis = tuple(
            FeatureCI(
                feature=f,
                point=point_imps[f],
                ci_low=point_imps[f],
                ci_high=point_imps[f],
                n_resamples=0,
            )
            for f in feat_names
        )
        return AttributionWithCI(
            base_report=base_report,
            cis=cis,
            bootstrap_distributions={f: [] for f in feat_names},
            method_used=base_report.method,
        )

    rng = random.Random(seed)
    boot: dict[str, list[float]] = {f: [] for f in feat_names}
    n_rows = X.shape[0]
    for b in range(n_resamples):
        idx = [rng.randrange(0, n_rows) for _ in range(n_rows)]
        X_b = X[idx]
        y_b = y[idx]
        # Skip resamples with constant y — model is degenerate
        if float(np.std(y_b)) == 0.0:
            for f in feat_names:
                boot[f].append(0.0)
            continue
        try:
            model_b = train_gbm_regressor(X_b, y_b, random_state=seed + b + 1)
            report_b = compute_shap_attribution(
                model_b, X_b, feat_names, y=y_b, method=method,
            )
        except Exception:
            for f in feat_names:
                boot[f].append(0.0)
            continue
        for r in report_b.rankings:
            boot[r.feature].append(float(r.mean_abs_shap))

    lo_q = ci_alpha / 2
    hi_q = 1 - ci_alpha / 2
    cis_list: list[FeatureCI] = []
    for f in feat_names:
        sorted_b = sorted(boot[f])
        if not sorted_b:
            cis_list.append(
                FeatureCI(
                    feature=f,
                    point=point_imps[f],
                    ci_low=point_imps[f],
                    ci_high=point_imps[f],
                    n_resamples=0,
                )
            )
            continue
        cis_list.append(
            FeatureCI(
                feature=f,
                point=point_imps[f],
                ci_low=_percentile(sorted_b, lo_q),
                ci_high=_percentile(sorted_b, hi_q),
                n_resamples=len(sorted_b),
            )
        )

    return AttributionWithCI(
        base_report=base_report,
        cis=tuple(cis_list),
        bootstrap_distributions={f: list(boot[f]) for f in feat_names},
        method_used=base_report.method,
    )


# ---------------------------------------------------------------------------
# Bonferroni-corrected H1/H2 importance-delta test
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureImportanceTest:
    """One row of :func:`h1_h2_importance_test` output.

    Attributes
    ----------
    feature : str
    h1_importance, h2_importance : float
        Point estimates (mean |SHAP|) on the H1 and H2 halves.
    delta : float
        ``h1_importance - h2_importance``.
    raw_p : float
        One-sided Welch's t-test p-value computed on the H1 vs H2
        bootstrap distributions (``H0: mean(H1) ≤ mean(H2)``).
    bonferroni_p : float
        ``min(1.0, raw_p × family_size)``. ``NaN`` propagates from
        ``raw_p`` (fewer than 2 bootstrap samples in either half →
        undefined).
    survives_bonferroni : bool
        ``bonferroni_p < alpha``.
    family_size : int
        Number of features in the Bonferroni family (informational).
    """

    feature: str
    h1_importance: float
    h2_importance: float
    delta: float
    raw_p: float
    bonferroni_p: float
    survives_bonferroni: bool
    family_size: int


def h1_h2_importance_test(
    h1_distributions: dict[str, list[float]],
    h2_distributions: dict[str, list[float]],
    feature_names: Sequence[str],
    *,
    alpha: float = 0.05,
    family_size: int | None = None,
) -> tuple[FeatureImportanceTest, ...]:
    """Test per-feature H1 vs H2 mean-importance via Welch's t.

    The two distributions are typically the per-bootstrap-resample mean
    |SHAP| traces from :func:`compute_shap_attribution_with_ci` run
    separately on the H1 / H2 sub-populations. Each feature's H1 and H2
    distributions are compared with a one-sided Welch's t-test, then
    p-values are Bonferroni-corrected across the feature family.

    Parameters
    ----------
    h1_distributions, h2_distributions : dict[str, list[float]]
        Per-feature bootstrap distributions of mean |SHAP|. Both must
        cover the same feature set (silently ignores extras).
    feature_names : sequence of str
        Iteration order. Defines the Bonferroni family and ranking.
    alpha : float, default 0.05
        Significance threshold post-Bonferroni.
    family_size : int, optional
        Bonferroni denominator. ``None`` ⇒ ``len(feature_names)``.

    Returns
    -------
    tuple of FeatureImportanceTest
    """
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    feats = list(feature_names)
    fam = family_size if family_size is not None else len(feats)
    if fam <= 0:
        return tuple()

    raw_records: list[tuple[str, float, float, float, float]] = []
    raw_p_values: list[float] = []
    for feat in feats:
        h1 = list(h1_distributions.get(feat, []) or [])
        h2 = list(h2_distributions.get(feat, []) or [])
        h1_mean = sum(h1) / len(h1) if h1 else 0.0
        h2_mean = sum(h2) / len(h2) if h2 else 0.0
        delta = h1_mean - h2_mean
        raw_p = _welch_t_p_one_sided(h1, h2)
        raw_records.append((feat, h1_mean, h2_mean, delta, raw_p))
        raw_p_values.append(raw_p)

    bonf_p_values = bonferroni_correct(raw_p_values, family_size=fam)

    out: list[FeatureImportanceTest] = []
    for (feat, h1_mean, h2_mean, delta, raw_p), bonf_p in zip(
        raw_records, bonf_p_values,
    ):
        survives = (
            isinstance(bonf_p, float)
            and math.isfinite(bonf_p)
            and bonf_p < alpha
        )
        out.append(
            FeatureImportanceTest(
                feature=feat,
                h1_importance=h1_mean,
                h2_importance=h2_mean,
                delta=delta,
                raw_p=raw_p,
                bonferroni_p=bonf_p,
                survives_bonferroni=survives,
                family_size=fam,
            )
        )
    return tuple(out)


# ---------------------------------------------------------------------------
# Bayesian linear regression — pure NumPy, conjugate normal-inverse-gamma
# ---------------------------------------------------------------------------

def bayesian_linear_attribution(
    X: np.ndarray,
    y: np.ndarray,
    feature_names: Sequence[str],
    *,
    prior_precision: float = 1e-3,
    prior_a: float = 1e-3,
    prior_b: float = 1e-3,
) -> dict:
    """Bayesian linear regression with weak conjugate priors.

    Model
    -----
    .. math::
        y = X^* \\beta + \\epsilon, \\quad \\epsilon \\sim N(0, \\sigma^2)

    Prior:  ``beta | sigma^2 ~ N(0, sigma^2 / prior_precision * I)``
            ``sigma^2 ~ InvGamma(prior_a, prior_b)``

    The conjugate posterior on ``(beta, sigma^2)`` is closed-form
    (Murphy 2012 §7.6.3). We standardise X (mean 0, unit std) before
    fitting so each posterior coefficient is comparable across
    features. An intercept column is appended; its posterior is
    returned as ``intercept`` rather than as a per-feature row.

    Parameters
    ----------
    X : np.ndarray, shape (n, p)
    y : np.ndarray, shape (n,)
    feature_names : sequence of str, length p
    prior_precision : float
        Diagonal of prior precision on standardised coefficients. Smaller
        = weaker prior. Default 1e-3 yields a near-flat prior.
    prior_a, prior_b : float
        Shape / scale on the inverse-gamma noise prior. Defaults yield a
        Jeffreys-style reference prior.

    Returns
    -------
    dict
        ``{
            "feature_means": dict[str, float],
            "feature_stds":  dict[str, float],
            "posterior_mean": dict[str, float],   # standardised-space coeffs
            "posterior_std":  dict[str, float],
            "rank_by_abs_mean": list[str],         # descending |posterior_mean|
            "raw_space_mean": dict[str, float],    # back-transformed to raw X scale
            "intercept": float,
            "noise_variance_mode": float,
            "n_samples": int,
        }``
    """
    if not isinstance(X, np.ndarray) or X.ndim != 2:
        raise ValueError("X must be a 2-D numpy array")
    if not isinstance(y, np.ndarray) or y.ndim != 1:
        raise ValueError("y must be a 1-D numpy array")
    if X.shape[0] != y.shape[0]:
        raise ValueError("row count mismatch")
    if X.shape[0] < 4:
        raise ValueError(f"need at least 4 samples, got {X.shape[0]}")

    feat_names = list(feature_names)
    if X.shape[1] != len(feat_names):
        raise ValueError("feature count mismatch")

    # Standardise X (per column)
    means = X.mean(axis=0)
    stds = X.std(axis=0)
    safe_stds = np.where(stds > 0, stds, 1.0)
    X_std = (X - means) / safe_stds

    # Append intercept column (constant 1) — never standardised.
    X_aug = np.hstack([X_std, np.ones((X_std.shape[0], 1))])
    p_aug = X_aug.shape[1]

    # Prior precision diagonal: small for slope columns, near-zero for intercept.
    Lambda0 = np.eye(p_aug) * prior_precision
    Lambda0[-1, -1] = 1e-6  # weakly-informative on intercept too

    XtX = X_aug.T @ X_aug
    Xty = X_aug.T @ y

    LambdaN = Lambda0 + XtX
    # Solve LambdaN @ mu = Xty for the posterior mean.
    posterior_mean_aug = np.linalg.solve(LambdaN, Xty)

    # Posterior on sigma^2: InvGamma(aN, bN)
    aN = prior_a + 0.5 * X_aug.shape[0]
    residual = y - X_aug @ posterior_mean_aug
    quad = 0.5 * (
        residual @ residual
        + posterior_mean_aug @ Lambda0 @ posterior_mean_aug
    )
    bN = prior_b + float(quad)
    # Mode of InvGamma(a, b) is b / (a + 1). Always positive when bN > 0.
    sigma2_mode = bN / (aN + 1.0) if aN > -1.0 else float("nan")

    # Posterior covariance on beta: sigma2_mode * inv(LambdaN)
    cov = sigma2_mode * np.linalg.inv(LambdaN)
    posterior_std_aug = np.sqrt(np.maximum(np.diag(cov), 0.0))

    posterior_mean = posterior_mean_aug[:-1]
    posterior_std = posterior_std_aug[:-1]
    intercept = float(posterior_mean_aug[-1])

    # Back-transform standardised coefficients to raw-X-space coefficients
    # so users can interpret "1 unit of feature X moves R by Y".
    raw_space_mean = posterior_mean / safe_stds

    feat_means = {n: float(means[i]) for i, n in enumerate(feat_names)}
    feat_stds = {n: float(stds[i]) for i, n in enumerate(feat_names)}
    posterior_mean_d = {n: float(posterior_mean[i]) for i, n in enumerate(feat_names)}
    posterior_std_d = {n: float(posterior_std[i]) for i, n in enumerate(feat_names)}
    raw_space_d = {n: float(raw_space_mean[i]) for i, n in enumerate(feat_names)}
    rank = sorted(feat_names, key=lambda n: -abs(posterior_mean_d[n]))

    return {
        "feature_means": feat_means,
        "feature_stds": feat_stds,
        "posterior_mean": posterior_mean_d,
        "posterior_std": posterior_std_d,
        "rank_by_abs_mean": rank,
        "raw_space_mean": raw_space_d,
        "intercept": intercept,
        "noise_variance_mode": float(sigma2_mode),
        "n_samples": int(X.shape[0]),
    }


# ---------------------------------------------------------------------------
# Convenience: SHAP rank vs Bayesian rank Spearman delta
# ---------------------------------------------------------------------------

def spearman_rank_delta(
    shap_ranking: tuple[FeatureRanking, ...],
    bayesian_ranking: list[str],
) -> dict:
    """Rank-correlation between SHAP and Bayesian feature orderings.

    Returns
    -------
    dict
        ``{"spearman_r": float, "n": int, "shap_order": [...],
           "bayesian_order": [...]}``
    """
    shap_order = [r.feature for r in shap_ranking]
    n = len(shap_order)
    if n == 0 or n != len(bayesian_ranking):
        return {
            "spearman_r": float("nan"),
            "n": n,
            "shap_order": shap_order,
            "bayesian_order": list(bayesian_ranking),
        }

    shap_rank = {f: i for i, f in enumerate(shap_order)}
    bay_rank = {f: i for i, f in enumerate(bayesian_ranking)}
    common = set(shap_rank) & set(bay_rank)
    if len(common) < 2:
        return {
            "spearman_r": float("nan"),
            "n": len(common),
            "shap_order": shap_order,
            "bayesian_order": list(bayesian_ranking),
        }

    sr = np.asarray([shap_rank[f] for f in common])
    br = np.asarray([bay_rank[f] for f in common])

    # Spearman's r = Pearson on rank vectors
    sr_centered = sr - sr.mean()
    br_centered = br - br.mean()
    denom = math.sqrt(float(sr_centered @ sr_centered) * float(br_centered @ br_centered))
    if denom == 0.0:
        rho = float("nan")
    else:
        rho = float(sr_centered @ br_centered) / denom

    return {
        "spearman_r": rho,
        "n": len(common),
        "shap_order": shap_order,
        "bayesian_order": list(bayesian_ranking),
    }
