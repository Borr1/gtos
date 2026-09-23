"""K51 — Decayed-Component Identification.

Rolling per-feature attribution + decay detection. Companion to ``K50``
(causal edge attribution at population level). Where K50 ranks components
by *current* R contribution, K51 zooms in on **time evolution** of each
component's contribution.

Strategic question
------------------
A1 says SYSTEM_DECAY — the AI lost selectivity. K50 ranks components by
current R contribution. K51 zooms in: track per-component R contribution
across rolling windows of trades over the full historical period. **Which
features that USED TO matter no longer do?**

Methodology — F5 update (proper SHAP + Bonferroni + bootstrap CI)
-----------------------------------------------------------------
For each non-overlapping rolling 50-trade window:

1. **Build feature matrix** from filled trades (same canonical feature
   helpers exposed here so K50 can reuse them).
2. **Compute per-feature importance**:

   - **SHAP path (preferred):** when ``shap`` and a tree backend
     (``lightgbm`` preferred, then ``xgboost``, then ``sklearn`` GBM)
     are importable, fit a tree regressor on the bucket-encoded feature
     matrix, run :class:`shap.TreeExplainer`, and take per-feature
     **mean(|SHAP|)** as the importance.
   - **Permutation-importance fallback:** when SHAP is not available,
     fall back to the original stratum-mean MSE-reduction estimator
     (importance = baseline-MSE − stratum-mean-MSE; preserved for
     deterministic test coverage in Python-only environments).

3. **Bootstrap 95% CI** per feature per window: resample
   ``bootstrap_n_resamples`` trades (with replacement, default 100),
   re-fit / re-compute, take the 2.5/97.5 percentiles. Driven through
   :func:`window_feature_importances_with_ci`.

4. **Identify decay**: per-feature trajectories are split into H1
   (first half of windows) and H2 (second half). For each feature:

   - Compute the **H1-vs-H2 importance difference** (one-sided t-test,
     null hypothesis "H1 mean ≤ H2 mean") → raw p-value.
   - Apply **Bonferroni correction** with family size =
     ``len(CANONICAL_FEATURES)`` (the H1/H2 importance-delta test is a
     hypothesis-test family across the canonical features; see
     ``bonferroni_survival.py`` for the same pattern).
   - A feature is "**decayed**" when (i) drop_pct ≥ ``threshold_pct``
     (default 40%) **and** (ii) ``bonferroni_p < alpha``.

Design notes
------------
* **Pure functions; only IO is in the CLI.**
* **Optional deps tolerated.** ``shap``/``lightgbm`` are imported via
  ``_try_import``; the SHAP path turns on automatically when they are
  available, otherwise the original permutation-importance path runs
  (and Bonferroni is still applied to the same feature family).
* **Walk-level evidence is not predictive of realized R.** Importance
  is computed against **realised R** outcomes — never gate-pass/reject
  walk-level proxies.
* **Realized-R sources.** Trades are loaded from
  ``knowledge_base/trade_records/{SYMBOL}/*.json`` and
  ``knowledge_base/index/_trade_index.json``.
* **K50 reuse contract.** :func:`extract_features`,
  ``CANONICAL_FEATURES``, :func:`build_feature_matrix` are exposed at
  module level so K50 can produce apples-to-apples attribution.

Schema
------
TrajectoryPoint (output) — one per ``(feature, window_index)``::

    TrajectoryPoint(
        feature="kill_zone",
        window_index=2,
        window_end_iso="2026-03-15T17:00:00+00:00",
        n=50,
        importance=0.082,
        ci_low=0.034,         # 2.5  percentile across bootstrap resamples
        ci_high=0.131,        # 97.5 percentile across bootstrap resamples
        method="shap_treeexplainer",
    )

DecayReport (output) — feature decay table includes Bonferroni::

    FeatureDecay(
        feature="kill_zone",
        h1_mean=0.123,
        h2_mean=0.041,
        drop_pct=0.667,
        n_h1_windows=2,
        n_h2_windows=2,
        raw_p=0.018,
        bonferroni_p=0.216,        # raw_p × family_size
        survives_bonferroni=False, # bonferroni_p < alpha
    )
"""

from __future__ import annotations

import json
import math
import random
import statistics
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


# ────────────────────────────────────────────────────────────────────────────
# Optional dependency probing (mirrors K50 edge_attribution.py pattern)
# ────────────────────────────────────────────────────────────────────────────

def _try_import(name: str) -> Any | None:
    """Best-effort optional import returning the module or None."""
    try:
        return __import__(name)
    except Exception:
        return None


_SHAP = _try_import("shap")
_LIGHTGBM = _try_import("lightgbm")
_XGBOOST = _try_import("xgboost")
_NUMPY = _try_import("numpy")
_SKLEARN_ENSEMBLE = None
if _NUMPY is not None:
    try:
        from sklearn.ensemble import GradientBoostingRegressor as _SKLEARN_ENSEMBLE  # type: ignore  # noqa: E501
    except Exception:
        _SKLEARN_ENSEMBLE = None


def _shap_available() -> bool:
    """True iff the SHAP path can run (needs SHAP + a tree backend + numpy)."""
    if _SHAP is None or _NUMPY is None:
        return False
    return _LIGHTGBM is not None or _XGBOOST is not None or _SKLEARN_ENSEMBLE is not None


# ────────────────────────────────────────────────────────────────────────────
# Canonical feature set (K50/K51 shared contract)
# ────────────────────────────────────────────────────────────────────────────

