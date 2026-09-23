"""Numeric result scoring for moonshot integrated execution rows.

This module consumes the latest integrated execution rows plus the already
computed action/branch replay evidence and emits concrete exact/proxy result
columns. It is research-only and has no live trading side effects.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


NUMERIC_SCORER_SURFACE = "src/research_infra/moonshot_integrated_result_numeric_scorer.py"

BROKER_EXACT_R_FIELDS = (
    "order_ticket",
    "deal_ticket",
    "broker_fill_time_utc",
    "executed_entry_price",
    "executed_exit_price",
    "executed_stop_price",
    "executed_target_price",
    "executed_lot_size",
    "commission",
    "swap",
    "slippage_price",
    "partial_exit_lifecycle",
)

EXACT_R_VALUE_KEYS = (
    "exact_r",
    "exact_R",
    "broker_exact_r",
    "broker_R",
    "realized_r",
    "realized_R",
    "net_r",
    "net_R",
)


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def _first_numeric(*rows: dict[str, Any] | None, keys: tuple[str, ...]) -> tuple[float | None, str | None]:
    for row in rows:
        if not row:
            continue
        for key in keys:
            numeric = to_float(row.get(key))
            if numeric is not None:
                return numeric, key
    return None, None


def _counter_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    return {str(key): to_int(count) for key, count in value.items()}


def target_stop_counts(*rows: dict[str, Any] | None) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        if not row:
            continue
        candidates = [
            row.get("target_stop_result_counts"),
            row.get("m1_spread_adjusted_first_touch_status_counts"),
        ]
        all_components = row.get("rstyle_proxy_all_components")
        if isinstance(all_components, dict):
            candidates.append(all_components.get("status_counts"))
        for candidate in candidates:
            counts.update(_counter_dict(candidate))
    return {key: int(counts[key]) for key in sorted(counts)}


def classify_target_stop_order(*rows: dict[str, Any] | None) -> tuple[str, dict[str, int], str]:
    counts = target_stop_counts(*rows)
    target = 0
    stop = 0
    ambiguous = 0
    no_touch = 0
    no_fill = 0
    for status, count in counts.items():
        text = status.upper()
        if "POST_SIGNAL_ENTRY_NOT_FILLED" in text or "NO_FILL" in text or "UNFILLED" in text:
            no_fill += count
        elif "NO_TARGET_OR_STOP" in text or "NO_TOUCH" in text:
            no_touch += count
        elif "TARGET" in text and "STOP" in text and "BEFORE" in text:
            if text.find("TARGET") < text.find("STOP"):
                target += count
            elif text.find("STOP") < text.find("TARGET"):
                stop += count
            else:
                ambiguous += count
        elif "AMBIG" in text or ("TARGET" in text and "STOP" in text and "SAME" in text):
            ambiguous += count
        elif "TARGET" in text and "STOP" not in text:
            target += count
        elif "STOP" in text and "TARGET" not in text:
            stop += count
    status_text = "|".join(
        str((row or {}).get(key) or "")
        for row in rows
        for key in ("target_stop_result", "market_first_touch_status", "first_touch_status_offset_proxy")
    ).upper()
    if not counts and "TARGET" in status_text and "STOP" not in status_text:
        target = 1
    elif not counts and "TARGET" in status_text and "STOP" in status_text and "BEFORE" in status_text:
        if status_text.find("TARGET") < status_text.find("STOP"):
            target = 1
        elif status_text.find("STOP") < status_text.find("TARGET"):
            stop = 1
        else:
            ambiguous = 1
    elif not counts and "STOP" in status_text and "TARGET" not in status_text:
        stop = 1
    elif not counts and ("AMBIG" in status_text or "UNRESOLVED" in status_text):
        ambiguous = 1
    elif not counts and ("NO_TARGET_OR_STOP" in status_text or "NO_TOUCH" in status_text):
        no_touch = 1

    if target > stop and target > ambiguous:
        return "TARGET_FIRST_PROXY_DOMINANT", counts, "target_count_gt_stop_count"
    if stop > target and stop > ambiguous:
        return "STOP_FIRST_PROXY_DOMINANT", counts, "stop_count_gt_target_count"
    if target or stop or ambiguous:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED", counts, "target_stop_counts_mixed_or_tied"
    if no_fill:
        return "NO_FILL_OR_UNFILLED_DOMINANT", counts, "no_fill_or_unfilled_status_counts"
    if no_touch:
        return "NEITHER_TARGET_NOR_STOP_TOUCH_PROXY", counts, "no_target_or_stop_touch_status"
    return "TARGET_STOP_ORDER_NOT_SOURCE_BOUND", counts, "target_stop_fields_absent"


def exact_r_evidence(
    execution_row: dict[str, Any],
    computed_row: dict[str, Any] | None = None,
    branch_row: dict[str, Any] | None = None,
    sidecar_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    exact_value, exact_key = _first_numeric(
        execution_row,
        computed_row,
        branch_row,
        sidecar_row,
        keys=EXACT_R_VALUE_KEYS,
    )
    if exact_value is not None:
        return {
            "exact_r_status": "EXACT_R_COMPUTED_FROM_SOURCE_ROW",
            "exact_r_value": round(exact_value, 6),
            "exact_r_source_key": exact_key,
            "exact_missing_field_proof": [],
        }

    merged: dict[str, Any] = {}
    for row in (execution_row, computed_row, branch_row, sidecar_row):
        if row:
            merged.update(row)
    missing = [field for field in BROKER_EXACT_R_FIELDS if merged.get(field) in (None, "")]
    exact_spread_context = str(
        merged.get("repair_feasibility_class")
        or merged.get("exact_spread_context_status")
        or merged.get("exact_descriptor_delta_join_status")
        or ""
    )
    if "EXACT_SPREAD_RECOMPUTED" in exact_spread_context:
        status = "EXACT_SPREAD_REPAIRED_PROXY_AVAILABLE_NOT_BROKER_EXACT_R"
    elif "DIRECT_JOIN_ABSENT" in exact_spread_context or "UNAVAILABLE" in exact_spread_context:
        status = "EXACT_R_NOT_COMPUTABLE_SOURCE_JOIN_ABSENT"
    else:
        status = "EXACT_R_NOT_COMPUTABLE_MISSING_BROKER_EXECUTION_GEOMETRY"
    return {
        "exact_r_status": status,
        "exact_r_value": None,
        "exact_r_source_key": None,
        "exact_missing_field_proof": missing,
    }


def proxy_r_evidence(
    execution_row: dict[str, Any],
    computed_row: dict[str, Any] | None = None,
    branch_row: dict[str, Any] | None = None,
    sidecar_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    branch_mid, _ = _first_numeric(branch_row, keys=("rstyle_midpoint_mean",))
    branch_low, _ = _first_numeric(branch_row, keys=("rstyle_lower_mean",))
    branch_high, _ = _first_numeric(branch_row, keys=("rstyle_upper_mean",))
    expectancy = None
    if branch_row and isinstance(branch_row.get("expectancy_style_proxy"), dict):
        expectancy = to_float(branch_row["expectancy_style_proxy"].get("midpoint_mean"))
    computed_delta, computed_key = _first_numeric(
        computed_row,
        execution_row,
        keys=("expectancy_style_proxy_delta", "computed_proxy_delta", "pass_control_delta_proxy"),
    )
    if branch_mid is not None:
        return {
            "proxy_r_status": "PROXY_RSTYLE_FROM_BRANCH_REPLAY_TABLE",
            "proxy_r_value": round(branch_mid, 6),
            "proxy_r_lower": round(branch_low, 6) if branch_low is not None else None,
            "proxy_r_upper": round(branch_high, 6) if branch_high is not None else None,
            "proxy_r_method": "branch_replay_rstyle_midpoint_mean",
            "expectancy_proxy_value": round(expectancy if expectancy is not None else branch_mid, 6),
            "expectancy_proxy_method": "branch_expectancy_style_proxy_midpoint",
        }
    if computed_delta is not None:
        return {
            "proxy_r_status": "PROXY_RSTYLE_FROM_COMPUTED_SIGNED_DELTA",
            "proxy_r_value": round(computed_delta, 6),
            "proxy_r_lower": None,
            "proxy_r_upper": None,
            "proxy_r_method": computed_key or "computed_signed_delta",
            "expectancy_proxy_value": round(computed_delta, 6),
            "expectancy_proxy_method": "computed_expectancy_style_proxy_delta",
        }
    return {
        "proxy_r_status": "PROXY_R_NOT_COMPUTABLE_FROM_CURRENT_FIELDS",
        "proxy_r_value": None,
        "proxy_r_lower": None,
        "proxy_r_upper": None,
        "proxy_r_method": "missing_computed_delta_and_branch_rstyle_proxy",
        "expectancy_proxy_value": None,
        "expectancy_proxy_method": "missing_proxy_expectancy_fields",
    }


def classify_proxy_delta(value: float | None) -> str:
    if value is None:
        return "NO_NUMERIC_PROXY_R"
    if value >= 0.15:
        return "STRONG_POSITIVE_PROXY_R"
    if value >= 0.05:
        return "POSITIVE_PROXY_R"
    if value > -0.05:
        return "NEUTRAL_PROXY_R"
    if value > -0.15:
        return "NEGATIVE_PROXY_R"
    return "STRONG_NEGATIVE_PROXY_R"


def cost_stress_evidence(
    branch_row: dict[str, Any] | None = None,
    sidecar_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = sidecar_row or {}
    branch = branch_row or {}
    cost_counts = _counter_dict(branch.get("cost_sensitivity", {}).get("branch_status_cost_counters")) if isinstance(branch.get("cost_sensitivity"), dict) else {}
    if not cost_counts:
        cost_counts = _counter_dict(source.get("cost_sensitivity_status_counts"))
    spread_distance, spread_key = _first_numeric(
        source,
        keys=("first_tick_spread_price_distance", "market_spread_proxy_price_distance"),
    )
    if cost_counts:
        sensitive = sum(
            count
            for status, count in cost_counts.items()
            if "GRADIENT" in status.upper() or "SHIFT" in status.upper() or "SENSITIVE" in status.upper()
        )
        total = sum(cost_counts.values())
        share = round(sensitive / total, 6) if total else None
        return {
            "cost_stress_status": "COST_STRESS_COMPUTED_FROM_SPREAD_SENSITIVITY_COUNTS",
            "cost_sensitivity_counts": cost_counts,
            "cost_sensitive_share": share,
            "spread_distance_proxy": spread_distance,
            "spread_distance_source_key": spread_key,
        }
    if spread_distance is not None:
        return {
            "cost_stress_status": "COST_STRESS_SPREAD_DISTANCE_PROXY_AVAILABLE",
            "cost_sensitivity_counts": {},
            "cost_sensitive_share": None,
            "spread_distance_proxy": round(spread_distance, 9),
            "spread_distance_source_key": spread_key,
        }
    return {
        "cost_stress_status": "COST_STRESS_NOT_COMPUTABLE_NO_SPREAD_OR_SLIPPAGE_FIELD",
        "cost_sensitivity_counts": {},
        "cost_sensitive_share": None,
        "spread_distance_proxy": None,
        "spread_distance_source_key": None,
    }


def keep_kill_redesign_implement_decision(
    execution_row: dict[str, Any],
    computed_row: dict[str, Any] | None,
    proxy_value: float | None,
    exact_status: str,
    target_stop_order_class: str,
) -> str:
    family = str(execution_row.get("integrated_result_execution_family") or "")
    component = str(execution_row.get("source_component") or "")
    current_claim_rejection = execution_row.get("current_claim_only_rejection") is True
    if current_claim_rejection:
        return "REJECT_CURRENT_CLAIM_PRESERVE_MECHANISM_OPPORTUNITY"
    if proxy_value is None:
        if "SOURCE" in family or "source" in component.lower() or "GUARD" in family:
            return "SOURCE_GEOMETRY_REPAIR_OR_GUARD_BINDING_REQUIRED"
        return "REDESIGN_OR_REPLAY_REPAIR_REQUIRED_NO_NUMERIC_PROXY"
    if proxy_value >= 0.15:
        if "SCORER" in family:
            return "IMPLEMENT_DEFAULT_OFF_SCORER_RESEARCH_MODULE"
        if "NOFILL" in family and "TARGET" in target_stop_order_class:
            return "KEEP_NOFILL_CHALLENGER_COMPARATOR_STRONG_POSITIVE"
        return "KEEP_STRONG_POSITIVE_PROXY_R_WITH_CONTROL"
    if proxy_value >= 0.05:
        if "AVOID" in family:
            return "KEEP_AVOID_INVERSE_FILTER_POSITIVE_PROXY"
        return "KEEP_POSITIVE_PROXY_R_WITH_CONTROL"
    if proxy_value <= -0.15:
        return "CONVERT_STRONG_NEGATIVE_TO_AVOID_INVERSE_OR_FAILURE_FILTER"
    if proxy_value < -0.05:
        return "REDESIGN_NEGATIVE_PROXY_OR_MERGE_AS_CONTEXT_FEATURE"
    if exact_status.startswith("EXACT_R_NOT_COMPUTABLE"):
        return "MERGE_AS_CONTROL_CONTEXT_PENDING_EXACT_GEOMETRY"
    return "KEEP_NEUTRAL_PROXY_AS_CONTEXT_OR_STRESS_CONTROL"


def numeric_result_row(
    execution_row: dict[str, Any],
    computed_row: dict[str, Any] | None,
    branch_row: dict[str, Any] | None,
    sidecar_row: dict[str, Any] | None,
    index: int,
    *,
    branch_match_count: int = 0,
    branch_match_status: str = "NO_BRANCH_SCOPE_MATCH",
) -> dict[str, Any]:
    exact = exact_r_evidence(execution_row, computed_row, branch_row, sidecar_row)
    proxy = proxy_r_evidence(execution_row, computed_row, branch_row, sidecar_row)
    target_class, target_counts, target_basis = classify_target_stop_order(branch_row, sidecar_row, computed_row, execution_row)
    cost = cost_stress_evidence(branch_row, sidecar_row)
    pass_control_delta, _ = _first_numeric(
        computed_row,
        execution_row,
        keys=("pass_control_delta_proxy", "computed_proxy_delta", "expectancy_style_proxy_delta"),
    )
    computed_proxy_score, _ = _first_numeric(
        computed_row,
        execution_row,
        keys=("computed_proxy_score", "proxy_score", "computed_proxy_delta"),
    )
    decision_proxy_value = proxy["proxy_r_value"]
    if pass_control_delta is not None:
        if decision_proxy_value is None:
            decision_proxy_value = pass_control_delta
        elif pass_control_delta >= 0 and decision_proxy_value >= 0:
            decision_proxy_value = max(decision_proxy_value, pass_control_delta)
        elif pass_control_delta <= 0 and decision_proxy_value <= 0:
            decision_proxy_value = min(decision_proxy_value, pass_control_delta)
    proxy_class = classify_proxy_delta(proxy["proxy_r_value"])
    decision = keep_kill_redesign_implement_decision(
        execution_row,
        computed_row,
        decision_proxy_value,
        exact["exact_r_status"],
        target_class,
    )
    return {
        "numeric_result_surface": NUMERIC_SCORER_SURFACE,
        "numeric_result_row_id": f"OHLC-GTOS-INTEGRATED-NUMERIC-RESULT-{index:06d}",
        "input_integrated_result_execution_row_id": execution_row.get("integrated_result_execution_row_id"),
        "input_unified_system_computed_action_row_id": execution_row.get("input_unified_system_computed_action_row_id"),
        "computed_action_row_joined": computed_row is not None,
        "branch_rstyle_row_joined": branch_row is not None,
        "sidecar_source_row_joined": sidecar_row is not None,
        "branch_match_count": branch_match_count,
        "branch_match_status": branch_match_status,
        "matched_branch_queue_id": (branch_row or {}).get("branch_queue_id"),
        "source_component": execution_row.get("source_component"),
        "source_row_id": execution_row.get("source_row_id"),
        "symbol": execution_row.get("symbol"),
        "route_session": execution_row.get("route_session"),
        "horizon_id": execution_row.get("horizon_id"),
        "primitive_flag": execution_row.get("primitive_flag"),
        "mechanical_scope_key": execution_row.get("mechanical_scope_key"),
        "integrated_result_execution_family": execution_row.get("integrated_result_execution_family"),
        "integrated_result_execution_status": execution_row.get("integrated_result_execution_status"),
        "computed_action_family": (computed_row or {}).get("computed_action_family"),
        "computed_action_status": (computed_row or {}).get("computed_action_status"),
        "computed_decision": (computed_row or {}).get("computed_decision"),
        "computed_proxy_delta": round(pass_control_delta, 6) if pass_control_delta is not None else None,
        "pass_control_delta_proxy": round(pass_control_delta, 6) if pass_control_delta is not None else None,
        "computed_proxy_score": round(computed_proxy_score, 6) if computed_proxy_score is not None else None,
        "decision_proxy_value": round(decision_proxy_value, 6) if decision_proxy_value is not None else None,
        "target_stop_order_class": target_class,
        "target_stop_order_basis": target_basis,
        "target_stop_status_counts": target_counts,
        "proxy_r_class": proxy_class,
        "keep_kill_redesign_implement_decision": decision,
        "negative_or_failure_intelligence_role": (
            "avoid_inverse_or_entry_failure_filter"
            if proxy["proxy_r_value"] is not None and proxy["proxy_r_value"] < -0.05
            else "not_negative_failure_role"
        ),
        "missing_geometry_source_decision": (
            "exact_missing_fields_proven_use_proxy_or_repair"
            if exact["exact_missing_field_proof"]
            else "exact_or_repaired_geometry_available"
        ),
        "source_hashes": {
            "execution_source_manifest_hash": execution_row.get("source_manifest_hash")
            or execution_row.get("upstream_source_manifest_hash"),
            "computed_source_manifest_hash": (computed_row or {}).get("source_manifest_hash"),
            "branch_source_manifest_hash": (branch_row or {}).get("source_manifest_hash"),
            "sidecar_source_manifest_hash": (sidecar_row or {}).get("source_manifest_hash"),
        },
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
        **exact,
        **proxy,
        **cost,
    }


def _numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [value for value in (to_float(row.get(key)) for row in rows) if value is not None]


def numeric_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    values = _numeric_values(rows, "proxy_r_value")
    expectancy = _numeric_values(rows, "expectancy_proxy_value")
    decisions = Counter(str(row.get("keep_kill_redesign_implement_decision")) for row in rows)
    exact = Counter(str(row.get("exact_r_status")) for row in rows)
    proxy = Counter(str(row.get("proxy_r_class")) for row in rows)
    target = Counter(str(row.get("target_stop_order_class")) for row in rows)
    cost = Counter(str(row.get("cost_stress_status")) for row in rows)
    return {
        "numeric_rollup_surface": NUMERIC_SCORER_SURFACE,
        "numeric_rollup_row_id": f"OHLC-GTOS-INTEGRATED-NUMERIC-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "row_count": len(rows),
        "numeric_proxy_r_count": len(values),
        "proxy_r_mean": round(mean(values), 6) if values else None,
        "proxy_r_min": round(min(values), 6) if values else None,
        "proxy_r_max": round(max(values), 6) if values else None,
        "expectancy_proxy_count": len(expectancy),
        "expectancy_proxy_mean": round(mean(expectancy), 6) if expectancy else None,
        "exact_r_status_counts": {key: int(exact[key]) for key in sorted(exact)},
        "proxy_r_class_counts": {key: int(proxy[key]) for key in sorted(proxy)},
        "target_stop_order_counts": {key: int(target[key]) for key in sorted(target)},
        "cost_stress_status_counts": {key: int(cost[key]) for key in sorted(cost)},
        "decision_counts": {key: int(decisions[key]) for key in sorted(decisions)},
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
