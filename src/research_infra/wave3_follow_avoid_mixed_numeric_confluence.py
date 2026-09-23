"""Wave3 numeric FOLLOW/AVOID/MIXED confluence helpers.

The helpers in this module turn categorical vNext evidence labels into an
auditable numeric source contract. They do not place orders, change broker
state, or grant trade permission from FOLLOW alone.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "wave3_follow_avoid_mixed_numeric_confluence_v4"
DEFAULT_FRESHNESS_MAX_AGE_SECONDS = 14 * 24 * 60 * 60
DEFAULT_MIN_RELIABILITY_N = 20.0

_TIMESTAMP_FIELDS = (
    "timestamp_utc",
    "generated_at_utc",
    "entry_time_utc",
    "event_time_utc",
    "candle_time_utc",
    "candle_close_utc",
    "as_of_utc",
)
_SOURCE_ID_FIELDS = (
    "review_row_id",
    "vnext_matrix_row_id",
    "event_scope_rollup_row_id",
    "registry_catalog_row_id",
    "numeric_router_catalog_runtime_row_id",
    "numeric_result_row_id",
    "survivor_failure_runtime_row_id",
    "branch_ambiguity_collapse_runtime_row_id",
    "branch_followup_computation_runtime_row_id",
    "adverse_stop_first_execution_runtime_row_id",
    "gate_selector_session_timeframe_runtime_row_id",
    "source_geometry_runtime_row_id",
    "source_geometry_repair_row_id",
    "recommendation_unified_candidate_id",
    "recommendation_scope_rollup_id",
    "recommendation_family_rollup_id",
    "bucket_id",
    "frontier_action_id",
    "source_row_id",
    "row_key",
)


def _to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _first_present(row: dict[str, Any], *fields: str) -> Any:
    for field in fields:
        value = row.get(field)
        if value not in (None, ""):
            return value
    return None


def _metric_trace(row: dict[str, Any], metric: str) -> dict[str, Any] | None:
    traces = row.get("r_metric_traces")
    if isinstance(traces, dict) and isinstance(traces.get(metric), dict):
        return traces[metric]
    metrics = row.get("r_metrics")
    if isinstance(metrics, dict) and isinstance(metrics.get(metric), dict):
        return metrics[metric]
    value = _first_present(row, metric, f"{metric}_sum", f"{metric}_value")
    numeric = _to_float(value)
    if numeric is None:
        return None
    return {
        "sum": numeric,
        "mean": numeric,
        "match_rows_with_metric": 1,
        "positive_rows": 1 if numeric > 0 else 0,
        "negative_rows": 1 if numeric < 0 else 0,
        "zero_rows": 1 if numeric == 0 else 0,
    }


def _metric_sum(row: dict[str, Any], metric: str) -> float | None:
    trace = _metric_trace(row, metric)
    if not trace:
        return None
    value = _to_float(trace.get("sum"))
    if value is not None:
        return value
    mean = _to_float(trace.get("mean"))
    count = _to_float(trace.get("match_rows_with_metric") or trace.get("count"))
    if mean is None:
        return None
    return mean * (count or 1.0)


def _metric_count(row: dict[str, Any], metric: str) -> float:
    trace = _metric_trace(row, metric)
    if not trace:
        return 0.0
    return _to_float(trace.get("match_rows_with_metric") or trace.get("count")) or 0.0


def _source_id(row: dict[str, Any]) -> str:
    for field in _SOURCE_ID_FIELDS:
        value = _normalized(row.get(field))
        if value:
            return value
    return "unknown_source_id"


def _direction(row: dict[str, Any]) -> str:
    scope = row.get("event_scope") if isinstance(row.get("event_scope"), dict) else {}
    raw = _normalized(
        row.get("direction")
        or row.get("side")
        or row.get("expected_sign_inferred")
        or scope.get("direction")
        or scope.get("side")
    ).upper()
    if raw in {"BUY", "BULL", "BULLISH", "LONG", "UP"}:
        return "LONG"
    if raw in {"SELL", "BEAR", "BEARISH", "SHORT", "DOWN"}:
        return "SHORT"
    if raw in {"BOTH", "TWO_SIDED", "TWO-SIDED"}:
        return "TWO_SIDED"
    return raw or "UNKNOWN"


def _parse_datetime(value: Any) -> datetime | None:
    text = _normalized(value)
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _configured_now(cfg: dict[str, Any] | None) -> datetime:
    raw = (cfg or {}).get("numeric_confluence_now_utc")
    parsed = _parse_datetime(raw)
    if parsed is not None:
        return parsed
    return datetime.now(timezone.utc)


def _freshness(row: dict[str, Any], cfg: dict[str, Any] | None) -> dict[str, Any]:
    timestamp_fields = tuple((cfg or {}).get("numeric_confluence_timestamp_fields") or _TIMESTAMP_FIELDS)
    for field in timestamp_fields:
        parsed = _parse_datetime(row.get(field))
        if parsed is None:
            continue
        now = _configured_now(cfg)
        age_seconds = max(0.0, (now - parsed).total_seconds())
        max_age = _to_float((cfg or {}).get("numeric_confluence_freshness_max_age_seconds"))
        max_age = max_age if max_age and max_age > 0 else DEFAULT_FRESHNESS_MAX_AGE_SECONDS
        score = max(0.0, min(1.0, 1.0 - age_seconds / max_age))
        return {
            "status": "timestamp_present",
            "timestamp_field": field,
            "timestamp_utc": parsed.isoformat(),
            "age_seconds": round(age_seconds, 6),
            "freshness_score": round(score, 6),
            "max_age_seconds": max_age,
        }
    return {
        "status": "source_timestamp_missing",
        "timestamp_field": None,
        "timestamp_utc": None,
        "age_seconds": None,
        "freshness_score": 0.5,
        "max_age_seconds": _to_float((cfg or {}).get("numeric_confluence_freshness_max_age_seconds"))
        or DEFAULT_FRESHNESS_MAX_AGE_SECONDS,
    }


def _evidence_class(row: dict[str, Any]) -> str:
    return _normalized(
        row.get("r_evidence_class")
        or row.get("evidence_class")
        or row.get("evidence_family")
        or row.get("source_role")
        or row.get("source_group")
    ) or "source_bound_runtime_evidence"


def _weighted_signal(row: dict[str, Any], cfg: dict[str, Any] | None) -> tuple[float, dict[str, float]]:
    cfg = cfg or {}
    weights = {
        "cost_adjusted_simulated_r": _to_float(cfg.get("conflict_cost_adjusted_r_weight")) or 1.0,
        "stress_simulated_r": _to_float(cfg.get("conflict_stress_r_weight")) or 0.25,
        "proxy_score": _to_float(cfg.get("conflict_proxy_score_weight")) or 1.0,
    }
    components: dict[str, float] = {}
    for metric, weight in weights.items():
        value = _metric_sum(row, metric)
        if value is None:
            continue
        components[metric] = round(value * weight, 12)
    return round(sum(components.values()), 12), components


def _reliability_history(row: dict[str, Any], cfg: dict[str, Any] | None) -> dict[str, Any]:
    effective_n = _metric_sum(row, "effective_n")
    if effective_n is None:
        effective_n = _to_float(
            _first_present(
                row,
                "effective_n",
                "row_count",
                "source_event_rows",
                "source_rows_represented",
                "event_count",
            )
        )
    metric_count = sum(
        _metric_count(row, metric)
        for metric in ("cost_adjusted_simulated_r", "stress_simulated_r", "proxy_score")
    )
    min_n = _to_float((cfg or {}).get("numeric_confluence_min_reliability_n"))
    min_n = min_n if min_n and min_n > 0 else DEFAULT_MIN_RELIABILITY_N
    score = min(1.0, max(0.0, float(effective_n or 0.0) / min_n))
    return {
        "effective_n": effective_n,
        "min_reliability_n": min_n,
        "metric_count": metric_count,
        "reliability_score": round(score, 6),
        "status": "reliability_metric_present" if effective_n is not None else "reliability_metric_missing",
    }


def _cost_sensitivity(row: dict[str, Any]) -> dict[str, Any]:
    cost = _metric_sum(row, "cost_adjusted_simulated_r")
    stress = _metric_sum(row, "stress_simulated_r")
    status = _normalized(row.get("cost_stress_status") or row.get("cost_sensitivity_status"))
    if cost is not None and stress is not None:
        delta = cost - stress
        return {
            "status": status or "cost_and_stress_metrics_present",
            "cost_adjusted_simulated_r": cost,
            "stress_simulated_r": stress,
            "stress_delta": round(delta, 12),
            "cost_sensitivity_score": round(abs(delta), 12),
        }
    if cost is not None:
        return {
            "status": status or "cost_metric_present_stress_missing",
            "cost_adjusted_simulated_r": cost,
            "stress_simulated_r": None,
            "stress_delta": None,
            "cost_sensitivity_score": 0.0,
        }
    return {
        "status": status or "cost_source_missing_or_not_applicable",
        "cost_adjusted_simulated_r": None,
        "stress_simulated_r": stress,
        "stress_delta": None,
        "cost_sensitivity_score": 0.0,
    }


def _avoid_invalidation_type(row: dict[str, Any]) -> str:
    text = " ".join(
        _normalized(row.get(field)).upper()
        for field in (
            "implementation_action",
            "action_class",
            "target_stop_order_class",
            "proxy_r_class",
            "runtime_effect_now",
            "source_group",
            "source_role",
        )
    )
    if "STOP_FIRST" in text:
        return "stop_first_or_adverse_path"
    if "COST" in text or "SWAP" in text or "SLIPPAGE" in text:
        return "broker_net_cost_or_slippage"
    if "SOURCE" in text and "REPAIR" in text:
        return "source_repair_required_before_use"
    if "NEGATIVE" in text or "FAILURE" in text or "AVOID" in text:
        return "negative_proxy_or_failure_filter"
    return "explicit_avoid_without_more_specific_invalidation"


def _source_completeness(
    row: dict[str, Any],
    *,
    source_id: str,
    direction: str,
    evidence_class: str,
    signal_components: dict[str, float],
    freshness: dict[str, Any],
) -> dict[str, Any]:
    checks = {
        "source_id": source_id != "unknown_source_id",
        "direction": direction != "UNKNOWN",
        "evidence_class": bool(evidence_class),
        "source_path_or_artifact": bool(
            _normalized(row.get("source_path") or row.get("source_artifact") or row.get("_gtos_vnext_loaded_from"))
        ),
        "source_component_or_family": bool(
            _normalized(row.get("source_component") or row.get("evidence_family") or row.get("source_name"))
        ),
        "numeric_signal": bool(signal_components),
        "freshness": freshness.get("status") == "timestamp_present",
    }
    missing = [field for field, present in checks.items() if not present]
    score = sum(1 for present in checks.values() if present) / len(checks)
    source_complete_flag = row.get("source_complete")
    if source_complete_flag is False:
        score = min(score, 0.5)
        missing.append("source_complete_flag_false")
    proof = row.get("exact_missing_field_proof")
    if isinstance(proof, list) and proof:
        score = min(score, 0.5)
        missing.append("exact_missing_field_proof")
    status = "complete" if score >= 0.999 else "partial" if score > 0 else "missing"
    return {
        "status": status,
        "score": round(score, 6),
        "required_checks": checks,
        "missing_fields": sorted(set(missing)),
        "source_complete_flag": source_complete_flag,
    }


def _conflict_reason(
    *,
    decision: str,
    row: dict[str, Any],
    signal_score: float,
    components: dict[str, float],
    completeness: dict[str, Any],
) -> str:
    if decision == "FOLLOW":
        return "source_pressure_supports_direction_not_trade_permission"
    if decision == "AVOID":
        return f"avoid_invalidation:{_avoid_invalidation_type(row)}"
    positive = any(value > 0 for value in components.values())
    negative = any(value < 0 for value in components.values())
    if positive and negative:
        return "mixed_structured_disagreement:positive_and_negative_numeric_components"
    if completeness.get("status") != "complete":
        return "mixed_structured_disagreement:source_incomplete_or_stale"
    if signal_score == 0:
        return "mixed_structured_disagreement:no_dominant_numeric_pressure"
    return "mixed_structured_disagreement:context_guard_or_repair_required"


def build_numeric_confluence_source(
    row: dict[str, Any],
    *,
    decision: str,
    cfg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the source-level numeric confluence contract for one row."""
    source_id = _source_id(row)
    direction = _direction(row)
    evidence_class = _evidence_class(row)
    signal_score, components = _weighted_signal(row, cfg)
    freshness = _freshness(row, cfg)
    reliability = _reliability_history(row, cfg)
    completeness = _source_completeness(
        row,
        source_id=source_id,
        direction=direction,
        evidence_class=evidence_class,
        signal_components=components,
        freshness=freshness,
    )
    confidence = round(
        reliability["reliability_score"]
        * completeness["score"]
        * float(freshness["freshness_score"]),
        6,
    )
    strength = round(abs(signal_score), 12)
    reason = _conflict_reason(
        decision=decision,
        row=row,
        signal_score=signal_score,
        components=components,
        completeness=completeness,
    )
    avoid_invalidation = _avoid_invalidation_type(row) if decision == "AVOID" else None
    structured_disagreement = {
        "present": decision == "MIXED",
        "reason": reason if decision == "MIXED" else None,
        "positive_component_count": sum(1 for value in components.values() if value > 0),
        "negative_component_count": sum(1 for value in components.values() if value < 0),
        "source_complete": completeness["status"] == "complete",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "source_id": source_id,
        "categorical_label": decision,
        "direction": direction,
        "strength": strength,
        "signed_strength": signal_score,
        "confidence": confidence,
        "reliability_history": reliability,
        "evidence_class": evidence_class,
        "freshness": freshness,
        "cost_sensitivity": _cost_sensitivity(row),
        "conflict_reason": reason,
        "source_completeness": completeness,
        "avoid_invalidation_type": avoid_invalidation,
        "structured_disagreement": structured_disagreement,
        "numeric_components": components,
        "source_path": _normalized(row.get("source_path") or row.get("source_artifact") or row.get("_gtos_vnext_loaded_from")) or None,
        "source_component": _normalized(row.get("source_component")) or None,
        "source_name": _normalized(row.get("source_name")) or None,
        "follow_is_trade_permission": False,
        "candidate_use_allowed_now_by_confluence": False,
        "runtime_candidate_use_permitted_by_confluence": False,
    }