# These categorical features are extracted from every trade dict. Names
# match the canonical schema used in ``trades_unified.csv``,
# ``knowledge_base/trade_records/{SYMBOL}/*.json``, and the legacy
# ``_trade_index.json``. Order is stable so callers can rely on a
# deterministic iteration order.
CANONICAL_CATEGORICAL_FEATURES: tuple[str, ...] = (
    "framework",
    "direction",
    "kill_zone",
    "daily_bias",
    "sweep_quality",
    "displacement_quality",
    "setup_grade",
    "liquidity_pool_type",
)

# Numerical features are bucketed into terciles per-window (low/mid/high)
# so the same stratum-mean predictor can be applied uniformly.
CANONICAL_NUMERICAL_FEATURES: tuple[str, ...] = (
    "planned_rr",
    "mfe_r",  # NB: mfe/mae are post-trade outcomes; included for K50/K51
    "mae_r",  # to characterise WHEN they correlate with R, not as predictors.
    "hold_time_candles",
)

CANONICAL_FEATURES: tuple[str, ...] = (
    CANONICAL_CATEGORICAL_FEATURES + CANONICAL_NUMERICAL_FEATURES
)

# Realised-R candidate field names (top-level or under "exit").
_REALIZED_R_FIELDS: tuple[str, ...] = (
    "realized_r",
    "realized_R",
    "actual_r",
    "actual_R",
    "r_multiple",
    "rR",
)

# Timestamp candidate field names.
_TIMESTAMP_FIELDS: tuple[str, ...] = (
    "candle_close_time",
    "candle_time",
    "timestamp",
    "exit_time",
    "date",
)


# ────────────────────────────────────────────────────────────────────────────
# Public dataclasses
# ────────────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TrajectoryPoint:
    """A single per-feature per-window importance observation.

    Attributes
    ----------
    feature : str
        Canonical feature name (in ``CANONICAL_FEATURES``).
    window_index : int
        0-based non-overlapping window index.
    window_end_iso : str
        ISO-8601 UTC timestamp of the LAST trade in the window.
    n : int
        Window size (== ``window`` for full windows; never partial).
    importance : float
        Per-feature importance (mean |SHAP| under the SHAP path; baseline-
        minus-stratum-mean MSE under the permutation fallback). ``>= 0``.
    ci_low, ci_high : float
        2.5 / 97.5 percentile of the bootstrap distribution. Both
        ``importance`` and the CI bounds are non-negative.
    method : str
        ``"shap_treeexplainer"`` or ``"permutation_importance"``. Recorded
        per point because the SHAP path can fail per-window (e.g. all-NaN
        targets) and downgrade gracefully.
    """

    feature: str
    window_index: int
    window_end_iso: str
    n: int
    importance: float
    ci_low: float = 0.0
    ci_high: float = 0.0
    method: str = "permutation_importance"


@dataclass(frozen=True)
class FeatureDecay:
    """Per-feature decay summary across H1 vs H2 baselines.

    Attributes
    ----------
    feature : str
    h1_mean, h2_mean : float
        Mean per-window importance for the H1 / H2 halves.
    drop_pct : float
        Fractional drop; ``0.40`` == 40% drop. Negative when H2 > H1.
    n_h1_windows, n_h2_windows : int
        Number of windows in each half (equal for even total, off-by-one
        for odd).
    raw_p : float
        Raw one-sided t-test p-value for ``H0: H1_mean ≤ H2_mean``
        (i.e. small p means evidence of decay). ``NaN`` when the test is
        underpowered (n_h1_windows < 2 or n_h2_windows < 2 or zero
        within-half variance with non-zero means).
    bonferroni_p : float
        ``min(1.0, raw_p × family_size)`` where ``family_size`` is the
        number of features tested in the same correction family. ``NaN``
        propagates from ``raw_p``.
    survives_bonferroni : bool
        ``bonferroni_p < alpha``. ``False`` when ``raw_p`` is ``NaN`` or
        when the Bonferroni-adjusted p crosses the threshold.
    family_size : int
        Number of features in the Bonferroni family (informational —
        identical across all features in one report).
    """

    feature: str
    h1_mean: float
    h2_mean: float
    drop_pct: float
    n_h1_windows: int
    n_h2_windows: int
    raw_p: float = float("nan")
    bonferroni_p: float = float("nan")
    survives_bonferroni: bool = False
    family_size: int = 0


@dataclass(frozen=True)
class DecayReport:
    """Top-level decay report covering all features."""

    threshold_pct: float
    alpha: float
    family_size: int
    h1_period: tuple[str, str] | None
    h2_period: tuple[str, str] | None
    decayed: tuple[FeatureDecay, ...]
    newly_important: tuple[FeatureDecay, ...]
    stable: tuple[FeatureDecay, ...]
    all_features: tuple[FeatureDecay, ...]
    n_total_windows: int
    n_total_trades: int
    method: str  # SHAP path actually used: "shap_treeexplainer" / "permutation_importance" / "mixed"


# ────────────────────────────────────────────────────────────────────────────
# Feature engineering helpers (shared with K50)
# ────────────────────────────────────────────────────────────────────────────

def _parse_timestamp(raw: Any) -> datetime | None:
    """Best-effort ISO-string-or-datetime → tz-aware UTC datetime."""
    if raw is None:
        return None
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if not isinstance(raw, str):
        return None
    s = raw.strip()
    if not s:
        return None
    if len(s) == 10 and s.count("-") == 2:
        try:
            return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None
    candidate = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _extract_realized_r(trade: dict) -> float | None:
    """Find a realised-R numeric on a trade dict; None if not present."""
    for name in _REALIZED_R_FIELDS:
        if name in trade and trade[name] is not None:
            try:
                return float(trade[name])
            except (TypeError, ValueError):
                continue
    exit_block = trade.get("exit") if isinstance(trade.get("exit"), dict) else None
    if exit_block:
        for name in _REALIZED_R_FIELDS:
            if name in exit_block and exit_block[name] is not None:
                try:
                    return float(exit_block[name])
                except (TypeError, ValueError):
                    continue
    return None


