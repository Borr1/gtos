"""K53 — Loser Anti-Pattern Classifier.

Pure-Python (sklearn-optional) clustering and binary classification primitives
for identifying systemic anti-patterns in losing trades.

Strategic question
------------------
Across the ~150+ losing trades in our historical record, do they cluster into
a small set of identifiable anti-patterns (e.g. "high touch_count + low
displacement + range regime")? If yes, those clusters become the feature
engineering hints that drive the K54 ML classifier.

Design notes
------------
* **Realized R is the ground truth.** Memory
  ``feedback_walk_level_evidence_not_predictive``: walk-level features
  vary per stratum, but the validation signal MUST be realized R. A
  trade is a "loser" when ``realized_r <= 0`` — including 0 (BE-stop /
  zero-R outcomes) avoids splitting hairs on near-zero outcomes.
* **No third-party hard dependency.** ``scikit-learn`` is optional. When
  it is present we use ``KMeans`` + ``LogisticRegression`` /
  ``GradientBoostingClassifier`` for the production-quality path; when
  it is not, we fall back to in-house implementations of:
    - Lloyd's k-means (random restart × ``n_init``, k-means++ seeding)
    - Silhouette score (Euclidean)
    - Logistic regression (L2-regularized, IRLS / batch gradient descent)
    - ROC-AUC (rank-pair sum, O(n log n))
* **Pure functions; no side effects.** Side-effects (writing reports,
  loading JSONL) live in ``scripts/research/run_k53_loser_anti_pattern.py``.
* **Time-slice cross-validation.** Regime non-stationarity is the
  number-one risk for any "anti-pattern" classifier — H1-2026 looks
  nothing like H2-2026 (XAUUSD WR 64.5% → 24.0%, χ²=0.006). We surface
  both train AUC and held-out time-slice AUC so the reader can see the
  drop. A train-test ratio < 0.85 typically flags strong regime drift.
* **Memory ``project_a1_dumb_baseline_verdict_2026-04-26``** — A1 found
  SYSTEM_DECAY (mechanical-vs-AI gap stable across the year). Losing
  trades are likely concentrated in setups where AI selectivity broke,
  so the clusters MAY skew toward H2-2026 frequency.
* **Memory ``project_trade_records_enrichment_gap``** — realized R lives
  in three places: ``knowledge_base/index/_trade_index.json`` (live
  trades), ``knowledge_base_backtest/sessions/`` (backtest), and
  ``research/accepted_candidates_loser_mining/unified_filled_cands.jsonl``
  (unified Phase 1 + Tier 2 schema, 217 rows, 101 losers). The CLI
  defaults to the unified jsonl and falls back to ``--input`` overrides.
* **F3 source-stratification (2026-04-27).** The original K53 (commit
  ``2d3afa4``) reported severe overfitting (train AUC 0.996 → H2 holdout
  0.598). Diagnosis: the jsonl conflates Phase 1 (XAUUSD/USDJPY full MSO
  schema, 75 rows) with Tier 2 (parsed AI-response only, 142 rows).
  Median-imputed missing fields make the source itself a label leakage
  signal. F3 adds ``cluster_losers_by_source`` and
  ``train_loss_classifier_per_source`` — clusters and classifiers run
  WITHIN each source so schema differences cannot drive the result.
  Use ``--source-filter phase1`` for the honest baseline; use
  ``--per-source`` for independent cluster/classifier sets per source.

Public API
----------
``cluster_losers(loser_features, k_range=(3, 7), feature_names=...) -> ClusterReport``
    K-means cluster losers. Picks optimal k by silhouette score.

``cluster_losers_by_source(losers, sources, k_range=...) -> dict[str, ClusterReport]``
    Run ``cluster_losers`` independently per source tag. Avoids the
    cross-source schema-confound failure mode.

``train_loss_classifier(X, y, time_slice_split=...) -> ClassifierReport``
    Fit a binary loss-vs-win classifier. Reports both random-split AUC
    and held-out time-slice AUC + per-feature importance.

``train_loss_classifier_per_source(X, y, sources, ...) -> dict[str, ClassifierReport]``
    Train one classifier per source tag. Returns a per-source dict.

``describe_cluster(cluster_id, centroid, feature_names) -> str``
    Human-readable per-cluster description (top-3 features by absolute
    deviation from population centroid).

Out of scope
------------
* Does NOT modify production code. Pure-research module.
* Does NOT call AI / Anthropic API.
* Does NOT propose system changes — that is K54's job.
"""

from __future__ import annotations

import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence


