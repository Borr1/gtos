"""Validation and anti-overfit controls for Wave3 V4.

This module is deterministic offline infrastructure. It builds validation
protocol rows, purged/embargoed split assignments, calibration metrics, and
promotion-gate checks. It never mutates broker state, never calls paid APIs,
and never enables runtime trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


FORBIDDEN_TRUE_FIELDS = (
    "live_deployment_allowed",
    "broker_mutation_allowed",
    "broker_runtime_change_status",
    "remote_push_allowed",
    "paid_api_call_allowed",
    "credential_mutation_allowed",
    "active_vps_process_change_allowed",
)

REQUIRED_CALIBRATION_METRICS = (
    "brier",
    "ece",
    "reliability_bins",
    "logloss",
)

DEFAULT_EMBARGO_MINUTES = 240
DEFAULT_BIN_COUNT = 10


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(payload: Any, length: int = 24) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:length]


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} is not a JSON object")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(canonical_json(row) + "\n")


def parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def extract_timestamp(row: dict[str, Any]) -> str | None:
    window = row.get("time_window")
    if isinstance(window, dict):
        for key in ("entry_time_utc", "timestamp_utc", "last_time_utc"):
            if window.get(key):
                return str(window[key])
    if isinstance(window, str):
        return window
    for key in ("timestamp_utc", "entry_time_utc", "last_time_utc"):
        if row.get(key):
            return str(row[key])
    return None


def utc_session(timestamp: datetime | None) -> str:
    if timestamp is None:
        return "timestamp_missing"
    hour = timestamp.hour
    if 0 <= hour < 6:
        return "asia"
    if 6 <= hour < 13:
        return "london"
    if 13 <= hour < 21:
        return "new_york"
    return "rollover"


def safe_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def normalize_validation_population(
    broker_rows: Sequence[dict[str, Any]],
    candidate_rows: Sequence[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize Wave2 broker/candidate rows into one validation population."""

    output: list[dict[str, Any]] = []

    def add_row(row: dict[str, Any], source_kind: str, index: int) -> None:
        metric_fields = row.get("metric_fields_used") or {}
        timestamp_text = extract_timestamp(row)
        parsed = parse_timestamp(timestamp_text)
        win_loss = metric_fields.get("win_loss")
        broker_net_cash = safe_float(
            metric_fields.get("broker_net_cash_from_deals")
            if "broker_net_cash_from_deals" in metric_fields
            else metric_fields.get("broker_real_pnl_cash")
        )
        if broker_net_cash is None:
            broker_net_cash = safe_float(row.get("broker_real_pnl_cash"))
        target_win = None
        if win_loss == "win":
            target_win = 1
        elif win_loss == "loss":
            target_win = 0
        source_row_id = str(row.get("row_id") or f"{source_kind}:{index}")
        source_family = row.get("source_family") or source_kind
        output.append(
            {
                "population_row_id": f"validation_population:{source_kind}:{index}:{stable_hash(source_row_id)}",
                "source_row_id": source_row_id,
                "source_kind": source_kind,
                "source_family": source_family,
                "evidence_class": row.get("evidence_class"),
                "symbol": row.get("symbol") or "UNKNOWN",
                "side": row.get("side") or "UNKNOWN",
                "timestamp_utc": parsed.isoformat() if parsed else None,
                "timestamp_source_value": timestamp_text,
                "session_utc": utc_session(parsed),
                "target_win": target_win,
                "target_source_status": "broker_real_win_loss_joined" if target_win is not None else "target_not_available_for_validation",
                "broker_net_cash": broker_net_cash,
                "proxy_r": safe_float(metric_fields.get("proxy_r")),
                "exact_r": safe_float(metric_fields.get("exact_r")),
                "expectancy_r_source_bound": safe_float(metric_fields.get("expectancy_r_source_bound")),
                "missing_fields": row.get("missing_fields") or [],
                "result_use_status": "validation_population_source_row_not_validation_result",
                "broker_runtime_change_status": False,
            }
        )

    for idx, row in enumerate(broker_rows, start=1):
        add_row(row, "broker_trade", idx)
    for idx, row in enumerate(candidate_rows, start=1):
        add_row(row, "candidate_or_live_authority", idx)
    return output


