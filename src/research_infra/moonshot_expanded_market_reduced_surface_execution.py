"""Main-side helpers for moonshot reduced-surface execution candidates.

The weekend moonshot worktree executes leakage-reduced expanded-market surfaces
against held implementation-selection rows. This module gives main a compact,
testable representation of those passing branch-local surfaces while keeping
runtime candidate use disabled.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


SURFACE = "src/research_infra/moonshot_expanded_market_reduced_surface_execution.py"
BOUNDARY_SCHEMA = "main_side_moonshot_expanded_market_reduced_surface_execution_v1"
DEFAULT_CANDIDATE_LEDGER = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization/"
    "MAIN_ORCH48_MOONSHOT_REDUCED_SURFACE_CANDIDATE_LEDGER_2026-05-18.jsonl"
)
BASE_SCOPE_KEYS = (
    "horizon_id",
    "market_timeframe",
    "route_session",
    "selected_side",
    "source_component",
    "source_symbol",
    "symbol",
)
AI_NARROWING_EVENT_REQUIRED_FIELDS = BASE_SCOPE_KEYS
SOURCE_IDENTITY_KEYS = ("source_path", "source_file_sha256")
NUMERIC_THRESHOLD_FIELDS = (
    "selected_intrabar_cost_adjusted_simulated_r",
    "selected_minus_rejected_intrabar_cost_adjusted_r",
    "temporal_positive_winner_fold_share",
    "temporal_winner_consistency_share",
)
DEFAULT_EVENT_REQUIRED_FIELDS = (*BASE_SCOPE_KEYS, *SOURCE_IDENTITY_KEYS, *NUMERIC_THRESHOLD_FIELDS)
FINAL_REVIEW_IMPLEMENT_READY_STATUS = "DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY"
FINAL_REVIEW_CAPACITY_BLOCKED_STATUS = "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN"
EVENT_FIELD_ALIASES = {
    "market_timeframe": ("market_timeframe", "timeframe"),
    "route_session": ("route_session", "session", "kill_zone"),
    "selected_side": ("selected_side", "side", "direction", "candidate_side"),
    "source_component": ("source_component", "component", "source_component_name"),
}
AI_NARROWING_RUNTIME_CONFIG_DEFAULTS = {
    "enabled": False,
    "mode": "shadow",
    "allow_ai_call_skip": False,
    "owner_approval_confirmed": False,
    "production_change_review_approved": False,
    "runtime_halt_removed": False,
    "capacity_blocklist_active": False,
}
AI_NARROWING_RUNTIME_FAILURE_STATUS = {
    "CONFIG_DISABLED": "AI_NARROWING_RUNTIME_KEEP_AI_CONFIG_DISABLED",
    "CONFIG_MODE_NOT_ACTIVE": "AI_NARROWING_RUNTIME_KEEP_AI_CONFIG_MODE_NOT_ACTIVE",
    "AI_CALL_SKIP_FLAG_DISABLED": "AI_NARROWING_RUNTIME_KEEP_AI_SKIP_FLAG_DISABLED",
    "POLICY_NOT_REVIEW_READY": "AI_NARROWING_RUNTIME_KEEP_AI_POLICY_NOT_REVIEW_READY",
    "PRODUCTION_CHANGE_REVIEW_NOT_APPROVED": (
        "AI_NARROWING_RUNTIME_KEEP_AI_PRODUCTION_CHANGE_REVIEW_REQUIRED"
    ),
    "OWNER_APPROVAL_NOT_CONFIRMED": "AI_NARROWING_RUNTIME_KEEP_AI_OWNER_APPROVAL_REQUIRED",
    "RUNTIME_HALT_ACTIVE": "AI_NARROWING_RUNTIME_KEEP_AI_RUNTIME_HALT_ACTIVE",
    "RUNTIME_HALT_REMOVAL_NOT_CONFIRMED": (
        "AI_NARROWING_RUNTIME_KEEP_AI_RUNTIME_HALT_REMOVAL_NOT_CONFIRMED"
    ),
    "CAPACITY_BLOCKLIST_NOT_ACTIVE": "AI_NARROWING_RUNTIME_KEEP_AI_CAPACITY_BLOCKLIST_REQUIRED",
}


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "main_side_research_compiler",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def safe_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def stable_hash(payload: dict[str, Any], length: int = 64) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:length]


def first_present(row: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in row and normalized(row.get(key)) != "":
            return row.get(key)
    return None


def execution_action_class(surface_decision: str | None) -> str:
    text = normalized(surface_decision)
    if text == "IMPLEMENT_EXPANDED_MARKET_PRESERVED_REDUCED_SURFACE":
        return "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_PRESERVED_REDUCED_SURFACE_CANDIDATE"
    if text == "IMPLEMENT_EXPANDED_MARKET_REDUCED_SURFACE":
        return "REGISTER_DEFAULT_OFF_BRANCH_LOCAL_LEAKAGE_REDUCED_SURFACE_CANDIDATE"
    return "PRESERVE_FOR_REDUCED_SURFACE_REDESIGN_OR_SCOPE_REPAIR"


def execution_integrity_status(execution_row: dict[str, Any]) -> str:
    if normalized(execution_row.get("execution_status")) != "REDUCED_SURFACE_EXECUTION_PASS":
        return "REDUCED_SURFACE_EXECUTION_REPAIR_REQUIRED"
    if int(execution_row.get("matched_nonimplement_rows") or 0) != 0:
        return "REDUCED_SURFACE_EXECUTION_REPAIR_REQUIRED"
    if int(execution_row.get("matched_implement_rows") or 0) <= 0:
        return "REDUCED_SURFACE_EXECUTION_REPAIR_REQUIRED"
    precision = safe_float(execution_row.get("selection_precision"))
    if precision is None or precision + 1e-12 < 1.0:
        return "REDUCED_SURFACE_EXECUTION_REPAIR_REQUIRED"
    return "REDUCED_SURFACE_EXECUTION_VERIFIED_PASS"


def surface_scope(surface_row: dict[str, Any]) -> dict[str, Any]:
    scope = surface_row.get("surface_scope")
    if isinstance(scope, dict) and scope:
        return dict(scope)
    rebuilt = {key: normalized(surface_row.get(key)) for key in BASE_SCOPE_KEYS}
    if surface_row.get("source_path") is not None:
        rebuilt["source_path"] = normalized(surface_row.get("source_path"))
    if surface_row.get("source_file_sha256") is not None:
        rebuilt["source_file_sha256"] = normalized(surface_row.get("source_file_sha256"))
    return rebuilt


def event_matches_surface_scope(event: dict[str, Any], scope: dict[str, Any]) -> bool:
    for key in BASE_SCOPE_KEYS:
        if normalized(event.get(key)) != normalized(scope.get(key)):
            return False
    if normalized(scope.get("source_path")) and normalized(event.get("source_path")) != normalized(scope.get("source_path")):
        return False
    if normalized(scope.get("source_file_sha256")) and normalized(event.get("source_file_sha256")) != normalized(
        scope.get("source_file_sha256")
    ):
        return False
    for field, threshold in (scope.get("numeric_thresholds") or {}).items():
        value = safe_float(event.get(field))
        if value is None or value + 1e-12 < float(threshold):
            return False
    return True


def scope_key_from_scope(scope: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalized(scope.get(key)) for key in BASE_SCOPE_KEYS)


def scope_key_from_event(event: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalized(event.get(key)) for key in BASE_SCOPE_KEYS)


def required_event_fields_for_candidate(candidate: dict[str, Any]) -> list[str]:
    scope = candidate.get("surface_scope") or {}
    source_fields = [field for field in SOURCE_IDENTITY_KEYS if normalized(scope.get(field))]
    numeric_fields = sorted((scope.get("numeric_thresholds") or {}).keys())
    return [*BASE_SCOPE_KEYS, *source_fields, *numeric_fields]


def event_from_candidate_scope(candidate: dict[str, Any]) -> dict[str, Any]:
    """Build a threshold-satisfying synthetic event from a candidate scope."""
    scope = candidate.get("surface_scope") or {}
    event = {key: scope.get(key) for key in BASE_SCOPE_KEYS}
    if scope.get("source_path") is not None:
        event["source_path"] = scope.get("source_path")
    if scope.get("source_file_sha256") is not None:
        event["source_file_sha256"] = scope.get("source_file_sha256")
    for field, threshold in (scope.get("numeric_thresholds") or {}).items():
        event[field] = threshold
    return event


def reduced_surface_event_from_source_row(
    source_row: dict[str, Any],
    *,
    event_row_id: str | None = None,
    source_kind: str = "moonshot_reduced_surface_source_row",
    source_artifact: str | None = None,
    source_line_no: int | None = None,
    source_sha256: str | None = None,
    required_event_fields: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Normalize a source row into the event contract consumed by the registry."""
    required_fields = list(dict.fromkeys(required_event_fields or DEFAULT_EVENT_REQUIRED_FIELDS))
    all_fields = list(dict.fromkeys([*BASE_SCOPE_KEYS, *SOURCE_IDENTITY_KEYS, *NUMERIC_THRESHOLD_FIELDS, *required_fields]))
    event: dict[str, Any] = {}
    missing_required_fields: list[str] = []
    invalid_numeric_fields: list[str] = []

    for field in all_fields:
        aliases = EVENT_FIELD_ALIASES.get(field, (field,))
        raw_value = first_present(source_row, aliases)
        if field in NUMERIC_THRESHOLD_FIELDS:
            numeric_value = safe_float(raw_value)
            event[field] = numeric_value
            if field in required_fields and numeric_value is None:
                missing_required_fields.append(field)
                if raw_value is not None:
                    invalid_numeric_fields.append(field)
        else:
            value = normalized(raw_value)
            event[field] = value
            if field in required_fields and not value:
                missing_required_fields.append(field)

    status = (
        "REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE"
        if not missing_required_fields and not invalid_numeric_fields
        else "REDUCED_SURFACE_EVENT_CONTRACT_INCOMPLETE"
    )
    event.update(
        {
            "event_row_id": event_row_id,
            "event_source_kind": source_kind,
            "event_source_artifact": source_artifact,
            "event_source_line_no": source_line_no,
            "event_source_sha256": source_sha256,
            "required_event_fields": required_fields,
            "required_event_field_count": len(required_fields),
            "missing_required_fields": missing_required_fields,
            "invalid_numeric_fields": invalid_numeric_fields,
            "event_adapter_status": status,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": research_boundary(),
        }
    )
    return event