# ────────────────────────────────────────────────────────────────────────────
# Public dataclasses
# ────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ClusterReport:
    """Result of clustering losing-trade feature vectors.

    Attributes
    ----------
    k : int
        Optimal cluster count (chosen by silhouette score).
    silhouette : float
        Silhouette score for the selected k. Range [-1, 1]; >0.5 is
        strong, 0.25-0.5 is reasonable, <0.25 is weak structure.
    silhouette_by_k : dict[int, float]
        Silhouette score for each k searched. Useful to see whether the
        peak is sharp or flat.
    labels : list[int]
        Cluster index for each loser, length == n_losers.
    centroids : list[list[float]]
        Per-cluster centroid in feature-vector space.
        ``centroids[c][f]`` is the mean of feature f within cluster c.
    cluster_sizes : list[int]
        Number of losers per cluster.
    cluster_means_r : list[float]
        Mean realized R per cluster. (Always ≤ 0 since losers only.)
    cluster_win_rates : list[float]
        Always 0.0 (clustering is on losers only) — present for symmetry
        with the full-population variant the caller can compute later.
    feature_names : list[str]
        Names of features in the order they appear in centroids.
    n_features : int
        Length of each feature vector.
    n_losers : int
        Number of losing trades clustered.
    population_centroid : list[float]
        Centroid of all losers (used by ``describe_cluster`` to compute
        cluster-vs-population deviation).
    n_init : int
        Number of random restarts used in k-means.
    converged : bool
        Whether the chosen-k k-means run converged within ``max_iter``.
    sklearn_used : bool
        Whether the result came from scikit-learn (True) or the
        in-house fallback (False).
    """

    k: int
    silhouette: float
    silhouette_by_k: dict[int, float]
    labels: list[int]
    centroids: list[list[float]]
    cluster_sizes: list[int]
    cluster_means_r: list[float]
    cluster_win_rates: list[float]
    feature_names: list[str]
    n_features: int
    n_losers: int
    population_centroid: list[float]
    n_init: int
    converged: bool
    sklearn_used: bool


@dataclass(frozen=True)
class ClassifierReport:
    """Result of training a binary loss-vs-win classifier.

    Attributes
    ----------
    train_auc : float
        ROC-AUC on the random-split training set (in-sample after fit
        — used as upper-bound reference, not a generalization metric).
    test_auc : float
        ROC-AUC on the held-out random-split test set.
    holdout_auc : float
        ROC-AUC on the time-slice held-out set (rows whose timestamp is
        ≥ ``time_slice_split``). This is the regime-non-stationarity
        metric — if it sags far below ``test_auc`` the classifier
        memorized the training regime.
    holdout_n : int
        Number of rows in the time-slice holdout.
    regime_stationarity_ratio : float
        ``holdout_auc / test_auc``. < 0.85 implies meaningful regime
        drift between train and holdout slice.
    feature_importance : list[tuple[str, float]]
        Per-feature contribution sorted descending by absolute weight.
        For LR this is the absolute standardized coefficient; for GBM
        it is the relative impurity-decrease feature importance.
    feature_names : list[str]
        Order of features in the trained model.
    classifier_type : str
        ``"logistic_regression"`` or ``"gradient_boosting"`` or
        ``"logistic_regression_inhouse"`` (sklearn fallback).
    n_train : int
        Train-split size (random split).
    n_test : int
        Test-split size (random split).
    converged : bool
        Whether the fit converged within budget.
    sklearn_used : bool
        Whether sklearn was available.
    """

    train_auc: float
    test_auc: float
    holdout_auc: float
    holdout_n: int
    regime_stationarity_ratio: float
    feature_importance: list[tuple[str, float]]
    feature_names: list[str]
    classifier_type: str
    n_train: int
    n_test: int
    converged: bool
    sklearn_used: bool


# ────────────────────────────────────────────────────────────────────────────
# sklearn detection
# ────────────────────────────────────────────────────────────────────────────


def _has_sklearn() -> bool:
    try:
        import sklearn  # noqa: F401
        return True
    except ImportError:
        return False


# ────────────────────────────────────────────────────────────────────────────
# In-house numerical primitives (used when sklearn is absent)
# ────────────────────────────────────────────────────────────────────────────


def _euclid_sq(a: Sequence[float], b: Sequence[float]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b))