def _partition_boundaries(rows: Sequence[dict[str, Any]]) -> tuple[datetime | None, datetime | None]:
    dated = [parse_timestamp(row.get("timestamp_utc")) for row in rows]
    dated = sorted(ts for ts in dated if ts is not None)
    if len(dated) < 3:
        return None, None
    train_end = dated[int(len(dated) * 0.60)]
    validation_end = dated[int(len(dated) * 0.80)]
    return train_end, validation_end


def build_purged_embargoed_split_ledger(
    population_rows: Sequence[dict[str, Any]],
    *,
    embargo_minutes: int = DEFAULT_EMBARGO_MINUTES,
) -> list[dict[str, Any]]:
    """Assign every material row to a deterministic purged/embargoed ledger."""

    train_end, validation_end = _partition_boundaries(population_rows)
    embargo = timedelta(minutes=embargo_minutes)
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(population_rows, start=1):
        ts = parse_timestamp(row.get("timestamp_utc"))
        if ts is None or train_end is None or validation_end is None:
            partition = "source_gap_timestamp_missing"
            embargo_status = "not_eligible_timestamp_missing"
            purge_reason = "timestamp_required_for_time_split_walk_forward"
        elif ts < train_end:
            partition = "discovery_train"
            near_boundary = abs(ts - train_end) <= embargo
            embargo_status = "purged_or_embargoed_near_validation_boundary" if near_boundary else "eligible"
            purge_reason = "purge_train_boundary_leakage" if near_boundary else ""
        elif ts < validation_end:
            partition = "validation_selection"
            near_boundary = abs(ts - train_end) <= embargo or abs(ts - validation_end) <= embargo
            embargo_status = "purged_or_embargoed_near_train_or_test_boundary" if near_boundary else "eligible"
            purge_reason = "purge_validation_boundary_leakage" if near_boundary else ""
        else:
            partition = "sealed_test"
            near_boundary = abs(ts - validation_end) <= embargo
            embargo_status = "purged_or_embargoed_near_validation_boundary" if near_boundary else "eligible"
            purge_reason = "purge_test_boundary_leakage" if near_boundary else ""

        symbol = str(row.get("symbol") or "UNKNOWN")
        side = str(row.get("side") or "UNKNOWN")
        session = str(row.get("session_utc") or "timestamp_missing")
        is_zero_trade = "zero_trade" in str(row.get("source_family")) or row.get("target_win") is None
        rows.append(
            {
                "row_id": f"split:{index:08d}:{stable_hash(row.get('population_row_id'))}",
                "population_row_id": row.get("population_row_id"),
                "source_row_id": row.get("source_row_id"),
                "source_kind": row.get("source_kind"),
                "symbol": symbol,
                "side": side,
                "session_utc": session,
                "timestamp_utc": row.get("timestamp_utc"),
                "time_split_walk_forward_partition": partition,
                "purge_embargo_status": embargo_status,
                "purge_embargo_minutes": embargo_minutes,
                "purge_reason": purge_reason,
                "symbol_holdout_id": f"leave_one_symbol_out:{symbol}",
                "session_holdout_id": f"leave_one_session_out:{session}",
                "side_holdout_id": f"leave_one_side_out:{side}",
                "regime_holdout_id": "regime_missing_until_market_whiteboard_v2" if session == "timestamp_missing" else f"session_proxy_regime:{session}",
                "outlier_sensitivity_id": "largest_winner_and_GER30_sensitivity_required",
                "cost_stress_id": "cost_swap_slippage_broker_net_stress_required",
                "zero_trade_counterfactual_membership": is_zero_trade,
                "label_use_gate": "labels_may_be_read_only_after_partition_freeze",
                "feature_use_gate": "features_must_be_asof_source_hashed_before_partition_boundary",
                "result_use_status": "sealed_split_assignment_not_outcome_result",
                "validation_result_status": False,
                "outcome_result_rows_status": False,
                "broker_runtime_change_status": False,
            }
        )
    return rows


def brier_score(predictions: Sequence[float], labels: Sequence[int]) -> float:
    _validate_prediction_inputs(predictions, labels)
    return sum((p - y) ** 2 for p, y in zip(predictions, labels)) / len(predictions)