def _extract_timestamp(trade: dict) -> datetime | None:
    """Find a usable timestamp on a trade dict."""
    for name in _TIMESTAMP_FIELDS:
        if name in trade and trade[name] is not None:
            ts = _parse_timestamp(trade[name])
            if ts is not None:
                return ts
    for parent in ("metadata", "exit", "trade_parameters"):
        block = trade.get(parent)
        if isinstance(block, dict):
            for name in _TIMESTAMP_FIELDS:
                if name in block and block[name] is not None:
                    ts = _parse_timestamp(block[name])
                    if ts is not None:
                        return ts
    return None


def _extract_categorical(trade: dict, name: str) -> str | None:
    """Pull a categorical feature value off a trade. Looks at top level
    then nested ``metadata`` / ``trade_parameters`` blocks."""
    if name in trade and trade[name] not in (None, ""):
        return str(trade[name]).lower().strip()
    for parent in ("metadata", "trade_parameters", "context"):
        block = trade.get(parent)
        if isinstance(block, dict) and name in block and block[name] not in (None, ""):
            return str(block[name]).lower().strip()
    return None


def _extract_numeric(trade: dict, name: str) -> float | None:
    """Pull a numeric feature value off a trade."""
    if name in trade and trade[name] is not None:
        try:
            v = float(trade[name])
            return v if math.isfinite(v) else None
        except (TypeError, ValueError):
            return None
    for parent in ("metadata", "trade_parameters", "exit"):
        block = trade.get(parent)
        if isinstance(block, dict) and name in block and block[name] is not None:
            try:
                v = float(block[name])
                return v if math.isfinite(v) else None
            except (TypeError, ValueError):
                continue
    return None


def extract_features(trade: dict) -> dict[str, Any]:
    """Extract canonical feature values from a trade dict.

    Returns a dict keyed by feature name. Missing categorical features
    map to the literal string ``"missing"`` so windows with mixed
    completeness still produce well-defined strata. Missing numeric
    features map to ``None`` and are treated as their own bucket
    downstream.

    K50 and K51 share this helper. The dict's iteration order matches
    ``CANONICAL_FEATURES``.
    """
    out: dict[str, Any] = {}
    for name in CANONICAL_CATEGORICAL_FEATURES:
        v = _extract_categorical(trade, name)
        out[name] = v if v is not None else "missing"
    for name in CANONICAL_NUMERICAL_FEATURES:
        out[name] = _extract_numeric(trade, name)
    return out


def build_feature_matrix(
    trades: list[dict],
) -> tuple[list[float], list[dict[str, Any]], list[datetime]]:
    """Build aligned (R, features, timestamps) arrays from a trade list.

    Drops trades without a usable realised R or timestamp. Output is
    ascending-sorted by timestamp so downstream rolling windows are
    chronological.

    Returns
    -------
    (rs, feature_dicts, timestamps) : tuple of three same-length lists.
    """
    enriched: list[tuple[datetime, float, dict[str, Any]]] = []
    for t in trades:
        if not isinstance(t, dict):
            continue
        ts = _extract_timestamp(t)
        r = _extract_realized_r(t)
        if ts is None or r is None or not math.isfinite(r):
            continue
        feats = extract_features(t)
        enriched.append((ts, r, feats))
    enriched.sort(key=lambda triple: triple[0])
    rs = [r for (_, r, _) in enriched]
    feats = [f for (_, _, f) in enriched]
    tss = [ts for (ts, _, _) in enriched]
    return rs, feats, tss


# ────────────────────────────────────────────────────────────────────────────
# Bucketing for numeric features
# ────────────────────────────────────────────────────────────────────────────