def _euclid(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(_euclid_sq(a, b))


def _kmeans_pp_init(
    data: list[list[float]], k: int, rng: random.Random
) -> list[list[float]]:
    """k-means++ seeding: pick centroids preferring points far from chosen ones."""
    n = len(data)
    centroids: list[list[float]] = []
    # First centroid uniformly at random.
    centroids.append(list(data[rng.randrange(n)]))
    while len(centroids) < k:
        d2: list[float] = []
        for p in data:
            best = min(_euclid_sq(p, c) for c in centroids)
            d2.append(best)
        s = sum(d2)
        if s <= 0:
            # All points coincide with chosen centroids → just pick at random.
            centroids.append(list(data[rng.randrange(n)]))
            continue
        r = rng.random() * s
        cum = 0.0
        chosen = n - 1
        for i, v in enumerate(d2):
            cum += v
            if cum >= r:
                chosen = i
                break
        centroids.append(list(data[chosen]))
    return centroids


def _kmeans_inhouse(
    data: list[list[float]],
    k: int,
    *,
    n_init: int = 10,
    max_iter: int = 300,
    tol: float = 1e-4,
    seed: int = 0,
) -> tuple[list[int], list[list[float]], float, bool]:
    """Lloyd's algorithm with k-means++ seeding and ``n_init`` random restarts.

    Returns ``(labels, centroids, inertia, converged)``.
    """
    n = len(data)
    if n == 0:
        return ([], [[0.0] * 0 for _ in range(k)], 0.0, True)
    if k <= 0:
        raise ValueError("k must be ≥ 1")
    if k > n:
        raise ValueError(f"k ({k}) must be ≤ n_samples ({n})")
    n_features = len(data[0])

    best_labels: list[int] = []
    best_centroids: list[list[float]] = []
    best_inertia = float("inf")
    best_converged = False

    base_rng = random.Random(seed)

    for restart in range(n_init):
        rng = random.Random(base_rng.randrange(1 << 30))
        centroids = _kmeans_pp_init(data, k, rng)
        labels = [0] * n
        converged = False
        for _it in range(max_iter):
            # Assignment.
            new_labels = []
            for p in data:
                best_c = 0
                best_d = _euclid_sq(p, centroids[0])
                for ci in range(1, k):
                    d = _euclid_sq(p, centroids[ci])
                    if d < best_d:
                        best_d = d
                        best_c = ci
                new_labels.append(best_c)
            # Centroid update.
            sums = [[0.0] * n_features for _ in range(k)]
            counts = [0] * k
            for li, p in zip(new_labels, data):
                for fi, v in enumerate(p):
                    sums[li][fi] += v
                counts[li] += 1
            new_centroids: list[list[float]] = []
            for ci in range(k):
                if counts[ci] == 0:
                    # Reseed empty cluster: pick the data point furthest from
                    # the current centroid set.
                    far_idx = 0
                    far_d = -1.0
                    for pi, p in enumerate(data):
                        d = min(_euclid_sq(p, c) for c in centroids)
                        if d > far_d:
                            far_d = d
                            far_idx = pi
                    new_centroids.append(list(data[far_idx]))
                else:
                    new_centroids.append([s / counts[ci] for s in sums[ci]])

            # Convergence check.
            shift = max(
                _euclid_sq(c_old, c_new)
                for c_old, c_new in zip(centroids, new_centroids)
            )
            centroids = new_centroids
            labels = new_labels
            if shift < tol * tol:
                converged = True
                break

        # Compute inertia.
        inertia = 0.0
        for li, p in zip(labels, data):
            inertia += _euclid_sq(p, centroids[li])

        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels
            best_centroids = centroids
            best_converged = converged

    return best_labels, best_centroids, best_inertia, best_converged


def _silhouette_inhouse(data: list[list[float]], labels: list[int]) -> float:
    """Mean silhouette coefficient over all points (Euclidean).

    Returns 0.0 when there is < 2 distinct clusters, mirroring sklearn
    behavior of returning a defined-but-meaningless value.
    """
    n = len(data)
    if n < 2:
        return 0.0
    distinct = len(set(labels))
    if distinct < 2:
        return 0.0

    # Group point indices by cluster for O(n*k) cost rather than O(n^2).
    by_cluster: dict[int, list[int]] = {}
    for i, c in enumerate(labels):
        by_cluster.setdefault(c, []).append(i)

    s_total = 0.0
    for i, p in enumerate(data):
        own = labels[i]
        # a(i): mean distance to other points in own cluster.
        own_indices = [j for j in by_cluster[own] if j != i]
        if not own_indices:
            # Singleton cluster contributes 0.
            continue
        a_i = sum(_euclid(p, data[j]) for j in own_indices) / len(own_indices)
        # b(i): min over other clusters of mean distance to that cluster.
        b_i = float("inf")
        for c, idxs in by_cluster.items():
            if c == own or not idxs:
                continue
            mean_d = sum(_euclid(p, data[j]) for j in idxs) / len(idxs)
            if mean_d < b_i:
                b_i = mean_d
        if b_i == float("inf"):
            continue
        denom = max(a_i, b_i)
        if denom == 0:
            continue
        s_total += (b_i - a_i) / denom

    return s_total / n


def _logistic_inhouse(
    X: list[list[float]],
    y: list[int],
    *,
    l2: float = 1.0,
    lr: float = 0.05,
    max_iter: int = 2000,
    tol: float = 1e-6,
) -> tuple[list[float], float, bool]:
    """L2-regularized logistic regression via batch gradient descent.

    Returns ``(weights, intercept, converged)``.
    Standardizes features internally (mean-0, std-1) so the L2 penalty is
    scale-invariant; the returned weights apply to standardized features.
    """
    n = len(X)
    if n == 0:
        return ([], 0.0, True)
    p = len(X[0])

    # Standardize.
    means = [sum(row[j] for row in X) / n for j in range(p)]
    stds = []
    for j in range(p):
        var = sum((row[j] - means[j]) ** 2 for row in X) / n
        s = math.sqrt(var) if var > 0 else 1.0
        stds.append(s)
    Xs = [[(row[j] - means[j]) / stds[j] for j in range(p)] for row in X]

    w = [0.0] * p
    b = 0.0
    prev_loss = float("inf")
    converged = False
    for _it in range(max_iter):
        # Predict.
        preds: list[float] = []
        for row in Xs:
            z = b + sum(w[j] * row[j] for j in range(p))
            # Sigmoid with overflow guard.
            if z >= 0:
                ez = math.exp(-z)
                preds.append(1.0 / (1.0 + ez))
            else:
                ez = math.exp(z)
                preds.append(ez / (1.0 + ez))
        # Loss (binary cross-entropy + L2/2).
        loss = 0.0
        for i, yi in enumerate(y):
            pi = preds[i]
            # clip to avoid log(0)
            pi = min(max(pi, 1e-12), 1 - 1e-12)
            loss -= yi * math.log(pi) + (1 - yi) * math.log(1 - pi)
        loss /= n
        loss += 0.5 * l2 * sum(wi * wi for wi in w) / n

        if abs(prev_loss - loss) < tol:
            converged = True
            break
        prev_loss = loss

        # Gradient.
        gw = [0.0] * p
        gb = 0.0
        for i, yi in enumerate(y):
            err = preds[i] - yi
            for j in range(p):
                gw[j] += err * Xs[i][j]
            gb += err
        for j in range(p):
            gw[j] = gw[j] / n + l2 * w[j] / n
        gb /= n
        # Step.
        for j in range(p):
            w[j] -= lr * gw[j]
        b -= lr * gb

    return w, b, converged


def _predict_proba_inhouse(
    X: list[list[float]],
    w: list[float],
    b: float,
    means: list[float],
    stds: list[float],
) -> list[float]:
    out = []
    for row in X:
        z = b
        for j, wj in enumerate(w):
            z += wj * (row[j] - means[j]) / (stds[j] if stds[j] > 0 else 1.0)
        if z >= 0:
            ez = math.exp(-z)
            out.append(1.0 / (1.0 + ez))
        else:
            ez = math.exp(z)
            out.append(ez / (1.0 + ez))
    return out


def _roc_auc(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """ROC-AUC via the rank-pair formula.

    Tied scores split the credit (Mann-Whitney U variant). Returns 0.5
    when one class is empty (degenerate).
    """
    pairs = sorted(zip(y_score, y_true))
    n_pos = sum(1 for v in y_true if v == 1)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
    # Sum of ranks of positives.
    rank_sum = 0.0
    i = 0
    rank = 1
    while i < len(pairs):
        j = i
        while j + 1 < len(pairs) and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (rank + rank + (j - i)) / 2.0
        for k in range(i, j + 1):
            if pairs[k][1] == 1:
                rank_sum += avg_rank
        rank += (j - i + 1)
        i = j + 1
    auc = (rank_sum - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return auc


# ────────────────────────────────────────────────────────────────────────────
# Public API
# ────────────────────────────────────────────────────────────────────────────


def cluster_losers(
    loser_features: list[list[float]],
    *,
    k_range: tuple[int, int] = (3, 7),
    feature_names: Optional[list[str]] = None,
    realized_r: Optional[list[float]] = None,
    n_init: int = 10,
    seed: int = 0,
    prefer_sklearn: bool = True,
) -> ClusterReport:
    """K-means cluster a population of losing-trade feature vectors.

    Parameters
    ----------
    loser_features : list[list[float]]
        Feature matrix for losers only. Shape ``[n_losers, n_features]``.
    k_range : tuple[int, int]
        Inclusive ``(k_min, k_max)`` range to search. Default ``(3, 7)``.
    feature_names : list[str], optional
        Per-feature human labels used by ``describe_cluster``.
    realized_r : list[float], optional
        Per-loser realized R-multiple. If provided, ``cluster_means_r``
        is the per-cluster mean. Otherwise it is filled with zeros.
    n_init : int
        Random restarts in k-means. Default 10.
    seed : int
        Seed for random initialization. Default 0.
    prefer_sklearn : bool
        Use sklearn when available. Default True.

    Returns
    -------
    ClusterReport
        Picks ``k`` by maximum silhouette score across ``k_range``.

    Raises
    ------
    ValueError
        If ``loser_features`` is empty or feature vectors are ragged.
    """
    n = len(loser_features)
    if n == 0:
        raise ValueError("loser_features is empty — need at least 1 loser")
    n_features = len(loser_features[0])
    if n_features == 0:
        raise ValueError("feature vectors are zero-length")
    for i, row in enumerate(loser_features):
        if len(row) != n_features:
            raise ValueError(
                f"ragged feature matrix: row {i} has {len(row)} features, "
                f"expected {n_features}"
            )

    if feature_names is None:
        feature_names = [f"f{i}" for i in range(n_features)]
    if len(feature_names) != n_features:
        raise ValueError(
            f"feature_names length {len(feature_names)} ≠ n_features {n_features}"
        )

    k_min, k_max = k_range
    if k_min < 2:
        raise ValueError("k_min must be ≥ 2 (silhouette undefined for k=1)")
    # Cap k_max at n_samples - 1 so k-means is well-defined.
    k_max = min(k_max, n - 1)
    if k_max < k_min:
        # Tiny dataset: collapse to a single k attempt.
        k_max = k_min = max(2, min(k_min, n - 1))

    silhouette_by_k: dict[int, float] = {}
    best_k: Optional[int] = None
    best_score = -2.0
    best_labels: list[int] = []
    best_centroids: list[list[float]] = []
    best_converged = False

    use_sklearn = prefer_sklearn and _has_sklearn()
    if use_sklearn:
        # Lazy import; tolerated to not break --no-sklearn fallback path.
        from sklearn.cluster import KMeans
        from sklearn.metrics import silhouette_score

        for k in range(k_min, k_max + 1):
            try:
                km = KMeans(
                    n_clusters=k,
                    n_init=n_init,
                    random_state=seed,
                    max_iter=300,
                )
                labels = km.fit_predict(loser_features).tolist()
                if len(set(labels)) < 2:
                    silhouette_by_k[k] = 0.0
                    continue
                score = float(silhouette_score(loser_features, labels))
            except Exception:
                # Defensive: degenerate input → fall back inhouse for this k.
                labels, cents, _inertia, conv = _kmeans_inhouse(
                    loser_features, k, n_init=n_init, seed=seed + k
                )
                score = _silhouette_inhouse(loser_features, labels)
                silhouette_by_k[k] = score
                if score > best_score:
                    best_score = score
                    best_k = k
                    best_labels = labels
                    best_centroids = cents
                    best_converged = conv
                continue

            silhouette_by_k[k] = score
            if score > best_score:
                best_score = score
                best_k = k
                best_labels = labels
                best_centroids = [list(c) for c in km.cluster_centers_]
                best_converged = bool(km.n_iter_ < 300)
    else:
        for k in range(k_min, k_max + 1):
            labels, cents, _inertia, conv = _kmeans_inhouse(
                loser_features, k, n_init=n_init, seed=seed + k
            )
            if len(set(labels)) < 2:
                silhouette_by_k[k] = 0.0
                continue
            score = _silhouette_inhouse(loser_features, labels)
            silhouette_by_k[k] = score
            if score > best_score:
                best_score = score
                best_k = k
                best_labels = labels
                best_centroids = cents
                best_converged = conv

    if best_k is None:
        # All ks degenerate — pick k_min as a sentinel and fill with single cluster.
        best_k = k_min
        best_score = 0.0
        labels, cents, _inertia, conv = _kmeans_inhouse(
            loser_features, k_min, n_init=n_init, seed=seed
        )
        best_labels = labels
        best_centroids = cents
        best_converged = conv

    # Cluster-size + per-cluster mean R.
    cluster_sizes = [0] * best_k
    cluster_r_sum = [0.0] * best_k
    cluster_r_n = [0] * best_k
    for i, ci in enumerate(best_labels):
        cluster_sizes[ci] += 1
        if realized_r is not None and realized_r[i] is not None:
            cluster_r_sum[ci] += realized_r[i]
            cluster_r_n[ci] += 1
    cluster_means_r = [
        (cluster_r_sum[c] / cluster_r_n[c]) if cluster_r_n[c] > 0 else 0.0
        for c in range(best_k)
    ]
    # Win rates within losers-only clusters are always zero.
    cluster_win_rates = [0.0] * best_k

    # Population centroid (across all losers).
    pop_centroid = [
        sum(row[j] for row in loser_features) / n for j in range(n_features)
    ]

    return ClusterReport(
        k=best_k,
        silhouette=best_score,
        silhouette_by_k=silhouette_by_k,
        labels=best_labels,
        centroids=best_centroids,
        cluster_sizes=cluster_sizes,
        cluster_means_r=cluster_means_r,
        cluster_win_rates=cluster_win_rates,
        feature_names=list(feature_names),
        n_features=n_features,
        n_losers=n,
        population_centroid=pop_centroid,
        n_init=n_init,
        converged=best_converged,
        sklearn_used=use_sklearn,
    )


def train_loss_classifier(
    X: list[list[float]],
    y: list[int],
    *,
    feature_names: Optional[list[str]] = None,
    timestamps: Optional[list[Any]] = None,
    time_slice_split: Optional[Any] = None,
    classifier: str = "logistic_regression",
    test_frac: float = 0.25,
    seed: int = 0,
    prefer_sklearn: bool = True,
) -> ClassifierReport:
    """Fit a binary loss-vs-win classifier with random + time-slice holdout.

    Parameters
    ----------
    X : list[list[float]]
        Full population feature matrix. Shape ``[n, p]``.
    y : list[int]
        Binary label. ``1`` = LOSS (realized_r ≤ 0), ``0`` = WIN.
    feature_names : list[str], optional
        Per-feature labels for the importance report.
    timestamps : list[Any], optional
        Per-row timestamps (anything orderable). Required when
        ``time_slice_split`` is non-None.
    time_slice_split : Any, optional
        Threshold value for time-slice holdout: rows with
        ``timestamps[i] >= time_slice_split`` go to the holdout. When
        None, ``holdout_auc`` is set to ``test_auc`` (no separate time
        slice computed).
    classifier : str
        ``"logistic_regression"`` (default) or ``"gradient_boosting"``.
        Falls back to in-house LR if sklearn is missing.
    test_frac : float
        Fraction of data held out for random-split test AUC.
    seed : int
        Reproducibility seed for splits.
    prefer_sklearn : bool
        Use sklearn when available.

    Returns
    -------
    ClassifierReport

    Raises
    ------
    ValueError
        If ``X`` is empty, ``y`` length mismatch, or only one class present.
    """
    n = len(X)
    if n == 0:
        raise ValueError("X is empty")
    if len(y) != n:
        raise ValueError(f"y length {len(y)} ≠ X length {n}")
    if len(set(y)) < 2:
        raise ValueError("need both classes (loss and win) in y")
    p = len(X[0])
    if feature_names is None:
        feature_names = [f"f{i}" for i in range(p)]
    if len(feature_names) != p:
        raise ValueError(
            f"feature_names length {len(feature_names)} ≠ n_features {p}"
        )

    if timestamps is not None and len(timestamps) != n:
        raise ValueError("timestamps length mismatch")

    rng = random.Random(seed)
    indices = list(range(n))
    rng.shuffle(indices)

    # Time-slice holdout BEFORE the random train/test split.
    holdout_idx: set[int] = set()
    if time_slice_split is not None and timestamps is not None:
        for i in range(n):
            if timestamps[i] is not None and timestamps[i] >= time_slice_split:
                holdout_idx.add(i)

    pool = [i for i in indices if i not in holdout_idx]
    n_pool = len(pool)
    n_test = max(1, int(round(n_pool * test_frac)))
    test_idx = set(pool[:n_test])
    train_idx = [i for i in pool if i not in test_idx]

    X_train = [X[i] for i in train_idx]
    y_train = [y[i] for i in train_idx]
    X_test = [X[i] for i in test_idx]
    y_test = [y[i] for i in test_idx]
    X_hold = [X[i] for i in holdout_idx]
    y_hold = [y[i] for i in holdout_idx]

    use_sklearn = prefer_sklearn and _has_sklearn()
    converged = True

    if use_sklearn and classifier in ("logistic_regression", "gradient_boosting"):
        from sklearn.linear_model import LogisticRegression
        from sklearn.ensemble import GradientBoostingClassifier
        from sklearn.preprocessing import StandardScaler

        if len(set(y_train)) < 2:
            # Degenerate train fold; fall through to inhouse on full data.
            use_sklearn = False
        else:
            if classifier == "logistic_regression":
                scaler = StandardScaler()
                Xs_train = scaler.fit_transform(X_train).tolist()
                Xs_test = scaler.transform(X_test).tolist() if X_test else []
                Xs_hold = scaler.transform(X_hold).tolist() if X_hold else []
                model = LogisticRegression(max_iter=2000, C=1.0, random_state=seed)
                model.fit(Xs_train, y_train)
                proba_train = [pi[1] for pi in model.predict_proba(Xs_train)]
                proba_test = (
                    [pi[1] for pi in model.predict_proba(Xs_test)] if Xs_test else []
                )
                proba_hold = (
                    [pi[1] for pi in model.predict_proba(Xs_hold)] if Xs_hold else []
                )
                # Importance: standardized abs coefficient (since scaler fit).
                coef = list(model.coef_[0])
                fi = list(zip(feature_names, [abs(c) for c in coef]))
                clf_label = "logistic_regression"
                converged = bool(model.n_iter_[0] < 2000)
            else:  # gradient_boosting
                model = GradientBoostingClassifier(
                    n_estimators=100,
                    max_depth=3,
                    random_state=seed,
                )
                model.fit(X_train, y_train)
                proba_train = [pi[1] for pi in model.predict_proba(X_train)]
                proba_test = (
                    [pi[1] for pi in model.predict_proba(X_test)] if X_test else []
                )
                proba_hold = (
                    [pi[1] for pi in model.predict_proba(X_hold)] if X_hold else []
                )
                fi = list(zip(feature_names, list(model.feature_importances_)))
                clf_label = "gradient_boosting"
                converged = True

    if not use_sklearn or classifier not in ("logistic_regression", "gradient_boosting"):
        # In-house LR fallback.
        if len(set(y_train)) < 2:
            # Cannot train on a single-class fold — fall back to full population.
            X_train = list(X)
            y_train = list(y)
        # Compute scaler params on the train fold.
        n_tr = len(X_train)
        means = [sum(row[j] for row in X_train) / n_tr for j in range(p)]
        stds = []
        for j in range(p):
            var = sum((row[j] - means[j]) ** 2 for row in X_train) / n_tr
            stds.append(math.sqrt(var) if var > 0 else 1.0)

        w, b, converged = _logistic_inhouse(X_train, y_train)
        proba_train = _predict_proba_inhouse(X_train, w, b, means, stds)
        proba_test = _predict_proba_inhouse(X_test, w, b, means, stds) if X_test else []
        proba_hold = _predict_proba_inhouse(X_hold, w, b, means, stds) if X_hold else []
        fi = list(zip(feature_names, [abs(wi) for wi in w]))
        clf_label = "logistic_regression_inhouse"

    train_auc = _roc_auc(y_train, proba_train) if y_train else 0.5
    test_auc = _roc_auc(y_test, proba_test) if y_test else 0.5
    if y_hold:
        holdout_auc = _roc_auc(y_hold, proba_hold)
    else:
        holdout_auc = test_auc

    fi.sort(key=lambda kv: kv[1], reverse=True)

    if test_auc <= 0:
        ratio = 0.0
    else:
        ratio = holdout_auc / test_auc

    return ClassifierReport(
        train_auc=train_auc,
        test_auc=test_auc,
        holdout_auc=holdout_auc,
        holdout_n=len(y_hold),
        regime_stationarity_ratio=ratio,
        feature_importance=fi,
        feature_names=list(feature_names),
        classifier_type=clf_label,
        n_train=len(y_train),
        n_test=len(y_test),
        converged=converged,
        sklearn_used=use_sklearn,
    )


def describe_cluster(
    cluster_id: int,
    centroid: Sequence[float],
    feature_names: Sequence[str],
    *,
    population_centroid: Optional[Sequence[float]] = None,
    top_k: int = 3,
) -> str:
    """Render a human-readable description of a single cluster.

    Top features are picked by absolute deviation from the population
    centroid (so a cluster that is "average on everything except touch
    count = 5" highlights touch count, not the average features).

    Parameters
    ----------
    cluster_id : int
    centroid : Sequence[float]
        Cluster centroid in feature-vector space.
    feature_names : Sequence[str]
        Feature labels in the same order as ``centroid``.
    population_centroid : Sequence[float], optional
        Centroid across ALL losers — used to compute deviation. When
        None, top features are chosen by absolute centroid magnitude
        (less informative; still works).
    top_k : int
        Number of distinguishing features to surface. Default 3.

    Returns
    -------
    str
        Multi-line human-readable description.
    """
    if len(centroid) != len(feature_names):
        raise ValueError("centroid / feature_names length mismatch")

    if population_centroid is not None and len(population_centroid) != len(centroid):
        raise ValueError("population_centroid length mismatch")

    if population_centroid is None:
        deviations = [(name, val, val) for name, val in zip(feature_names, centroid)]
    else:
        deviations = [
            (name, val, val - pop)
            for name, val, pop in zip(feature_names, centroid, population_centroid)
        ]
    # Sort by absolute deviation descending.
    ranked = sorted(deviations, key=lambda t: abs(t[2]), reverse=True)

    lines = [f"Cluster {cluster_id} — top {top_k} distinguishing features:"]
    for name, val, dev in ranked[:top_k]:
        if population_centroid is None:
            lines.append(f"  - {name}: {val:.3f}")
        else:
            sign = "+" if dev >= 0 else ""
            lines.append(
                f"  - {name}: {val:.3f} ({sign}{dev:.3f} vs population mean)"
            )
    # Render ALL feature centroids for completeness — tests rely on every
    # feature appearing in the rendered string.
    lines.append("  All feature centroids:")
    for name, val in zip(feature_names, centroid):
        lines.append(f"    {name}: {val:.3f}")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────────────
# F3 — Source-stratified API (avoid Phase 1 vs Tier 2 schema confound)
# ────────────────────────────────────────────────────────────────────────────


def cluster_losers_by_source(
    loser_features: list[list[float]],
    sources: Sequence[str],
    *,
    k_range: tuple[int, int] = (3, 7),
    feature_names: Optional[list[str]] = None,
    realized_r: Optional[list[float]] = None,
    n_init: int = 10,
    seed: int = 0,
    prefer_sklearn: bool = True,
    min_n_per_source: int = 8,
) -> dict[str, ClusterReport]:
    """Cluster losers WITHIN each source independently.

    The original K53 ran a single k-means across the joined Phase 1 + Tier 2
    matrix, which let the source-schema gap (Phase 1 carries full MSO numeric
    fields, Tier 2 has median-imputed defaults) drive clustering. This
    function partitions losers by ``sources`` tag and clusters each subset
    independently — every returned ``ClusterReport`` is honest within its
    own source.

    Parameters
    ----------
    loser_features : list[list[float]]
        Loser-only feature matrix.
    sources : Sequence[str]
        Per-row source tag, length == len(loser_features). Free-form;
        common values are ``"phase1"``, ``"tier2"``, ``"batch_session"``,
        ``"legacy"``.
    k_range : tuple[int, int]
        Inclusive ``(k_min, k_max)`` for each per-source clustering. The
        upper bound is clamped per source by ``cluster_losers``.
    feature_names : list[str], optional
    realized_r : list[float], optional
        Per-loser realized R; per-source mean R is recorded.
    n_init, seed, prefer_sklearn :
        Pass-through to ``cluster_losers``.
    min_n_per_source : int
        Minimum loser count to attempt clustering for a source. Sources
        below this threshold are still returned as a ClusterReport with
        ``k=1`` and silhouette=0.0 (sentinel: "not enough data"). Default
        8 (k_min=3 needs at least k+1 = 4, but silhouette plateaus below
        about 8 points per cluster).

    Returns
    -------
    dict[str, ClusterReport]
        ``{source: ClusterReport}``. Sources with fewer than
        ``min_n_per_source`` losers map to a sentinel report with
        ``k=1`` and silhouette ``0.0`` so the caller can render the
        empty case without branching.

    Raises
    ------
    ValueError
        If lengths mismatch, realized_r length mismatches, or all sources
        contain fewer than ``min_n_per_source`` losers (caller should
        not have called this).
    """
    if len(sources) != len(loser_features):
        raise ValueError(
            f"sources length {len(sources)} ≠ loser_features length "
            f"{len(loser_features)}"
        )
    if realized_r is not None and len(realized_r) != len(loser_features):
        raise ValueError(
            f"realized_r length {len(realized_r)} ≠ loser_features length "
            f"{len(loser_features)}"
        )

    # Group row indices by source tag.
    by_source: dict[str, list[int]] = {}
    for i, s in enumerate(sources):
        by_source.setdefault(s, []).append(i)

    out: dict[str, ClusterReport] = {}
    for src, idxs in by_source.items():
        sub_X = [loser_features[i] for i in idxs]
        sub_r = [realized_r[i] for i in idxs] if realized_r is not None else None
        if len(sub_X) < min_n_per_source:
            # Return sentinel: a single-cluster degenerate report.
            n_features = len(sub_X[0]) if sub_X else (
                len(feature_names) if feature_names else 0
            )
            fnames = feature_names or [f"f{i}" for i in range(n_features)]
            pop = (
                [sum(row[j] for row in sub_X) / len(sub_X) for j in range(n_features)]
                if sub_X
                else [0.0] * n_features
            )
            mean_r = (
                (sum(sub_r) / len(sub_r)) if sub_r else 0.0
            ) if sub_r else 0.0
            out[src] = ClusterReport(
                k=1,
                silhouette=0.0,
                silhouette_by_k={},
                labels=[0] * len(sub_X),
                centroids=[pop] if pop else [],
                cluster_sizes=[len(sub_X)] if sub_X else [],
                cluster_means_r=[mean_r] if sub_X else [],
                cluster_win_rates=[0.0] if sub_X else [],
                feature_names=list(fnames),
                n_features=n_features,
                n_losers=len(sub_X),
                population_centroid=pop,
                n_init=n_init,
                converged=True,
                sklearn_used=False,
            )
            continue

        # Clamp k_max so we never request k > n - 1 per source.
        k_min, k_max = k_range
        capped = (k_min, min(k_max, max(k_min, len(sub_X) - 1)))
        out[src] = cluster_losers(
            sub_X,
            k_range=capped,
            feature_names=feature_names,
            realized_r=sub_r,
            n_init=n_init,
            seed=seed,
            prefer_sklearn=prefer_sklearn,
        )

    if not out:
        raise ValueError("no source groups produced — sources collection is empty")
    return out


def train_loss_classifier_per_source(
    X: list[list[float]],
    y: list[int],
    sources: Sequence[str],
    *,
    feature_names: Optional[list[str]] = None,
    timestamps: Optional[list[Any]] = None,
    time_slice_split: Optional[Any] = None,
    classifier: str = "logistic_regression",
    test_frac: float = 0.25,
    seed: int = 0,
    prefer_sklearn: bool = True,
    min_n_per_source: int = 20,
) -> dict[str, ClassifierReport]:
    """Train one classifier per source tag.

    F3 mandate: the original K53 trained on the joined Phase 1 + Tier 2
    matrix and got train AUC 0.996 → H2 holdout 0.598. Joint training lets
    the model memorize the source-schema gap as a label-leakage signal.
    This per-source path trains independent classifiers — the per-source
    holdout AUCs are the honest generalization metric.

    Parameters
    ----------
    X, y, feature_names, timestamps, time_slice_split, classifier,
    test_frac, seed, prefer_sklearn :
        Pass-through to ``train_loss_classifier``.
    sources : Sequence[str]
        Per-row source tag, length == len(X).
    min_n_per_source : int
        Minimum n to attempt fitting for a source. Sources below this
        threshold (default 20) are skipped — single-source classifiers
        on n < 20 are noise-dominated. Skipped sources do NOT appear in
        the returned dict.

    Returns
    -------
    dict[str, ClassifierReport]
        ``{source: ClassifierReport}``. Sources skipped for size or
        single-class y are absent from the dict (caller decides handling).

    Raises
    ------
    ValueError
        Length mismatch on sources or y or timestamps.
    """
    if len(sources) != len(X):
        raise ValueError(
            f"sources length {len(sources)} ≠ X length {len(X)}"
        )
    if len(y) != len(X):
        raise ValueError(f"y length {len(y)} ≠ X length {len(X)}")
    if timestamps is not None and len(timestamps) != len(X):
        raise ValueError(
            f"timestamps length {len(timestamps)} ≠ X length {len(X)}"
        )

    by_source: dict[str, list[int]] = {}
    for i, s in enumerate(sources):
        by_source.setdefault(s, []).append(i)

    out: dict[str, ClassifierReport] = {}
    for src, idxs in by_source.items():
        if len(idxs) < min_n_per_source:
            continue
        sub_X = [X[i] for i in idxs]
        sub_y = [y[i] for i in idxs]
        if len(set(sub_y)) < 2:
            # Single-class fold cannot train a classifier — skip.
            continue
        sub_ts = [timestamps[i] for i in idxs] if timestamps is not None else None
        try:
            out[src] = train_loss_classifier(
                sub_X,
                sub_y,
                feature_names=feature_names,
                timestamps=sub_ts,
                time_slice_split=time_slice_split,
                classifier=classifier,
                test_frac=test_frac,
                seed=seed,
                prefer_sklearn=prefer_sklearn,
            )
        except ValueError:
            # Training degenerate for this source (e.g. ts holdout single-class).
            continue
    return out


# ────────────────────────────────────────────────────────────────────────────
# Cluster-frequency helper (used by the CLI to compute H2-2026 frequency
# per cluster — pure-Python; tests cover the math path)
# ────────────────────────────────────────────────────────────────────────────


def cluster_frequency_in_window(
    labels: Sequence[int],
    timestamps: Sequence[Any],
    *,
    window_start: Any,
    window_end: Optional[Any] = None,
    n_clusters: Optional[int] = None,
) -> dict[int, dict[str, float]]:
    """Compute per-cluster frequency in a time window.

    Parameters
    ----------
    labels : Sequence[int]
        Cluster index per row, length == len(timestamps).
    timestamps : Sequence[Any]
        Anything orderable; a ``None`` timestamp is excluded.
    window_start, window_end : Any
        Half-open window ``[window_start, window_end)``. When
        ``window_end`` is None, the window is open-ended (≥ start).
    n_clusters : int, optional
        Total cluster count. When None, derived from labels.

    Returns
    -------
    dict[int, dict[str, float]]
        ``{cluster_id: {"n_in_window": int, "frequency": float}}`` where
        frequency is fraction of the cluster falling in the window.
        A cluster with 0 members in the window still appears with
        ``frequency = 0.0``.
    """
    if len(labels) != len(timestamps):
        raise ValueError("labels / timestamps length mismatch")

    if n_clusters is None:
        n_clusters = (max(labels) + 1) if labels else 0

    in_window = [0] * n_clusters
    cluster_total = [0] * n_clusters
    for c, ts in zip(labels, timestamps):
        if c < 0 or c >= n_clusters:
            continue
        cluster_total[c] += 1
        if ts is None:
            continue
        if window_end is None:
            if ts >= window_start:
                in_window[c] += 1
        else:
            if window_start <= ts < window_end:
                in_window[c] += 1

    out: dict[int, dict[str, float]] = {}
    for c in range(n_clusters):
        out[c] = {
            "n_in_window": in_window[c],
            "frequency": (in_window[c] / cluster_total[c]) if cluster_total[c] else 0.0,
        }
    return out
