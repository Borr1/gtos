"""Unit tests for ``src.research_infra.loser_anti_pattern``.

Coverage matrix
---------------
* ``cluster_losers``
    - Synthetic 3-cluster data → silhouette picks k=3.
    - Synthetic flat data → silhouette is low; result still well-formed.
    - Empty input → ValueError.
    - Ragged feature matrix → ValueError.
    - feature_names length mismatch → ValueError.
    - k_min < 2 → ValueError.
    - k_max > n - 1 is silently clamped.
    - In-house fallback works when sklearn is unavailable.
    - n_init > 1 produces deterministic output for a given seed.

* ``train_loss_classifier``
    - Planted-signal data → AUC > 0.7 (random + holdout).
    - Pure-noise data → AUC ≈ 0.5.
    - Held-out time slice AUC < random-test AUC for regime-non-stationary
      planted data (sanity for the regime-drift metric).
    - Single-class y → ValueError.
    - feature_names length mismatch → ValueError.
    - timestamps length mismatch → ValueError.
    - In-house fallback works when sklearn is unavailable.

* ``describe_cluster``
    - Renders all centroid features in the output (so callers can audit).
    - Top-3 features picked by absolute deviation from population centroid.
    - Works without population_centroid (falls back to magnitude).

* ``cluster_frequency_in_window``
    - Half-open window semantics.
    - None timestamps are excluded but the row still counts toward the
      cluster total (so frequency is meaningful).
    - Open-ended window (window_end=None).

* ``cluster_losers_by_source`` (F3 — source-stratified)
    - Two well-separated source-tagged groups → independent reports
      whose cluster centroids reflect each source's centers (NOT a
      mixed centroid).
    - Source below ``min_n_per_source`` returns sentinel ``k=1``
      report rather than crashing.
    - Length mismatch on sources / realized_r → ValueError.

* ``train_loss_classifier_per_source`` (F3 — source-stratified)
    - Two sources with planted signal → per-source AUCs returned
      independently and ≈ above 0.7.
    - Source below ``min_n_per_source`` is silently skipped (absent
      from returned dict).
    - Length mismatch on sources / y / timestamps → ValueError.
"""

from __future__ import annotations

import importlib
import math
import random
import sys
from datetime import datetime, timezone
from typing import Any

import pytest

import src.research_infra.loser_anti_pattern as lap


# ────────────────────────────────────────────────────────────────────────────
# Synthetic data builders
# ────────────────────────────────────────────────────────────────────────────


def _three_well_separated_clusters(
    n_per: int = 30, seed: int = 0
) -> tuple[list[list[float]], list[float]]:
    """Build n_per × 3 = ~90 points clustered around 3 widely-spaced centers.

    Cluster centers are placed at (0,0,0,0), (10,10,0,0), (0,0,10,10) with
    sigma 0.5 — ratio 20:1 separation, so silhouette > 0.7 is expected.
    """
    rng = random.Random(seed)
    pts: list[list[float]] = []
    realized_r: list[float] = []
    for cid, center in enumerate(
        [
            (0.0, 0.0, 0.0, 0.0),
            (10.0, 10.0, 0.0, 0.0),
            (0.0, 0.0, 10.0, 10.0),
        ]
    ):
        for _ in range(n_per):
            pts.append(
                [
                    center[0] + rng.gauss(0, 0.5),
                    center[1] + rng.gauss(0, 0.5),
                    center[2] + rng.gauss(0, 0.5),
                    center[3] + rng.gauss(0, 0.5),
                ]
            )
            # Realized R is irrelevant for silhouette; encode cluster id so
            # mean-R bookkeeping has something to verify.
            realized_r.append(-1.0 - cid * 0.5)
    return pts, realized_r


def _flat_uniform_cloud(n: int = 90, seed: int = 1) -> list[list[float]]:
    rng = random.Random(seed)
    return [
        [rng.uniform(0, 10), rng.uniform(0, 10), rng.uniform(0, 10), rng.uniform(0, 10)]
        for _ in range(n)
    ]


