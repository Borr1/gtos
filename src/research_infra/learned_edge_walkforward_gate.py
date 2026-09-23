"""Walk-forward acceptance gate for the learned mechanical edge layer.

Scores every VALIDATION-role row of the counterfactual training frame with a
FROZEN learned-edge artifact (``src/components/learned_edge_layer_v4.py``)
and decides — mechanically, with fixed thresholds — whether the learned layer
beats the heuristic static-floor policy on out-of-train days:

- calibration:   pooled outcome Brier <= 0.24 and ECE <= 0.10
- economics:     learned admitted net-R sum >= heuristic admitted net-R sum
- capture:       learned admitted positive R / positive pool >= 0.25
- loss control:  learned admitted-loser rate <= heuristic admitted-loser rate
- incrementality: |admitted_learned ∩ admitted_heuristic| / |admitted_learned|
                  < 0.80 (the layer must add information, not mimic floors)
- integrity:     scorer refusal rate <= 1% of validation rows

The gate FAILS CLOSED: unreadable artifact, missing frame, zero validation
rows, or non-computable pooled metrics all yield ``overall_pass = False`` with
an explicit reason. Per-fold metrics, the PBO diagnostic, and baselines are
telemetry and never silently substitute for a gate.

Boundary: research-only offline evaluation. No broker calls, no AI calls, no
runtime behavior change. Labels remain replay/proxy evidence
(``post_asof_timewarp_replay_label_not_decision_input``), never broker-real
claims.
"""

from __future__ import annotations

import argparse
import json
import math
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.components.learned_edge_layer_v4 import (
    load_learned_edge_artifact,
    score_learned_edge,
)
from src.research_infra.learned_edge_dataset_builder import (
    read_jsonl,
    stable_sha256,
)
from src.research_infra.learned_edge_trainer import DEFAULT_THRESHOLDS
from src.research_infra.methodology_gate import cscv_pbo
from src.research_infra.validation_anti_overfit_v4 import (
    brier_score,
    expected_calibration_error,
    logloss,
    reliability_bins,
)

GATE_SCHEMA_VERSION = "ultimate_learned_edge_walkforward_gate_v1"
EVIDENCE_CLASS = "post_asof_timewarp_replay_walkforward_gate_not_broker_results"

BOUNDARY = {
    "broker_operation": False,
    "paid_api_or_vendor_call": False,
    "broker_runtime_change_status": False,
    "validation_result_status": False,
    "outcome_result_rows_status": False,
}

# Fixed acceptance thresholds (mechanical; no tuning at evaluation time).
GATE_OUTCOME_BRIER_MAX = 0.24
GATE_OUTCOME_ECE_MAX = 0.10
GATE_CAPTURE_RATIO_MIN = 0.25
GATE_OVERLAP_MAX = 0.80
GATE_REFUSAL_RATE_MAX = 0.01
ADMITTED_LOSER_NET_R_FLOOR = -0.5