def logloss(predictions: Sequence[float], labels: Sequence[int], *, eps: float = 1e-15) -> float:
    _validate_prediction_inputs(predictions, labels)
    total = 0.0
    for p, y in zip(predictions, labels):
        clipped = min(max(p, eps), 1.0 - eps)
        total += -(y * math.log(clipped) + (1 - y) * math.log(1.0 - clipped))
    return total / len(predictions)


def reliability_bins(
    predictions: Sequence[float],
    labels: Sequence[int],
    *,
    bin_count: int = DEFAULT_BIN_COUNT,
) -> list[dict[str, Any]]:
    _validate_prediction_inputs(predictions, labels)
    if bin_count <= 0:
        raise ValueError("bin_count must be positive")
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bin_count)]
    for p, y in zip(predictions, labels):
        index = min(int(p * bin_count), bin_count - 1)
        buckets[index].append((p, y))
    rows: list[dict[str, Any]] = []
    total = len(predictions)
    for index, bucket in enumerate(buckets):
        lower = index / bin_count
        upper = (index + 1) / bin_count
        if bucket:
            avg_prediction = sum(p for p, _ in bucket) / len(bucket)
            empirical_rate = sum(y for _, y in bucket) / len(bucket)
        else:
            avg_prediction = None
            empirical_rate = None
        rows.append(
            {
                "bin_id": f"bin_{index:02d}",
                "lower_inclusive": lower,
                "upper_exclusive": upper if index < bin_count - 1 else 1.000000000001,
                "row_count": len(bucket),
                "row_fraction": len(bucket) / total,
                "avg_prediction": avg_prediction,
                "empirical_rate": empirical_rate,
                "absolute_calibration_error": (
                    abs(avg_prediction - empirical_rate)
                    if avg_prediction is not None and empirical_rate is not None
                    else None
                ),
            }
        )
    return rows


def expected_calibration_error(bin_rows: Sequence[dict[str, Any]]) -> float:
    return sum(
        float(row["row_fraction"]) * float(row["absolute_calibration_error"])
        for row in bin_rows
        if row.get("absolute_calibration_error") is not None
    )


def _validate_prediction_inputs(predictions: Sequence[float], labels: Sequence[int]) -> None:
    if len(predictions) != len(labels):
        raise ValueError("predictions and labels must have equal length")
    if not predictions:
        raise ValueError("at least one prediction is required")
    for p in predictions:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"prediction outside [0, 1]: {p}")
    for label in labels:
        if label not in (0, 1):
            raise ValueError(f"label must be 0 or 1: {label}")


def calibration_fixture_rows() -> list[dict[str, Any]]:
    predictions = [0.03, 0.08, 0.14, 0.22, 0.31, 0.47, 0.53, 0.61, 0.74, 0.82, 0.91, 0.97]
    labels = [0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1]
    return [
        {
            "row_id": f"calibration_fixture:{idx:03d}",
            "prediction": prediction,
            "label": label,
            "evidence_class": "deterministic_metric_fixture_not_trading_result",
            "result_use_status": "metric_formula_fixture_not_validation_result",
            "validation_result_status": False,
            "outcome_result_rows_status": False,
            "broker_runtime_change_status": False,
        }
        for idx, (prediction, label) in enumerate(zip(predictions, labels), start=1)
    ]


def calibration_metric_result(rows: Sequence[dict[str, Any]], *, bin_count: int = DEFAULT_BIN_COUNT) -> dict[str, Any]:
    predictions = [float(row["prediction"]) for row in rows]
    labels = [int(row["label"]) for row in rows]
    bins = reliability_bins(predictions, labels, bin_count=bin_count)
    return {
        "row_count": len(rows),
        "metrics": {
            "brier": brier_score(predictions, labels),
            "logloss": logloss(predictions, labels),
            "ece": expected_calibration_error(bins),
            "reliability_bins": bins,
        },
        "metric_names_required": list(REQUIRED_CALIBRATION_METRICS),
        "metric_source_status": "deterministic_formula_fixture_no_asof_gtos_prediction_scores_in_wave2",
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
    }