def summarize_numeric_confluence_sources(sources: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate source-level confluence without dropping individual rows."""
    labels = Counter(str(row.get("categorical_label") or "") for row in sources)
    directions = Counter(str(row.get("direction") or "") for row in sources)
    evidence_classes = Counter(str(row.get("evidence_class") or "") for row in sources)
    incomplete = [
        row
        for row in sources
        if (row.get("source_completeness") or {}).get("status") != "complete"
    ]
    stale = [
        row
        for row in sources
        if (row.get("freshness") or {}).get("status") != "timestamp_present"
    ]
    follow_strength = sum(float(row.get("strength") or 0.0) for row in sources if row.get("categorical_label") == "FOLLOW")
    avoid_strength = sum(float(row.get("strength") or 0.0) for row in sources if row.get("categorical_label") == "AVOID")
    mixed_strength = sum(float(row.get("strength") or 0.0) for row in sources if row.get("categorical_label") == "MIXED")
    confidence_values = [float(row.get("confidence") or 0.0) for row in sources]
    return {
        "schema_version": SCHEMA_VERSION,
        "source_count": len(sources),
        "source_ids": [row.get("source_id") for row in sources],
        "label_counts": {key: value for key, value in labels.items() if key},
        "direction_counts": {key: value for key, value in directions.items() if key},
        "evidence_class_counts": {key: value for key, value in evidence_classes.items() if key},
        "strength_by_label": {
            "FOLLOW": round(follow_strength, 12),
            "AVOID": round(avoid_strength, 12),
            "MIXED": round(mixed_strength, 12),
        },
        "confidence": {
            "min": min(confidence_values) if confidence_values else None,
            "max": max(confidence_values) if confidence_values else None,
            "mean": round(sum(confidence_values) / len(confidence_values), 6)
            if confidence_values
            else None,
        },
        "source_completeness": {
            "complete_sources": len(sources) - len(incomplete),
            "incomplete_sources": len(incomplete),
            "incomplete_source_ids": [row.get("source_id") for row in incomplete],
        },
        "freshness": {
            "timestamped_sources": len(sources) - len(stale),
            "missing_timestamp_sources": len(stale),
            "missing_timestamp_source_ids": [row.get("source_id") for row in stale],
        },
        "structured_disagreement_sources": [
            row.get("source_id")
            for row in sources
            if (row.get("structured_disagreement") or {}).get("present")
        ],
        "sources": sources,
        "follow_is_trade_permission": False,
        "candidate_use_allowed_now_by_confluence": False,
        "runtime_candidate_use_permitted_by_confluence": False,
    }


def final_numeric_confluence_mapping(
    *,
    selected_decision: str,
    resolution_evidence: dict[str, Any],
    confluence_summary: dict[str, Any],
) -> dict[str, Any]:
    """Attach final decision mapping while preserving non-permission semantics."""
    strengths = confluence_summary.get("strength_by_label") or {}
    if selected_decision == "AVOID":
        action_type = "avoid_invalidation_or_veto"
    elif selected_decision == "FOLLOW":
        action_type = "follow_candidate_for_downstream_probability_scheduler_audit"
    elif selected_decision == "MIXED":
        action_type = "structured_disagreement_requires_downstream_resolution"
    else:
        action_type = "legacy_no_numeric_confluence_match"
    return {
        "schema_version": SCHEMA_VERSION,
        "selected_label": selected_decision,
        "action_type": action_type,
        "selected_strength": strengths.get(selected_decision, 0.0),
        "resolution_mode": resolution_evidence.get("mode"),
        "raw_decision_counts": resolution_evidence.get("raw_decision_counts", {}),
        "selected_decision": resolution_evidence.get("selected_decision", selected_decision),
        "follow_pressure": resolution_evidence.get("follow_pressure"),
        "avoid_pressure": resolution_evidence.get("avoid_pressure"),
        "dominance_ratio": resolution_evidence.get("dominance_ratio"),
        "source_count": confluence_summary.get("source_count", 0),
        "source_completeness": confluence_summary.get("source_completeness", {}),
        "freshness": confluence_summary.get("freshness", {}),
        "follow_is_trade_permission": False,
        "candidate_use_allowed_now_by_confluence": False,
        "runtime_candidate_use_permitted_by_confluence": False,
    }