def source_capture_contract_for_candidate(
    candidate: dict[str, Any],
    *,
    contract_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    scope = candidate.get("surface_scope") or {}
    numeric_fields = sorted((scope.get("numeric_thresholds") or {}).keys())
    source_fields = [
        field
        for field in ("source_path", "source_file_sha256")
        if normalized(scope.get(field))
    ]
    required_fields = [*BASE_SCOPE_KEYS, *source_fields, *numeric_fields]
    return {
        "contract_row_id": contract_row_id,
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "candidate_row_id": candidate.get("candidate_row_id"),
        "surface_scope_sha256": candidate.get("surface_scope_sha256"),
        "main_compiler_action": candidate.get("main_compiler_action"),
        "branch_local_candidate_status": candidate.get("branch_local_candidate_status"),
        "symbol": candidate.get("symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "market_timeframe": candidate.get("market_timeframe"),
        "route_session": candidate.get("route_session"),
        "horizon_id": candidate.get("horizon_id"),
        "source_component": candidate.get("source_component"),
        "selected_side": candidate.get("selected_side"),
        "required_base_scope_fields": list(BASE_SCOPE_KEYS),
        "required_source_identity_fields": source_fields,
        "required_numeric_threshold_fields": numeric_fields,
        "required_event_fields": required_fields,
        "required_event_field_count": len(required_fields),
        "event_evaluation_surface": "ReducedSurfaceCandidateRegistry.evaluate_event",
        "source_capture_contract_status": "READY_DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_CONTRACT",
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def compact_reduced_surface_execution_row(
    execution_row: dict[str, Any],
    surface_row: dict[str, Any],
    *,
    candidate_row_id: str,
    execution_source_artifact: str,
    execution_source_line_no: int,
    execution_source_sha256: str,
    surface_source_artifact: str,
    surface_source_line_no: int,
    surface_source_sha256: str,
) -> dict[str, Any]:
    scope = surface_scope(surface_row)
    surface_decision = normalized(surface_row.get("keep_kill_redesign_implement_decision"))
    average_r = safe_float(execution_row.get("average_selected_intrabar_cost_adjusted_simulated_r"))
    selected_target_r = safe_float(surface_row.get("target_selected_intrabar_cost_adjusted_simulated_r"))
    selected_minus_rejected = safe_float(surface_row.get("target_selected_minus_rejected_intrabar_cost_adjusted_r"))
    integrity = execution_integrity_status(execution_row)
    action = execution_action_class(surface_decision)
    output = {
        "candidate_row_id": candidate_row_id,
        "execution_source_artifact": execution_source_artifact,
        "execution_source_line_no": execution_source_line_no,
        "execution_source_sha256": execution_source_sha256,
        "surface_source_artifact": surface_source_artifact,
        "surface_source_line_no": surface_source_line_no,
        "surface_source_sha256": surface_source_sha256,
        "source_reduced_surface_execution_row_id": execution_row.get("reduced_surface_execution_row_id"),
        "source_reduced_surface_row_id": surface_row.get("reduced_surface_row_id"),
        "source_leakage_reduction_row_id": execution_row.get("input_leakage_reduction_row_id"),
        "input_code_candidate_execution_row_id": surface_row.get("input_code_candidate_execution_row_id"),
        "input_code_candidate_row_id": surface_row.get("input_code_candidate_row_id"),
        "input_implementation_selection_row_id": surface_row.get("input_implementation_selection_row_id"),
        "candidate_function_name": surface_row.get("candidate_function_name"),
        "surface_function_name": execution_row.get("surface_function_name") or surface_row.get("surface_function_name"),
        "symbol": execution_row.get("symbol"),
        "source_symbol": execution_row.get("source_symbol"),
        "market_timeframe": execution_row.get("market_timeframe"),
        "route_session": execution_row.get("route_session"),
        "horizon_id": execution_row.get("horizon_id"),
        "source_component": execution_row.get("source_component"),
        "selected_side": execution_row.get("selected_side"),
        "source_path": execution_row.get("source_path"),
        "source_file_sha256": execution_row.get("source_file_sha256"),
        "surface_scope": scope,
        "surface_scope_sha256": execution_row.get("surface_scope_sha256") or surface_row.get("surface_scope_sha256")
        or stable_hash(scope),
        "branch_local_code_expression": surface_row.get("branch_local_code_expression"),
        "expected_matched_selection_rows": int(execution_row.get("expected_matched_selection_rows") or 0),
        "matched_selection_rows": int(execution_row.get("matched_selection_rows") or 0),
        "matched_implement_rows": int(execution_row.get("matched_implement_rows") or 0),
        "matched_nonimplement_rows": int(execution_row.get("matched_nonimplement_rows") or 0),
        "matched_avoid_rows": int(execution_row.get("matched_avoid_rows") or 0),
        "matched_kill_rows": int(execution_row.get("matched_kill_rows") or 0),
        "matched_redesign_rows": int(execution_row.get("matched_redesign_rows") or 0),
        "selection_precision": safe_float(execution_row.get("selection_precision")),
        "average_selected_intrabar_cost_adjusted_simulated_r": average_r,
        "target_selected_intrabar_cost_adjusted_simulated_r": selected_target_r,
        "target_rejected_intrabar_cost_adjusted_simulated_r": safe_float(
            surface_row.get("target_rejected_intrabar_cost_adjusted_simulated_r")
        ),
        "target_selected_minus_rejected_intrabar_cost_adjusted_r": selected_minus_rejected,
        "target_temporal_winner_consistency_share": safe_float(surface_row.get("target_temporal_winner_consistency_share")),
        "target_temporal_positive_winner_fold_share": safe_float(
            surface_row.get("target_temporal_positive_winner_fold_share")
        ),
        "target_effective_n": safe_float(surface_row.get("target_effective_n")),
        "target_selected_intrabar_target_first_count": int(surface_row.get("target_selected_intrabar_target_first_count") or 0),
        "target_selected_intrabar_stop_first_count": int(surface_row.get("target_selected_intrabar_stop_first_count") or 0),
        "target_selected_intrabar_neither_count": int(surface_row.get("target_selected_intrabar_neither_count") or 0),
        "target_selected_intrabar_ambiguous_count": int(surface_row.get("target_selected_intrabar_ambiguous_count") or 0),
        "source_surface_decision": surface_decision,
        "source_execution_decision": execution_row.get("keep_kill_redesign_implement_decision"),
        "source_execution_status": execution_row.get("execution_status"),
        "source_follow_inverse_default_off_avoid_class": execution_row.get("follow_inverse_default_off_avoid_class"),
        "main_compiler_action": action,
        "main_compiler_action_class": "IMPLEMENT_DEFAULT_OFF",
        "execution_integrity_status": integrity,
        "branch_local_candidate_status": "READY_DEFAULT_OFF_BRANCH_LOCAL_CANDIDATE"
        if integrity.endswith("PASS")
        else "REPAIR_REQUIRED",
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "replay_r_reference_field": "average_selected_intrabar_cost_adjusted_simulated_r",
        "research_boundary": research_boundary(),
        "expanded_market_reduced_surface_execution_surface": SURFACE,
    }
    return output


def summarize_reduced_surface_candidates(rows: list[dict[str, Any]]) -> dict[str, Any]:
    average_values = [
        value
        for row in rows
        if (value := safe_float(row.get("average_selected_intrabar_cost_adjusted_simulated_r"))) is not None
    ]
    target_values = [
        value
        for row in rows
        if (value := safe_float(row.get("target_selected_intrabar_cost_adjusted_simulated_r"))) is not None
    ]
    return {
        "rows": len(rows),
        "main_compiler_action_counts": dict(
            sorted(Counter(normalized(row.get("main_compiler_action")) for row in rows).items())
        ),
        "source_surface_decision_counts": dict(
            sorted(Counter(normalized(row.get("source_surface_decision")) for row in rows).items())
        ),
        "execution_integrity_status_counts": dict(
            sorted(Counter(normalized(row.get("execution_integrity_status")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(normalized(row.get("route_session")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "selected_side_counts": dict(sorted(Counter(normalized(row.get("selected_side")) for row in rows).items())),
        "matched_selection_rows": sum(int(row.get("matched_selection_rows") or 0) for row in rows),
        "matched_implement_rows": sum(int(row.get("matched_implement_rows") or 0) for row in rows),
        "matched_nonimplement_rows": sum(int(row.get("matched_nonimplement_rows") or 0) for row in rows),
        "average_selected_intrabar_cost_adjusted_simulated_r_rows": len(average_values),
        "average_selected_intrabar_cost_adjusted_simulated_r_sum_reference": rounded(sum(average_values)),
        "average_selected_intrabar_cost_adjusted_simulated_r_mean_reference": rounded(
            sum(average_values) / len(average_values) if average_values else None
        ),
        "target_selected_intrabar_cost_adjusted_simulated_r_rows": len(target_values),
        "target_selected_intrabar_cost_adjusted_simulated_r_sum_reference": rounded(sum(target_values)),
        "target_selected_intrabar_cost_adjusted_simulated_r_mean_reference": rounded(
            sum(target_values) / len(target_values) if target_values else None
        ),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def summarize_source_capture_contracts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_field_counts = Counter()
    required_field_counts = Counter()
    for row in rows:
        for field in row.get("required_numeric_threshold_fields") or []:
            numeric_field_counts[str(field)] += 1
        for field in row.get("required_event_fields") or []:
            required_field_counts[str(field)] += 1
    return {
        "rows": len(rows),
        "contract_status_counts": dict(
            sorted(Counter(normalized(row.get("source_capture_contract_status")) for row in rows).items())
        ),
        "main_compiler_action_counts": dict(
            sorted(Counter(normalized(row.get("main_compiler_action")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "required_numeric_threshold_field_counts": dict(sorted(numeric_field_counts.items())),
        "required_event_field_counts": dict(sorted(required_field_counts.items())),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def summarize_reduced_surface_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_field_counts = Counter()
    invalid_numeric_counts = Counter()
    for row in rows:
        for field in row.get("missing_required_fields") or []:
            missing_field_counts[str(field)] += 1
        for field in row.get("invalid_numeric_fields") or []:
            invalid_numeric_counts[str(field)] += 1
    return {
        "rows": len(rows),
        "event_adapter_status_counts": dict(
            sorted(Counter(normalized(row.get("event_adapter_status")) for row in rows).items())
        ),
        "event_source_kind_counts": dict(
            sorted(Counter(normalized(row.get("event_source_kind")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "missing_required_field_counts": dict(sorted(missing_field_counts.items())),
        "invalid_numeric_field_counts": dict(sorted(invalid_numeric_counts.items())),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def reduced_surface_event_score(
    event: dict[str, Any],
    registry: "ReducedSurfaceCandidateRegistry",
    *,
    event_score_row_id: str | None = None,
) -> dict[str, Any]:
    adapter_status = normalized(event.get("event_adapter_status"))
    if adapter_status == "REDUCED_SURFACE_EVENT_CONTRACT_INCOMPLETE":
        matches: list[dict[str, Any]] = []
        score_status = "DEFAULT_OFF_REDUCED_SURFACE_EVENT_NOT_SCORED_CONTRACT_INCOMPLETE"
    else:
        matches = registry.evaluate_event(event)
        score_status = (
            "DEFAULT_OFF_REDUCED_SURFACE_EVENT_SCORED_MATCH"
            if matches
            else "DEFAULT_OFF_REDUCED_SURFACE_EVENT_SCORED_NO_MATCH"
        )
    matched_ids = [str(row.get("candidate_row_id") or "") for row in matches]
    return {
        "event_score_row_id": event_score_row_id,
        "event_row_id": event.get("event_row_id"),
        "event_adapter_status": adapter_status,
        "event_score_status": score_status,
        "registry_matched_candidate_rows": len(matches),
        "registry_matched_candidate_row_ids": matched_ids,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def reduced_surface_candidate_event_rollups(
    candidates: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    registry = ReducedSurfaceCandidateRegistry(candidates)
    match_counts: Counter[str] = Counter()
    expected_counts: Counter[str] = Counter()
    for index, event in enumerate(events, start=1):
        score = reduced_surface_event_score(event, registry, event_score_row_id=f"EVENT-SCORE-{index:08d}")
        for candidate_id in score["registry_matched_candidate_row_ids"]:
            match_counts[candidate_id] += 1
        expected_candidate_id = normalized(event.get("expected_candidate_row_id"))
        if expected_candidate_id and event.get("expected_candidate_found") is not False:
            expected_counts[expected_candidate_id] += 1

    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = normalized(candidate.get("candidate_row_id"))
        event_matches = int(match_counts.get(candidate_id, 0))
        expected_events = int(expected_counts.get(candidate_id, 0))
        rows.append(
            {
                "candidate_row_id": candidate_id,
                "surface_scope_sha256": candidate.get("surface_scope_sha256"),
                "main_compiler_action": candidate.get("main_compiler_action"),
                "branch_local_candidate_status": candidate.get("branch_local_candidate_status"),
                "symbol": candidate.get("symbol"),
                "source_symbol": candidate.get("source_symbol"),
                "market_timeframe": candidate.get("market_timeframe"),
                "route_session": candidate.get("route_session"),
                "horizon_id": candidate.get("horizon_id"),
                "source_component": candidate.get("source_component"),
                "selected_side": candidate.get("selected_side"),
                "event_registry_match_rows": event_matches,
                "expected_candidate_event_rows": expected_events,
                "duplicate_scope_event_match_rows": max(0, event_matches - expected_events),
                "average_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                    "average_selected_intrabar_cost_adjusted_simulated_r"
                ),
                "target_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                    "target_selected_intrabar_cost_adjusted_simulated_r"
                ),
                "candidate_event_rollup_status": "DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_HAS_EVENT_MATCHES"
                if event_matches > 0
                else "DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_NO_EVENT_MATCHES_REPAIR_REQUIRED",
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def summarize_reduced_surface_candidate_event_rollups(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "candidate_event_rollup_status_counts": dict(
            sorted(Counter(normalized(row.get("candidate_event_rollup_status")) for row in rows).items())
        ),
        "main_compiler_action_counts": dict(
            sorted(Counter(normalized(row.get("main_compiler_action")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "event_registry_match_rows": sum(int(row.get("event_registry_match_rows") or 0) for row in rows),
        "expected_candidate_event_rows": sum(int(row.get("expected_candidate_event_rows") or 0) for row in rows),
        "duplicate_scope_event_match_rows": sum(int(row.get("duplicate_scope_event_match_rows") or 0) for row in rows),
        "candidates_with_event_matches": sum(int(row.get("event_registry_match_rows") or 0) > 0 for row in rows),
        "candidates_without_event_matches": sum(int(row.get("event_registry_match_rows") or 0) == 0 for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def final_review_source_capture_priority_status(
    *,
    implementation_ready_candidate_rows: int,
    capacity_blocked_candidate_rows: int,
    event_registry_match_rows: int,
    has_final_review_overlay: bool,
) -> str:
    if event_registry_match_rows <= 0:
        return "DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_PRIORITY_REPAIR_REQUIRED"
    if not has_final_review_overlay:
        return "DEFAULT_OFF_REDUCED_SURFACE_SOURCE_CAPTURE_PRIORITY_READY"
    if implementation_ready_candidate_rows > 0 and capacity_blocked_candidate_rows == 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY"
    if implementation_ready_candidate_rows > 0 and capacity_blocked_candidate_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY_WITH_REDESIGN_SUBSET"
    if capacity_blocked_candidate_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_REDESIGN_ONLY"
    return "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_BINDING_REPAIR_REQUIRED"


def final_review_source_capture_class(
    *,
    implementation_ready_candidate_rows: int,
    capacity_blocked_candidate_rows: int,
    has_final_review_overlay: bool,
) -> str:
    if not has_final_review_overlay:
        return "NOT_FINAL_REVIEW_ADJUSTED_SOURCE_CAPTURE"
    if implementation_ready_candidate_rows > 0 and capacity_blocked_candidate_rows == 0:
        return "FINAL_REVIEW_IMPLEMENT_READY_CAPTURE"
    if implementation_ready_candidate_rows > 0 and capacity_blocked_candidate_rows > 0:
        return "FINAL_REVIEW_IMPLEMENT_READY_WITH_CAPACITY_REDESIGN_SUBSET_CAPTURE"
    if capacity_blocked_candidate_rows > 0:
        return "FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN_ONLY_CAPTURE"
    return "FINAL_REVIEW_BINDING_REPAIR_REQUIRED_CAPTURE"


def reduced_surface_source_capture_priority_groups(
    rollups: list[dict[str, Any]],
    contracts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    contract_by_candidate = {normalized(row.get("candidate_row_id")): row for row in contracts}
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for rollup in rollups:
        key = scope_key_from_event(rollup)
        group = groups.setdefault(
            key,
            {
                **{field: rollup.get(field) for field in BASE_SCOPE_KEYS},
                "candidate_row_ids": [],
                "candidate_rows": 0,
                "event_registry_match_rows": 0,
                "expected_candidate_event_rows": 0,
                "duplicate_scope_event_match_rows": 0,
                "required_event_fields": set(),
                "required_source_identity_fields": set(),
                "required_numeric_threshold_fields": set(),
                "average_selected_intrabar_cost_adjusted_simulated_r_values": [],
                "main_compiler_actions": Counter(),
                "main_compiler_final_review_actions": Counter(),
                "final_review_adjusted_rollup_statuses": Counter(),
                "implementation_ready_candidate_row_ids": [],
                "capacity_blocked_candidate_row_ids": [],
                "final_review_overlay_bound_rows": 0,
            },
        )
        candidate_id = normalized(rollup.get("candidate_row_id"))
        contract = contract_by_candidate.get(candidate_id, {})
        group["candidate_row_ids"].append(candidate_id)
        group["candidate_rows"] += 1
        group["event_registry_match_rows"] += int(rollup.get("event_registry_match_rows") or 0)
        group["expected_candidate_event_rows"] += int(rollup.get("expected_candidate_event_rows") or 0)
        group["duplicate_scope_event_match_rows"] += int(rollup.get("duplicate_scope_event_match_rows") or 0)
        group["required_event_fields"].update(str(field) for field in contract.get("required_event_fields") or BASE_SCOPE_KEYS)
        group["required_source_identity_fields"].update(
            str(field) for field in contract.get("required_source_identity_fields") or []
        )
        group["required_numeric_threshold_fields"].update(
            str(field) for field in contract.get("required_numeric_threshold_fields") or []
        )
        value = safe_float(rollup.get("average_selected_intrabar_cost_adjusted_simulated_r"))
        if value is not None:
            group["average_selected_intrabar_cost_adjusted_simulated_r_values"].append(value)
        group["main_compiler_actions"][normalized(rollup.get("main_compiler_action"))] += 1
        final_review_action = normalized(rollup.get("main_compiler_final_review_action"))
        if final_review_action:
            group["main_compiler_final_review_actions"][final_review_action] += 1
        final_review_status = normalized(rollup.get("final_review_adjusted_rollup_status"))
        if final_review_status:
            group["final_review_adjusted_rollup_statuses"][final_review_status] += 1
        if rollup.get("final_review_overlay_bound") is True:
            group["final_review_overlay_bound_rows"] += 1
        if final_review_status == FINAL_REVIEW_IMPLEMENT_READY_STATUS:
            group["implementation_ready_candidate_row_ids"].append(candidate_id)
        elif final_review_status == FINAL_REVIEW_CAPACITY_BLOCKED_STATUS:
            group["capacity_blocked_candidate_row_ids"].append(candidate_id)

    rows: list[dict[str, Any]] = []
    for group in groups.values():
        values = group.pop("average_selected_intrabar_cost_adjusted_simulated_r_values")
        required_source_fields = sorted(group.pop("required_source_identity_fields"))
        required_numeric_fields = sorted(group.pop("required_numeric_threshold_fields"))
        required_event_fields = sorted(group.pop("required_event_fields"))
        actions = group.pop("main_compiler_actions")
        final_review_actions = group.pop("main_compiler_final_review_actions")
        final_review_statuses = group.pop("final_review_adjusted_rollup_statuses")
        implementation_ready_candidate_row_ids = sorted(group.pop("implementation_ready_candidate_row_ids"))
        capacity_blocked_candidate_row_ids = sorted(group.pop("capacity_blocked_candidate_row_ids"))
        final_review_overlay_bound_rows = int(group.pop("final_review_overlay_bound_rows") or 0)
        implementation_ready_candidate_rows = len(implementation_ready_candidate_row_ids)
        capacity_blocked_candidate_rows = len(capacity_blocked_candidate_row_ids)
        has_final_review_overlay = bool(final_review_statuses)
        source_capture_class = (
            "LEAKAGE_REDUCED_SOURCE_IDENTITY_AND_NUMERIC_CAPTURE"
            if required_source_fields or required_numeric_fields
            else "PRESERVED_BASE_SCOPE_CAPTURE"
        )
        priority_status = final_review_source_capture_priority_status(
            implementation_ready_candidate_rows=implementation_ready_candidate_rows,
            capacity_blocked_candidate_rows=capacity_blocked_candidate_rows,
            event_registry_match_rows=int(group["event_registry_match_rows"]),
            has_final_review_overlay=has_final_review_overlay,
        )
        rows.append(
            {
                **group,
                "candidate_row_ids": sorted(group["candidate_row_ids"]),
                "implementation_ready_candidate_row_ids": implementation_ready_candidate_row_ids,
                "capacity_blocked_candidate_row_ids": capacity_blocked_candidate_row_ids,
                "required_event_fields": required_event_fields,
                "required_event_field_count": len(required_event_fields),
                "required_source_identity_fields": required_source_fields,
                "required_numeric_threshold_fields": required_numeric_fields,
                "main_compiler_action_counts": dict(sorted(actions.items())),
                "main_compiler_final_review_action_counts": dict(sorted(final_review_actions.items())),
                "final_review_adjusted_rollup_status_counts": dict(sorted(final_review_statuses.items())),
                "final_review_overlay_bound_rows": final_review_overlay_bound_rows,
                "implementation_ready_candidate_rows": implementation_ready_candidate_rows,
                "capacity_blocked_candidate_rows": capacity_blocked_candidate_rows,
                "average_selected_intrabar_cost_adjusted_simulated_r_rows": len(values),
                "average_selected_intrabar_cost_adjusted_simulated_r_sum_reference": rounded(sum(values)),
                "average_selected_intrabar_cost_adjusted_simulated_r_mean_reference": rounded(
                    sum(values) / len(values) if values else None
                ),
                "source_capture_priority_class": source_capture_class,
                "final_review_source_capture_class": final_review_source_capture_class(
                    implementation_ready_candidate_rows=implementation_ready_candidate_rows,
                    capacity_blocked_candidate_rows=capacity_blocked_candidate_rows,
                    has_final_review_overlay=has_final_review_overlay,
                ),
                "source_capture_priority_status": priority_status,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": research_boundary(),
            }
        )

    rows.sort(
        key=lambda row: (
            -int(row["event_registry_match_rows"]),
            -int(row["expected_candidate_event_rows"]),
            normalized(row.get("source_component")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("selected_side")),
            normalized(row.get("horizon_id")),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["source_capture_priority_rank"] = index
    return rows


def summarize_reduced_surface_source_capture_priority_groups(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_field_counts = Counter()
    numeric_field_counts = Counter()
    source_identity_field_counts = Counter()
    final_review_status_counts = Counter()
    final_review_action_counts = Counter()
    for row in rows:
        for field in row.get("required_event_fields") or []:
            required_field_counts[str(field)] += 1
        for field in row.get("required_numeric_threshold_fields") or []:
            numeric_field_counts[str(field)] += 1
        for field in row.get("required_source_identity_fields") or []:
            source_identity_field_counts[str(field)] += 1
        final_review_status_counts.update(row.get("final_review_adjusted_rollup_status_counts") or {})
        final_review_action_counts.update(row.get("main_compiler_final_review_action_counts") or {})
    return {
        "rows": len(rows),
        "source_capture_priority_status_counts": dict(
            sorted(Counter(normalized(row.get("source_capture_priority_status")) for row in rows).items())
        ),
        "source_capture_priority_class_counts": dict(
            sorted(Counter(normalized(row.get("source_capture_priority_class")) for row in rows).items())
        ),
        "final_review_source_capture_class_counts": dict(
            sorted(Counter(normalized(row.get("final_review_source_capture_class")) for row in rows).items())
        ),
        "final_review_adjusted_rollup_status_counts": dict(sorted(final_review_status_counts.items())),
        "main_compiler_final_review_action_counts": dict(sorted(final_review_action_counts.items())),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
        "final_review_overlay_bound_rows": sum(int(row.get("final_review_overlay_bound_rows") or 0) for row in rows),
        "implementation_ready_candidate_rows": sum(
            int(row.get("implementation_ready_candidate_rows") or 0) for row in rows
        ),
        "capacity_blocked_candidate_rows": sum(int(row.get("capacity_blocked_candidate_rows") or 0) for row in rows),
        "event_registry_match_rows": sum(int(row.get("event_registry_match_rows") or 0) for row in rows),
        "expected_candidate_event_rows": sum(int(row.get("expected_candidate_event_rows") or 0) for row in rows),
        "duplicate_scope_event_match_rows": sum(int(row.get("duplicate_scope_event_match_rows") or 0) for row in rows),
        "required_event_field_counts": dict(sorted(required_field_counts.items())),
        "required_numeric_threshold_field_counts": dict(sorted(numeric_field_counts.items())),
        "required_source_identity_field_counts": dict(sorted(source_identity_field_counts.items())),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def event_emitter_contract_status_for_priority_group(priority_group: dict[str, Any]) -> str:
    priority_status = normalized(priority_group.get("source_capture_priority_status"))
    if priority_status == "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY":
        return "READY_DEFAULT_OFF_FINAL_REVIEW_EVENT_EMITTER_CONTRACT"
    if priority_status == "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_IMPLEMENT_READY_WITH_REDESIGN_SUBSET":
        return "READY_DEFAULT_OFF_FINAL_REVIEW_EVENT_EMITTER_CONTRACT_WITH_REDESIGN_SUBSET"
    if priority_status == "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_REDESIGN_ONLY":
        return "BLOCKED_DEFAULT_OFF_FINAL_REVIEW_REDESIGN_EVENT_EMITTER_CONTRACT"
    if priority_status == "DEFAULT_OFF_FINAL_REVIEW_SOURCE_CAPTURE_PRIORITY_BINDING_REPAIR_REQUIRED":
        return "BLOCKED_DEFAULT_OFF_FINAL_REVIEW_BINDING_REPAIR_EVENT_EMITTER_CONTRACT"
    return "READY_DEFAULT_OFF_REDUCED_SURFACE_EVENT_EMITTER_CONTRACT"


def reduced_surface_event_emitter_contract_for_priority_group(
    priority_group: dict[str, Any],
    *,
    contract_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    required_event_fields = list(priority_group.get("required_event_fields") or BASE_SCOPE_KEYS)
    required_source_fields = list(priority_group.get("required_source_identity_fields") or [])
    required_numeric_fields = list(priority_group.get("required_numeric_threshold_fields") or [])
    return {
        "emitter_contract_row_id": contract_row_id,
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "source_capture_priority_rank": priority_group.get("source_capture_priority_rank"),
        "source_capture_priority_class": priority_group.get("source_capture_priority_class"),
        "final_review_source_capture_class": priority_group.get("final_review_source_capture_class"),
        "source_capture_priority_status": priority_group.get("source_capture_priority_status"),
        "candidate_rows": priority_group.get("candidate_rows"),
        "final_review_overlay_bound_rows": priority_group.get("final_review_overlay_bound_rows"),
        "implementation_ready_candidate_rows": priority_group.get("implementation_ready_candidate_rows"),
        "capacity_blocked_candidate_rows": priority_group.get("capacity_blocked_candidate_rows"),
        "implementation_ready_candidate_row_ids": priority_group.get("implementation_ready_candidate_row_ids") or [],
        "capacity_blocked_candidate_row_ids": priority_group.get("capacity_blocked_candidate_row_ids") or [],
        "final_review_adjusted_rollup_status_counts": priority_group.get(
            "final_review_adjusted_rollup_status_counts"
        )
        or {},
        "main_compiler_final_review_action_counts": priority_group.get("main_compiler_final_review_action_counts") or {},
        "event_registry_match_rows": priority_group.get("event_registry_match_rows"),
        "expected_candidate_event_rows": priority_group.get("expected_candidate_event_rows"),
        "duplicate_scope_event_match_rows": priority_group.get("duplicate_scope_event_match_rows"),
        "symbol": priority_group.get("symbol"),
        "source_symbol": priority_group.get("source_symbol"),
        "market_timeframe": priority_group.get("market_timeframe"),
        "route_session": priority_group.get("route_session"),
        "horizon_id": priority_group.get("horizon_id"),
        "source_component": priority_group.get("source_component"),
        "selected_side": priority_group.get("selected_side"),
        "required_base_scope_fields": list(BASE_SCOPE_KEYS),
        "required_event_fields": required_event_fields,
        "required_event_field_count": len(required_event_fields),
        "required_source_identity_fields": required_source_fields,
        "required_numeric_threshold_fields": required_numeric_fields,
        "event_adapter_surface": "reduced_surface_event_from_source_row",
        "event_emitter_surface": "emit_reduced_surface_event_for_priority_group",
        "event_score_surface": "reduced_surface_event_score",
        "source_hash_alias_policy": "DO_NOT_TREAT_GENERIC_SOURCE_HASH_AS_SOURCE_FILE_SHA256",
        "emitter_contract_status": event_emitter_contract_status_for_priority_group(priority_group),
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def emit_reduced_surface_event_for_priority_group(
    source_row: dict[str, Any],
    priority_group: dict[str, Any],
    *,
    event_row_id: str | None = None,
    source_kind: str = "future_reduced_surface_replay_or_shadow_row",
    source_artifact: str | None = None,
    source_line_no: int | None = None,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    event = reduced_surface_event_from_source_row(
        source_row,
        event_row_id=event_row_id,
        source_kind=source_kind,
        source_artifact=source_artifact,
        source_line_no=source_line_no,
        source_sha256=source_sha256,
        required_event_fields=list(priority_group.get("required_event_fields") or BASE_SCOPE_KEYS),
    )
    event.update(
        {
            "source_capture_priority_rank": priority_group.get("source_capture_priority_rank"),
            "source_capture_priority_class": priority_group.get("source_capture_priority_class"),
            "final_review_source_capture_class": priority_group.get("final_review_source_capture_class"),
            "source_capture_priority_status": priority_group.get("source_capture_priority_status"),
            "emitter_contract_status": "REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_BLOCKED_FINAL_REVIEW_REDESIGN"
            if event_emitter_contract_status_for_priority_group(priority_group).startswith("BLOCKED_")
            else (
                "REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_COMPLETE"
                if event.get("event_adapter_status") == "REDUCED_SURFACE_EVENT_CONTRACT_COMPLETE"
                else "REDUCED_SURFACE_EVENT_EMITTER_CONTRACT_INCOMPLETE"
            ),
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "replay_r_reference_counted_as_new_main_result": False,
        }
    )
    return event


def summarize_reduced_surface_event_emitter_contracts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_field_counts = Counter()
    numeric_field_counts = Counter()
    source_identity_field_counts = Counter()
    final_review_status_counts = Counter()
    final_review_action_counts = Counter()
    for row in rows:
        for field in row.get("required_event_fields") or []:
            required_field_counts[str(field)] += 1
        for field in row.get("required_numeric_threshold_fields") or []:
            numeric_field_counts[str(field)] += 1
        for field in row.get("required_source_identity_fields") or []:
            source_identity_field_counts[str(field)] += 1
        final_review_status_counts.update(row.get("final_review_adjusted_rollup_status_counts") or {})
        final_review_action_counts.update(row.get("main_compiler_final_review_action_counts") or {})
    return {
        "rows": len(rows),
        "emitter_contract_status_counts": dict(
            sorted(Counter(normalized(row.get("emitter_contract_status")) for row in rows).items())
        ),
        "source_capture_priority_class_counts": dict(
            sorted(Counter(normalized(row.get("source_capture_priority_class")) for row in rows).items())
        ),
        "final_review_source_capture_class_counts": dict(
            sorted(Counter(normalized(row.get("final_review_source_capture_class")) for row in rows).items())
        ),
        "final_review_adjusted_rollup_status_counts": dict(sorted(final_review_status_counts.items())),
        "main_compiler_final_review_action_counts": dict(sorted(final_review_action_counts.items())),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "candidate_rows": sum(int(row.get("candidate_rows") or 0) for row in rows),
        "final_review_overlay_bound_rows": sum(int(row.get("final_review_overlay_bound_rows") or 0) for row in rows),
        "implementation_ready_candidate_rows": sum(
            int(row.get("implementation_ready_candidate_rows") or 0) for row in rows
        ),
        "capacity_blocked_candidate_rows": sum(int(row.get("capacity_blocked_candidate_rows") or 0) for row in rows),
        "event_registry_match_rows": sum(int(row.get("event_registry_match_rows") or 0) for row in rows),
        "expected_candidate_event_rows": sum(int(row.get("expected_candidate_event_rows") or 0) for row in rows),
        "duplicate_scope_event_match_rows": sum(int(row.get("duplicate_scope_event_match_rows") or 0) for row in rows),
        "required_event_field_counts": dict(sorted(required_field_counts.items())),
        "required_numeric_threshold_field_counts": dict(sorted(numeric_field_counts.items())),
        "required_source_identity_field_counts": dict(sorted(source_identity_field_counts.items())),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def final_review_registry_score_status(
    *,
    implementation_ready_registry_match_rows: int,
    capacity_blocked_registry_match_rows: int,
    binding_repair_registry_match_rows: int,
) -> str:
    if implementation_ready_registry_match_rows > 0 and capacity_blocked_registry_match_rows == 0:
        return "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_MATCHES_ONLY"
    if implementation_ready_registry_match_rows > 0 and capacity_blocked_registry_match_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_IMPLEMENT_READY_WITH_REDESIGN_MATCHES"
    if implementation_ready_registry_match_rows == 0 and capacity_blocked_registry_match_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_REDESIGN_BLOCKED_MATCHES_ONLY"
    if binding_repair_registry_match_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_BINDING_REPAIR_REQUIRED"
    return "DEFAULT_OFF_FINAL_REVIEW_REGISTRY_SCORE_NO_MATCH_REPAIR_REQUIRED"


def final_review_adjusted_event_registry_scores(
    events: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    adjusted_rollups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    registry = ReducedSurfaceCandidateRegistry(candidates)
    overlay_by_candidate = {normalized(row.get("candidate_row_id")): row for row in adjusted_rollups}
    rows: list[dict[str, Any]] = []
    for event in events:
        matches = registry.evaluate_event(event)
        implementation_ready_ids: list[str] = []
        capacity_blocked_ids: list[str] = []
        binding_repair_ids: list[str] = []
        match_action_counts: Counter[str] = Counter()
        match_status_counts: Counter[str] = Counter()
        for match in matches:
            candidate_id = normalized(match.get("candidate_row_id"))
            overlay = overlay_by_candidate.get(candidate_id, {})
            final_review_status = normalized(overlay.get("final_review_adjusted_rollup_status"))
            final_review_action = normalized(overlay.get("main_compiler_final_review_action"))
            if final_review_status:
                match_status_counts[final_review_status] += 1
            if final_review_action:
                match_action_counts[final_review_action] += 1
            if final_review_status == FINAL_REVIEW_IMPLEMENT_READY_STATUS:
                implementation_ready_ids.append(candidate_id)
            elif final_review_status == FINAL_REVIEW_CAPACITY_BLOCKED_STATUS:
                capacity_blocked_ids.append(candidate_id)
            else:
                binding_repair_ids.append(candidate_id)

        expected_candidate_id = normalized(event.get("expected_candidate_row_id"))
        expected_overlay = overlay_by_candidate.get(expected_candidate_id, {})
        expected_status = normalized(expected_overlay.get("final_review_adjusted_rollup_status"))
        expected_action = normalized(expected_overlay.get("main_compiler_final_review_action"))
        expected_found_in_registry = expected_candidate_id in {
            normalized(match.get("candidate_row_id")) for match in matches
        }
        implementation_ready_count = len(implementation_ready_ids)
        capacity_blocked_count = len(capacity_blocked_ids)
        binding_repair_count = len(binding_repair_ids)
        rows.append(
            {
                "event_row_id": event.get("event_row_id"),
                "event_source_kind": event.get("event_source_kind"),
                "source_artifact": event.get("source_artifact"),
                "source_line_no": event.get("source_line_no"),
                "source_sha256": event.get("source_sha256"),
                "expected_candidate_row_id": expected_candidate_id,
                "expected_candidate_found_in_registry": expected_found_in_registry,
                "expected_candidate_final_review_status": expected_status,
                "expected_candidate_final_review_action": expected_action,
                "expected_candidate_implementation_ready": expected_status == FINAL_REVIEW_IMPLEMENT_READY_STATUS,
                "expected_candidate_capacity_blocked": expected_status == FINAL_REVIEW_CAPACITY_BLOCKED_STATUS,
                "registry_match_rows": len(matches),
                "implementation_ready_registry_match_rows": implementation_ready_count,
                "capacity_blocked_registry_match_rows": capacity_blocked_count,
                "binding_repair_registry_match_rows": binding_repair_count,
                "implementation_ready_candidate_row_ids": sorted(implementation_ready_ids),
                "capacity_blocked_candidate_row_ids": sorted(capacity_blocked_ids),
                "binding_repair_candidate_row_ids": sorted(binding_repair_ids),
                "final_review_registry_match_status_counts": dict(sorted(match_status_counts.items())),
                "main_compiler_final_review_action_counts": dict(sorted(match_action_counts.items())),
                "final_review_registry_score_status": final_review_registry_score_status(
                    implementation_ready_registry_match_rows=implementation_ready_count,
                    capacity_blocked_registry_match_rows=capacity_blocked_count,
                    binding_repair_registry_match_rows=binding_repair_count,
                ),
                **{field: event.get(field) for field in BASE_SCOPE_KEYS},
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def summarize_final_review_adjusted_event_registry_scores(rows: list[dict[str, Any]]) -> dict[str, Any]:
    match_status_counts = Counter()
    match_action_counts = Counter()
    for row in rows:
        match_status_counts.update(row.get("final_review_registry_match_status_counts") or {})
        match_action_counts.update(row.get("main_compiler_final_review_action_counts") or {})
    return {
        "rows": len(rows),
        "final_review_registry_score_status_counts": dict(
            sorted(Counter(normalized(row.get("final_review_registry_score_status")) for row in rows).items())
        ),
        "final_review_registry_match_status_counts": dict(sorted(match_status_counts.items())),
        "main_compiler_final_review_action_counts": dict(sorted(match_action_counts.items())),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "registry_match_rows": sum(int(row.get("registry_match_rows") or 0) for row in rows),
        "implementation_ready_registry_match_rows": sum(
            int(row.get("implementation_ready_registry_match_rows") or 0) for row in rows
        ),
        "capacity_blocked_registry_match_rows": sum(
            int(row.get("capacity_blocked_registry_match_rows") or 0) for row in rows
        ),
        "binding_repair_registry_match_rows": sum(
            int(row.get("binding_repair_registry_match_rows") or 0) for row in rows
        ),
        "expected_candidate_found_in_registry_rows": sum(
            bool(row.get("expected_candidate_found_in_registry")) for row in rows
        ),
        "expected_candidate_implementation_ready_rows": sum(
            bool(row.get("expected_candidate_implementation_ready")) for row in rows
        ),
        "expected_candidate_capacity_blocked_rows": sum(bool(row.get("expected_candidate_capacity_blocked")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def final_review_selector_recommendation_status(
    *,
    implementation_ready_candidate_rows: int,
    capacity_blocked_candidate_rows: int,
    binding_repair_candidate_rows: int,
) -> str:
    if implementation_ready_candidate_rows > 0 and capacity_blocked_candidate_rows == 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE"
    if implementation_ready_candidate_rows > 0 and capacity_blocked_candidate_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST"
    if implementation_ready_candidate_rows == 0 and capacity_blocked_candidate_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE"
    if binding_repair_candidate_rows > 0:
        return "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BINDING_REPAIR_REQUIRED"
    return "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_NO_MATCH_REPAIR_REQUIRED"


def final_review_adjusted_selector_recommendations(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], dict[str, Any]] = {}
    for score in score_rows:
        key = scope_key_from_event(score)
        group = groups.setdefault(
            key,
            {
                **{field: score.get(field) for field in BASE_SCOPE_KEYS},
                "event_rows": 0,
                "registry_match_rows": 0,
                "implementation_ready_registry_match_rows": 0,
                "capacity_blocked_registry_match_rows": 0,
                "binding_repair_registry_match_rows": 0,
                "expected_candidate_found_in_registry_rows": 0,
                "expected_candidate_implementation_ready_rows": 0,
                "expected_candidate_capacity_blocked_rows": 0,
                "implementation_ready_candidate_row_ids": set(),
                "capacity_blocked_candidate_row_ids": set(),
                "binding_repair_candidate_row_ids": set(),
                "final_review_registry_score_statuses": Counter(),
            },
        )
        group["event_rows"] += 1
        group["registry_match_rows"] += int(score.get("registry_match_rows") or 0)
        group["implementation_ready_registry_match_rows"] += int(score.get("implementation_ready_registry_match_rows") or 0)
        group["capacity_blocked_registry_match_rows"] += int(score.get("capacity_blocked_registry_match_rows") or 0)
        group["binding_repair_registry_match_rows"] += int(score.get("binding_repair_registry_match_rows") or 0)
        group["expected_candidate_found_in_registry_rows"] += int(bool(score.get("expected_candidate_found_in_registry")))
        group["expected_candidate_implementation_ready_rows"] += int(bool(score.get("expected_candidate_implementation_ready")))
        group["expected_candidate_capacity_blocked_rows"] += int(bool(score.get("expected_candidate_capacity_blocked")))
        group["implementation_ready_candidate_row_ids"].update(score.get("implementation_ready_candidate_row_ids") or [])
        group["capacity_blocked_candidate_row_ids"].update(score.get("capacity_blocked_candidate_row_ids") or [])
        group["binding_repair_candidate_row_ids"].update(score.get("binding_repair_candidate_row_ids") or [])
        group["final_review_registry_score_statuses"][normalized(score.get("final_review_registry_score_status"))] += 1

    rows: list[dict[str, Any]] = []
    for group in groups.values():
        implementation_ready_ids = sorted(group.pop("implementation_ready_candidate_row_ids"))
        capacity_blocked_ids = sorted(group.pop("capacity_blocked_candidate_row_ids"))
        binding_repair_ids = sorted(group.pop("binding_repair_candidate_row_ids"))
        score_statuses = group.pop("final_review_registry_score_statuses")
        rows.append(
            {
                **group,
                "implementation_ready_candidate_row_ids": implementation_ready_ids,
                "capacity_blocked_candidate_row_ids": capacity_blocked_ids,
                "binding_repair_candidate_row_ids": binding_repair_ids,
                "implementation_ready_candidate_rows": len(implementation_ready_ids),
                "capacity_blocked_candidate_rows": len(capacity_blocked_ids),
                "binding_repair_candidate_rows": len(binding_repair_ids),
                "capacity_blocked_selector_blocklist_required": bool(capacity_blocked_ids),
                "final_review_registry_score_status_counts": dict(sorted(score_statuses.items())),
                "selector_recommendation_status": final_review_selector_recommendation_status(
                    implementation_ready_candidate_rows=len(implementation_ready_ids),
                    capacity_blocked_candidate_rows=len(capacity_blocked_ids),
                    binding_repair_candidate_rows=len(binding_repair_ids),
                ),
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": research_boundary(),
            }
        )

    rows.sort(
        key=lambda row: (
            -int(row["event_rows"]),
            -int(row["implementation_ready_registry_match_rows"]),
            int(row["capacity_blocked_registry_match_rows"]),
            normalized(row.get("source_component")),
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("selected_side")),
            normalized(row.get("horizon_id")),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["selector_recommendation_rank"] = index
    return rows


def summarize_final_review_adjusted_selector_recommendations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    score_status_counts = Counter()
    for row in rows:
        score_status_counts.update(row.get("final_review_registry_score_status_counts") or {})
    return {
        "rows": len(rows),
        "selector_recommendation_status_counts": dict(
            sorted(Counter(normalized(row.get("selector_recommendation_status")) for row in rows).items())
        ),
        "final_review_registry_score_status_counts": dict(sorted(score_status_counts.items())),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "event_rows": sum(int(row.get("event_rows") or 0) for row in rows),
        "registry_match_rows": sum(int(row.get("registry_match_rows") or 0) for row in rows),
        "implementation_ready_registry_match_rows": sum(
            int(row.get("implementation_ready_registry_match_rows") or 0) for row in rows
        ),
        "capacity_blocked_registry_match_rows": sum(
            int(row.get("capacity_blocked_registry_match_rows") or 0) for row in rows
        ),
        "binding_repair_registry_match_rows": sum(int(row.get("binding_repair_registry_match_rows") or 0) for row in rows),
        "expected_candidate_found_in_registry_rows": sum(
            int(row.get("expected_candidate_found_in_registry_rows") or 0) for row in rows
        ),
        "expected_candidate_implementation_ready_rows": sum(
            int(row.get("expected_candidate_implementation_ready_rows") or 0) for row in rows
        ),
        "expected_candidate_capacity_blocked_rows": sum(
            int(row.get("expected_candidate_capacity_blocked_rows") or 0) for row in rows
        ),
        "implementation_ready_candidate_rows": sum(
            int(row.get("implementation_ready_candidate_rows") or 0) for row in rows
        ),
        "capacity_blocked_candidate_rows": sum(int(row.get("capacity_blocked_candidate_rows") or 0) for row in rows),
        "binding_repair_candidate_rows": sum(int(row.get("binding_repair_candidate_rows") or 0) for row in rows),
        "capacity_blocked_selector_blocklist_required_rows": sum(
            bool(row.get("capacity_blocked_selector_blocklist_required")) for row in rows
        ),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def final_review_selector_production_change_dossier_status(selector_status: str | None) -> str:
    text = normalized(selector_status)
    if text == "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_SCOPE":
        return "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY"
    if text == "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST":
        return "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST"
    if text == "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BLOCK_REDESIGN_ONLY_SCOPE":
        return "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_REDESIGN_ONLY_BLOCKED"
    if text == "DEFAULT_OFF_FINAL_REVIEW_SELECTOR_BINDING_REPAIR_REQUIRED":
        return "PROD_CHANGE_DOSSIER_SELECTOR_BINDING_REPAIR_REQUIRED"
    return "PROD_CHANGE_DOSSIER_SELECTOR_REPAIR_REQUIRED"


def final_review_selector_ai_architecture_recommendation(dossier_status: str | None) -> str:
    text = normalized(dossier_status)
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY":
        return "MECHANICAL_SELECTOR_CAN_PRECEDE_OR_REPLACE_AI_FOR_SCOPE_AFTER_SEPARATE_PRODUCTION_REVIEW"
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST":
        return "MECHANICAL_SELECTOR_WITH_CAPACITY_BLOCKLIST_REQUIRES_REVIEW_BEFORE_AI_NARROWING"
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_REDESIGN_ONLY_BLOCKED":
        return "KEEP_AI_UNCHANGED_FOR_SCOPE_AND_ROUTE_MECHANICAL_SCOPE_TO_REDESIGN"
    return "KEEP_AI_UNCHANGED_UNTIL_SELECTOR_REPAIR"


def final_review_selector_production_change_dossier_row(
    recommendation: dict[str, Any],
    *,
    dossier_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    selector_status = normalized(recommendation.get("selector_recommendation_status"))
    dossier_status = final_review_selector_production_change_dossier_status(selector_status)
    implement_ready = dossier_status in {
        "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY",
        "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST",
    }
    scope = {field: normalized(recommendation.get(field)) for field in BASE_SCOPE_KEYS}
    return {
        "production_change_dossier_row_id": dossier_row_id,
        "schema_version": "main_orch48_final_review_selector_production_change_dossier_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "selector_recommendation_rank": recommendation.get("selector_recommendation_rank"),
        "selector_recommendation_status": selector_status,
        "production_change_dossier_status": dossier_status,
        "selector_scope_key": stable_hash(scope, length=24),
        **scope,
        "event_rows": int(recommendation.get("event_rows") or 0),
        "registry_match_rows": int(recommendation.get("registry_match_rows") or 0),
        "implementation_ready_registry_match_rows": int(
            recommendation.get("implementation_ready_registry_match_rows") or 0
        ),
        "capacity_blocked_registry_match_rows": int(recommendation.get("capacity_blocked_registry_match_rows") or 0),
        "binding_repair_registry_match_rows": int(recommendation.get("binding_repair_registry_match_rows") or 0),
        "expected_candidate_found_in_registry_rows": int(
            recommendation.get("expected_candidate_found_in_registry_rows") or 0
        ),
        "expected_candidate_implementation_ready_rows": int(
            recommendation.get("expected_candidate_implementation_ready_rows") or 0
        ),
        "expected_candidate_capacity_blocked_rows": int(
            recommendation.get("expected_candidate_capacity_blocked_rows") or 0
        ),
        "implementation_ready_candidate_rows": int(recommendation.get("implementation_ready_candidate_rows") or 0),
        "capacity_blocked_candidate_rows": int(recommendation.get("capacity_blocked_candidate_rows") or 0),
        "binding_repair_candidate_rows": int(recommendation.get("binding_repair_candidate_rows") or 0),
        "capacity_blocked_selector_blocklist_required": bool(
            recommendation.get("capacity_blocked_selector_blocklist_required")
        ),
        "implementation_ready_candidate_row_ids": recommendation.get("implementation_ready_candidate_row_ids") or [],
        "capacity_blocked_candidate_row_ids": recommendation.get("capacity_blocked_candidate_row_ids") or [],
        "binding_repair_candidate_row_ids": recommendation.get("binding_repair_candidate_row_ids") or [],
        "final_review_registry_score_status_counts": recommendation.get(
            "final_review_registry_score_status_counts"
        )
        or {},
        "mechanical_selector_scope_draft_ready_for_separate_review": implement_ready,
        "separate_production_change_review_required": True,
        "owner_approval_required_before_runtime_enablement": True,
        "production_change_opened_now": False,
        "live_selector_change_now": False,
        "ai_architecture_recommendation": final_review_selector_ai_architecture_recommendation(dossier_status),
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def summarize_final_review_selector_production_change_dossier(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "production_change_dossier_status_counts": dict(
            sorted(Counter(normalized(row.get("production_change_dossier_status")) for row in rows).items())
        ),
        "selector_recommendation_status_counts": dict(
            sorted(Counter(normalized(row.get("selector_recommendation_status")) for row in rows).items())
        ),
        "ai_architecture_recommendation_counts": dict(
            sorted(Counter(normalized(row.get("ai_architecture_recommendation")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "event_rows": sum(int(row.get("event_rows") or 0) for row in rows),
        "registry_match_rows": sum(int(row.get("registry_match_rows") or 0) for row in rows),
        "implementation_ready_registry_match_rows": sum(
            int(row.get("implementation_ready_registry_match_rows") or 0) for row in rows
        ),
        "capacity_blocked_registry_match_rows": sum(
            int(row.get("capacity_blocked_registry_match_rows") or 0) for row in rows
        ),
        "binding_repair_registry_match_rows": sum(int(row.get("binding_repair_registry_match_rows") or 0) for row in rows),
        "expected_candidate_found_in_registry_rows": sum(
            int(row.get("expected_candidate_found_in_registry_rows") or 0) for row in rows
        ),
        "expected_candidate_implementation_ready_rows": sum(
            int(row.get("expected_candidate_implementation_ready_rows") or 0) for row in rows
        ),
        "expected_candidate_capacity_blocked_rows": sum(
            int(row.get("expected_candidate_capacity_blocked_rows") or 0) for row in rows
        ),
        "implementation_ready_candidate_rows": sum(
            int(row.get("implementation_ready_candidate_rows") or 0) for row in rows
        ),
        "capacity_blocked_candidate_rows": sum(int(row.get("capacity_blocked_candidate_rows") or 0) for row in rows),
        "binding_repair_candidate_rows": sum(int(row.get("binding_repair_candidate_rows") or 0) for row in rows),
        "capacity_blocked_selector_blocklist_required_rows": sum(
            bool(row.get("capacity_blocked_selector_blocklist_required")) for row in rows
        ),
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": sum(
            bool(row.get("mechanical_selector_scope_draft_ready_for_separate_review")) for row in rows
        ),
        "separate_production_change_review_required_rows": sum(
            bool(row.get("separate_production_change_review_required")) for row in rows
        ),
        "owner_approval_required_before_runtime_enablement_rows": sum(
            bool(row.get("owner_approval_required_before_runtime_enablement")) for row in rows
        ),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def final_review_ai_narrowing_policy_status(dossier_status: str | None) -> str:
    text = normalized(dossier_status)
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY":
        return "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY"
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST":
        return "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST"
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_REDESIGN_ONLY_BLOCKED":
        return "AI_NARROWING_POLICY_KEEP_AI_UNCHANGED_MECHANICAL_SCOPE_REDESIGN_ONLY"
    return "AI_NARROWING_POLICY_KEEP_AI_UNCHANGED_SELECTOR_REPAIR_REQUIRED"


def final_review_ai_role_after_owner_approval(policy_status: str | None) -> str:
    text = normalized(policy_status)
    if text == "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY":
        return "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_FOR_SCOPE_AFTER_REVIEW"
    if text == "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST":
        return "MECHANICAL_SELECTOR_CAN_PRECEDE_AI_ONLY_WITH_CAPACITY_BLOCKLIST_AFTER_REVIEW"
    return "KEEP_PRIMARY_ANALYZER_FULL_SCOPE_FOR_THIS_SELECTOR_SCOPE"


def final_review_selector_ai_narrowing_policy_row(
    dossier_row: dict[str, Any],
    *,
    policy_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    dossier_status = normalized(dossier_row.get("production_change_dossier_status"))
    policy_status = final_review_ai_narrowing_policy_status(dossier_status)
    review_ready = policy_status in {
        "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY",
        "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST",
    }
    capacity_blocklist_required = (
        policy_status == "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST"
    )
    scope = {field: normalized(dossier_row.get(field)) for field in BASE_SCOPE_KEYS}
    return {
        "ai_narrowing_policy_row_id": policy_row_id,
        "schema_version": "main_orch48_ai_narrowing_policy_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "production_change_dossier_row_id": dossier_row.get("production_change_dossier_row_id"),
        "production_change_dossier_status": dossier_status,
        "ai_narrowing_policy_status": policy_status,
        "ai_role_after_owner_approval": final_review_ai_role_after_owner_approval(policy_status),
        "selector_scope_key": dossier_row.get("selector_scope_key") or stable_hash(scope, length=24),
        **scope,
        "event_rows": int(dossier_row.get("event_rows") or 0),
        "registry_match_rows": int(dossier_row.get("registry_match_rows") or 0),
        "implementation_ready_registry_match_rows": int(
            dossier_row.get("implementation_ready_registry_match_rows") or 0
        ),
        "capacity_blocked_registry_match_rows": int(dossier_row.get("capacity_blocked_registry_match_rows") or 0),
        "expected_candidate_found_in_registry_rows": int(
            dossier_row.get("expected_candidate_found_in_registry_rows") or 0
        ),
        "expected_candidate_implementation_ready_rows": int(
            dossier_row.get("expected_candidate_implementation_ready_rows") or 0
        ),
        "expected_candidate_capacity_blocked_rows": int(
            dossier_row.get("expected_candidate_capacity_blocked_rows") or 0
        ),
        "implementation_ready_candidate_rows": int(dossier_row.get("implementation_ready_candidate_rows") or 0),
        "capacity_blocked_candidate_rows": int(dossier_row.get("capacity_blocked_candidate_rows") or 0),
        "capacity_blocklist_required_before_ai_narrowing": capacity_blocklist_required,
        "ai_narrowing_review_ready": review_ready,
        "current_ai_entrypoint": "src/components/orchestrator.py::run_cycle -> PrimaryAnalyzer.analyze",
        "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
        "default_off_policy_surface": "PRE_AI_MECHANICAL_SELECTOR_REVIEW_ONLY",
        "runtime_enablement_prerequisites": [
            "separate_production_change_review",
            "owner_approval_before_runtime_enablement",
            "explicit_config_flag_default_off_to_on",
            "runtime_halt_removed_by_owner",
        ],
        "mechanical_selector_scope_draft_ready_for_separate_review": bool(
            dossier_row.get("mechanical_selector_scope_draft_ready_for_separate_review")
        ),
        "separate_production_change_review_required": True,
        "owner_approval_required_before_runtime_enablement": True,
        "production_change_opened_now": False,
        "live_ai_runtime_change_now": False,
        "live_selector_change_now": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def summarize_final_review_selector_ai_narrowing_policy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "ai_narrowing_policy_status_counts": dict(
            sorted(Counter(normalized(row.get("ai_narrowing_policy_status")) for row in rows).items())
        ),
        "ai_role_after_owner_approval_counts": dict(
            sorted(Counter(normalized(row.get("ai_role_after_owner_approval")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "event_rows": sum(int(row.get("event_rows") or 0) for row in rows),
        "registry_match_rows": sum(int(row.get("registry_match_rows") or 0) for row in rows),
        "implementation_ready_registry_match_rows": sum(
            int(row.get("implementation_ready_registry_match_rows") or 0) for row in rows
        ),
        "capacity_blocked_registry_match_rows": sum(
            int(row.get("capacity_blocked_registry_match_rows") or 0) for row in rows
        ),
        "expected_candidate_found_in_registry_rows": sum(
            int(row.get("expected_candidate_found_in_registry_rows") or 0) for row in rows
        ),
        "expected_candidate_implementation_ready_rows": sum(
            int(row.get("expected_candidate_implementation_ready_rows") or 0) for row in rows
        ),
        "expected_candidate_capacity_blocked_rows": sum(
            int(row.get("expected_candidate_capacity_blocked_rows") or 0) for row in rows
        ),
        "implementation_ready_candidate_rows": sum(
            int(row.get("implementation_ready_candidate_rows") or 0) for row in rows
        ),
        "capacity_blocked_candidate_rows": sum(int(row.get("capacity_blocked_candidate_rows") or 0) for row in rows),
        "ai_narrowing_review_ready_rows": sum(bool(row.get("ai_narrowing_review_ready")) for row in rows),
        "capacity_blocklist_required_before_ai_narrowing_rows": sum(
            bool(row.get("capacity_blocklist_required_before_ai_narrowing")) for row in rows
        ),
        "mechanical_selector_scope_draft_ready_for_separate_review_rows": sum(
            bool(row.get("mechanical_selector_scope_draft_ready_for_separate_review")) for row in rows
        ),
        "separate_production_change_review_required_rows": sum(
            bool(row.get("separate_production_change_review_required")) for row in rows
        ),
        "owner_approval_required_before_runtime_enablement_rows": sum(
            bool(row.get("owner_approval_required_before_runtime_enablement")) for row in rows
        ),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def ai_narrowing_capacity_blocklist_status(dossier_status: str | None) -> str:
    text = normalized(dossier_status)
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_IMPLEMENT_READY_WITH_REDESIGN_BLOCKLIST":
        return "AI_NARROWING_CAPACITY_BLOCKLIST_REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW"
    if text == "PROD_CHANGE_DOSSIER_DEFAULT_OFF_SELECTOR_REDESIGN_ONLY_BLOCKED":
        return "AI_NARROWING_CAPACITY_BLOCKLIST_PRESERVED_REDESIGN_ONLY_KEEP_AI_UNCHANGED"
    return "AI_NARROWING_CAPACITY_BLOCKLIST_NOT_REQUIRED"


def final_review_ai_narrowing_capacity_blocklist_row(
    dossier_row: dict[str, Any],
    *,
    blocklist_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    candidate_ids = list(dict.fromkeys(str(item) for item in dossier_row.get("capacity_blocked_candidate_row_ids") or []))
    implementation_ids = list(
        dict.fromkeys(str(item) for item in dossier_row.get("implementation_ready_candidate_row_ids") or [])
    )
    status = ai_narrowing_capacity_blocklist_status(dossier_row.get("production_change_dossier_status"))
    scope = {field: normalized(dossier_row.get(field)) for field in BASE_SCOPE_KEYS}
    pre_ai_blocklist = status == "AI_NARROWING_CAPACITY_BLOCKLIST_REQUIRED_FOR_PRE_AI_SELECTOR_REVIEW"
    redesign_only = status == "AI_NARROWING_CAPACITY_BLOCKLIST_PRESERVED_REDESIGN_ONLY_KEEP_AI_UNCHANGED"
    return {
        "ai_narrowing_capacity_blocklist_row_id": blocklist_row_id,
        "schema_version": "main_orch48_ai_narrowing_capacity_blocklist_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "production_change_dossier_row_id": dossier_row.get("production_change_dossier_row_id"),
        "production_change_dossier_status": dossier_row.get("production_change_dossier_status"),
        "selector_scope_key": dossier_row.get("selector_scope_key") or stable_hash(scope, length=24),
        **scope,
        "ai_narrowing_capacity_blocklist_status": status,
        "pre_ai_selector_blocklist_required_before_runtime_enablement": pre_ai_blocklist,
        "keep_ai_unchanged_redesign_only_scope": redesign_only,
        "capacity_blocked_candidate_rows": len(candidate_ids),
        "capacity_blocked_candidate_row_ids": candidate_ids,
        "capacity_blocked_candidate_id_set_sha256": stable_hash(candidate_ids, length=32),
        "implementation_ready_candidate_rows": len(implementation_ids),
        "implementation_ready_candidate_row_ids": implementation_ids,
        "capacity_blocklist_surface": "DEFAULT_OFF_CAPACITY_BLOCKLIST_REVIEW_ONLY",
        "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
        "runtime_enablement_prerequisites": [
            "separate_production_change_review",
            "owner_approval_before_runtime_enablement",
            "explicit_ai_narrowing_config_enabled_active",
            "capacity_blocklist_active_config_true",
            "runtime_halt_removed_by_owner",
            "focused_parser_selector_canary_tests",
        ],
        "separate_production_change_review_required": True,
        "owner_approval_required_before_runtime_enablement": True,
        "capacity_blocklist_active_now": False,
        "ai_call_skip_allowed_now": False,
        "production_change_opened_now": False,
        "live_ai_runtime_change_now": False,
        "live_selector_change_now": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def summarize_ai_narrowing_capacity_blocklist(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidate_ids = [item for row in rows for item in (row.get("capacity_blocked_candidate_row_ids") or [])]
    pre_ai_candidate_ids = [
        item
        for row in rows
        if row.get("pre_ai_selector_blocklist_required_before_runtime_enablement")
        for item in (row.get("capacity_blocked_candidate_row_ids") or [])
    ]
    redesign_candidate_ids = [
        item
        for row in rows
        if row.get("keep_ai_unchanged_redesign_only_scope")
        for item in (row.get("capacity_blocked_candidate_row_ids") or [])
    ]
    return {
        "rows": len(rows),
        "ai_narrowing_capacity_blocklist_status_counts": dict(
            sorted(Counter(normalized(row.get("ai_narrowing_capacity_blocklist_status")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "capacity_blocked_candidate_ref_rows": len(candidate_ids),
        "unique_capacity_blocked_candidate_ids": len(set(candidate_ids)),
        "pre_ai_selector_blocklist_scope_rows": sum(
            bool(row.get("pre_ai_selector_blocklist_required_before_runtime_enablement")) for row in rows
        ),
        "pre_ai_selector_blocked_candidate_ref_rows": len(pre_ai_candidate_ids),
        "unique_pre_ai_selector_blocked_candidate_ids": len(set(pre_ai_candidate_ids)),
        "redesign_only_blocklist_scope_rows": sum(bool(row.get("keep_ai_unchanged_redesign_only_scope")) for row in rows),
        "redesign_only_blocked_candidate_ref_rows": len(redesign_candidate_ids),
        "unique_redesign_only_blocked_candidate_ids": len(set(redesign_candidate_ids)),
        "capacity_blocklist_active_now_rows": sum(bool(row.get("capacity_blocklist_active_now")) for row in rows),
        "ai_call_skip_allowed_now_rows": sum(bool(row.get("ai_call_skip_allowed_now")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


class AINarrowingCapacityBlocklist:
    """Default-off candidate-id blocklist for capacity-blocked selector scopes."""

    def __init__(self, blocklist_rows: list[dict[str, Any]]) -> None:
        self.blocklist_rows = list(blocklist_rows)
        self._by_candidate_id: dict[str, list[dict[str, Any]]] = {}
        for row in self.blocklist_rows:
            for candidate_id in row.get("capacity_blocked_candidate_row_ids") or []:
                self._by_candidate_id.setdefault(str(candidate_id), []).append(row)

    def evaluate_candidate(self, candidate_row_id: str, *, evaluation_row_id: str | None = None) -> dict[str, Any]:
        matches = self._by_candidate_id.get(str(candidate_row_id), [])
        status_counts = Counter(normalized(row.get("ai_narrowing_capacity_blocklist_status")) for row in matches)
        pre_ai_blocked = any(row.get("pre_ai_selector_blocklist_required_before_runtime_enablement") for row in matches)
        redesign_only = bool(matches) and not pre_ai_blocked
        if pre_ai_blocked:
            eval_status = "AI_NARROWING_CAPACITY_BLOCKLIST_MATCH_BLOCK_PRE_AI_SELECTOR"
        elif redesign_only:
            eval_status = "AI_NARROWING_CAPACITY_BLOCKLIST_MATCH_REDESIGN_ONLY_KEEP_AI_UNCHANGED"
        else:
            eval_status = "AI_NARROWING_CAPACITY_BLOCKLIST_NO_MATCH"
        return {
            "ai_narrowing_capacity_blocklist_eval_row_id": evaluation_row_id
            or stable_hash(
                {
                    "schema_version": "main_orch48_ai_narrowing_capacity_blocklist_eval_v1",
                    "candidate_row_id": candidate_row_id,
                    "matched_blocklist_row_ids": [
                        row.get("ai_narrowing_capacity_blocklist_row_id") for row in matches
                    ],
                },
                length=32,
            ),
            "schema_version": "main_orch48_ai_narrowing_capacity_blocklist_eval_v1",
            "candidate_row_id": str(candidate_row_id),
            "matched_blocklist_rows": len(matches),
            "matched_blocklist_row_ids": [row.get("ai_narrowing_capacity_blocklist_row_id") for row in matches],
            "ai_narrowing_capacity_blocklist_status_counts": dict(sorted(status_counts.items())),
            "ai_narrowing_capacity_blocklist_eval_status": eval_status,
            "pre_ai_selector_candidate_blocked": pre_ai_blocked,
            "keep_ai_unchanged_redesign_only_candidate": redesign_only,
            "capacity_blocklist_active_now": False,
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": research_boundary(),
        }

    def summarize(self) -> dict[str, Any]:
        return {
            "blocklist_rows": len(self.blocklist_rows),
            "unique_candidate_ids": len(self._by_candidate_id),
            "rows_with_pre_ai_selector_blocklist_required": sum(
                bool(row.get("pre_ai_selector_blocklist_required_before_runtime_enablement"))
                for row in self.blocklist_rows
            ),
            "rows_with_redesign_only_blocklist": sum(
                bool(row.get("keep_ai_unchanged_redesign_only_scope")) for row in self.blocklist_rows
            ),
            "capacity_blocklist_active_now_rows": sum(
                bool(row.get("capacity_blocklist_active_now")) for row in self.blocklist_rows
            ),
            "runtime_candidate_use_permitted_rows": sum(
                bool(row.get("runtime_candidate_use_permitted")) for row in self.blocklist_rows
            ),
        }


def ai_narrowing_policy_scope_event(policy_row: dict[str, Any], *, event_row_id: str) -> dict[str, Any]:
    scope = {field: normalized(policy_row.get(field)) for field in BASE_SCOPE_KEYS}
    return {
        "ai_narrowing_policy_event_row_id": event_row_id,
        "schema_version": "main_orch48_ai_narrowing_policy_registry_event_v1",
        **scope,
        "selector_scope_key": policy_row.get("selector_scope_key") or stable_hash(scope, length=24),
    }


def ai_narrowing_event_from_source_row(
    source_row: dict[str, Any],
    *,
    event_row_id: str | None = None,
    source_kind: str = "ai_narrowing_policy_source_row",
    source_artifact: str | None = None,
    source_line_no: int | None = None,
    source_sha256: str | None = None,
    required_event_fields: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Normalize a source row into the event contract consumed by the AI narrowing registry."""
    required_fields = list(dict.fromkeys(required_event_fields or AI_NARROWING_EVENT_REQUIRED_FIELDS))
    event = {
        field: normalized(first_present(source_row, EVENT_FIELD_ALIASES.get(field, (field,))))
        for field in BASE_SCOPE_KEYS
    }
    missing_required_fields = [field for field in required_fields if not normalized(event.get(field))]
    status = (
        "AI_NARROWING_EVENT_CONTRACT_COMPLETE"
        if not missing_required_fields
        else "AI_NARROWING_EVENT_CONTRACT_INCOMPLETE"
    )
    event.update(
        {
            "ai_narrowing_policy_event_row_id": event_row_id,
            "schema_version": "main_orch48_ai_narrowing_policy_registry_event_v1",
            "selector_scope_key": stable_hash({field: event.get(field) for field in BASE_SCOPE_KEYS}, length=24),
            "event_source_kind": source_kind,
            "event_source_artifact": source_artifact,
            "event_source_line_no": source_line_no,
            "event_source_sha256": source_sha256,
            "required_event_fields": required_fields,
            "required_event_field_count": len(required_fields),
            "missing_required_fields": missing_required_fields,
            "event_adapter_status": status,
            "event_evaluation_surface": "AINarrowingPolicyRegistry.evaluate_event",
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": research_boundary(),
        }
    )
    return event


def event_matches_ai_narrowing_policy_scope(event: dict[str, Any], policy_row: dict[str, Any]) -> bool:
    return all(normalized(event.get(field)) == normalized(policy_row.get(field)) for field in BASE_SCOPE_KEYS)


def ai_narrowing_registry_eval_status(matched_rows: list[dict[str, Any]]) -> str:
    statuses = {normalized(row.get("ai_narrowing_policy_status")) for row in matched_rows}
    if not statuses:
        return "AI_NARROWING_REGISTRY_NO_POLICY_MATCH_KEEP_AI"
    if "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY_WITH_CAPACITY_BLOCKLIST" in statuses:
        return "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_WITH_CAPACITY_BLOCKLIST"
    if "AI_NARROWING_POLICY_DEFAULT_OFF_PRE_AI_MECHANICAL_SELECTOR_READY" in statuses:
        return "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY"
    return "AI_NARROWING_REGISTRY_MATCH_KEEP_AI_UNCHANGED"


class AINarrowingPolicyRegistry:
    """Default-off evaluator over AI narrowing policy rows."""

    def __init__(self, policy_rows: list[dict[str, Any]]) -> None:
        self.policy_rows = list(policy_rows)
        self._by_scope_key: dict[str, list[dict[str, Any]]] = {}
        for row in self.policy_rows:
            scope = {field: normalized(row.get(field)) for field in BASE_SCOPE_KEYS}
            key = normalized(row.get("selector_scope_key")) or stable_hash(scope, length=24)
            self._by_scope_key.setdefault(key, []).append(row)

    def evaluate_event(self, event: dict[str, Any], *, evaluation_row_id: str) -> dict[str, Any]:
        scope = {field: normalized(event.get(field)) for field in BASE_SCOPE_KEYS}
        scope_key = normalized(event.get("selector_scope_key")) or stable_hash(scope, length=24)
        candidates = self._by_scope_key.get(scope_key, [])
        matched = [row for row in candidates if event_matches_ai_narrowing_policy_scope(event, row)]
        eval_status = ai_narrowing_registry_eval_status(matched)
        status_counts = Counter(normalized(row.get("ai_narrowing_policy_status")) for row in matched)
        role_counts = Counter(normalized(row.get("ai_role_after_owner_approval")) for row in matched)
        return {
            "ai_narrowing_registry_eval_row_id": evaluation_row_id,
            "schema_version": "main_orch48_ai_narrowing_policy_registry_eval_v1",
            "input_event_row_id": event.get("ai_narrowing_policy_event_row_id") or event.get("event_row_id") or "",
            "selector_scope_key": scope_key,
            **scope,
            "matched_policy_rows": len(matched),
            "matched_policy_row_ids": [row.get("ai_narrowing_policy_row_id") for row in matched],
            "ai_narrowing_policy_status_counts": dict(sorted(status_counts.items())),
            "ai_role_after_owner_approval_counts": dict(sorted(role_counts.items())),
            "ai_narrowing_registry_eval_status": eval_status,
            "ai_narrowing_review_ready": eval_status in {
                "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_READY",
                "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_WITH_CAPACITY_BLOCKLIST",
            },
            "capacity_blocklist_required_before_ai_narrowing": (
                eval_status == "AI_NARROWING_REGISTRY_MATCH_PRE_AI_SELECTOR_REVIEW_WITH_CAPACITY_BLOCKLIST"
            ),
            "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
            "ai_call_skip_allowed_now": False,
            "production_change_opened_now": False,
            "live_ai_runtime_change_now": False,
            "live_selector_change_now": False,
            "paid_api_or_vendor_call": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": research_boundary(),
        }


def summarize_ai_narrowing_policy_registry_evaluations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(normalized(row.get("ai_narrowing_registry_eval_status")) for row in rows)
    policy_status_counts = Counter()
    role_counts = Counter()
    for row in rows:
        policy_status_counts.update(row.get("ai_narrowing_policy_status_counts") or {})
        role_counts.update(row.get("ai_role_after_owner_approval_counts") or {})
    return {
        "rows": len(rows),
        "ai_narrowing_registry_eval_status_counts": dict(sorted(status_counts.items())),
        "ai_narrowing_policy_status_counts": dict(sorted(policy_status_counts.items())),
        "ai_role_after_owner_approval_counts": dict(sorted(role_counts.items())),
        "matched_policy_rows": sum(int(row.get("matched_policy_rows") or 0) for row in rows),
        "ai_narrowing_review_ready_rows": sum(bool(row.get("ai_narrowing_review_ready")) for row in rows),
        "capacity_blocklist_required_before_ai_narrowing_rows": sum(
            bool(row.get("capacity_blocklist_required_before_ai_narrowing")) for row in rows
        ),
        "ai_call_skip_allowed_now_rows": sum(bool(row.get("ai_call_skip_allowed_now")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def summarize_ai_narrowing_policy_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_field_counts = Counter()
    for row in rows:
        missing_field_counts.update(row.get("missing_required_fields") or [])
    return {
        "rows": len(rows),
        "event_adapter_status_counts": dict(
            sorted(Counter(normalized(row.get("event_adapter_status")) for row in rows).items())
        ),
        "event_source_kind_counts": dict(
            sorted(Counter(normalized(row.get("event_source_kind")) for row in rows).items())
        ),
        "missing_required_field_counts": dict(sorted(missing_field_counts.items())),
        "contract_complete_rows": sum(
            normalized(row.get("event_adapter_status")) == "AI_NARROWING_EVENT_CONTRACT_COMPLETE" for row in rows
        ),
        "ai_call_skip_allowed_now_rows": sum(bool(row.get("ai_call_skip_allowed_now")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def normalize_ai_narrowing_runtime_config(config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return the explicit default-off AI narrowing runtime guard config."""
    source = config or {}
    if isinstance(source.get("ai_narrowing"), dict):
        source = source["ai_narrowing"]
    normalized_config = dict(AI_NARROWING_RUNTIME_CONFIG_DEFAULTS)
    for key in AI_NARROWING_RUNTIME_CONFIG_DEFAULTS:
        if key in source:
            normalized_config[key] = source[key]
    normalized_config["enabled"] = bool(normalized_config.get("enabled"))
    normalized_config["allow_ai_call_skip"] = bool(normalized_config.get("allow_ai_call_skip"))
    normalized_config["owner_approval_confirmed"] = bool(normalized_config.get("owner_approval_confirmed"))
    normalized_config["production_change_review_approved"] = bool(
        normalized_config.get("production_change_review_approved")
    )
    normalized_config["runtime_halt_removed"] = bool(normalized_config.get("runtime_halt_removed"))
    normalized_config["capacity_blocklist_active"] = bool(normalized_config.get("capacity_blocklist_active"))
    normalized_config["mode"] = normalized(normalized_config.get("mode") or "shadow").lower()
    return normalized_config


def ai_narrowing_runtime_config_guard_decision(
    evaluation: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
    runtime_halt_active: bool = True,
    decision_row_id: str | None = None,
) -> dict[str, Any]:
    """Evaluate an AI narrowing registry result against the default-off runtime guard.

    This helper deliberately does not return live AI-skip permission. It records
    whether a policy event would be eligible after every prerequisite is true,
    while keeping the current PrimaryAnalyzer path unchanged.
    """
    guard_config = normalize_ai_narrowing_runtime_config(config)
    review_ready = bool(evaluation.get("ai_narrowing_review_ready"))
    capacity_blocklist_required = bool(evaluation.get("capacity_blocklist_required_before_ai_narrowing"))
    failures: list[str] = []
    if not guard_config["enabled"]:
        failures.append("CONFIG_DISABLED")
    if guard_config["mode"] != "active":
        failures.append("CONFIG_MODE_NOT_ACTIVE")
    if not guard_config["allow_ai_call_skip"]:
        failures.append("AI_CALL_SKIP_FLAG_DISABLED")
    if not review_ready:
        failures.append("POLICY_NOT_REVIEW_READY")
    if not guard_config["production_change_review_approved"]:
        failures.append("PRODUCTION_CHANGE_REVIEW_NOT_APPROVED")
    if not guard_config["owner_approval_confirmed"]:
        failures.append("OWNER_APPROVAL_NOT_CONFIRMED")
    if runtime_halt_active:
        failures.append("RUNTIME_HALT_ACTIVE")
    if not guard_config["runtime_halt_removed"]:
        failures.append("RUNTIME_HALT_REMOVAL_NOT_CONFIRMED")
    if capacity_blocklist_required and not guard_config["capacity_blocklist_active"]:
        failures.append("CAPACITY_BLOCKLIST_NOT_ACTIVE")

    eligible_after_all_gates = not failures
    status = (
        "AI_NARROWING_RUNTIME_ELIGIBLE_AFTER_ALL_GATES_BUT_NOT_WIRED"
        if eligible_after_all_gates
        else AI_NARROWING_RUNTIME_FAILURE_STATUS[failures[0]]
    )
    scope = {field: normalized(evaluation.get(field)) for field in BASE_SCOPE_KEYS}
    return {
        "ai_narrowing_runtime_guard_decision_row_id": decision_row_id
        or stable_hash(
            {
                "schema_version": "main_orch48_ai_narrowing_runtime_config_guard_decision_v1",
                "evaluation_row_id": evaluation.get("ai_narrowing_registry_eval_row_id"),
                "selector_scope_key": evaluation.get("selector_scope_key"),
                "runtime_halt_active": runtime_halt_active,
                "guard_config": guard_config,
            },
            length=32,
        ),
        "schema_version": "main_orch48_ai_narrowing_runtime_config_guard_decision_v1",
        "input_ai_narrowing_registry_eval_row_id": evaluation.get("ai_narrowing_registry_eval_row_id"),
        "selector_scope_key": evaluation.get("selector_scope_key") or stable_hash(scope, length=24),
        **scope,
        "matched_policy_rows": int(evaluation.get("matched_policy_rows") or 0),
        "matched_policy_row_ids": evaluation.get("matched_policy_row_ids") or [],
        "ai_narrowing_registry_eval_status": evaluation.get("ai_narrowing_registry_eval_status"),
        "ai_narrowing_review_ready": review_ready,
        "capacity_blocklist_required_before_ai_narrowing": capacity_blocklist_required,
        "runtime_guard_config_enabled": guard_config["enabled"],
        "runtime_guard_config_mode": guard_config["mode"],
        "runtime_guard_allow_ai_call_skip_config": guard_config["allow_ai_call_skip"],
        "runtime_guard_owner_approval_confirmed": guard_config["owner_approval_confirmed"],
        "runtime_guard_production_change_review_approved": guard_config["production_change_review_approved"],
        "runtime_guard_runtime_halt_removed_config": guard_config["runtime_halt_removed"],
        "runtime_halt_active": bool(runtime_halt_active),
        "runtime_guard_capacity_blocklist_active": guard_config["capacity_blocklist_active"],
        "runtime_enablement_gate_failures": failures,
        "runtime_enablement_gate_failure_count": len(failures),
        "runtime_eligible_after_all_gates": eligible_after_all_gates,
        "ai_narrowing_runtime_guard_decision_status": status,
        "current_ai_runtime_behavior": "UNCHANGED_DEFAULT_AI_DECISION_GATE",
        "ai_call_skip_allowed_now": False,
        "production_change_opened_now": False,
        "live_ai_runtime_change_now": False,
        "live_selector_change_now": False,
        "paid_api_or_vendor_call": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
    }


def summarize_ai_narrowing_runtime_config_guard_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    failure_counts = Counter()
    for row in rows:
        failure_counts.update(row.get("runtime_enablement_gate_failures") or [])
    return {
        "rows": len(rows),
        "ai_narrowing_runtime_guard_decision_status_counts": dict(
            sorted(Counter(normalized(row.get("ai_narrowing_runtime_guard_decision_status")) for row in rows).items())
        ),
        "runtime_enablement_gate_failure_counts": dict(sorted(failure_counts.items())),
        "ai_narrowing_registry_eval_status_counts": dict(
            sorted(Counter(normalized(row.get("ai_narrowing_registry_eval_status")) for row in rows).items())
        ),
        "matched_policy_rows": sum(int(row.get("matched_policy_rows") or 0) for row in rows),
        "ai_narrowing_review_ready_rows": sum(bool(row.get("ai_narrowing_review_ready")) for row in rows),
        "capacity_blocklist_required_before_ai_narrowing_rows": sum(
            bool(row.get("capacity_blocklist_required_before_ai_narrowing")) for row in rows
        ),
        "runtime_guard_config_enabled_rows": sum(bool(row.get("runtime_guard_config_enabled")) for row in rows),
        "runtime_guard_allow_ai_call_skip_config_rows": sum(
            bool(row.get("runtime_guard_allow_ai_call_skip_config")) for row in rows
        ),
        "runtime_halt_active_rows": sum(bool(row.get("runtime_halt_active")) for row in rows),
        "runtime_eligible_after_all_gates_rows": sum(bool(row.get("runtime_eligible_after_all_gates")) for row in rows),
        "ai_call_skip_allowed_now_rows": sum(bool(row.get("ai_call_skip_allowed_now")) for row in rows),
        "production_change_opened_now_rows": sum(bool(row.get("production_change_opened_now")) for row in rows),
        "live_ai_runtime_change_now_rows": sum(bool(row.get("live_ai_runtime_change_now")) for row in rows),
        "live_selector_change_now_rows": sum(bool(row.get("live_selector_change_now")) for row in rows),
        "paid_api_or_vendor_call_rows": sum(bool(row.get("paid_api_or_vendor_call")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def load_candidate_rows(path: Path | str = DEFAULT_CANDIDATE_LEDGER) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


class ReducedSurfaceCandidateRegistry:
    """Default-off evaluator over reduced-surface candidate rows."""

    def __init__(self, candidates: list[dict[str, Any]]) -> None:
        self.candidates = list(candidates)
        self._by_base_scope: dict[tuple[str, ...], list[dict[str, Any]]] = {}
        for candidate in self.candidates:
            scope = candidate.get("surface_scope") or {}
            self._by_base_scope.setdefault(scope_key_from_scope(scope), []).append(candidate)

    @classmethod
    def from_jsonl(cls, path: Path | str = DEFAULT_CANDIDATE_LEDGER) -> "ReducedSurfaceCandidateRegistry":
        return cls(load_candidate_rows(path))

    def evaluate_event(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for candidate in self._by_base_scope.get(scope_key_from_event(event), []):
            scope = candidate.get("surface_scope") or {}
            if not event_matches_surface_scope(event, scope):
                continue
            matches.append(
                {
                    "candidate_row_id": candidate.get("candidate_row_id"),
                    "surface_scope_sha256": candidate.get("surface_scope_sha256"),
                    "main_compiler_action": candidate.get("main_compiler_action"),
                    "branch_local_candidate_status": candidate.get("branch_local_candidate_status"),
                    "symbol": candidate.get("symbol"),
                    "source_symbol": candidate.get("source_symbol"),
                    "market_timeframe": candidate.get("market_timeframe"),
                    "route_session": candidate.get("route_session"),
                    "horizon_id": candidate.get("horizon_id"),
                    "source_component": candidate.get("source_component"),
                    "selected_side": candidate.get("selected_side"),
                    "average_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "average_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "target_selected_intrabar_cost_adjusted_simulated_r": candidate.get(
                        "target_selected_intrabar_cost_adjusted_simulated_r"
                    ),
                    "registry_evaluation_status": "DEFAULT_OFF_REDUCED_SURFACE_CANDIDATE_MATCH",
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "replay_r_reference_counted_as_new_main_result": False,
                    "research_boundary": research_boundary(),
                }
            )
        return matches

    def summarize_registry(self) -> dict[str, Any]:
        duplicate_scope_counts = [len(rows) for rows in self._by_base_scope.values() if len(rows) > 1]
        return {
            "candidate_rows": len(self.candidates),
            "unique_base_scopes": len(self._by_base_scope),
            "duplicate_base_scope_count": len(duplicate_scope_counts),
            "max_duplicate_base_scope_size": max(duplicate_scope_counts) if duplicate_scope_counts else 1,
            "action_counts": dict(
                sorted(Counter(normalized(row.get("main_compiler_action")) for row in self.candidates).items())
            ),
            "runtime_candidate_use_permitted_rows": sum(
                bool(row.get("runtime_candidate_use_permitted")) for row in self.candidates
            ),
        }