def concentration_rows(population_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], dict[str, Any]] = {}
    for row in population_rows:
        if row.get("source_kind") != "broker_trade":
            continue
        for family, key in (
            ("symbol", str(row.get("symbol") or "UNKNOWN")),
            ("side", str(row.get("side") or "UNKNOWN")),
            ("symbol_side", f"{row.get('symbol') or 'UNKNOWN'}:{row.get('side') or 'UNKNOWN'}"),
        ):
            bucket = groups.setdefault(
                (family, key),
                {
                    "group_family": family,
                    "group_key": key,
                    "broker_trade_rows": 0,
                    "wins": 0,
                    "losses": 0,
                    "broker_net_cash_sum": 0.0,
                    "largest_winner_cash": None,
                    "largest_loser_cash": None,
                },
            )
            cash = safe_float(row.get("broker_net_cash"))
            target = row.get("target_win")
            bucket["broker_trade_rows"] += 1
            if target == 1:
                bucket["wins"] += 1
            elif target == 0:
                bucket["losses"] += 1
            if cash is not None:
                bucket["broker_net_cash_sum"] += cash
                bucket["largest_winner_cash"] = cash if bucket["largest_winner_cash"] is None else max(bucket["largest_winner_cash"], cash)
                bucket["largest_loser_cash"] = cash if bucket["largest_loser_cash"] is None else min(bucket["largest_loser_cash"], cash)

    total_trades = sum(1 for row in population_rows if row.get("source_kind") == "broker_trade")
    output = []
    for index, bucket in enumerate(sorted(groups.values(), key=lambda item: (item["group_family"], item["group_key"])), start=1):
        trades = bucket["broker_trade_rows"]
        largest_winner = bucket.get("largest_winner_cash")
        cash_sum = float(bucket["broker_net_cash_sum"])
        output.append(
            {
                "row_id": f"concentration:{index:04d}:{stable_hash(bucket)}",
                **bucket,
                "trade_fraction": trades / total_trades if total_trades else 0.0,
                "win_rate": bucket["wins"] / trades if trades else None,
                "cash_without_largest_winner": cash_sum - largest_winner if largest_winner and largest_winner > 0 else cash_sum,
                "concentration_status": "full_group_preserved_no_top_n_truncation",
                "anti_overfit_use": "reject production-return claim if edge depends on one group or one outlier",
                "validation_result_status": False,
                "outcome_result_rows_status": False,
                "broker_runtime_change_status": False,
            }
        )
    return output


def multiple_testing_rows(validation_contract: dict[str, Any]) -> list[dict[str, Any]]:
    families: list[str] = []
    for key in ("sealed_validation_requirements", "required_execution_lanes", "anti_overfit_fail_conditions"):
        values = validation_contract.get(key) or []
        if isinstance(values, list):
            families.extend(str(value) for value in values)
    rows: list[dict[str, Any]] = []
    m = len(families)
    for index, family in enumerate(families, start=1):
        rows.append(
            {
                "row_id": f"multiple_testing:{index:03d}:{stable_hash(family)}",
                "hypothesis_family": family,
                "family_index": index,
                "family_count": m,
                "raw_alpha": 0.05,
                "holm_bonferroni_alpha": 0.05 / (m - index + 1) if m else None,
                "benjamini_hochberg_rank_alpha": (index / m) * 0.05 if m else None,
                "p_value_source_status": "required_from_future_sealed_validation_result_before_promotion",
                "decision_rule": "no production-return claim unless family passes correction, holdout, concentration, leakage, and cost stress gates",
                "result_use_status": "multiple_testing_control_design_not_validation_result",
                "validation_result_status": False,
                "outcome_result_rows_status": False,
                "broker_runtime_change_status": False,
            }
        )
    return rows