# Heuristic static-floor comparator (the pre-learned admission policy).
DEFAULT_BASELINE = {
    "probability_feature": "f_heuristic_probability",
    "ev_feature": "f_heuristic_ev_r",
    "alt_probability_feature": "f_thesis_uncalibrated_probability",
    "probability_floor": 0.58,
    "ev_floor": 0.10,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _baseline_prediction(row: Mapping[str, Any], feature: str) -> float:
    """Clipped-[0,1] baseline probability; 0.5 when the source is missing."""

    value = _as_float(row.get(feature))
    if value is None:
        return 0.5
    return min(1.0, max(0.0, value))


def _feature_view(row: Mapping[str, Any]) -> dict[str, Any]:
    """Predecision feature mapping only (defense in depth: no label fields)."""

    return {key: value for key, value in row.items() if key.startswith("f_")}


def _classification_metrics(
    predictions: Sequence[float], labels: Sequence[int]
) -> dict[str, Any] | None:
    if not predictions:
        return None
    bins = reliability_bins(predictions, labels)
    return {
        "n": len(predictions),
        "brier": brier_score(predictions, labels),
        "logloss": logloss(predictions, labels),
        "ece": expected_calibration_error(bins),
    }


def learned_admits(scored: Mapping[str, Any], thresholds: Mapping[str, Any]) -> bool:
    """Artifact admission rule: expected net R and fill probability floors."""

    if scored.get("status") != "scored":
        return False
    expected_net_r = _as_float(scored.get("expected_net_r"))
    fill_probability = _as_float(scored.get("fill_probability"))
    if expected_net_r is None or fill_probability is None:
        return False
    t_trade = _as_float(thresholds.get("t_trade_expected_net_r"))
    min_fill = _as_float(thresholds.get("min_fill_probability"))
    if t_trade is None or min_fill is None:
        return False
    return expected_net_r >= t_trade and fill_probability >= min_fill


def heuristic_admits(row: Mapping[str, Any], baseline: Mapping[str, Any]) -> bool:
    """Static-floor admission rule on the heuristic predecision scores."""

    probability = _as_float(row.get(str(baseline["probability_feature"])))
    ev_r = _as_float(row.get(str(baseline["ev_feature"])))
    if probability is None or ev_r is None:
        return False
    return probability >= float(baseline["probability_floor"]) and ev_r >= float(
        baseline["ev_floor"]
    )


def _capture_stats(
    outcome_rows: Sequence[Mapping[str, Any]], admitted_keys: set[str]
) -> dict[str, Any]:
    """Weighted positive-R capture among label_outcome_valid rows."""

    positive_pool_r = 0.0
    admitted_positive_r = 0.0
    admitted_loser_r = 0.0
    admitted_net_r_sum = 0.0
    admitted_n = 0
    admitted_loser_count = 0
    for row in outcome_rows:
        net_r = _as_float(row.get("label_net_r"))
        if net_r is None:
            continue
        weight = _as_float(row.get("weight_duplicate_group"))
        weight = weight if weight is not None else 1.0
        positive_pool_r += max(0.0, net_r) * weight
        if str(row.get("row_key")) in admitted_keys:
            admitted_n += 1
            admitted_positive_r += max(0.0, net_r) * weight
            admitted_loser_r += min(0.0, net_r) * weight
            admitted_net_r_sum += net_r * weight
            if net_r < ADMITTED_LOSER_NET_R_FLOOR:
                admitted_loser_count += 1
    return {
        "admitted_n": admitted_n,
        "positive_pool_r": positive_pool_r,
        "admitted_positive_r": admitted_positive_r,
        "admitted_loser_r": admitted_loser_r,
        "admitted_net_r_sum": admitted_net_r_sum,
        "capture_ratio": (
            admitted_positive_r / positive_pool_r if positive_pool_r > 0 else None
        ),
        "admitted_loser_count": admitted_loser_count,
        # No admissions -> no admitted losers (well-defined zero, not None).
        "admitted_loser_rate": (
            admitted_loser_count / admitted_n if admitted_n > 0 else 0.0
        ),
    }


def overlap_stats(learned_keys: set[str], heuristic_keys: set[str]) -> dict[str, Any]:
    intersection = learned_keys & heuristic_keys
    union = learned_keys | heuristic_keys
    return {
        "admitted_learned_n": len(learned_keys),
        "admitted_heuristic_n": len(heuristic_keys),
        "intersection_n": len(intersection),
        # Fail-closed: no learned admissions -> overlap not computable -> the
        # adds_information gate fails on None.
        "overlap_of_learned": (
            len(intersection) / len(learned_keys) if learned_keys else None
        ),
        "jaccard": (len(intersection) / len(union)) if union else None,
    }


def _gate_row(gate: str, value: Any, threshold: Any, passed: bool) -> dict[str, Any]:
    return {"gate": gate, "value": value, "threshold": threshold, "pass": bool(passed)}


def _refused_report(
    *,
    frame_path: Path,
    artifact_path: Path,
    validation_roles: tuple[str, ...],
    reason: str,
    out_path: Path | None,
) -> dict[str, Any]:
    report = {
        "schema_version": GATE_SCHEMA_VERSION,
        "generated_at_utc": utc_now_iso(),
        "evidence_class": EVIDENCE_CLASS,
        "frame_path": str(frame_path),
        "artifact_path": str(artifact_path),
        "validation_roles": list(validation_roles),
        "status": "refused_fail_closed",
        "failure_reason": reason,
        "gate_table": [],
        "fold_table": [],
        "overall_pass": False,
        **BOUNDARY,
    }
    if out_path is not None:
        _write_report(out_path, report)
    return report


def _write_report(out_path: Path, report: Mapping[str, Any]) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(report, indent=1, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )


def _head_metric_block(
    rows: Sequence[Mapping[str, Any]],
    scored_by_key: Mapping[str, Mapping[str, Any]],
    baseline: Mapping[str, Any],
    *,
    head: str,
) -> dict[str, Any] | None:
    """Learned vs baseline calibration metrics for one head on one row set."""

    learned_preds: list[float] = []
    heuristic_preds: list[float] = []
    alt_preds: list[float] = []
    labels: list[int] = []
    for row in rows:
        scored = scored_by_key.get(str(row.get("row_key")))
        if scored is None or scored.get("status") != "scored":
            continue
        if head == "outcome":
            label = row.get("label_target_before_stop")
            prediction = _as_float(scored.get("probability"))
        else:
            label = row.get("label_fill")
            prediction = _as_float(scored.get("fill_probability"))
        if label not in (0, 1) or prediction is None:
            continue
        learned_preds.append(min(1.0, max(0.0, prediction)))
        heuristic_preds.append(
            _baseline_prediction(row, str(baseline["probability_feature"]))
        )
        alt_preds.append(
            _baseline_prediction(row, str(baseline["alt_probability_feature"]))
        )
        labels.append(int(label))
    if not labels:
        return None
    return {
        "learned": _classification_metrics(learned_preds, labels),
        "heuristic_baseline": _classification_metrics(heuristic_preds, labels),
        "alt_baseline": _classification_metrics(alt_preds, labels),
    }


def evaluate_walkforward_gate(
    frame_path: str | Path,
    artifact_path: str | Path,
    *,
    validation_roles: tuple[str, ...] = ("VALIDATION",),
    baseline: Mapping[str, Any] | None = None,
    out_path: str | Path | None = None,
) -> dict[str, Any]:
    """Evaluate the frozen artifact against validation folds. Fails closed."""

    frame_path = Path(frame_path)
    artifact_path = Path(artifact_path)
    out = Path(out_path) if out_path is not None else None
    baseline_spec = {**DEFAULT_BASELINE, **dict(baseline or {})}

    try:
        artifact = load_learned_edge_artifact(artifact_path)
    except Exception as exc:  # corrupt/unreadable artifact: refuse, never guess
        return _refused_report(
            frame_path=frame_path,
            artifact_path=artifact_path,
            validation_roles=validation_roles,
            reason=f"artifact_load_failed:{type(exc).__name__}:{exc}",
            out_path=out,
        )

    try:
        all_rows = read_jsonl(frame_path)
    except OSError as exc:
        return _refused_report(
            frame_path=frame_path,
            artifact_path=artifact_path,
            validation_roles=validation_roles,
            reason=f"frame_load_failed:{type(exc).__name__}:{exc}",
            out_path=out,
        )
    if not all_rows:
        return _refused_report(
            frame_path=frame_path,
            artifact_path=artifact_path,
            validation_roles=validation_roles,
            reason="frame_empty",
            out_path=out,
        )
    header = all_rows[0] if all_rows[0].get("row_kind") == "frame_header" else {}
    data_rows = all_rows[1:] if header else all_rows

    rows = [
        row for row in data_rows if str(row.get("partition_role")) in validation_roles
    ]
    if not rows:
        return _refused_report(
            frame_path=frame_path,
            artifact_path=artifact_path,
            validation_roles=validation_roles,
            reason=(
                "no_validation_rows_for_roles_"
                + "|".join(validation_roles)
                + "_frame_has_"
                + "|".join(sorted({str(r.get("partition_role")) for r in data_rows}))
            ),
            out_path=out,
        )

    thresholds = dict(DEFAULT_THRESHOLDS)
    artifact_thresholds = artifact.get("thresholds")
    if isinstance(artifact_thresholds, Mapping):
        thresholds.update(artifact_thresholds)

    # ---- score every validation row (refusals counted, never silently kept)
    scored_by_key: dict[str, Mapping[str, Any]] = {}
    refusal_statuses: dict[str, int] = {}
    refusals = 0
    for row in rows:
        scored = score_learned_edge(_feature_view(row), artifact)
        scored_by_key[str(row.get("row_key"))] = scored
        if scored.get("status") != "scored":
            refusals += 1
            status = str(scored.get("status"))
            refusal_statuses[status] = refusal_statuses.get(status, 0) + 1
    refusal_rate = refusals / len(rows)

    def outcome_rows_of(pool: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        return [
            r for r in pool if r.get("label_outcome_valid") and r.get("label_fill") == 1
        ]

    def fill_rows_of(pool: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        return [r for r in pool if r.get("label_fill") in (0, 1)]

    # ---- admissions (pooled sets of row keys)
    learned_admitted: set[str] = set()
    heuristic_admitted: set[str] = set()
    for row in rows:
        key = str(row.get("row_key"))
        if learned_admits(scored_by_key[key], thresholds):
            learned_admitted.add(key)
        if heuristic_admits(row, baseline_spec):
            heuristic_admitted.add(key)

    # ---- per-fold table
    fold_keys = sorted({str(row.get("fold_key")) for row in rows})
    fold_table: list[dict[str, Any]] = []
    pbo_matrix: list[list[float]] = []
    for fold_key in fold_keys:
        fold_rows = [row for row in rows if str(row.get("fold_key")) == fold_key]
        fold_outcome_rows = outcome_rows_of(fold_rows)
        learned_capture = _capture_stats(fold_outcome_rows, learned_admitted)
        heuristic_capture = _capture_stats(fold_outcome_rows, heuristic_admitted)
        fold_table.append(
            {
                "fold_key": fold_key,
                "n_rows": len(fold_rows),
                "n_refused": sum(
                    1
                    for row in fold_rows
                    if scored_by_key[str(row.get("row_key"))].get("status") != "scored"
                ),
                "outcome": _head_metric_block(
                    fold_outcome_rows, scored_by_key, baseline_spec, head="outcome"
                ),
                "fill": _head_metric_block(
                    fill_rows_of(fold_rows), scored_by_key, baseline_spec, head="fill"
                ),
                "capture_learned": learned_capture,
                "capture_heuristic": heuristic_capture,
            }
        )
        pbo_matrix.append(
            [
                float(learned_capture["admitted_net_r_sum"]),
                float(heuristic_capture["admitted_net_r_sum"]),
            ]
        )

    # ---- pooled metrics
    pooled_outcome_rows = outcome_rows_of(rows)
    pooled_outcome = _head_metric_block(
        pooled_outcome_rows, scored_by_key, baseline_spec, head="outcome"
    )
    pooled_fill = _head_metric_block(
        fill_rows_of(rows), scored_by_key, baseline_spec, head="fill"
    )
    pooled_capture_learned = _capture_stats(pooled_outcome_rows, learned_admitted)
    pooled_capture_heuristic = _capture_stats(pooled_outcome_rows, heuristic_admitted)
    overlap = overlap_stats(learned_admitted, heuristic_admitted)

    # ---- PBO diagnostic (telemetry: trials = [learned, heuristic] per fold)
    try:
        pbo = cscv_pbo(pbo_matrix).to_dict()
    except (ValueError, ZeroDivisionError) as exc:
        pbo = {"status": "not_computable", "reason": f"{type(exc).__name__}:{exc}"}

    # ---- gates (fixed thresholds; None values fail closed)
    learned_brier = (pooled_outcome or {}).get("learned", {}) or {}
    outcome_brier = learned_brier.get("brier")
    outcome_ece = learned_brier.get("ece")
    learned_net_sum = pooled_capture_learned["admitted_net_r_sum"]
    heuristic_net_sum = pooled_capture_heuristic["admitted_net_r_sum"]
    capture_ratio = pooled_capture_learned["capture_ratio"]
    learned_loser_rate = pooled_capture_learned["admitted_loser_rate"]
    heuristic_loser_rate = pooled_capture_heuristic["admitted_loser_rate"]
    overlap_of_learned = overlap["overlap_of_learned"]

    gate_table = [
        _gate_row(
            "outcome_brier_max",
            outcome_brier,
            GATE_OUTCOME_BRIER_MAX,
            outcome_brier is not None and outcome_brier <= GATE_OUTCOME_BRIER_MAX,
        ),
        _gate_row(
            "outcome_ece_max",
            outcome_ece,
            GATE_OUTCOME_ECE_MAX,
            outcome_ece is not None and outcome_ece <= GATE_OUTCOME_ECE_MAX,
        ),
        _gate_row(
            "learned_admitted_net_r_ge_heuristic",
            learned_net_sum,
            heuristic_net_sum,
            learned_net_sum >= heuristic_net_sum,
        ),
        _gate_row(
            "capture_ratio_min",
            capture_ratio,
            GATE_CAPTURE_RATIO_MIN,
            capture_ratio is not None and capture_ratio >= GATE_CAPTURE_RATIO_MIN,
        ),
        _gate_row(
            "admitted_loser_rate_le_heuristic",
            learned_loser_rate,
            heuristic_loser_rate,
            learned_loser_rate <= heuristic_loser_rate,
        ),
        _gate_row(
            "adds_information_overlap_max",
            overlap_of_learned,
            GATE_OVERLAP_MAX,
            overlap_of_learned is not None and overlap_of_learned < GATE_OVERLAP_MAX,
        ),
        _gate_row(
            "refusal_rate_max",
            refusal_rate,
            GATE_REFUSAL_RATE_MAX,
            refusal_rate <= GATE_REFUSAL_RATE_MAX,
        ),
    ]
    overall_pass = all(gate["pass"] for gate in gate_table)

    report = {
        "schema_version": GATE_SCHEMA_VERSION,
        "generated_at_utc": utc_now_iso(),
        "evidence_class": EVIDENCE_CLASS,
        "frame_path": str(frame_path),
        "artifact_path": str(artifact_path),
        "artifact_hash_sha256": artifact.get("artifact_hash_sha256"),
        "frame_header_sha256": stable_sha256(header),
        "validation_roles": list(validation_roles),
        "validation_rows": len(rows),
        "validation_folds": fold_keys,
        "thresholds": thresholds,
        "baseline_spec": baseline_spec,
        "refusals": {
            "count": refusals,
            "rate": refusal_rate,
            "statuses": dict(sorted(refusal_statuses.items())),
        },
        "pooled": {
            "outcome": pooled_outcome,
            "fill": pooled_fill,
            "capture_learned": pooled_capture_learned,
            "capture_heuristic": pooled_capture_heuristic,
            "overlap": overlap,
        },
        "pbo": pbo,
        "fold_table": fold_table,
        "gate_table": gate_table,
        "status": "evaluated",
        "overall_pass": overall_pass,
        **BOUNDARY,
    }
    if out is not None:
        _write_report(out, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frame", required=True, help="Training frame JSONL path.")
    parser.add_argument("--artifact", required=True, help="Frozen artifact JSON path.")
    parser.add_argument("--out", required=True, help="Gate report JSON output path.")
    parser.add_argument(
        "--validation-roles",
        default="VALIDATION",
        help="Comma-separated partition roles to evaluate.",
    )
    args = parser.parse_args(argv)
    report = evaluate_walkforward_gate(
        Path(args.frame),
        Path(args.artifact),
        validation_roles=tuple(args.validation_roles.split(",")),
        out_path=Path(args.out),
    )
    summary = {
        "status": report.get("status"),
        "overall_pass": report.get("overall_pass"),
        "failure_reason": report.get("failure_reason"),
        "validation_rows": report.get("validation_rows"),
        "gate_table": report.get("gate_table"),
        "artifact_hash_sha256": report.get("artifact_hash_sha256"),
    }
    print(json.dumps(summary, indent=1, sort_keys=True, default=str))
    return 0 if report.get("overall_pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