def _bucket_numeric(values: list[float | None]) -> list[str]:
    """Bucket a list of numeric (or None) values into terciles + ``"missing"``.

    Returns parallel list of bucket labels: ``"low"`` / ``"mid"`` /
    ``"high"`` / ``"missing"``. Within-window terciles are computed only
    from the non-None subset.
    """
    finite = [v for v in values if v is not None and math.isfinite(v)]
    n_finite = len(finite)
    if n_finite < 3:
        # Not enough variance to bucket — single bucket for present, "missing" for None
        return ["present" if (v is not None and math.isfinite(v)) else "missing" for v in values]
    sorted_vals = sorted(finite)
    q1 = sorted_vals[n_finite // 3]
    q2 = sorted_vals[(2 * n_finite) // 3]
    out: list[str] = []
    for v in values:
        if v is None or not math.isfinite(v):
            out.append("missing")
        elif v <= q1:
            out.append("low")
        elif v <= q2:
            out.append("mid")
        else:
            out.append("high")
    return out


# ────────────────────────────────────────────────────────────────────────────
# Permutation-importance per window (original / fallback path)
# ────────────────────────────────────────────────────────────────────────────

def _mse(values: list[float], baseline: float) -> float:
    """Mean squared error of ``values`` against a single baseline."""
    if not values:
        return 0.0
    return sum((v - baseline) ** 2 for v in values) / len(values)


def _stratum_mean_mse(rs: list[float], buckets: list[str]) -> float:
    """MSE of a stratum-mean predictor.

    Predictor: for each trade, predict the mean R of all trades sharing
    the same bucket label. Reduces to baseline mean if the feature is
    uninformative (all trades same bucket).
    """
    n = len(rs)
    if n == 0 or len(buckets) != n:
        return 0.0
    by_bucket: dict[str, list[float]] = {}
    for r, b in zip(rs, buckets):
        by_bucket.setdefault(b, []).append(r)
    means: dict[str, float] = {b: (sum(v) / len(v)) for b, v in by_bucket.items()}
    total = 0.0
    for r, b in zip(rs, buckets):
        diff = r - means[b]
        total += diff * diff
    return total / n


def _permutation_window_importances(
    rs: list[float],
    feature_dicts: list[dict[str, Any]],
    features: tuple[str, ...],
) -> dict[str, float]:
    """Permutation-importance proxy via a stratum-mean predictor.

    Returns importance >= 0 per feature. A feature with one bucket
    (everything missing) → 0.
    """
    n = len(rs)
    if n == 0:
        return {f: 0.0 for f in features}
    mean_r = sum(rs) / n
    baseline_mse = _mse(rs, mean_r)
    out: dict[str, float] = {}
    for feat in features:
        if feat in CANONICAL_NUMERICAL_FEATURES:
            raw = [fd.get(feat) for fd in feature_dicts]
            buckets = _bucket_numeric(raw)
        else:
            buckets = [str(fd.get(feat, "missing")) for fd in feature_dicts]
        feat_mse = _stratum_mean_mse(rs, buckets)
        importance = baseline_mse - feat_mse
        if importance < 0 or not math.isfinite(importance):
            importance = 0.0
        out[feat] = importance
    return out


# ────────────────────────────────────────────────────────────────────────────
# SHAP-path: fit tree regressor on bucket-encoded features → mean(|SHAP|)
# ────────────────────────────────────────────────────────────────────────────

def _bucket_encode_window(
    feature_dicts: list[dict[str, Any]],
    features: tuple[str, ...],
) -> tuple[list[list[int]], dict[str, dict[str, int]]]:
    """Integer-encode bucketed feature values across a window.

    Returns
    -------
    matrix : list[list[int]]
        ``len(feature_dicts)`` rows × ``len(features)`` cols. Each cell
        is the integer index for that trade's feature bucket.
    encoders : dict[feature, dict[bucket_label, int]]
        Per-feature label → integer-index map (informational; useful for
        debugging / reproducibility).
    """
    n = len(feature_dicts)
    matrix: list[list[int]] = [[0] * len(features) for _ in range(n)]
    encoders: dict[str, dict[str, int]] = {}
    for fi, feat in enumerate(features):
        if feat in CANONICAL_NUMERICAL_FEATURES:
            raw = [fd.get(feat) for fd in feature_dicts]
            buckets = _bucket_numeric(raw)
        else:
            buckets = [str(fd.get(feat, "missing")) for fd in feature_dicts]
        # Stable, deterministic ordering: sorted unique bucket labels.
        unique_labels = sorted({str(b) for b in buckets})
        enc: dict[str, int] = {label: idx for idx, label in enumerate(unique_labels)}
        encoders[feat] = enc
        for ri, b in enumerate(buckets):
            matrix[ri][fi] = enc[str(b)]
    return matrix, encoders


def _fit_tree_regressor(X: Any, y: Any, random_state: int = 0) -> Any:
    """Fit a tree regressor with conservative defaults.

    Backend preference: lightgbm > xgboost > sklearn-GBM. Tags the
    fitted model with ``_k51_backend`` so callers can introspect.
    """
    if _NUMPY is None:
        raise RuntimeError("numpy is required for the SHAP path")
    np = _NUMPY  # type: ignore[assignment]
    X_arr = np.asarray(X, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)
    if X_arr.ndim != 2:
        raise ValueError(f"X must be 2-D, got shape {X_arr.shape}")
    if X_arr.shape[0] < 4:
        raise ValueError(f"need ≥4 samples to fit, got {X_arr.shape[0]}")

    if _LIGHTGBM is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = _LIGHTGBM.LGBMRegressor(  # type: ignore[attr-defined]
                n_estimators=100,
                max_depth=4,
                num_leaves=15,
                learning_rate=0.05,
                min_child_samples=2,
                random_state=random_state,
                verbosity=-1,
                force_col_wise=True,
            )
            model.fit(X_arr, y_arr)
        model._k51_backend = "lightgbm"
        return model

    if _XGBOOST is not None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = _XGBOOST.XGBRegressor(  # type: ignore[attr-defined]
                n_estimators=100,
                max_depth=4,
                learning_rate=0.05,
                random_state=random_state,
                verbosity=0,
                objective="reg:squarederror",
            )
            model.fit(X_arr, y_arr)
        model._k51_backend = "xgboost"
        return model

    if _SKLEARN_ENSEMBLE is not None:
        model = _SKLEARN_ENSEMBLE(  # type: ignore[misc]
            n_estimators=100,
            max_depth=3,
            learning_rate=0.05,
            random_state=random_state,
        )
        model.fit(X_arr, y_arr)
        model._k51_backend = "sklearn"
        return model

    raise RuntimeError("no tree-regressor backend available")


def _shap_window_importances(
    rs: list[float],
    feature_dicts: list[dict[str, Any]],
    features: tuple[str, ...],
    *,
    random_state: int = 0,
) -> tuple[dict[str, float], str]:
    """Mean(|SHAP|) per feature for one window using TreeExplainer.

    Returns
    -------
    (importances, method) : tuple
        ``importances[feat]`` is mean(|SHAP|) across rows. ``method`` is
        ``"shap_treeexplainer"`` on success.

    Raises
    ------
    RuntimeError
        If SHAP, numpy, or any tree backend is unavailable, or if the
        fit / explain step fails.
    """
    if not _shap_available():
        raise RuntimeError("SHAP path unavailable (missing shap / numpy / tree backend)")
    np = _NUMPY  # type: ignore[assignment]
    if len(rs) < 4:
        raise RuntimeError(f"SHAP path requires ≥4 trades, got {len(rs)}")
    X_int, _encoders = _bucket_encode_window(feature_dicts, features)
    X = np.asarray(X_int, dtype=np.float64)
    y = np.asarray(rs, dtype=np.float64)
    # If y is constant, tree regressor will produce trivial output and
    # SHAP values will all be zero — that is the correct "no signal"
    # answer, but skip the fit cost.
    if float(np.std(y)) == 0.0:
        return {f: 0.0 for f in features}, "shap_treeexplainer"
    model = _fit_tree_regressor(X, y, random_state=random_state)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        explainer = _SHAP.TreeExplainer(model)  # type: ignore[attr-defined]
        shap_vals = explainer.shap_values(X)
    if isinstance(shap_vals, list):
        shap_vals = shap_vals[0]
    shap_arr = np.asarray(shap_vals, dtype=np.float64)
    if shap_arr.ndim == 1:  # single-row edge case
        shap_arr = shap_arr.reshape(1, -1)
    if shap_arr.shape[1] != len(features):
        raise RuntimeError(
            f"shap shape mismatch: got {shap_arr.shape}, expected (n, {len(features)})"
        )
    mean_abs = np.mean(np.abs(shap_arr), axis=0)
    return {f: float(mean_abs[i]) for i, f in enumerate(features)}, "shap_treeexplainer"


# ────────────────────────────────────────────────────────────────────────────
# Public API: per-window importance (with method dispatch + bootstrap CI)
# ────────────────────────────────────────────────────────────────────────────

def window_feature_importances(
    rs: list[float],
    feature_dicts: list[dict[str, Any]],
    features: tuple[str, ...] = CANONICAL_FEATURES,
    *,
    method: str = "auto",
) -> dict[str, float]:
    """Compute per-feature importance for one window.

    Parameters
    ----------
    rs : list of float
        Realised R for each trade in the window.
    feature_dicts : list of dict
        Per-trade feature dicts (from ``extract_features``).
    features : tuple of str
        Which features to compute importance for.
    method : str
        ``"auto"`` (default) → SHAP path when available, permutation
        fallback otherwise. ``"shap"`` forces SHAP and raises if it is
        unavailable. ``"permutation"`` forces the permutation fallback.

    Returns
    -------
    dict[str, float]
        Feature name → importance. Always non-negative.
    """
    n = len(rs)
    if n == 0:
        return {f: 0.0 for f in features}
    if len(feature_dicts) != n:
        raise ValueError(
            f"feature_dicts length {len(feature_dicts)} != rs length {n}"
        )
    if method == "shap":
        imps, _ = _shap_window_importances(rs, feature_dicts, features)
        return imps
    if method == "permutation":
        return _permutation_window_importances(rs, feature_dicts, features)
    # auto
    if _shap_available() and n >= 4:
        try:
            imps, _ = _shap_window_importances(rs, feature_dicts, features)
            return imps
        except Exception:
            return _permutation_window_importances(rs, feature_dicts, features)
    return _permutation_window_importances(rs, feature_dicts, features)


def window_feature_importances_with_ci(
    rs: list[float],
    feature_dicts: list[dict[str, Any]],
    features: tuple[str, ...] = CANONICAL_FEATURES,
    *,
    method: str = "auto",
    bootstrap_n_resamples: int = 100,
    bootstrap_seed: int = 0,
    ci_alpha: float = 0.05,
) -> tuple[dict[str, float], dict[str, tuple[float, float]], str]:
    """Importance + bootstrap 95% CI per feature for one window.

    Parameters
    ----------
    rs, feature_dicts, features, method
        See :func:`window_feature_importances`.
    bootstrap_n_resamples : int
        Number of within-window resamples. ``0`` skips bootstrap; CIs
        equal point estimate.
    bootstrap_seed : int
        Seed for the per-window resampler. K51 calls this with
        ``window_index`` to make every window deterministically
        reproducible while still varying across windows.
    ci_alpha : float
        Two-sided CI level. Default 0.05 → 2.5/97.5 percentiles (95% CI).

    Returns
    -------
    (importances, ci_bounds, method_actually_used)
        ``importances[feat]``: point estimate.
        ``ci_bounds[feat]``: ``(low, high)``.
        ``method_actually_used``: ``"shap_treeexplainer"`` or
        ``"permutation_importance"``.
    """
    n = len(rs)
    use_shap = method == "shap" or (method == "auto" and _shap_available() and n >= 4)
    actual_method = "permutation_importance"

    # Point estimate
    if use_shap:
        try:
            imps, _ = _shap_window_importances(rs, feature_dicts, features)
            actual_method = "shap_treeexplainer"
        except Exception:
            if method == "shap":
                raise
            imps = _permutation_window_importances(rs, feature_dicts, features)
            use_shap = False
    else:
        imps = _permutation_window_importances(rs, feature_dicts, features)

    # Bootstrap CI
    if bootstrap_n_resamples <= 0 or n < 2:
        return imps, {f: (imps[f], imps[f]) for f in features}, actual_method

    if not 0 < ci_alpha < 1:
        raise ValueError(f"ci_alpha must be in (0, 1), got {ci_alpha}")

    rng = random.Random(bootstrap_seed)
    boot_samples: dict[str, list[float]] = {f: [] for f in features}
    for b in range(bootstrap_n_resamples):
        idx = [rng.randrange(0, n) for _ in range(n)]
        rs_boot = [rs[i] for i in idx]
        feats_boot = [feature_dicts[i] for i in idx]
        if use_shap:
            try:
                bi, _ = _shap_window_importances(
                    rs_boot, feats_boot, features, random_state=b,
                )
            except Exception:
                bi = _permutation_window_importances(rs_boot, feats_boot, features)
        else:
            bi = _permutation_window_importances(rs_boot, feats_boot, features)
        for f in features:
            boot_samples[f].append(bi[f])

    lo_q = ci_alpha / 2
    hi_q = 1 - ci_alpha / 2
    ci: dict[str, tuple[float, float]] = {}
    for f in features:
        sorted_b = sorted(boot_samples[f])
        if not sorted_b:
            ci[f] = (imps[f], imps[f])
            continue
        ci[f] = (
            _percentile(sorted_b, lo_q),
            _percentile(sorted_b, hi_q),
        )
    return imps, ci, actual_method


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


# ────────────────────────────────────────────────────────────────────────────
# Rolling attribution (public API)
# ────────────────────────────────────────────────────────────────────────────

def rolling_attribution(
    trades: list[dict],
    window: int = 50,
    features: tuple[str, ...] = CANONICAL_FEATURES,
    *,
    method: str = "auto",
    bootstrap_n_resamples: int = 100,
    bootstrap_seed: int = 0,
    ci_alpha: float = 0.05,
) -> dict[str, list[TrajectoryPoint]]:
    """Compute per-feature importance series across non-overlapping
    rolling windows.

    Parameters
    ----------
    trades : list of dict
        Filled-trade dicts. Trades without realised R or timestamp are
        dropped silently.
    window : int, default 50
        Window size. Must be ≥ 3 (terciles need at least 3 distinct
        values; tests cover this lower bound).
    features : tuple of str, optional
        Subset of canonical features to evaluate.
    method : str, default "auto"
        ``"auto"`` / ``"shap"`` / ``"permutation"``. See
        :func:`window_feature_importances`.
    bootstrap_n_resamples, bootstrap_seed, ci_alpha
        Bootstrap parameters; see :func:`window_feature_importances_with_ci`.

    Returns
    -------
    dict[str, list[TrajectoryPoint]]
        Feature name → list of trajectory points (in window-index order).
        Returns ``{f: [] for f in features}`` if fewer than ``window``
        valid trades are present.
    """
    if window < 3:
        raise ValueError(f"window must be >= 3, got {window}")
    if not isinstance(trades, list):
        raise TypeError(f"trades must be a list, got {type(trades).__name__}")

    rs, feats, tss = build_feature_matrix(trades)
    total = len(rs)
    out: dict[str, list[TrajectoryPoint]] = {f: [] for f in features}
    if total < window:
        return out

    n_full = total // window
    for k in range(n_full):
        start = k * window
        end = start + window
        chunk_rs = rs[start:end]
        chunk_feats = feats[start:end]
        chunk_end_ts = tss[end - 1]
        importances, ci_bounds, method_used = window_feature_importances_with_ci(
            chunk_rs,
            chunk_feats,
            features,
            method=method,
            bootstrap_n_resamples=bootstrap_n_resamples,
            bootstrap_seed=bootstrap_seed + k,  # vary per window
            ci_alpha=ci_alpha,
        )
        for feat in features:
            lo, hi = ci_bounds[feat]
            out[feat].append(
                TrajectoryPoint(
                    feature=feat,
                    window_index=k,
                    window_end_iso=chunk_end_ts.isoformat(),
                    n=window,
                    importance=importances[feat],
                    ci_low=lo,
                    ci_high=hi,
                    method=method_used,
                )
            )
    return out


# ────────────────────────────────────────────────────────────────────────────
# Bonferroni-corrected H1/H2 t-test
# ────────────────────────────────────────────────────────────────────────────

def _welch_t_p_one_sided(h1: list[float], h2: list[float]) -> float:
    """One-sided Welch's t-test p-value for ``H0: mean(H1) ≤ mean(H2)``.

    A small p-value means H1 mean is significantly LARGER than H2 (i.e.
    evidence of decay). Pure-Python; uses the survival-function of a
    Student-t approximation derived from the Welch-Satterthwaite
    degrees-of-freedom.

    Returns ``NaN`` when the test is undefined (n < 2 in either half,
    zero variance in both halves with equal means).
    """
    n1 = len(h1)
    n2 = len(h2)
    if n1 < 2 or n2 < 2:
        return float("nan")
    m1 = sum(h1) / n1
    m2 = sum(h2) / n2
    # Sample variances (Bessel-corrected)
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
    # Welch-Satterthwaite df
    num = (v1 / n1 + v2 / n2) ** 2
    denom = (v1 ** 2) / ((n1 ** 2) * (n1 - 1)) + (v2 ** 2) / ((n2 ** 2) * (n2 - 1))
    if denom == 0.0:
        return float("nan")
    df = num / denom
    # One-sided survival function: P(T > t) under H0 where mean(H1) == mean(H2).
    return _student_t_sf(t, df)


def _student_t_sf(t: float, df: float) -> float:
    """One-sided Student-t survival function P(T > t) via regularised
    incomplete beta function.

    Uses the relation
        P(T > t) = 0.5 * I_x(df/2, 0.5)   for t >= 0,  x = df / (df + t^2)
        P(T > t) = 1 - P(T > -t)          for t <  0.
    """
    if not math.isfinite(t) or not math.isfinite(df) or df <= 0:
        return float("nan")
    if t == 0:
        return 0.5
    # Use the identity in closed form via betainc.
    if t > 0:
        x = df / (df + t * t)
        return 0.5 * _betainc_regularised(df / 2.0, 0.5, x)
    return 1.0 - _student_t_sf(-t, df)


def _betainc_regularised(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function I_x(a, b).

    Pure-Python implementation via the Lentz continued-fraction expansion
    of Numerical Recipes (Press et al., 1992, §6.4). Sufficient accuracy
    for p-values down to ~1e-10.
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


def _betacf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-16) -> float:
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
    return h  # max_iter reached — accept current value


def bonferroni_correct(p_values: list[float], family_size: int | None = None) -> list[float]:
    """Apply Bonferroni correction across a family of raw p-values.

    Returns ``[min(1.0, p * family_size)]`` with ``NaN`` propagated
    unchanged. ``family_size`` defaults to ``len(p_values)`` (consistent
    with the K52 ``bonferroni_survival.bonferroni_correct``).
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


# ────────────────────────────────────────────────────────────────────────────
# Decay identification (public API)
# ────────────────────────────────────────────────────────────────────────────

def _classify_periods(
    points: list[TrajectoryPoint],
) -> tuple[list[TrajectoryPoint], list[TrajectoryPoint], tuple[str, str] | None, tuple[str, str] | None]:
    """Split a per-feature trajectory into H1 / H2 halves by window
    index.

    H1 = first half (window indexes [0, n//2)).
    H2 = second half (window indexes [n//2, n)).

    With odd n, H2 has one more window than H1 (e.g., n=5 → H1=[0,1],
    H2=[2,3,4]).
    """
    if not points:
        return [], [], None, None
    pts_sorted = sorted(points, key=lambda p: p.window_index)
    n = len(pts_sorted)
    mid = n // 2
    h1 = pts_sorted[:mid]
    h2 = pts_sorted[mid:]
    h1_period = (
        (pts_sorted[0].window_end_iso[:10], pts_sorted[mid - 1].window_end_iso[:10])
        if h1
        else None
    )
    h2_period = (
        (pts_sorted[mid].window_end_iso[:10], pts_sorted[-1].window_end_iso[:10])
        if h2
        else None
    )
    return h1, h2, h1_period, h2_period


def identify_decay(
    series: dict[str, list[TrajectoryPoint]],
    threshold_pct: float = 0.40,
    *,
    alpha: float = 0.05,
) -> DecayReport:
    """Identify which features have decayed ≥``threshold_pct`` H1→H2,
    Bonferroni-corrected at ``alpha``.

    A feature is **decayed** when ALL of:
      - ``(h1_mean - h2_mean) / h1_mean >= threshold_pct``
      - ``h1_mean > 0``
      - both halves have ≥1 window
      - ``bonferroni_p < alpha`` (i.e. survives Bonferroni correction
        across the canonical-feature family)

    A feature is **newly important** when:
      - ``h2_mean > 0``, ``h1_mean == 0``
      - ``h2_mean - h1_mean >= threshold_pct * h2_mean``

    A feature is **stable** when it has windows in both halves but
    neither rule fires (including features that have a numerically
    large drop but fail Bonferroni — in that case they are not
    "decayed", just suggestive).

    Parameters
    ----------
    series : dict[str, list[TrajectoryPoint]]
        Output of :func:`rolling_attribution`.
    threshold_pct : float, default 0.40
        Fractional drop threshold. ``0.40`` == 40%.
    alpha : float, default 0.05
        Per-test Bonferroni significance threshold. ``bonferroni_p <
        alpha`` is required for a "decayed" classification.
    """
    if threshold_pct < 0 or threshold_pct > 1 or not math.isfinite(threshold_pct):
        raise ValueError(f"threshold_pct must be in [0, 1], got {threshold_pct}")
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    feature_list = list(series.keys())
    family_size = len(feature_list)

    decayed: list[FeatureDecay] = []
    newly_important: list[FeatureDecay] = []
    stable: list[FeatureDecay] = []
    all_features: list[FeatureDecay] = []

    overall_h1: tuple[str, str] | None = None
    overall_h2: tuple[str, str] | None = None
    n_total_windows = 0
    methods_seen: set[str] = set()

    # Pass 1: compute drops + raw p-values per feature
    raw_records: list[tuple[str, float, float, float, int, int, float]] = []  # (feature, h1_mean, h2_mean, drop_pct, n_h1, n_h2, raw_p)
    raw_p_values: list[float] = []
    for feature in feature_list:
        points = series[feature]
        h1_pts, h2_pts, h1_period, h2_period = _classify_periods(points)
        n_total_windows = max(n_total_windows, len(points))
        if overall_h1 is None and h1_period is not None:
            overall_h1 = h1_period
        if overall_h2 is None and h2_period is not None:
            overall_h2 = h2_period
        for p in points:
            methods_seen.add(p.method)

        if not h1_pts and not h2_pts:
            continue

        h1_imps = [p.importance for p in h1_pts]
        h2_imps = [p.importance for p in h2_pts]
        h1_mean = sum(h1_imps) / len(h1_imps) if h1_imps else 0.0
        h2_mean = sum(h2_imps) / len(h2_imps) if h2_imps else 0.0
        if h1_mean > 0:
            drop_pct = (h1_mean - h2_mean) / h1_mean
        elif h2_mean > 0:
            drop_pct = -1.0
        else:
            drop_pct = 0.0

        raw_p = _welch_t_p_one_sided(h1_imps, h2_imps)
        raw_records.append((
            feature, h1_mean, h2_mean, drop_pct,
            len(h1_pts), len(h2_pts), raw_p,
        ))
        raw_p_values.append(raw_p)

    # Pass 2: apply Bonferroni correction across the full feature family.
    bonf_p_values = bonferroni_correct(raw_p_values, family_size=family_size)

    for (feature, h1_mean, h2_mean, drop_pct, n_h1, n_h2, raw_p), bonf_p in zip(
        raw_records, bonf_p_values
    ):
        survives = (
            isinstance(bonf_p, float)
            and math.isfinite(bonf_p)
            and bonf_p < alpha
        )
        record = FeatureDecay(
            feature=feature,
            h1_mean=h1_mean,
            h2_mean=h2_mean,
            drop_pct=drop_pct,
            n_h1_windows=n_h1,
            n_h2_windows=n_h2,
            raw_p=raw_p,
            bonferroni_p=bonf_p,
            survives_bonferroni=survives,
            family_size=family_size,
        )
        all_features.append(record)
        if (
            n_h1 >= 1 and n_h2 >= 1
            and h1_mean > 0
            and drop_pct >= threshold_pct
            and survives
        ):
            decayed.append(record)
        elif (
            n_h1 >= 1 and n_h2 >= 1
            and h1_mean == 0
            and h2_mean > 0
            and (h2_mean - h1_mean) >= threshold_pct * h2_mean
        ):
            newly_important.append(record)
        elif n_h1 >= 1 and n_h2 >= 1:
            stable.append(record)

    # Sorting
    decayed.sort(key=lambda r: r.drop_pct, reverse=True)
    newly_important.sort(key=lambda r: r.h2_mean - r.h1_mean, reverse=True)
    stable.sort(key=lambda r: r.feature)
    all_features.sort(key=lambda r: r.feature)

    # Method label
    if not methods_seen:
        method_label = "permutation_importance"
    elif len(methods_seen) == 1:
        method_label = methods_seen.pop()
    else:
        method_label = "mixed"

    # n_total_trades — we get this from any feature's first point's n
    n_per_window = 0
    for points in series.values():
        if points:
            n_per_window = points[0].n
            break

    return DecayReport(
        threshold_pct=threshold_pct,
        alpha=alpha,
        family_size=family_size,
        h1_period=overall_h1,
        h2_period=overall_h2,
        decayed=tuple(decayed),
        newly_important=tuple(newly_important),
        stable=tuple(stable),
        all_features=tuple(all_features),
        n_total_windows=n_total_windows,
        n_total_trades=n_total_windows * n_per_window,
        method=method_label,
    )


# ────────────────────────────────────────────────────────────────────────────
# Aux loaders (mirror the convention of decay_velocity.py)
# ────────────────────────────────────────────────────────────────────────────

def load_trades_from_disk(
    trade_records_dir: Path | None = None,
    aux_index_path: Path | None = None,
    symbols: Iterable[str] | None = None,
) -> list[dict]:
    """Load filled trades from the canonical disk locations.

    Parameters
    ----------
    trade_records_dir : Path, optional
        ``knowledge_base/trade_records/`` (per-symbol subdirs of JSON
        decision records). Default: skip if None.
    aux_index_path : Path, optional
        ``knowledge_base/index/_trade_index.json`` (legacy batch trades
        with compact schema). Default: skip if None.
    symbols : iterable of str, optional
        Restrict to these symbols (case-insensitive). None == all.

    Returns
    -------
    list[dict]
        All filled trades found. De-duplicated by ``trade_id`` when
        available.
    """
    requested_set: set[str] | None = (
        {s.upper() for s in symbols} if symbols is not None else None
    )
    out: list[dict] = []
    seen_ids: set[str] = set()

    if trade_records_dir is not None:
        d = Path(trade_records_dir)
        if d.is_dir():
            for sym_dir in sorted(d.iterdir()):
                if not sym_dir.is_dir():
                    continue
                symbol = sym_dir.name.upper()
                if requested_set is not None and symbol not in requested_set:
                    continue
                for fp in sorted(sym_dir.glob("*.json")):
                    try:
                        record = json.loads(fp.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if not isinstance(record, dict):
                        continue
                    if "symbol" not in record or not record.get("symbol"):
                        record["symbol"] = symbol
                    r = _extract_realized_r(record)
                    if r is None or not math.isfinite(r):
                        continue
                    tid = record.get("trade_id")
                    if tid:
                        if tid in seen_ids:
                            continue
                        seen_ids.add(tid)
                    out.append(record)

    if aux_index_path is not None:
        aux = Path(aux_index_path)
        if aux.exists():
            try:
                doc = json.loads(aux.read_text(encoding="utf-8"))
            except Exception:
                doc = None
            if isinstance(doc, dict):
                aux_trades = doc.get("trades")
                if isinstance(aux_trades, list):
                    for t in aux_trades:
                        if not isinstance(t, dict):
                            continue
                        sym_raw = t.get("symbol") or ""
                        sym = str(sym_raw).upper()
                        if not sym:
                            continue
                        if requested_set is not None and sym not in requested_set:
                            continue
                        r = _extract_realized_r(t)
                        if r is None or not math.isfinite(r):
                            continue
                        tid = t.get("trade_id")
                        if tid and tid in seen_ids:
                            continue
                        if tid:
                            seen_ids.add(tid)
                        out.append(t)

    return out


__all__ = [
    "CANONICAL_FEATURES",
    "CANONICAL_CATEGORICAL_FEATURES",
    "CANONICAL_NUMERICAL_FEATURES",
    "TrajectoryPoint",
    "FeatureDecay",
    "DecayReport",
    "extract_features",
    "build_feature_matrix",
    "window_feature_importances",
    "window_feature_importances_with_ci",
    "rolling_attribution",
    "identify_decay",
    "load_trades_from_disk",
    "bonferroni_correct",
]