def source_gap_rows(population_rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    counters: Counter[str] = Counter()
    for row in population_rows:
        if row.get("target_win") is None:
            counters["missing_asof_label_or_non_outcome_source"] += 1
        if not row.get("timestamp_utc"):
            counters["missing_timestamp_for_purged_split"] += 1
        for field in row.get("missing_fields") or []:
            counters[f"missing_field:{field}"] += 1
    rows = []
    for index, (gap, count) in enumerate(sorted(counters.items()), start=1):
        rows.append(
            {
                "row_id": f"source_gap:{index:04d}:{stable_hash(gap)}",
                "gap_family": gap,
                "affected_rows": count,
                "repair_status": "bounded_or_handed_to_source_capture_owner",
                "same_evidence_class_repair_status": "non_generatable_historical_truth_or_downstream_capture_required",
                "owner_access_source_capture_requirement": "LiveDecisionPacketV4, Feature Store V2, and Label Store V2 must persist as-of prediction, feature, label, source hash, split id, and broker-local namespace fields prospectively.",
                "validation_result_status": False,
                "outcome_result_rows_status": False,
                "broker_runtime_change_status": False,
            }
        )
    return rows


def semantic_ownership_rows() -> list[dict[str, Any]]:
    rows = [
        (
            "same_symbol_same_instrument_lifecycle_v4",
            "same-symbol lifecycle owns scale/reduce/close/reverse/no duplicate exposure state before validation can score allocator decisions",
        ),
        (
            "probability_debate_team_engine_v4",
            "probability/debate owns as-of action probabilities, EV, uncertainty, vetoes, missing-source penalties, and selected alternatives before Brier/ECE/logloss can become real validation metrics",
        ),
        (
            "follow_avoid_mixed_numeric_confluence_v4",
            "numeric confluence owns FOLLOW/AVOID/MIXED strength, confidence, reliability history, evidence class, freshness, cost sensitivity, conflict reason, and source completeness",
        ),
        (
            "wave4_wave5_ml_feature_label_model_owners",
            "Feature Store, Label Store, Digital Twin, ML baselines, model registry, challengers, walk-forward, leakage guards, and promotion gates remain downstream ML owners, not AI reliability side effects",
        ),
    ]
    return [
        {
            "row_id": f"semantic_ownership:{index:03d}:{stable_hash(owner)}",
            "semantic_owner": owner,
            "handoff_contract": contract,
            "implementation_status": "contract_preserved_or_handed_to_first_class_owner",
            "validation_lane_dependency": "validation_anti_overfit_v4_blocks_production_return_claims_until owner outputs are source-hashed and partitioned",
            "broker_runtime_change_status": False,
        }
        for index, (owner, contract) in enumerate(rows, start=1)
    ]


def production_disposition_rows(route_dir: str) -> list[dict[str, Any]]:
    surfaces = [
        ("src/research_infra/validation_anti_overfit_v4.py", "staged_default_off", "offline validation control library; no runtime trade authority"),
        ("config/agent_config.yaml", "staged_default_off", "default-off config authority and artifact paths only"),
        (f"{route_dir}/build_wave3_validation_anti_overfit_v4.py", "research_only", "route artifact materializer"),
        (f"{route_dir}/verify_wave3_validation_anti_overfit_v4.py", "research_only", "route verifier"),
        ("tests/research_infra/test_validation_anti_overfit_v4.py", "research_only", "focused non-live unit tests"),
    ]
    return [
        {
            "row_id": f"production_disposition:{index:03d}:{stable_hash(path)}",
            "component_path": path,
            "production_code_disposition": disposition,
            "disposition_reason": reason,
            "runtime_effect_now": False,
            "broker_runtime_change_status": False,
            "live_deployment_allowed": False,
            "remote_push_allowed": False,
        }
        for index, (path, disposition, reason) in enumerate(surfaces, start=1)
    ]


def forbidden_surface_issues(payloads: Iterable[Any]) -> list[str]:
    issues: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in FORBIDDEN_TRUE_FIELDS and child is True:
                    issues.append(f"forbidden_true:{child_path}")
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    for payload in payloads:
        visit(payload, "")
    return issues


def summarize_split_ledger(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "split_rows": len(rows),
        "partition_counts": dict(sorted(Counter(row["time_split_walk_forward_partition"] for row in rows).items())),
        "purge_embargo_status_counts": dict(sorted(Counter(row["purge_embargo_status"] for row in rows).items())),
        "source_kind_counts": dict(sorted(Counter(row["source_kind"] for row in rows).items())),
        "symbol_count": len({row["symbol"] for row in rows}),
        "side_counts": dict(sorted(Counter(row["side"] for row in rows).items())),
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
    }