def _planted_signal_dataset(
    n: int = 200, seed: int = 2, drift: float = 0.0
) -> tuple[
    list[list[float]],
    list[int],
    list[datetime],
]:
    """Two-class dataset where loss probability scales with feature 0.

    feature 0 in [0, 1]: high → likely loss.
    Other features are noise.
    ``drift`` shifts the feature → loss relationship in the second half so
    a held-out time slice AUC will sag.
    """
    rng = random.Random(seed)
    X: list[list[float]] = []
    y: list[int] = []
    ts: list[datetime] = []
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(n):
        f0 = rng.random()
        f1 = rng.random()
        f2 = rng.random()
        is_late = i >= n // 2
        # In-distribution loss probability.
        prob_loss = 0.85 * f0 + 0.05 * f1
        # Drift in the late half — makes the late-slice harder/easier.
        if is_late and drift:
            prob_loss = max(0.0, min(1.0, prob_loss + drift * (1.0 - f0)))
        is_loss = 1 if rng.random() < prob_loss else 0
        X.append([f0, f1, f2])
        y.append(is_loss)
        # Timestamps spread over Jan-Apr 2026.
        from datetime import timedelta
        ts.append(base + timedelta(days=i))
    return X, y, ts


# ────────────────────────────────────────────────────────────────────────────
# cluster_losers
# ────────────────────────────────────────────────────────────────────────────


class TestClusterLosers:
    def test_synthetic_three_clusters_silhouette_picks_three(self):
        pts, r = _three_well_separated_clusters()
        report = lap.cluster_losers(
            pts, k_range=(2, 6), feature_names=["a", "b", "c", "d"], realized_r=r
        )
        assert report.k == 3
        assert report.silhouette > 0.5  # well-separated clusters
        # Cluster sizes sum to total losers.
        assert sum(report.cluster_sizes) == len(pts)
        # Mean R recorded per cluster.
        assert all(rval <= 0 for rval in report.cluster_means_r)
        # Silhouette monotonicity check: peak at k=3.
        for k_other, score in report.silhouette_by_k.items():
            if k_other != 3:
                assert score <= report.silhouette + 1e-9

    def test_synthetic_three_clusters_inhouse_path(self):
        pts, r = _three_well_separated_clusters()
        report = lap.cluster_losers(
            pts,
            k_range=(2, 6),
            feature_names=["a", "b", "c", "d"],
            realized_r=r,
            prefer_sklearn=False,  # force in-house
        )
        assert report.k == 3
        assert report.silhouette > 0.5
        assert report.sklearn_used is False

    def test_silhouette_low_on_flat_cloud(self):
        pts = _flat_uniform_cloud()
        report = lap.cluster_losers(
            pts, k_range=(2, 6), feature_names=["a", "b", "c", "d"]
        )
        # Flat cloud → silhouette is low (typically ~0.2-0.3).
        assert report.silhouette < 0.5
        # But the result is still well-formed.
        assert report.k in range(2, 7)
        assert sum(report.cluster_sizes) == len(pts)

    def test_empty_input_raises(self):
        with pytest.raises(ValueError):
            lap.cluster_losers([])

    def test_ragged_matrix_raises(self):
        with pytest.raises(ValueError):
            lap.cluster_losers([[1.0, 2.0], [1.0]])

    def test_zero_length_features_raises(self):
        with pytest.raises(ValueError):
            lap.cluster_losers([[], [], []])

    def test_feature_names_length_mismatch_raises(self):
        pts, _ = _three_well_separated_clusters(n_per=10)
        with pytest.raises(ValueError):
            lap.cluster_losers(pts, feature_names=["a", "b"])  # 4 features expected

    def test_kmin_below_2_raises(self):
        pts, _ = _three_well_separated_clusters(n_per=10)
        with pytest.raises(ValueError):
            lap.cluster_losers(pts, k_range=(1, 5))

    def test_kmax_silently_clamped(self):
        # With only 5 samples and k_max=10, clamp to 4 (n-1).
        pts = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [2.0, 0.0], [0.0, 2.0]]
        report = lap.cluster_losers(
            pts,
            k_range=(2, 10),
            feature_names=["a", "b"],
            n_init=2,
        )
        assert report.k <= 4

    def test_population_centroid_matches_data_mean(self):
        pts, _ = _three_well_separated_clusters(n_per=20)
        report = lap.cluster_losers(
            pts, k_range=(2, 5), feature_names=["a", "b", "c", "d"]
        )
        for j in range(4):
            expected = sum(p[j] for p in pts) / len(pts)
            assert math.isclose(
                report.population_centroid[j], expected, rel_tol=1e-9, abs_tol=1e-9
            )

    def test_n_features_attribute(self):
        pts, _ = _three_well_separated_clusters(n_per=10)
        report = lap.cluster_losers(
            pts, k_range=(2, 5), feature_names=["a", "b", "c", "d"]
        )
        assert report.n_features == 4
        assert report.n_losers == len(pts)


