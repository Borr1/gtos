"""Research-only runtime work helpers for observable implementation candidates."""

from __future__ import annotations

from typing import Any


RUNTIME_WORK_SURFACE = "src/research_infra/moonshot_observable_runtime_work.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def parse_scope_key(scope_key: Any) -> dict[str, str | None]:
    parts = {"symbol": None, "session": None, "horizon": None, "primitive": None}
    for chunk in str(scope_key or "").split("|"):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        if key in parts:
            parts[key] = None if value == "None" else value
    return parts


def _priority(row: dict[str, Any], bonus: float = 0.0) -> float:
    return clamp01((to_float(row.get("implementation_priority_score")) or 0.0) + bonus)


def runtime_work_decision(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_candidate_status") or "")
    if status == "OBSERVABLE_IMPL_ENABLE_CONTROLLED_CHALLENGER_SCORER":
        work_status = "RUNTIME_WORK_ENABLE_CONTROLLED_OBSERVABLE_SCORER"
        operation = "REGISTER_BRANCH_LOCAL_CONTROLLED_SCORER"
        decision = "EXECUTE_SCORER_REGISTRATION_NOW"
        ready = True
        control_required = False
        repair_required = False
        bonus = 0.04
    elif status == "OBSERVABLE_IMPL_REGISTER_DENOMINATOR_GUARDED_SHADOW":
        work_status = "RUNTIME_WORK_REGISTER_DENOMINATOR_GUARDED_OBSERVABLE"
        operation = "REGISTER_BRANCH_LOCAL_DENOMINATOR_GUARDED_OBSERVABLE"
        decision = "EXECUTE_GUARDED_OBSERVABLE_REGISTRATION_NOW"
        ready = True
        control_required = False
        repair_required = False
        bonus = 0.02
    elif status == "OBSERVABLE_IMPL_BUILD_CONTROL_SCOPE_BEFORE_ENABLE":
        work_status = "RUNTIME_WORK_BUILD_CONTROL_SCOPE"
        operation = "MATERIALIZE_OR_PROXY_CONTROL_SCOPE"
        decision = "EXECUTE_CONTROL_SCOPE_BUILDER"
        ready = False
        control_required = True
        repair_required = False
        bonus = 0.0
    elif status in {"SOURCE_IMPL_GUARDED_PROXY_SCORER", "SOURCE_IMPL_AMBIGUOUS_PROXY_CONTROL_SCORER"}:
        work_status = "RUNTIME_WORK_REGISTER_SOURCE_PROXY_SCORER"
        operation = "REGISTER_SOURCE_PROXY_SCORER_WITH_GUARDS"
        decision = "EXECUTE_SOURCE_PROXY_SCORER_REGISTRATION"
        ready = True
        control_required = status == "SOURCE_IMPL_AMBIGUOUS_PROXY_CONTROL_SCORER"
        repair_required = False
        bonus = 0.02
    elif status in {
        "SOURCE_IMPL_EXACT_SOURCE_REPAIR_WORK_ORDER",
        "SOURCE_IMPL_HORIZON_REPAIR_KILL_CHECK",
        "SOURCE_IMPL_HORIZON_REPAIR_RESCORE",
    }:
        work_status = "RUNTIME_WORK_EXECUTE_SOURCE_REPAIR"
        operation = "EXECUTE_SOURCE_OR_HORIZON_REPAIR_WORK"
        decision = "EXECUTE_SOURCE_REPAIR_WORK_ORDER"
        ready = False
        control_required = False
        repair_required = True
        bonus = 0.01
    elif status == "CONTROL_IMPL_COMPARATOR_READY":
        work_status = "RUNTIME_WORK_CONTROL_COMPARATOR_READY"
        operation = "REGISTER_CONTROL_COMPARATOR"
        decision = "EXECUTE_CONTROL_COMPARATOR_REGISTRATION"
        ready = True
        control_required = False
        repair_required = False
        bonus = 0.0
    elif status.startswith("DENOMINATOR_IMPL_"):
        work_status = "RUNTIME_WORK_ENFORCE_DENOMINATOR_GUARD"
        operation = "REGISTER_DENOMINATOR_GUARD"
        decision = "EXECUTE_DENOMINATOR_GUARD_REGISTRATION"
        ready = True
        control_required = False
        repair_required = False
        bonus = 0.0
    else:
        work_status = "RUNTIME_WORK_PRESERVE_CONTEXT"
        operation = "PRESERVE_CONTEXT"
        decision = "PRESERVE_CONTEXT_ONLY"
        ready = False
        control_required = bool(row.get("control_builder_required"))
        repair_required = bool(row.get("source_repair_required"))
        bonus = 0.0
    return {
        "runtime_work_surface": RUNTIME_WORK_SURFACE,
        "runtime_work_status": work_status,
        "runtime_operation": operation,
        "runtime_decision": decision,
        "runtime_ready": ready,
        "runtime_control_required": control_required,
        "runtime_source_repair_required": repair_required,
        "runtime_priority_score": _priority(row, bonus),
        "runtime_effect": "branch_local_shadow_work_only",
        "live_effect": False,
    }


def _control_scope_parts(row: dict[str, Any]) -> dict[str, str | None]:
    return parse_scope_key(row.get("observable_scope_key"))


def _matches(parts: dict[str, str | None], row: dict[str, Any], keys: tuple[str, ...]) -> bool:
    candidate = _control_scope_parts(row)
    return all(candidate.get(key) == parts.get(key) for key in keys)


def control_scope_build_attempt(
    row: dict[str, Any],
    action_row: dict[str, Any],
    control_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    parts = parse_scope_key(row.get("observable_scope_key"))
    exact = [candidate for candidate in control_rows if candidate.get("observable_scope_key") == row.get("observable_scope_key")]
    same_symbol_session_horizon = [
        candidate for candidate in control_rows if _matches(parts, candidate, ("symbol", "session", "horizon"))
    ]
    same_symbol_session = [candidate for candidate in control_rows if _matches(parts, candidate, ("symbol", "session"))]
    same_symbol = [candidate for candidate in control_rows if _matches(parts, candidate, ("symbol",))]
    if exact:
        status = "CONTROL_SCOPE_BUILDER_EXACT_SCOPE_READY"
        decision = "USE_EXACT_CONTROL_SCOPE"
        matched = exact
    elif len(same_symbol_session_horizon) >= 20:
        status = "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_SESSION_HORIZON_N20"
        decision = "USE_PROXY_CONTROL_WITH_SCOPE_GUARD"
        matched = same_symbol_session_horizon
    elif len(same_symbol_session) >= 20:
        status = "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_SESSION_N20"
        decision = "USE_PROXY_CONTROL_WITH_SESSION_GUARD"
        matched = same_symbol_session
    elif len(same_symbol) >= 20:
        status = "CONTROL_SCOPE_BUILDER_PROXY_SAME_SYMBOL_N20"
        decision = "USE_PROXY_CONTROL_WITH_SYMBOL_GUARD"
        matched = same_symbol
    elif control_rows:
        status = "CONTROL_SCOPE_BUILDER_UNDERPOWERED_GLOBAL_PROXY_ONLY"
        decision = "BUILD_EXACT_CONTROL_DENOMINATOR_BEFORE_SCORING"
        matched = control_rows
    else:
        status = "CONTROL_SCOPE_BUILDER_NO_CONTROL_ROWS_AVAILABLE"
        decision = "BUILD_CONTROL_DENOMINATOR_BEFORE_SCORING"
        matched = []
    selected_candidate_ids = [
        candidate.get("implementation_candidate_row_id")
        or candidate.get("input_implementation_candidate_row_id")
        or candidate.get("runtime_work_row_id")
        for candidate in matched
    ]
    return {
        "runtime_work_surface": RUNTIME_WORK_SURFACE,
        "control_scope_build_status": status,
        "control_scope_build_decision": decision,
        "desired_control_family": action_row.get("desired_control_family"),
        "missing_control_scope_key": action_row.get("missing_control_scope_key") or row.get("observable_scope_key"),
        "exact_control_count": len(exact),
        "same_symbol_session_horizon_control_count": len(same_symbol_session_horizon),
        "same_symbol_session_control_count": len(same_symbol_session),
        "same_symbol_control_count": len(same_symbol),
        "selected_control_count": len(matched),
        "selected_control_candidate_ids": selected_candidate_ids,
        "selected_control_runtime_work_row_ids": [candidate.get("runtime_work_row_id") for candidate in matched],
        "selected_control_input_candidate_ids": [candidate.get("input_implementation_candidate_row_id") for candidate in matched],
        "selected_control_scope_keys": sorted({str(candidate.get("observable_scope_key")) for candidate in matched}),
        "runtime_ready": bool(exact),
        "runtime_control_required": True,
        "live_effect": False,
    }


def source_repair_runtime_work(row: dict[str, Any], action_row: dict[str, Any], duplicate_scope_count: int) -> dict[str, Any]:
    status = str(row.get("implementation_candidate_status") or "")
    if status == "SOURCE_IMPL_EXACT_SOURCE_REPAIR_WORK_ORDER":
        repair_status = "SOURCE_REPAIR_RUNTIME_EXACT_SOURCE_REBUILD_OR_ACQUIRE"
        repair_action = "REBUILD_OR_ACQUIRE_EXACT_SOURCE_ROWS"
        fail_if_negative = False
    elif status == "SOURCE_IMPL_HORIZON_REPAIR_KILL_CHECK":
        repair_status = "SOURCE_REPAIR_RUNTIME_REBUILD_HORIZON_KILL_CHECK"
        repair_action = "REBUILD_TARGETABLE_HORIZON_AND_KILL_IF_NEGATIVE_PERSISTS"
        fail_if_negative = True
    elif status == "SOURCE_IMPL_HORIZON_REPAIR_RESCORE":
        repair_status = "SOURCE_REPAIR_RUNTIME_REBUILD_HORIZON_RESCORE"
        repair_action = "REBUILD_TARGETABLE_HORIZON_AND_RESCORE"
        fail_if_negative = False
    else:
        repair_status = "SOURCE_REPAIR_RUNTIME_CONTEXT_ONLY"
        repair_action = "PRESERVE_SOURCE_REPAIR_CONTEXT"
        fail_if_negative = False
    return {
        "runtime_work_surface": RUNTIME_WORK_SURFACE,
        "source_repair_runtime_status": repair_status,
        "source_repair_action": repair_action,
        "source_action_result_family": action_row.get("source_action_result_family"),
        "source_action_result_status": action_row.get("action_result_status"),
        "duplicate_repair_scope_count": duplicate_scope_count,
        "fail_if_negative_persists": fail_if_negative,
        "runtime_ready": False,
        "runtime_source_repair_required": True,
        "live_effect": False,
    }
