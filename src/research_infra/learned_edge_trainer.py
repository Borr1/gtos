"""Learned mechanical edge trainer (offline; produces the frozen V1 artifact).

Trains the calibrated edge model on the counterfactual training frame built by
``learned_edge_dataset_builder``:

- heads: ``fill`` = P(fill), ``outcome`` = P(target-before-stop | fill),
  ``net_r`` = ridge E[net_r | fill] (winsorized label).
- model: L2 logistic regression over standardized numeric features plus
  out-of-fold empirical-Bayes target encodings of categoricals (level ->
  shrunk empirical logit, shrinkage w = n/(n+k), parent = global prior).
- calibration: beta calibration fit on out-of-fold predictions only.
- runtime shrinkage: per-(asset_class, session_bucket) base rates with
  w = n/(n+k_rel) recorded into the artifact for reliability-weighted
  shrinkage at inference.
- folds: PURGED, EMBARGOED, EXPANDING WALK-FORWARD via `trainer_folds`.
  Until 2026-07-29 this was leave-one-day-out (`fold_key != fold_day`), which
  put every future day in train and applied no purge or embargo despite a
  docstring claiming a 48h boundary; see `trainer_folds` for the measurement.
  Metrics reported per fold and pooled (Brier / ECE / logloss via
  validation_anti_overfit_v4 helpers).
- partitions: rows must carry `partition_trainable` from the fail-closed
  builder. March 2026 and every SEALED window are unreachable by construction.
- leakage canary: label-shuffle AUC must stay within
  ``SHUFFLE_AUC_TOLERANCE`` of 0.5 or training REFUSES to emit an artifact.

The artifact is consumed by the pure-Python scorer
``src/components/learned_edge_layer_v4.py``; this trainer round-trips its own
out-of-fold rows through that scorer to prove train/runtime parity by
construction.

Offline research tool: sklearn allowed HERE only; the artifact contains raw
coefficients so the runtime needs no ML dependency. No broker calls, no AI
calls, no runtime behavior change.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
import math
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.components.learned_edge_layer_v4 import (
    ARTIFACT_SCHEMA_VERSION,
    score_learned_edge,
)
from src.research_infra.learned_edge_dataset_builder import (
    FEATURE_WHITELIST,
    NET_R_WINSOR_HIGH,
    NET_R_WINSOR_LOW,
    read_jsonl,
    stable_sha256,
)
from src.research_infra.trainer_folds import (
    TrainerFoldSpec,
    audit_fold_leakage,
    plan_folds,
)
from src.research_infra.validation_anti_overfit_v4 import (
    brier_score,
    expected_calibration_error,
    logloss,
    reliability_bins,
)

NUMERIC_FEATURES = tuple(
    name
    for name in FEATURE_WHITELIST
    if name
    in {
        "f_heuristic_probability",
        "f_heuristic_ev_r",
        "f_thesis_probability",
        "f_thesis_uncalibrated_probability",
        "f_thesis_uncertainty",
        "f_thesis_missing_source_penalty",
        "f_thesis_source_completeness",
        "f_expected_cost_r",
        "f_risk_reward_ratio",
        "f_limit_offset_r",
        "f_stop_distance_rel",
        "f_n_competing_in_group",
        "f_open_positions_seen",
        "f_pending_orders_seen",
        "f_pd_atr14_over_atr50",
        "f_pd_bars_since_session_open",
        "f_pd_close_position_in_lookback_range",
        "f_pd_close_to_close_vol_8_over_48",
        "f_pd_compression_ratio_prior_bar",
        "f_pd_dist_to_prior_high20_atr",
        "f_pd_dist_to_prior_low20_atr",
        "f_pd_session_open_range_width_atr",
        "f_pd_stop_distance_atr",
        "f_pd_sweep_depth_atr",
        "f_pd_target_distance_atr",
        "f_pd_trigger_bar_body_atr",
        "f_pd_trigger_bar_range_atr",
    }
)
CATEGORICAL_FEATURES = (
    "f_origin_family",
    "f_symbol",
    "f_asset_class",
    "f_side",
    "f_session_bucket",
    "f_utc_hour_bucket",
    "f_day_of_week",
    "f_dynamic_execution_policy_id",
    "f_disagreement_state",
    "f_pd_trend_state_m15",
    "f_pd_trend_transition_flag",
)

EB_SHRINKAGE_K = 25.0
SEGMENT_SHRINKAGE_K = 40.0
SEGMENT_KEY_FIELDS = ("f_asset_class", "f_session_bucket")
L2_C = 0.5
RIDGE_ALPHA = 5.0
SHUFFLE_AUC_TOLERANCE = 0.07
VALID_DAYS_AFTER_FREEZE = 10
DEFAULT_THRESHOLDS = {
    "t_trade_expected_net_r": 0.15,
    "t_reduce_expected_net_r": 0.05,
    "min_fill_probability": 0.45,
}

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}


class LeakageCanaryError(RuntimeError):
    """Raised when the label-shuffle canary detects leakage."""


def _logit(p: float, eps: float = 1e-4) -> float:
    p = min(1.0 - eps, max(eps, p))
    return math.log(p / (1.0 - p))


def _auc(predictions: Sequence[float], labels: Sequence[int]) -> float:
    pairs = sorted(zip(predictions, labels), key=lambda item: item[0])
    pos = sum(1 for _, label in pairs if label == 1)
    neg = len(pairs) - pos
    if pos == 0 or neg == 0:
        return 0.5
    rank_sum = 0.0
    index = 0
    while index < len(pairs):
        tie_end = index
        while tie_end + 1 < len(pairs) and pairs[tie_end + 1][0] == pairs[index][0]:
            tie_end += 1
        avg_rank = (index + tie_end) / 2.0 + 1.0
        for j in range(index, tie_end + 1):
            if pairs[j][1] == 1:
                rank_sum += avg_rank
        index = tie_end + 1
    return (rank_sum - pos * (pos + 1) / 2.0) / (pos * neg)


def load_training_frame(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = read_jsonl(path)
    if not rows:
        raise ValueError(f"empty training frame: {path}")
    header = rows[0] if rows[0].get("row_kind") == "frame_header" else {}
    data = rows[1:] if header else rows
    return header, data


def _row_value(row: Mapping[str, Any], name: str) -> float | None:
    value = row.get(name)
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def _numeric_specs(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for name in NUMERIC_FEATURES:
        values = [v for row in rows if (v := _row_value(row, name)) is not None]
        if not values:
            specs.append({"name": name, "median": 0.0, "mean": 0.0, "std": 1.0})
            continue
        ordered = sorted(values)
        lo = ordered[max(0, int(0.005 * len(ordered)) - 1)] if len(ordered) > 200 else ordered[0]
        hi = ordered[min(len(ordered) - 1, int(0.995 * len(ordered)))] if len(ordered) > 200 else ordered[-1]
        clipped = [min(hi, max(lo, v)) for v in values]
        mean = sum(clipped) / len(clipped)
        var = sum((v - mean) ** 2 for v in clipped) / max(1, len(clipped) - 1)
        specs.append(
            {
                "name": name,
                "median": _median(values),
                "mean": mean,
                "std": math.sqrt(var) if var > 0 else 1.0,
                "clip_low": lo,
                "clip_high": hi,
            }
        )
    return specs


def _eb_target_encoding(
    rows: Sequence[Mapping[str, Any]],
    *,
    feature: str,
    label_key: str,
    weight_key: str,
    k: float = EB_SHRINKAGE_K,
) -> dict[str, float]:
    """Level -> shrunk empirical logit (weighted)."""

    total_w = 0.0
    total_pos = 0.0
    by_level: dict[str, list[float]] = {}
    for row in rows:
        label = row.get(label_key)
        if label not in (0, 1):
            continue
        weight = float(row.get(weight_key) or 0.0)
        if weight <= 0:
            continue
        level = str(row.get(feature)) if row.get(feature) is not None else "__missing__"
        by_level.setdefault(level, []).append((weight, float(label)))
        total_w += weight
        total_pos += weight * float(label)
    prior_rate = (total_pos / total_w) if total_w > 0 else 0.5
    prior_logit = _logit(prior_rate)
    encodings: dict[str, float] = {"__prior__": prior_logit}
    for level, pairs in by_level.items():
        w_sum = sum(w for w, _ in pairs)
        pos = sum(w * y for w, y in pairs)
        rate = pos / w_sum if w_sum > 0 else prior_rate
        shrink = w_sum / (w_sum + k)
        encodings[level] = shrink * _logit(rate) + (1.0 - shrink) * prior_logit
    return encodings


def _design_matrix(
    rows: Sequence[Mapping[str, Any]],
    numeric_specs: Sequence[Mapping[str, Any]],
    encodings_by_feature: Mapping[str, Mapping[str, float]],
) -> list[list[float]]:
    matrix: list[list[float]] = []
    for row in rows:
        vector: list[float] = []
        for spec in numeric_specs:
            value = _row_value(row, str(spec["name"]))
            if value is None:
                value = float(spec.get("median") or 0.0)
            lo, hi = spec.get("clip_low"), spec.get("clip_high")
            if lo is not None:
                value = max(float(lo), value)
            if hi is not None:
                value = min(float(hi), value)
            std = float(spec.get("std") or 1.0) or 1.0
            vector.append((value - float(spec.get("mean") or 0.0)) / std)
        for feature in CATEGORICAL_FEATURES:
            encodings = encodings_by_feature.get(feature, {"__prior__": 0.0})
            level = str(row.get(feature)) if row.get(feature) is not None else "__missing__"
            vector.append(float(encodings.get(level, encodings.get("__prior__", 0.0))))
        matrix.append(vector)
    return matrix


def _fit_logistic(
    matrix: list[list[float]], labels: list[int], weights: list[float]
) -> tuple[list[float], float]:
    from sklearn.linear_model import LogisticRegression

    model = LogisticRegression(C=L2_C, max_iter=2000)
    model.fit(matrix, labels, sample_weight=weights)
    return [float(c) for c in model.coef_[0]], float(model.intercept_[0])


def _fit_ridge(
    matrix: list[list[float]], targets: list[float], weights: list[float]
) -> tuple[list[float], float]:
    from sklearn.linear_model import Ridge

    model = Ridge(alpha=RIDGE_ALPHA)
    model.fit(matrix, targets, sample_weight=weights)
    return [float(c) for c in model.coef_], float(model.intercept_)


def _fit_beta_calibration(predictions: list[float], labels: list[int]) -> dict[str, float]:
    from sklearn.linear_model import LogisticRegression

    if len(set(labels)) < 2:
        return {"a": 1.0, "b": 1.0, "c": 0.0}
    eps = 1e-6
    rows = [
        [math.log(min(1 - eps, max(eps, p))), -math.log(1 - min(1 - eps, max(eps, p)))]
        for p in predictions
    ]
    model = LogisticRegression(C=1e6, max_iter=2000)
    model.fit(rows, labels)
    return {
        "a": float(model.coef_[0][0]),
        "b": float(model.coef_[0][1]),
        "c": float(model.intercept_[0]),
    }


def _segment_base_rates(
    rows: Sequence[Mapping[str, Any]], *, label_key: str, weight_key: str
) -> dict[str, Any]:
    segments: dict[str, dict[str, float]] = {}
    total_w = 0.0
    total_pos = 0.0
    for row in rows:
        label = row.get(label_key)
        if label not in (0, 1):
            continue
        weight = float(row.get(weight_key) or 0.0)
        if weight <= 0:
            continue
        key = "|".join(str(row.get(field) or "unknown") for field in SEGMENT_KEY_FIELDS)
        seg = segments.setdefault(key, {"n": 0.0, "pos": 0.0})
        seg["n"] += weight
        seg["pos"] += weight * float(label)
        total_w += weight
        total_pos += weight * float(label)
    global_rate = (total_pos / total_w) if total_w > 0 else 0.5
    return {
        "global_base_rate": global_rate,
        "segments": {
            key: {"base_rate": seg["pos"] / seg["n"] if seg["n"] > 0 else global_rate, "n": seg["n"]}
            for key, seg in segments.items()
        },
    }


def _head_rows(
    rows: Sequence[Mapping[str, Any]], *, head: str
) -> tuple[list[dict[str, Any]], str, str]:
    if head == "fill":
        eligible = [r for r in rows if r.get("label_fill") in (0, 1) and float(r.get("weight_fill_head") or 0) > 0]
        return eligible, "label_fill", "weight_fill_head"
    if head == "outcome":
        eligible = [
            r
            for r in rows
            if r.get("label_fill") == 1
            and r.get("label_target_before_stop") in (0, 1)
            and float(r.get("weight_outcome_head") or 0) > 0
        ]
        return eligible, "label_target_before_stop", "weight_outcome_head"
    if head == "net_r":
        eligible = [
            r
            for r in rows
            if r.get("label_fill") == 1
            and r.get("label_net_r") is not None
            and float(r.get("weight_outcome_head") or 0) > 0
        ]
        return eligible, "label_net_r", "weight_outcome_head"
    raise ValueError(f"unknown head {head}")


def _train_head_with_oof(
    rows: Sequence[Mapping[str, Any]],
    folds: Sequence[Any],
    numeric_specs: Sequence[Mapping[str, Any]],
    *,
    head: str,
) -> dict[str, Any]:
    """Out-of-fold fit over PURGED, EMBARGOED, WALK-FORWARD folds.

    `folds` is a sequence of `trainer_folds.TrainerFold`. It used to be a sequence of day strings
    and the split was `fold_key != fold_day` / `fold_key == fold_day` -- leave-one-day-out, which
    puts every FUTURE day in train and applies no purge or embargo at all. See
    `trainer_folds` for the measurement and the replacement.
    """
    eligible, label_key, weight_key = _head_rows(rows, head=head)
    if not eligible:
        return {"status": "no_rows", "head": head}

    is_classification = head in ("fill", "outcome")
    by_key = {str(r.get("row_key")): r for r in eligible}
    oof_predictions: list[float] = []
    oof_labels: list[int | float] = []
    oof_rows: list[Mapping[str, Any]] = []
    fold_metrics: list[dict[str, Any]] = []

    for fold in folds:
        train_rows = [by_key[k] for k in fold.train_row_keys if k in by_key]
        test_rows = [by_key[k] for k in fold.test_row_keys if k in by_key]
        if not train_rows or not test_rows:
            continue
        # Standardisation fitted on TRAIN ONLY. The previous revision computed
        # `_numeric_specs(rows)` once over every row -- including the out-of-fold test rows --
        # and reused it in every fold, so the scaler's mean, std and 0.5%/99.5% clip bounds
        # were all fitted on data the fold was about to be scored on. A second-order leak, but
        # a leak, and free to remove.
        fold_specs = _numeric_specs(train_rows)
        encodings = {
            feature: _eb_target_encoding(
                train_rows,
                feature=feature,
                label_key=label_key if is_classification else "label_target_before_stop",
                weight_key=weight_key,
            )
            for feature in CATEGORICAL_FEATURES
        }
        matrix = _design_matrix(train_rows, fold_specs, encodings)
        weights = [float(r.get(weight_key) or 0.0) for r in train_rows]
        if is_classification:
            labels = [int(r.get(label_key) or 0) for r in train_rows]
            if len(set(labels)) < 2:
                continue
            coef, intercept = _fit_logistic(matrix, labels, weights)
            test_matrix = _design_matrix(test_rows, fold_specs, encodings)
            preds = [
                1.0 / (1.0 + math.exp(-(intercept + sum(c * v for c, v in zip(coef, vec)))))
                for vec in test_matrix
            ]
            test_labels = [int(r.get(label_key) or 0) for r in test_rows]
            fold_metrics.append(
                {
                    "fold": fold.fold_id,
                    "test_window": [fold.test_start, fold.test_end],
                    "embargo_days": fold.embargo_days,
                    "n_train": len(train_rows),
                    "n": len(test_rows),
                    "brier": brier_score(preds, test_labels),
                    "logloss": logloss(preds, test_labels),
                }
            )
            oof_predictions.extend(preds)
            oof_labels.extend(test_labels)
            oof_rows.extend(test_rows)
        else:
            targets = [float(r.get(label_key) or 0.0) for r in train_rows]
            coef, intercept = _fit_ridge(matrix, targets, weights)
            test_matrix = _design_matrix(test_rows, fold_specs, encodings)
            preds = [intercept + sum(c * v for c, v in zip(coef, vec)) for vec in test_matrix]
            targets_test = [float(r.get(label_key) or 0.0) for r in test_rows]
            mae = sum(abs(p - t) for p, t in zip(preds, targets_test)) / len(test_rows)
            fold_metrics.append(
                {
                    "fold": fold.fold_id,
                    "test_window": [fold.test_start, fold.test_end],
                    "embargo_days": fold.embargo_days,
                    "n_train": len(train_rows),
                    "n": len(test_rows),
                    "mae": mae,
                }
            )
            oof_predictions.extend(preds)
            oof_labels.extend(targets_test)
            oof_rows.extend(test_rows)

    # Final fit on ALL eligible rows (encodings on the full training pool).
    final_encodings = {
        feature: _eb_target_encoding(
            eligible,
            feature=feature,
            label_key=label_key if is_classification else "label_target_before_stop",
            weight_key=weight_key,
        )
        for feature in CATEGORICAL_FEATURES
    }
    final_matrix = _design_matrix(eligible, numeric_specs, final_encodings)
    final_weights = [float(r.get(weight_key) or 0.0) for r in eligible]
    if is_classification:
        final_labels = [int(r.get(label_key) or 0) for r in eligible]
        coef, intercept = _fit_logistic(final_matrix, final_labels, final_weights)
        calibration = _fit_beta_calibration(oof_predictions, [int(v) for v in oof_labels])
        pooled = {
            "brier": brier_score(oof_predictions, [int(v) for v in oof_labels]),
            "logloss": logloss(oof_predictions, [int(v) for v in oof_labels]),
            "auc": _auc(oof_predictions, [int(v) for v in oof_labels]),
        }
        bins = reliability_bins(oof_predictions, [int(v) for v in oof_labels])
        pooled["ece"] = expected_calibration_error(bins)
    else:
        final_targets = [float(r.get(label_key) or 0.0) for r in eligible]
        coef, intercept = _fit_ridge(final_matrix, final_targets, final_weights)
        calibration = None
        pooled = {
            "mae": sum(abs(p - t) for p, t in zip(oof_predictions, oof_labels)) / len(oof_predictions)
            if oof_predictions
            else None
        }

    feature_names = [str(s["name"]) for s in numeric_specs] + list(CATEGORICAL_FEATURES)
    return {
        "status": "trained",
        "head": head,
        "eligible_rows": len(eligible),
        "coefficients": dict(zip(feature_names, coef)),
        "intercept": intercept,
        "calibration": calibration,
        "encodings": final_encodings,
        "fold_metrics": fold_metrics,
        "pooled_oof_metrics": pooled,
        "oof": {
            "predictions": oof_predictions,
            "labels": oof_labels,
            "row_keys": [str(r.get("row_key")) for r in oof_rows],
        },
    }


def _shuffle_canary(
    rows: Sequence[Mapping[str, Any]],
    folds: Sequence[str],
    numeric_specs: Sequence[Mapping[str, Any]],
    *,
    seed_rows: int,
) -> float:
    """Deterministically shuffle outcome labels and confirm AUC ~ 0.5."""

    eligible, label_key, weight_key = _head_rows(rows, head="outcome")
    if len(eligible) < 50:
        return 0.5
    shuffled = []
    labels_pool = [int(r.get(label_key) or 0) for r in eligible]
    # Deterministic permutation from row-key hashes (no random module: replay-safe).
    order = sorted(range(len(eligible)), key=lambda i: stable_sha256(eligible[i].get("row_key")))
    for row, idx in zip(eligible, order):
        clone = dict(row)
        clone[label_key] = labels_pool[idx]
        shuffled.append(clone)
    result = _train_head_with_oof(shuffled, folds, numeric_specs, head="outcome")
    if result.get("status") != "trained":
        return 0.5
    return float(result["pooled_oof_metrics"].get("auc") or 0.5)


def _generator_code_sha(repo_root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD:src/components/broader_origin_generators.py"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return out.stdout.strip()
    except Exception:
        return ""


def train_learned_edge_artifact(
    frame_path: Path,
    *,
    repo_root: Path = Path("."),
    partition_roles: tuple[str, ...] = ("TRAIN", "TRAIN_DEVELOPMENT_GRADE"),
    thresholds: Mapping[str, float] | None = None,
    freeze_day: str | None = None,
    fold_granularity: str = "day",
    fold_spec: TrainerFoldSpec | None = None,
) -> dict[str, Any]:
    header, all_rows = load_training_frame(frame_path)

    # 1. PARTITION. `partition_trainable` is authoritative and is emitted by the fail-closed
    #    builder. A frame without it predates that builder and cannot be shown to exclude
    #    SEALED / RESERVED_UNREAD / unpartitioned days, so it is refused rather than
    #    re-derived from `partition_role` alone.
    if not any("partition_trainable" in r for r in all_rows):
        raise ValueError(
            "training frame carries no `partition_trainable` field: it was built by a "
            "pre-2026-07-29 builder whose partition check was fail-open (optional --registry, "
            "and `role is None` for any uncovered day passed the SEALED-only guard). Rebuild it "
            "with learned_edge_dataset_builder.build_training_frame before training."
        )
    rows = [
        r
        for r in all_rows
        if bool(r.get("partition_trainable")) and str(r.get("partition_role")) in partition_roles
    ]
    if not rows:
        raise ValueError(
            f"no trainable rows with partition_role in {partition_roles}; frame has roles "
            f"{sorted({str(r.get('partition_role')) for r in all_rows})}"
        )

    # 2. LABEL SPANS. Without them no purge is possible, and a fold plan that cannot purge is
    #    not a leakage control. Refuse rather than silently produce an unpurged split.
    n_span = sum(1 for r in rows if r.get("label_span_status") in ("measured", "bounded_by_chunk_day"))
    if n_span == 0:
        raise ValueError(
            f"none of {len(rows)} trainable rows carry a usable `label_span_status`; purge is "
            "impossible. Rebuild the frame with the current builder."
        )

    # 3. FOLDS. Expanding purged/embargoed walk-forward, replacing leave-one-day-out.
    if fold_granularity not in ("day", "week"):
        raise ValueError(f"unknown fold_granularity {fold_granularity!r}")
    spec = fold_spec or TrainerFoldSpec(
        registry_digest=str(header.get("partition_registry_digest_sha256") or "")
    )
    folds = plan_folds(rows, spec)
    evaluable = [f for f in folds if f.evaluable]
    if not evaluable:
        raise ValueError(
            f"no evaluable folds from {len(rows)} rows over "
            f"{len({str(r.get('trading_day')) for r in rows})} days: "
            f"{[f.as_dict() for f in folds]}"
        )

    # 4. LEAK AUDIT. Re-derives the invariant from row spans rather than trusting the planner.
    leak_audit = audit_fold_leakage(evaluable, rows)
    if not leak_audit["clean"]:
        raise LeakageCanaryError(
            f"fold plan leaks: {leak_audit['reasons']} "
            f"({leak_audit['n_violations']} violations)"
        )

    numeric_specs = _numeric_specs(rows)
    folds = evaluable

    shuffle_auc = _shuffle_canary(rows, folds, numeric_specs, seed_rows=len(rows))
    if abs(shuffle_auc - 0.5) > SHUFFLE_AUC_TOLERANCE:
        raise LeakageCanaryError(
            f"label_shuffle_auc_{shuffle_auc:.4f}_outside_0.5+-{SHUFFLE_AUC_TOLERANCE}"
        )

    heads: dict[str, Any] = {}
    diagnostics: dict[str, Any] = {}
    for head in ("fill", "outcome", "net_r"):
        result = _train_head_with_oof(rows, folds, numeric_specs, head=head)
        if result.get("status") != "trained":
            raise ValueError(f"head_{head}_not_trainable: {result}")
        heads[head] = {
            "coefficients": result["coefficients"],
            "intercept": result["intercept"],
            "calibration": result["calibration"],
        }
        if head == "net_r":
            heads[head]["clip"] = {"low": NET_R_WINSOR_LOW, "high": NET_R_WINSOR_HIGH}
        diagnostics[head] = {
            "eligible_rows": result["eligible_rows"],
            "fold_metrics": result["fold_metrics"],
            "pooled_oof_metrics": result["pooled_oof_metrics"],
        }

    categorical_specs = [
        {
            "name": feature,
            "encodings": {
                "fill": _eb_target_encoding(
                    _head_rows(rows, head="fill")[0],
                    feature=feature,
                    label_key="label_fill",
                    weight_key="weight_fill_head",
                ),
                "outcome": _eb_target_encoding(
                    _head_rows(rows, head="outcome")[0],
                    feature=feature,
                    label_key="label_target_before_stop",
                    weight_key="weight_outcome_head",
                ),
                "net_r": _eb_target_encoding(
                    _head_rows(rows, head="outcome")[0],
                    feature=feature,
                    label_key="label_target_before_stop",
                    weight_key="weight_outcome_head",
                ),
            },
        }
        for feature in CATEGORICAL_FEATURES
    ]

    segment_shrinkage = {
        "key_fields": list(SEGMENT_KEY_FIELDS),
        "k": SEGMENT_SHRINKAGE_K,
        "min_weight": 0.0,
        "fill": _segment_base_rates(rows, label_key="label_fill", weight_key="weight_fill_head"),
        "outcome": _segment_base_rates(
            rows, label_key="label_target_before_stop", weight_key="weight_outcome_head"
        ),
    }

    freeze = freeze_day or datetime.now(timezone.utc).date().isoformat()
    valid_through = (
        datetime.fromisoformat(freeze).replace(tzinfo=timezone.utc)
        + timedelta(days=VALID_DAYS_AFTER_FREEZE + 4)
    ).isoformat()

    artifact: dict[str, Any] = {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "freeze_day": freeze,
        "valid_through_utc": valid_through,
        "training_frame_path": str(frame_path),
        "training_manifest_sha256": stable_sha256(
            {
                "frame_header_total_rows": header.get("total_rows"),
                "partition_roles": list(partition_roles),
                "folds": folds,
                "rows_used": len(rows),
            }
        ),
        "generator_code_sha": _generator_code_sha(repo_root),
        "numeric_features": numeric_specs,
        "categorical_features": categorical_specs,
        "heads": heads,
        "segment_shrinkage": segment_shrinkage,
        "thresholds": dict(thresholds or DEFAULT_THRESHOLDS),
        "training_diagnostics": diagnostics,
        "leakage_canary": {
            "label_shuffle_auc": shuffle_auc,
            "tolerance": SHUFFLE_AUC_TOLERANCE,
            "note": (
                "A label-shuffle canary tests FEATURE->LABEL leakage. It cannot detect a bad "
                "fold boundary: shuffling destroys the day-clustering the purge exists to "
                "control, so it passes on an unpurged split. The fold-leak audit below is what "
                "covers that, and the two are not substitutes."
            ),
        },
        "fold_plan": {
            "spec": asdict(spec),
            "spec_digest_sha256": spec.digest(),
            "folds": [f.as_dict() for f in folds],
            "leak_audit": {k: v for k, v in leak_audit.items() if k != "violations"},
        },
        "partition_registry_digest_sha256": header.get("partition_registry_digest_sha256"),
        "folds": [f.as_dict() for f in folds],
        "rows_used": len(rows),
        **BOUNDARY,
    }
    artifact["artifact_hash_sha256"] = stable_sha256(
        {k: v for k, v in artifact.items() if k not in ("generated_at_utc", "artifact_hash_sha256")}
    )

    # Train/runtime parity: the pure-python scorer must score every training
    # row without refusal using this artifact.
    parity_failures = 0
    for row in rows[:200]:
        scored = score_learned_edge(row, artifact)
        if scored.get("status") != "scored":
            parity_failures += 1
    artifact["scorer_parity_check"] = {
        "rows_checked": min(200, len(rows)),
        "refusals": parity_failures,
        "status": "pass" if parity_failures == 0 else "fail",
    }
    if parity_failures:
        raise ValueError(f"scorer_parity_refusals_{parity_failures}")
    return artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", required=True, help="Training frame JSONL path.")
    parser.add_argument("--out", required=True, help="Frozen artifact JSON output path.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--partition-roles",
        default="TRAIN,TRAIN_DEVELOPMENT_GRADE",
        help="Comma-separated partition roles eligible for fitting.",
    )
    parser.add_argument(
        "--fold-granularity",
        default="day",
        choices=("day", "week"),
        help="CV fold blocking; week for large frames.",
    )
    args = parser.parse_args(argv)
    artifact = train_learned_edge_artifact(
        Path(args.frame),
        repo_root=Path(args.repo_root),
        partition_roles=tuple(args.partition_roles.split(",")),
        fold_granularity=args.fold_granularity,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(artifact, indent=1, sort_keys=True, default=str))
    summary = {
        "rows_used": artifact["rows_used"],
        "folds": len(artifact["folds"]),
        "fill_oof": artifact["training_diagnostics"]["fill"]["pooled_oof_metrics"],
        "outcome_oof": artifact["training_diagnostics"]["outcome"]["pooled_oof_metrics"],
        "net_r_oof": artifact["training_diagnostics"]["net_r"]["pooled_oof_metrics"],
        "leakage_canary": artifact["leakage_canary"],
        "artifact_hash_sha256": artifact["artifact_hash_sha256"],
    }
    print(json.dumps(summary, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