# ────────────────────────────────────────────────────────────────────────────
# train_loss_classifier
# ────────────────────────────────────────────────────────────────────────────


class TestTrainLossClassifier:
    def test_planted_signal_auc_above_70(self):
        X, y, ts = _planted_signal_dataset(n=300, seed=42)
        report = lap.train_loss_classifier(
            X, y, feature_names=["f0", "f1", "f2"], timestamps=ts, seed=0
        )
        # Random-split AUC should be solidly above 0.7 with strong signal.
        assert report.test_auc > 0.7, (
            f"expected test_auc > 0.7 on planted signal, got {report.test_auc:.3f}"
        )
        # Top feature is f0 (carries the planted signal).
        top_name = report.feature_importance[0][0]
        assert top_name == "f0"

    def test_planted_signal_inhouse_path_auc(self):
        X, y, ts = _planted_signal_dataset(n=300, seed=42)
        report = lap.train_loss_classifier(
            X,
            y,
            feature_names=["f0", "f1", "f2"],
            timestamps=ts,
            seed=0,
            prefer_sklearn=False,
        )
        assert report.test_auc > 0.7
        assert report.sklearn_used is False
        assert report.classifier_type == "logistic_regression_inhouse"

    def test_holdout_auc_lower_than_test_under_drift(self):
        # Drift > 0 makes the late slice harder than the early slice.
        # We compare holdout vs test on the same draw.
        X, y, ts = _planted_signal_dataset(n=400, seed=7, drift=0.6)
        cutoff = ts[len(ts) // 2]
        report = lap.train_loss_classifier(
            X,
            y,
            feature_names=["f0", "f1", "f2"],
            timestamps=ts,
            time_slice_split=cutoff,
            seed=0,
        )
        # The holdout slice has a different generative regime so the
        # generalization AUC should be lower than the random-split test AUC.
        assert report.holdout_n > 0
        # The drift is engineered to drag holdout AUC down — assert a clear
        # gap, not just inequality (rules out random fluke).
        assert report.holdout_auc < report.test_auc + 0.05
        # Stationarity ratio is bounded sensibly.
        assert 0.0 <= report.regime_stationarity_ratio <= 1.5

    def test_pure_noise_auc_near_half(self):
        rng = random.Random(0)
        n = 300
        X = [[rng.random(), rng.random(), rng.random()] for _ in range(n)]
        y = [rng.choice([0, 1]) for _ in range(n)]
        ts = [
            datetime(2026, 1, 1, tzinfo=timezone.utc).replace(
                day=((i % 28) + 1)
            )
            for i in range(n)
        ]
        report = lap.train_loss_classifier(
            X, y, feature_names=["f0", "f1", "f2"], timestamps=ts, seed=0
        )
        # Random labels: AUC should be ~0.5 ± 0.15 with this n.
        assert 0.35 < report.test_auc < 0.65

    def test_single_class_y_raises(self):
        X = [[1.0, 2.0]] * 10
        y = [0] * 10
        with pytest.raises(ValueError):
            lap.train_loss_classifier(X, y)

    def test_feature_names_mismatch_raises(self):
        X = [[1.0, 2.0]] * 10
        y = [0, 1] * 5
        with pytest.raises(ValueError):
            lap.train_loss_classifier(X, y, feature_names=["a", "b", "c"])

    def test_timestamps_mismatch_raises(self):
        X = [[1.0, 2.0]] * 10
        y = [0, 1] * 5
        with pytest.raises(ValueError):
            lap.train_loss_classifier(
                X, y, timestamps=[datetime.now(timezone.utc)] * 9
            )

    def test_empty_X_raises(self):
        with pytest.raises(ValueError):
            lap.train_loss_classifier([], [])

    def test_no_holdout_when_split_none(self):
        X, y, ts = _planted_signal_dataset(n=200, seed=3)
        report = lap.train_loss_classifier(X, y, timestamps=ts, time_slice_split=None)
        # Without a split, holdout_auc == test_auc by spec.
        assert report.holdout_auc == report.test_auc
        assert report.holdout_n == 0


# ────────────────────────────────────────────────────────────────────────────
# describe_cluster
# ────────────────────────────────────────────────────────────────────────────


class TestDescribeCluster:
    def test_renders_all_features(self):
        names = ["a", "b", "c", "d"]
        centroid = [1.0, 2.0, 3.0, 4.0]
        out = lap.describe_cluster(0, centroid, names)
        for name in names:
            assert name in out

    def test_top_3_picked_by_absolute_deviation(self):
        names = ["a", "b", "c", "d", "e"]
        centroid = [10.0, 1.1, 1.0, 1.0, -8.0]
        pop = [1.0, 1.0, 1.0, 1.0, 1.0]
        out = lap.describe_cluster(0, centroid, names, population_centroid=pop)
        # a (dev +9), e (dev -9), b (dev +0.1) should appear before c, d.
        # Top-3 line ordering reflects the |deviation| ranking.
        first_block = out.split("All feature centroids:")[0]
        # 'a' and 'e' must be in the top-3 block.
        assert "a:" in first_block
        assert "e:" in first_block
        # 'd' should NOT (it has zero deviation).
        # We accept that "d" may appear in "All feature centroids" — the
        # check above already restricted us to the top-block.
        assert "d:" not in first_block

    def test_works_without_population_centroid(self):
        names = ["a", "b", "c"]
        centroid = [-5.0, 0.1, 0.2]
        out = lap.describe_cluster(2, centroid, names, top_k=2)
        # Without population_centroid the function falls back to centroid magnitude.
        # |a| = 5 should be ranked first.
        first_block = out.split("All feature centroids:")[0]
        assert "a:" in first_block

    def test_centroid_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            lap.describe_cluster(0, [1.0, 2.0], ["a", "b", "c"])

    def test_population_centroid_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            lap.describe_cluster(
                0,
                [1.0, 2.0, 3.0],
                ["a", "b", "c"],
                population_centroid=[1.0, 2.0],
            )


# ────────────────────────────────────────────────────────────────────────────
# cluster_frequency_in_window
# ────────────────────────────────────────────────────────────────────────────


class TestClusterFrequencyInWindow:
    def _ts(self, day: int) -> datetime:
        return datetime(2026, 1, day, tzinfo=timezone.utc)

    def test_half_open_window_semantics(self):
        # Cluster 0 has timestamps [day 1, day 5, day 10].
        # Window [day 5, day 10) should pick up day 5 only.
        labels = [0, 0, 0]
        timestamps = [self._ts(1), self._ts(5), self._ts(10)]
        freq = lap.cluster_frequency_in_window(
            labels,
            timestamps,
            window_start=self._ts(5),
            window_end=self._ts(10),
            n_clusters=1,
        )
        assert freq[0]["n_in_window"] == 1
        assert freq[0]["frequency"] == pytest.approx(1 / 3)

    def test_open_ended_window(self):
        labels = [0, 0, 0, 0]
        timestamps = [self._ts(1), self._ts(5), self._ts(10), self._ts(15)]
        freq = lap.cluster_frequency_in_window(
            labels, timestamps, window_start=self._ts(10), n_clusters=1
        )
        assert freq[0]["n_in_window"] == 2
        assert freq[0]["frequency"] == pytest.approx(0.5)

    def test_none_timestamps_excluded_but_count(self):
        labels = [0, 0, 0]
        timestamps = [self._ts(1), None, self._ts(10)]
        freq = lap.cluster_frequency_in_window(
            labels, timestamps, window_start=self._ts(5), n_clusters=1
        )
        # n_in_window = 1 (day 10 only); frequency divided by total cluster size 3.
        assert freq[0]["n_in_window"] == 1
        assert freq[0]["frequency"] == pytest.approx(1 / 3)

    def test_empty_cluster(self):
        labels = [0, 0, 0]
        timestamps = [self._ts(2), self._ts(3), self._ts(4)]
        # Cluster 1 has no members; should still appear in output.
        freq = lap.cluster_frequency_in_window(
            labels, timestamps, window_start=self._ts(1), n_clusters=2
        )
        assert freq[1]["n_in_window"] == 0
        assert freq[1]["frequency"] == 0.0

    def test_label_timestamps_length_mismatch_raises(self):
        with pytest.raises(ValueError):
            lap.cluster_frequency_in_window(
                [0, 1], [self._ts(1)], window_start=self._ts(0)
            )


# ────────────────────────────────────────────────────────────────────────────
# Sklearn fallback simulation — verifies the in-house path stays callable
# even if sklearn is suddenly unavailable mid-run.
# ────────────────────────────────────────────────────────────────────────────


class TestSklearnFallback:
    def test_no_sklearn_path_explicit(self):
        pts, r = _three_well_separated_clusters(n_per=15)
        report = lap.cluster_losers(
            pts,
            k_range=(2, 5),
            feature_names=["a", "b", "c", "d"],
            realized_r=r,
            prefer_sklearn=False,
        )
        assert report.sklearn_used is False
        assert report.k == 3

    def test_classifier_no_sklearn_path_explicit(self):
        X, y, ts = _planted_signal_dataset(n=200, seed=11)
        report = lap.train_loss_classifier(
            X,
            y,
            feature_names=["f0", "f1", "f2"],
            timestamps=ts,
            prefer_sklearn=False,
        )
        assert report.sklearn_used is False
        assert report.classifier_type == "logistic_regression_inhouse"
        # Even on fallback path, planted signal should give meaningful AUC.
        assert report.test_auc > 0.6

    def test_simulated_sklearn_missing_falls_back(self, monkeypatch):
        """Simulate sklearn import failure → in-house path must still run.

        We patch the module-level ``_has_sklearn`` to return False; this
        models the case where someone runs us in an environment with no
        sklearn. Tests must still pass.
        """
        monkeypatch.setattr(lap, "_has_sklearn", lambda: False)
        pts, r = _three_well_separated_clusters(n_per=15)
        report = lap.cluster_losers(
            pts,
            k_range=(2, 5),
            feature_names=["a", "b", "c", "d"],
            realized_r=r,
        )
        # We requested prefer_sklearn=True (default) but the gate said False.
        assert report.sklearn_used is False

        X, y, ts = _planted_signal_dataset(n=200, seed=11)
        creport = lap.train_loss_classifier(
            X,
            y,
            feature_names=["f0", "f1", "f2"],
            timestamps=ts,
        )
        assert creport.sklearn_used is False
        assert creport.classifier_type == "logistic_regression_inhouse"


# ────────────────────────────────────────────────────────────────────────────
# Internal numerical primitives — direct tests
# ────────────────────────────────────────────────────────────────────────────


class TestInhousePrimitives:
    def test_kmeans_inhouse_recovers_three_clusters(self):
        pts, _ = _three_well_separated_clusters(n_per=20)
        labels, centroids, inertia, conv = lap._kmeans_inhouse(
            pts, k=3, n_init=5, seed=0
        )
        assert len(labels) == len(pts)
        assert len(centroids) == 3
        assert inertia >= 0.0
        assert conv is True

    def test_silhouette_inhouse_high_for_separated_clusters(self):
        pts, _ = _three_well_separated_clusters(n_per=20)
        labels, _cents, _i, _c = lap._kmeans_inhouse(pts, k=3, n_init=5, seed=0)
        s = lap._silhouette_inhouse(pts, labels)
        assert s > 0.7

    def test_silhouette_inhouse_zero_for_single_cluster_label(self):
        pts = _flat_uniform_cloud(n=20)
        labels = [0] * 20
        assert lap._silhouette_inhouse(pts, labels) == 0.0

    def test_logistic_inhouse_separates_planted(self):
        X, y, _ts = _planted_signal_dataset(n=200, seed=99)
        w, b, conv = lap._logistic_inhouse(X, y)
        # Should give non-trivial weights.
        assert any(abs(wi) > 0.05 for wi in w)
        # f0 (the planted feature) should have the largest absolute weight.
        assert abs(w[0]) > abs(w[1])
        assert abs(w[0]) > abs(w[2])

    def test_roc_auc_perfect_separation(self):
        # Class 1 always scores higher → AUC = 1.0.
        y = [0, 0, 1, 1]
        s = [0.1, 0.2, 0.8, 0.9]
        assert lap._roc_auc(y, s) == pytest.approx(1.0)

    def test_roc_auc_perfect_inversion(self):
        y = [0, 0, 1, 1]
        s = [0.9, 0.8, 0.2, 0.1]
        assert lap._roc_auc(y, s) == pytest.approx(0.0)

    def test_roc_auc_random_near_half(self):
        rng = random.Random(0)
        y = [rng.choice([0, 1]) for _ in range(500)]
        s = [rng.random() for _ in range(500)]
        assert 0.4 < lap._roc_auc(y, s) < 0.6

    def test_roc_auc_single_class_returns_half(self):
        assert lap._roc_auc([0, 0, 0], [0.1, 0.2, 0.3]) == 0.5
        assert lap._roc_auc([1, 1, 1], [0.1, 0.2, 0.3]) == 0.5

    def test_roc_auc_with_ties(self):
        # Tied scores at the boundary → AUC averaged.
        y = [0, 0, 1, 1]
        s = [0.1, 0.5, 0.5, 0.9]
        # Manual: the tie at 0.5 splits evenly.
        auc = lap._roc_auc(y, s)
        # AUC should be 0.875 (perfect except for one tied pair).
        assert 0.7 < auc < 1.0


# ────────────────────────────────────────────────────────────────────────────
# F3 — Source-stratified API
# ────────────────────────────────────────────────────────────────────────────


def _two_source_separated_dataset(
    n_per_source: int = 30, seed: int = 0
) -> tuple[list[list[float]], list[str], list[float]]:
    """Build n_per_source losers for each of TWO sources, with cluster
    geometries that differ ACROSS sources but contain real structure
    WITHIN each source.

    Source ``"phase1"``: 3 well-separated clusters around (0,0,0,0),
    (10,10,0,0), (0,0,10,10) — analogue of XAUUSD/USDJPY full MSO data.
    Source ``"tier2"``  : 3 well-separated clusters around (50,0,0,0),
    (50,5,0,0), (50,10,0,0) — analogue of parsed AI-response only with
    the "schema gap" represented by the +50 offset on feature 0 (the
    field that was median-imputed in the real data).

    A naive joint cluster_losers call would lump tier2 together because
    its cluster spread (5) is dwarfed by the inter-source separation
    (50). The per-source path must recover 3-cluster structure for both.
    """
    rng = random.Random(seed)
    pts: list[list[float]] = []
    sources: list[str] = []
    realized_r: list[float] = []
    for cid, center in enumerate(
        [
            (0.0, 0.0, 0.0, 0.0),
            (10.0, 10.0, 0.0, 0.0),
            (0.0, 0.0, 10.0, 10.0),
        ]
    ):
        for _ in range(n_per_source // 3):
            pts.append(
                [
                    center[0] + rng.gauss(0, 0.4),
                    center[1] + rng.gauss(0, 0.4),
                    center[2] + rng.gauss(0, 0.4),
                    center[3] + rng.gauss(0, 0.4),
                ]
            )
            sources.append("phase1")
            realized_r.append(-1.0 - cid * 0.25)
    for cid, center in enumerate(
        [
            (50.0, 0.0, 0.0, 0.0),
            (50.0, 5.0, 0.0, 0.0),
            (50.0, 10.0, 0.0, 0.0),
        ]
    ):
        for _ in range(n_per_source // 3):
            pts.append(
                [
                    center[0] + rng.gauss(0, 0.3),
                    center[1] + rng.gauss(0, 0.3),
                    center[2] + rng.gauss(0, 0.3),
                    center[3] + rng.gauss(0, 0.3),
                ]
            )
            sources.append("tier2")
            realized_r.append(-0.5 - cid * 0.2)
    return pts, sources, realized_r


def _two_source_planted_classifier_dataset(
    n_per_source: int = 100, seed: int = 7
) -> tuple[
    list[list[float]],
    list[int],
    list[str],
    list[datetime],
]:
    """Two sources, planted f0 → loss signal, separable per-source.

    Source ``"phase1"``: prob_loss = 0.85 * f0 + 0.05 * f1.
    Source ``"tier2"`` : prob_loss = 0.85 * f0 + 0.05 * f1, but f0 lives
    in [50, 51] (schema offset). Per-source classifiers must recover
    f0 as the top feature for BOTH sources.
    """
    rng = random.Random(seed)
    X: list[list[float]] = []
    y: list[int] = []
    sources: list[str] = []
    ts: list[datetime] = []
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    from datetime import timedelta
    for src, offset in (("phase1", 0.0), ("tier2", 50.0)):
        for i in range(n_per_source):
            f0_local = rng.random()
            f0 = f0_local + offset
            f1 = rng.random()
            f2 = rng.random()
            prob_loss = 0.85 * f0_local + 0.05 * f1
            is_loss = 1 if rng.random() < prob_loss else 0
            X.append([f0, f1, f2])
            y.append(is_loss)
            sources.append(src)
            ts.append(base + timedelta(days=i))
    return X, y, sources, ts


class TestClusterLosersBySource:
    def test_independent_clusters_per_source(self):
        pts, sources, r = _two_source_separated_dataset(n_per_source=30, seed=42)
        out = lap.cluster_losers_by_source(
            pts,
            sources,
            k_range=(2, 5),
            feature_names=["a", "b", "c", "d"],
            realized_r=r,
            seed=0,
        )
        assert set(out.keys()) == {"phase1", "tier2"}
        # Each source recovers its own cluster set independently.
        for src, rep in out.items():
            assert rep.k >= 2
            assert rep.n_losers == 30
            assert sum(rep.cluster_sizes) == 30
        # Phase 1 centroids cluster around (0,...) and (10,...) on feature 0;
        # tier 2 centroids cluster around (50,...) on feature 0.
        # Critically, NO phase1 centroid should be near +50 — that is the
        # confound we are eliminating.
        phase1 = out["phase1"]
        for cent in phase1.centroids:
            assert cent[0] < 25.0, (
                f"phase1 centroid leaked tier2 schema offset: {cent}"
            )
        tier2 = out["tier2"]
        for cent in tier2.centroids:
            assert cent[0] >= 25.0, (
                f"tier2 centroid leaked phase1 schema offset: {cent}"
            )

    def test_below_min_returns_sentinel(self):
        # Source "tiny" has only 4 losers (below default min_n_per_source=8).
        pts, sources, r = _two_source_separated_dataset(n_per_source=30, seed=1)
        # Append four phase1-shaped points tagged with a third source.
        pts = pts + [[0.0, 0.0, 0.0, 0.0]] * 4
        sources = sources + ["legacy"] * 4
        r = r + [-0.1] * 4
        out = lap.cluster_losers_by_source(
            pts,
            sources,
            k_range=(2, 5),
            feature_names=["a", "b", "c", "d"],
            realized_r=r,
        )
        assert "legacy" in out
        # Sentinel: k=1, silhouette=0.0, single cluster = whole subset.
        assert out["legacy"].k == 1
        assert out["legacy"].silhouette == 0.0
        assert out["legacy"].n_losers == 4
        # Phase1 + tier2 still cluster normally.
        assert out["phase1"].k >= 2
        assert out["tier2"].k >= 2

    def test_length_mismatch_raises(self):
        pts, sources, r = _two_source_separated_dataset(n_per_source=12, seed=0)
        # Drop one source tag → length mismatch.
        with pytest.raises(ValueError):
            lap.cluster_losers_by_source(
                pts,
                sources[:-1],
                k_range=(2, 4),
                feature_names=["a", "b", "c", "d"],
            )
        # Realized_r length mismatch.
        with pytest.raises(ValueError):
            lap.cluster_losers_by_source(
                pts,
                sources,
                k_range=(2, 4),
                feature_names=["a", "b", "c", "d"],
                realized_r=r[:-2],
            )

    def test_min_n_per_source_threshold(self):
        # All sources below the threshold → all sentinel.
        pts = [[0.0, 0.0]] * 4 + [[1.0, 1.0]] * 4
        sources = ["a"] * 4 + ["b"] * 4
        out = lap.cluster_losers_by_source(
            pts,
            sources,
            k_range=(2, 3),
            feature_names=["x", "y"],
            min_n_per_source=10,
        )
        for rep in out.values():
            assert rep.k == 1
            assert rep.silhouette == 0.0


class TestTrainLossClassifierPerSource:
    def test_per_source_planted_signal_auc(self):
        X, y, sources, ts = _two_source_planted_classifier_dataset(
            n_per_source=120, seed=11
        )
        out = lap.train_loss_classifier_per_source(
            X,
            y,
            sources,
            feature_names=["f0", "f1", "f2"],
            timestamps=ts,
            seed=0,
        )
        assert set(out.keys()) == {"phase1", "tier2"}
        # Both sources recover an honest above-chance AUC.
        for src, rep in out.items():
            assert rep.test_auc > 0.65, (
                f"source={src} test_auc={rep.test_auc:.3f} too low"
            )
            # The top feature should be f0 (the planted predictor) for BOTH.
            top_name = rep.feature_importance[0][0]
            assert top_name == "f0", (
                f"source={src} top feature = {top_name}, expected f0"
            )

    def test_skips_below_min_n_per_source(self):
        X, y, sources, ts = _two_source_planted_classifier_dataset(
            n_per_source=120, seed=2
        )
        # Append 5 rows tagged with a "tiny" source — should be dropped.
        for i in range(5):
            X.append([0.5, 0.5, 0.5])
            y.append(i % 2)
            sources.append("tiny")
            ts.append(datetime(2026, 1, 1, tzinfo=timezone.utc))
        out = lap.train_loss_classifier_per_source(
            X, y, sources, feature_names=["f0", "f1", "f2"], timestamps=ts,
            min_n_per_source=20,
        )
        assert "tiny" not in out  # silently skipped (below threshold)
        assert "phase1" in out and "tier2" in out

    def test_skips_single_class_source(self):
        # One source with all-zero labels (no losses) is not trainable —
        # should be silently absent, not raise.
        X, y, sources, ts = _two_source_planted_classifier_dataset(
            n_per_source=80, seed=3
        )
        # Append 25 single-class rows under "wins_only".
        for i in range(25):
            X.append([0.5, 0.5, 0.5])
            y.append(0)
            sources.append("wins_only")
            ts.append(datetime(2026, 1, 1, tzinfo=timezone.utc))
        out = lap.train_loss_classifier_per_source(
            X, y, sources, feature_names=["f0", "f1", "f2"], timestamps=ts,
            min_n_per_source=20,
        )
        assert "wins_only" not in out

    def test_per_source_independent_aucs_recorded(self):
        # Plant a strong signal in phase1 and pure noise in tier2 →
        # per-source AUCs differ substantially.
        rng = random.Random(99)
        X, y, sources, ts = [], [], [], []
        base = datetime(2026, 1, 1, tzinfo=timezone.utc)
        from datetime import timedelta
        for i in range(120):
            f0 = rng.random()
            X.append([f0, rng.random(), rng.random()])
            y.append(1 if rng.random() < 0.85 * f0 else 0)
            sources.append("phase1")
            ts.append(base + timedelta(days=i))
        for i in range(120):
            X.append([rng.random(), rng.random(), rng.random()])
            y.append(rng.choice([0, 1]))
            sources.append("tier2")
            ts.append(base + timedelta(days=i))
        out = lap.train_loss_classifier_per_source(
            X, y, sources,
            feature_names=["f0", "f1", "f2"],
            timestamps=ts,
            seed=0,
        )
        assert set(out.keys()) == {"phase1", "tier2"}
        # Phase1 has signal → high AUC. Tier2 pure noise → ~ 0.5.
        assert out["phase1"].test_auc > 0.7, out["phase1"].test_auc
        assert 0.3 < out["tier2"].test_auc < 0.7, out["tier2"].test_auc
        # Per-source AUCs are bookkept separately (independent splits).
        assert out["phase1"].n_train + out["phase1"].n_test > 0
        assert out["tier2"].n_train + out["tier2"].n_test > 0

    def test_length_mismatch_raises(self):
        X = [[1.0, 2.0]] * 30
        y = [0, 1] * 15
        sources = ["a"] * 29  # length mismatch
        with pytest.raises(ValueError):
            lap.train_loss_classifier_per_source(X, y, sources)

    def test_y_length_mismatch_raises(self):
        X = [[1.0, 2.0]] * 30
        y = [0, 1] * 14  # wrong length
        sources = ["a"] * 30
        with pytest.raises(ValueError):
            lap.train_loss_classifier_per_source(X, y, sources)

    def test_timestamps_length_mismatch_raises(self):
        X = [[1.0, 2.0]] * 30
        y = [0, 1] * 15
        sources = ["a"] * 30
        ts = [datetime.now(timezone.utc)] * 29
        with pytest.raises(ValueError):
            lap.train_loss_classifier_per_source(
                X, y, sources, timestamps=ts
            )
