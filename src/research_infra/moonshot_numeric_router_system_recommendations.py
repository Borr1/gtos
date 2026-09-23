"""Main-side intake helpers for moonshot numeric-router system recommendations."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


BOUNDARY_SCHEMA = "main_side_moonshot_numeric_router_system_recommendations_v1"
DEFAULT_NUMERIC_ROUTER_CATALOG_LEDGER_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "main_orchestrator_24h_full_stack_research_integration_materialization"
)
NUMERIC_ROUTER_CATALOG_EVENT_KEYS = (
    "symbol",
    "route_session",
    "horizon_id",
    "source_component",
    "primitive_flag",
    "proxy_r_class",
    "target_stop_order_class",
    "repair_action",
    "missing_field_count",
)
NUMERIC_ROUTER_CATALOG_EVENT_FIELD_ALIASES = {
    "symbol": ("symbol", "broker_symbol"),
    "route_session": ("route_session", "session", "session_tag", "kill_zone"),
    "horizon_id": ("horizon_id",),
    "source_component": ("source_component", "strategy_family", "framework", "source_file"),
    "primitive_flag": ("primitive_flag",),
    "proxy_r_class": ("proxy_r_class",),
    "target_stop_order_class": ("target_stop_order_class",),
    "repair_action": ("repair_action",),
    "missing_field_count": ("missing_field_count",),
}
NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS = {
    "horizon_id",
    "primitive_flag",
    "proxy_r_class",
    "target_stop_order_class",
}
NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_FIELDS = (
    "source_repair_plan_row_id",
    "input_numeric_router_catalog_entry_id",
    "input_numeric_router_family_spec_id",
)
NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_ORDER_IDENTITY_ANY_OF = (
    "order_ticket",
    "deal_ticket",
)
NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_GEOMETRY_FIELDS = (
    "broker_fill_time_utc",
    "commission",
    "deal_ticket",
    "executed_entry_price",
    "executed_exit_price",
    "executed_lot_size",
    "executed_stop_price",
    "executed_target_price",
    "order_ticket",
    "partial_exit_lifecycle",
    "slippage_price",
    "swap",
)
NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_DIRECT_EXECUTION_IDENTITY_FIELDS = (
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
NUMERIC_ROUTER_SOURCE_PRODUCER_OWNERS = {
    "shadow_logs/strategy_follow_candidates.jsonl": {
        "producer_owner": "src/research_infra/forward_capture.py::build_strategy_follow_candidate_row",
        "route_session_status": "ALIAS_AVAILABLE_FROM_session_or_kill_zone",
    },
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl": {
        "producer_owner": "src/research_infra/live_mechanical_shadow.py::build_strategy_outcome_rows",
        "route_session_status": "PATCHED_PROSPECTIVE_FROM_candidate_or_path_context",
    },
    "shadow_logs/candidate_features_log.jsonl": {
        "producer_owner": "src/components/candidate_features_logger.py::_build_row",
        "route_session_status": "ALIAS_AVAILABLE_FROM_session_tag_or_kill_zone",
    },
    "shadow_logs/candidate_path_follow.jsonl": {
        "producer_owner": "scripts/follow_live_candidate_paths.py::build_follow_row",
        "route_session_status": "PATCHED_PROSPECTIVE_FROM_candidate_context",
    },
    "shadow_logs/candidate_ltf_path_order.jsonl": {
        "producer_owner": "src/research_infra/live_shadow_gap_closure.py::base_row",
        "route_session_status": "PATCHED_PROSPECTIVE_FROM_candidate_context",
    },
    "shadow_logs/fvg_ob_confluence.jsonl": {
        "producer_owner": "src/research_infra/forward_capture.py::build_fvg_ob_confluence_row",
        "route_session_status": "ALIAS_AVAILABLE_FROM_session_or_kill_zone",
    },
    "shadow_logs/fvg_ob_confluence_audit.jsonl": {
        "producer_owner": "src/research_infra/fvg_ob_confluence_audit.py::build_fvg_ob_confluence_audit_rows",
        "route_session_status": "ALIAS_AVAILABLE_FROM_session_or_kill_zone",
    },
}


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def numeric_router_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "main_side_research_compiler",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def compact_scope_system_decision(
    row: dict[str, Any],
    *,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    return {
        "scope_system_decision_row_id": row.get("scope_system_decision_row_id"),
        "input_scope_router_decision_row_id": row.get("input_scope_router_decision_row_id"),
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "implementation_candidate_type": row.get("implementation_candidate_type"),
        "router_scope_decision": row.get("router_scope_decision"),
        "row_count": row.get("row_count"),
        "score_count": row.get("score_count"),
        "score_min": row.get("score_min"),
        "score_mean": row.get("score_mean"),
        "score_max": row.get("score_max"),
        "scorer_event_count": row.get("scorer_event_count"),
        "avoid_inverse_event_count": row.get("avoid_inverse_event_count"),
        "context_stress_event_count": row.get("context_stress_event_count"),
        "source_repair_event_count": row.get("source_repair_event_count"),
        "source_manifest_hash": row.get("source_manifest_hash"),
        "summary_only_terminal": bool(row.get("summary_only_terminal")),
        "not_completion": bool(row.get("not_completion")),
        "live_effect": False,
        "runtime_score_allowed": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "live_effect": False,
            "outcome_review_opened": False,
            "validation_safe": False,
        },
        "research_boundary": numeric_router_boundary(),
    }


def compact_system_recommendation(
    row: dict[str, Any],
    *,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    return {
        "system_recommendation_row_id": row.get("system_recommendation_row_id"),
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "system_recommendation": row.get("system_recommendation"),
        "scope_decision_counts": row.get("scope_decision_counts") or {},
        "scope_system_decision_rows": row.get("scope_system_decision_rows"),
        "scorer_registry_surface_rows": row.get("scorer_registry_surface_rows"),
        "avoid_comparator_score_rows": row.get("avoid_comparator_score_rows"),
        "context_guard_input_rows": row.get("context_guard_input_rows"),
        "source_repair_proof_rows": row.get("source_repair_proof_rows"),
        "next_same_resource_layer": row.get("next_same_resource_layer"),
        "source_manifest_hash": row.get("source_manifest_hash"),
        "not_completion": bool(row.get("not_completion")),
        "not_terminal": bool(row.get("not_terminal")),
        "live_effect": False,
        "safe_flags": {
            "NO_PROMOTION_VERDICT": True,
            "live_effect": False,
            "outcome_review_opened": False,
            "validation_safe": False,
        },
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def compact_numeric_router_output_row(
    row: dict[str, Any],
    *,
    output_family: str,
    output_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    return {
        "numeric_router_output_row_id": output_row_id,
        "output_family": output_family,
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "source_row": row,
        "source_row_keys": sorted(row.keys()),
        "live_effect": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_scope_system_decisions(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "router_scope_decision_counts": dict(
            sorted(Counter(normalized(row.get("router_scope_decision")) for row in rows).items())
        ),
        "implementation_candidate_type_counts": dict(
            sorted(Counter(normalized(row.get("implementation_candidate_type")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "row_count_sum": sum(int(row.get("row_count") or 0) for row in rows),
        "score_count_sum": sum(int(row.get("score_count") or 0) for row in rows),
        "scorer_event_count_sum": sum(int(row.get("scorer_event_count") or 0) for row in rows),
        "avoid_inverse_event_count_sum": sum(int(row.get("avoid_inverse_event_count") or 0) for row in rows),
        "context_stress_event_count_sum": sum(int(row.get("context_stress_event_count") or 0) for row in rows),
        "source_repair_event_count_sum": sum(int(row.get("source_repair_event_count") or 0) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "summary_only_terminal_rows": sum(bool(row.get("summary_only_terminal")) for row in rows),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
    }


def summarize_numeric_router_output_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "output_family_counts": dict(sorted(Counter(normalized(row.get("output_family")) for row in rows).items())),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_action_from_output_row(row: dict[str, Any]) -> str:
    source_row = row.get("source_row") or {}
    family = normalized(row.get("output_family"))
    if family == "scorer_registry_surface":
        return normalized(source_row.get("registry_surface_status")) or "DEFAULT_OFF_SCORER_SURFACE_REVIEW_REQUIRED"
    if family == "avoid_comparator_score":
        return normalized(source_row.get("avoid_comparator_action")) or "AVOID_COMPARATOR_REVIEW_REQUIRED"
    if family == "context_guard_input":
        return normalized(source_row.get("context_guard_decision")) or "CONTEXT_GUARD_REVIEW_REQUIRED"
    if family == "source_repair_proof":
        return normalized(source_row.get("source_repair_system_decision")) or "SOURCE_REPAIR_REVIEW_REQUIRED"
    return "NUMERIC_ROUTER_OUTPUT_FAMILY_REVIEW_REQUIRED"


def compact_numeric_router_action_queue_row(
    row: dict[str, Any],
    *,
    action_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    source_row = row.get("source_row") or {}
    return {
        "numeric_router_action_row_id": action_row_id,
        "input_numeric_router_output_row_id": row.get("numeric_router_output_row_id"),
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "output_family": row.get("output_family"),
        "numeric_router_action": numeric_router_action_from_output_row(row),
        "symbol": source_row.get("symbol"),
        "route_session": source_row.get("route_session"),
        "horizon_id": source_row.get("horizon_id"),
        "source_component": source_row.get("source_component"),
        "primitive_flag": source_row.get("primitive_flag"),
        "proxy_r_class": source_row.get("proxy_r_class"),
        "target_stop_order_class": source_row.get("target_stop_order_class"),
        "registry_surface_score": source_row.get("registry_surface_score"),
        "avoid_comparator_score": source_row.get("avoid_comparator_score"),
        "missing_field_count": source_row.get("missing_field_count"),
        "repair_action": source_row.get("repair_action"),
        "source_row_id": source_row.get("source_row_id"),
        "source_manifest_hash": source_row.get("source_manifest_hash"),
        "summary_only_terminal": bool(source_row.get("summary_only_terminal")),
        "live_effect": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_action_queue(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "output_family_counts": dict(sorted(Counter(normalized(row.get("output_family")) for row in rows).items())),
        "numeric_router_action_counts": dict(
            sorted(Counter(normalized(row.get("numeric_router_action")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "summary_only_terminal_rows": sum(bool(row.get("summary_only_terminal")) for row in rows),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_family_spec_type(row: dict[str, Any]) -> str:
    family = normalized(row.get("output_family"))
    action = normalized(row.get("numeric_router_action"))
    if family == "scorer_registry_surface":
        return "default_off_scorer_registry_surface_spec"
    if family == "avoid_comparator_score":
        if action == "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE":
            return "avoid_filter_negative_proxy_failure_feature_spec"
        if action == "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY":
            return "avoid_filter_stop_first_proxy_spec"
        if action == "FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY":
            return "avoid_filter_ambiguous_negative_proxy_spec"
        return "avoid_filter_review_required_spec"
    if family == "context_guard_input":
        return "context_stress_guard_input_spec"
    if family == "source_repair_proof":
        if action == "BROKER_EXECUTION_GEOMETRY_REQUIRED_FOR_EXACT_R":
            return "source_repair_broker_execution_geometry_queue_spec"
        if action == "SOURCE_JOIN_REPAIR_REQUIRED_WITH_CURRENT_PACKET_ABSENCE_PROOF":
            return "source_repair_join_absence_proof_queue_spec"
        if action == "BROKER_GEOMETRY_ATTACHMENT_REQUIRED_FOR_EXACT_SPREAD_PROXY":
            return "source_repair_broker_geometry_attachment_queue_spec"
        return "source_repair_review_required_queue_spec"
    return "numeric_router_family_review_required_spec"


def numeric_router_family_implementation_target(family_spec_type: str) -> str:
    if family_spec_type.startswith("default_off_scorer_registry_surface"):
        return "default_off_research_scorer_registry_catalog"
    if family_spec_type.startswith("avoid_filter"):
        return "default_off_avoid_filter_spec_catalog"
    if family_spec_type.startswith("context_stress_guard"):
        return "default_off_context_guard_spec_catalog"
    if family_spec_type.startswith("source_repair"):
        return "source_repair_queue_catalog"
    return "numeric_router_manual_review_catalog"


def _family_spec_group_key(row: dict[str, Any]) -> tuple[str, ...]:
    family_spec_type = numeric_router_family_spec_type(row)
    return (
        normalized(row.get("output_family")),
        family_spec_type,
        normalized(row.get("numeric_router_action")),
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("primitive_flag")),
        normalized(row.get("proxy_r_class")),
        normalized(row.get("target_stop_order_class")),
        normalized(row.get("repair_action")),
        normalized(row.get("missing_field_count")),
    )


def _numeric_stats(rows: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values: list[float] = []
    for row in rows:
        value = row.get(field)
        if isinstance(value, bool) or value is None:
            continue
        if isinstance(value, (int, float)):
            values.append(float(value))
    if not values:
        return {"count": 0, "min": None, "mean": None, "max": None}
    return {
        "count": len(values),
        "min": round(min(values), 6),
        "mean": round(mean(values), 6),
        "max": round(max(values), 6),
    }


def _source_locator_refs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: dict[tuple[str, str], list[int]] = {}
    for row in rows:
        key = (normalized(row.get("source_artifact")), normalized(row.get("source_sha256")))
        refs.setdefault(key, []).append(int(row.get("source_line_no") or 0))

    locators: list[dict[str, Any]] = []
    for (artifact, sha256), line_numbers in sorted(refs.items()):
        positive_lines = [line for line in line_numbers if line > 0]
        locators.append(
            {
                "source_artifact": artifact,
                "source_sha256": sha256,
                "line_count": len(line_numbers),
                "first_line": min(positive_lines) if positive_lines else None,
                "last_line": max(positive_lines) if positive_lines else None,
            }
        )
    return locators


def build_numeric_router_family_action_specs(
    rows: list[dict[str, Any]],
    *,
    spec_id_prefix: str = "MAIN-ORCH48-NUMERIC-ROUTER-FAMILY-SPEC",
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(_family_spec_group_key(row), []).append(row)

    specs: list[dict[str, Any]] = []
    for index, (key, group_rows) in enumerate(sorted(grouped.items()), start=1):
        (
            output_family,
            family_spec_type,
            numeric_router_action,
            symbol,
            route_session,
            horizon_id,
            source_component,
            primitive_flag,
            proxy_r_class,
            target_stop_order_class,
            repair_action,
            missing_field_count,
        ) = key
        action_row_ids = sorted(normalized(row.get("numeric_router_action_row_id")) for row in group_rows)
        source_row_ids = sorted(
            {normalized(row.get("source_row_id")) for row in group_rows if normalized(row.get("source_row_id"))}
        )
        specs.append(
            {
                "numeric_router_family_spec_id": f"{spec_id_prefix}-{index:08d}",
                "schema_version": "main_orch48_numeric_router_family_action_spec_v1",
                "activation_state": "DEFAULT_OFF",
                "output_family": output_family,
                "family_spec_type": family_spec_type,
                "numeric_router_action": numeric_router_action,
                "implementation_target": numeric_router_family_implementation_target(family_spec_type),
                "symbol": symbol,
                "route_session": route_session,
                "horizon_id": horizon_id,
                "source_component": source_component,
                "primitive_flag": primitive_flag,
                "proxy_r_class": proxy_r_class,
                "target_stop_order_class": target_stop_order_class,
                "repair_action": repair_action,
                "missing_field_count": missing_field_count,
                "input_action_rows": len(group_rows),
                "input_action_row_id_first": action_row_ids[0] if action_row_ids else None,
                "input_action_row_id_last": action_row_ids[-1] if action_row_ids else None,
                "source_row_id_sample": source_row_ids[:5],
                "source_locator_refs": _source_locator_refs(group_rows),
                "registry_surface_score_stats": _numeric_stats(group_rows, "registry_surface_score"),
                "avoid_comparator_score_stats": _numeric_stats(group_rows, "avoid_comparator_score"),
                "missing_field_count_stats": _numeric_stats(group_rows, "missing_field_count"),
                "requires_source_guard": True,
                "requires_default_off_registration": output_family
                in {"scorer_registry_surface", "avoid_comparator_score", "context_guard_input"},
                "requires_source_repair_before_exact_r": output_family == "source_repair_proof",
                "promotion_blockers": [
                    "default_off_only",
                    "source_rows_require_review_before_runtime_use",
                    "no_exact_broker_account_r_claim_from_this_artifact",
                ],
                "live_effect": False,
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": numeric_router_boundary(),
            }
        )
    return specs


def summarize_numeric_router_family_action_specs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "output_family_counts": dict(sorted(Counter(normalized(row.get("output_family")) for row in rows).items())),
        "output_family_input_action_counts": dict(
            sorted(
                {
                    family: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("output_family")) == family
                    )
                    for family in {normalized(row.get("output_family")) for row in rows}
                }.items()
            )
        ),
        "family_spec_type_counts": dict(
            sorted(Counter(normalized(row.get("family_spec_type")) for row in rows).items())
        ),
        "numeric_router_action_counts": dict(
            sorted(
                {
                    action: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("numeric_router_action")) == action
                    )
                    for action in {normalized(row.get("numeric_router_action")) for row in rows}
                }.items()
            )
        ),
        "implementation_target_counts": dict(
            sorted(Counter(normalized(row.get("implementation_target")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_catalog_type(row: dict[str, Any]) -> str:
    target = normalized(row.get("implementation_target"))
    if target == "default_off_research_scorer_registry_catalog":
        return "default_off_scorer_registry_catalog_entry"
    if target == "default_off_avoid_filter_spec_catalog":
        return "default_off_avoid_filter_catalog_entry"
    if target == "default_off_context_guard_spec_catalog":
        return "default_off_context_guard_catalog_entry"
    if target == "source_repair_queue_catalog":
        return "source_repair_queue_entry"
    return "numeric_router_manual_review_catalog_entry"


def numeric_router_catalog_priority_bucket(row: dict[str, Any]) -> str:
    action = normalized(row.get("numeric_router_action"))
    family_spec_type = normalized(row.get("family_spec_type"))
    if family_spec_type.startswith("source_repair_broker_execution_geometry"):
        return "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY"
    if family_spec_type.startswith("source_repair_join_absence"):
        return "P0_SOURCE_REPAIR_JOIN_ABSENCE_PROOF"
    if family_spec_type.startswith("source_repair_broker_geometry_attachment"):
        return "P0_SOURCE_REPAIR_SPREAD_GEOMETRY_ATTACHMENT"
    if action == "FAIL_CLOSED_OR_DOWNWEIGHT_AMBIGUOUS_NEGATIVE_PROXY":
        return "P1_AVOID_AMBIGUOUS_NEGATIVE_PROXY_FAIL_CLOSED"
    if action == "AVOID_CURRENT_ENTRY_STOP_FIRST_PROXY":
        return "P1_AVOID_STOP_FIRST_PROXY"
    if action == "REGISTER_NEGATIVE_PROXY_FAILURE_FEATURE":
        return "P2_AVOID_NEGATIVE_PROXY_FAILURE_FEATURE"
    if action == "DEFAULT_OFF_SCORER_SURFACE_READY_WITH_SOURCE_GUARDS":
        return "P3_SCORER_DEFAULT_OFF_SURFACE"
    if action == "MERGE_AS_CONTEXT_STRESS_GUARD_INPUT":
        return "P4_CONTEXT_STRESS_GUARD_INPUT"
    return "P9_MANUAL_REVIEW_REQUIRED"


def numeric_router_catalog_priority_rank(priority_bucket: str) -> int:
    prefix = priority_bucket.split("_", 1)[0]
    if prefix.startswith("P") and prefix[1:].isdigit():
        return int(prefix[1:])
    return 9


def build_numeric_router_catalog_entries(
    rows: list[dict[str, Any]],
    *,
    entry_id_prefix: str = "MAIN-ORCH48-NUMERIC-ROUTER-CATALOG-ENTRY",
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    sorted_rows = sorted(
        rows,
        key=lambda row: (
            numeric_router_catalog_priority_rank(numeric_router_catalog_priority_bucket(row)),
            -int(row.get("input_action_rows") or 0),
            normalized(row.get("implementation_target")),
            normalized(row.get("numeric_router_family_spec_id")),
        ),
    )
    for index, row in enumerate(sorted_rows, start=1):
        priority_bucket = numeric_router_catalog_priority_bucket(row)
        catalog_type = numeric_router_catalog_type(row)
        entries.append(
            {
                "numeric_router_catalog_entry_id": f"{entry_id_prefix}-{index:08d}",
                "schema_version": "main_orch48_numeric_router_implementation_catalog_entry_v1",
                "input_numeric_router_family_spec_id": row.get("numeric_router_family_spec_id"),
                "catalog_type": catalog_type,
                "catalog_priority_bucket": priority_bucket,
                "catalog_priority_rank": numeric_router_catalog_priority_rank(priority_bucket),
                "catalog_priority_weight": int(row.get("input_action_rows") or 0),
                "catalog_entry_status": "READY_FOR_SOURCE_REPAIR_QUEUE"
                if catalog_type == "source_repair_queue_entry"
                else "READY_FOR_DEFAULT_OFF_CATALOG_REGISTRATION",
                "activation_state": "DEFAULT_OFF",
                "output_family": row.get("output_family"),
                "family_spec_type": row.get("family_spec_type"),
                "numeric_router_action": row.get("numeric_router_action"),
                "implementation_target": row.get("implementation_target"),
                "symbol": row.get("symbol"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "source_component": row.get("source_component"),
                "primitive_flag": row.get("primitive_flag"),
                "proxy_r_class": row.get("proxy_r_class"),
                "target_stop_order_class": row.get("target_stop_order_class"),
                "repair_action": row.get("repair_action"),
                "missing_field_count": row.get("missing_field_count"),
                "input_action_rows": row.get("input_action_rows"),
                "source_locator_refs": row.get("source_locator_refs") or [],
                "registry_surface_score_stats": row.get("registry_surface_score_stats") or {},
                "avoid_comparator_score_stats": row.get("avoid_comparator_score_stats") or {},
                "missing_field_count_stats": row.get("missing_field_count_stats") or {},
                "recommended_next_step": _numeric_router_catalog_recommended_next_step(catalog_type, priority_bucket),
                "live_effect": False,
                "runtime_score_allowed": False,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "unconditional_scalar_use_allowed": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": numeric_router_boundary(),
            }
        )
    return entries


def _numeric_router_catalog_recommended_next_step(catalog_type: str, priority_bucket: str) -> str:
    if catalog_type == "source_repair_queue_entry":
        return "repair_or_join_source_geometry_before_any_exact_r_or_runtime_claim"
    if catalog_type == "default_off_avoid_filter_catalog_entry":
        return "register_default_off_avoid_filter_spec_then_require_sealed_replay_before_runtime_use"
    if catalog_type == "default_off_scorer_registry_catalog_entry":
        return "register_default_off_scorer_surface_then_require_source_guard_and_sealed_replay"
    if catalog_type == "default_off_context_guard_catalog_entry":
        return "register_context_stress_guard_input_then_validate_as_non_decision_context"
    if priority_bucket == "P9_MANUAL_REVIEW_REQUIRED":
        return "manual_review_before_catalog_registration"
    return "catalog_for_default_off_review"


def summarize_numeric_router_catalog_entries(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "catalog_type_counts": dict(sorted(Counter(normalized(row.get("catalog_type")) for row in rows).items())),
        "catalog_priority_bucket_counts": dict(
            sorted(Counter(normalized(row.get("catalog_priority_bucket")) for row in rows).items())
        ),
        "catalog_priority_bucket_input_action_counts": dict(
            sorted(
                {
                    bucket: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("catalog_priority_bucket")) == bucket
                    )
                    for bucket in {normalized(row.get("catalog_priority_bucket")) for row in rows}
                }.items()
            )
        ),
        "implementation_target_counts": dict(
            sorted(Counter(normalized(row.get("implementation_target")) for row in rows).items())
        ),
        "numeric_router_action_counts": dict(
            sorted(
                {
                    action: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("numeric_router_action")) == action
                    )
                    for action in {normalized(row.get("numeric_router_action")) for row in rows}
                }.items()
            )
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def load_numeric_router_catalog_entries(paths: list[Path | str] | tuple[Path | str, ...]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with Path(path).open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def numeric_router_catalog_event_from_entry(entry: dict[str, Any]) -> dict[str, Any]:
    event = {key: entry.get(key) for key in NUMERIC_ROUTER_CATALOG_EVENT_KEYS if normalized(entry.get(key))}
    event.update(
        {
            "event_source_catalog_entry_id": entry.get("numeric_router_catalog_entry_id"),
            "event_source_catalog_type": entry.get("catalog_type"),
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": numeric_router_boundary(),
        }
    )
    return event


def numeric_router_required_event_fields_for_catalog_entry(entry: dict[str, Any]) -> list[str]:
    return [key for key in NUMERIC_ROUTER_CATALOG_EVENT_KEYS if normalized(entry.get(key))]


def numeric_router_catalog_event_contract_for_entry(
    entry: dict[str, Any],
    *,
    contract_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    required_fields = numeric_router_required_event_fields_for_catalog_entry(entry)
    return {
        "contract_row_id": contract_row_id,
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_numeric_router_catalog_entry_id": entry.get("numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": entry.get("input_numeric_router_family_spec_id"),
        "catalog_type": entry.get("catalog_type"),
        "catalog_priority_bucket": entry.get("catalog_priority_bucket"),
        "numeric_router_action": entry.get("numeric_router_action"),
        "implementation_target": entry.get("implementation_target"),
        "symbol": entry.get("symbol"),
        "route_session": entry.get("route_session"),
        "horizon_id": entry.get("horizon_id"),
        "source_component": entry.get("source_component"),
        "primitive_flag": entry.get("primitive_flag"),
        "proxy_r_class": entry.get("proxy_r_class"),
        "target_stop_order_class": entry.get("target_stop_order_class"),
        "repair_action": entry.get("repair_action"),
        "missing_field_count": entry.get("missing_field_count"),
        "input_action_rows": entry.get("input_action_rows"),
        "required_event_fields": required_fields,
        "required_event_field_count": len(required_fields),
        "source_capture_contract_status": "READY_DEFAULT_OFF_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def numeric_router_catalog_event_from_source_row(
    source_row: dict[str, Any],
    *,
    event_row_id: str | None = None,
    source_kind: str = "numeric_router_catalog_source_row",
    source_artifact: str | None = None,
    source_line_no: int | None = None,
    source_sha256: str | None = None,
    required_event_fields: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    required_fields = list(dict.fromkeys(required_event_fields or NUMERIC_ROUTER_CATALOG_EVENT_KEYS))
    event: dict[str, Any] = {}
    missing_required_fields: list[str] = []
    event_field_sources: dict[str, str] = {}
    for field in NUMERIC_ROUTER_CATALOG_EVENT_KEYS:
        value = ""
        source_alias = ""
        for alias in NUMERIC_ROUTER_CATALOG_EVENT_FIELD_ALIASES.get(field, (field,)):
            candidate = normalized(source_row.get(alias))
            if candidate:
                value = candidate
                source_alias = alias
                break
        event[field] = value
        if source_alias:
            event_field_sources[field] = source_alias
        if field in required_fields and not value:
            missing_required_fields.append(field)
    event.update(
        {
            "event_row_id": event_row_id,
            "event_source_kind": source_kind,
            "event_source_artifact": source_artifact,
            "event_source_line_no": source_line_no,
            "event_source_sha256": source_sha256,
            "required_event_fields": required_fields,
            "required_event_field_count": len(required_fields),
            "event_field_sources": event_field_sources,
            "missing_required_fields": missing_required_fields,
            "event_adapter_status": "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_COMPLETE"
            if not missing_required_fields
            else "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_INCOMPLETE",
            "runtime_score_allowed": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": numeric_router_boundary(),
        }
    )
    return event


def numeric_router_catalog_event_from_source_row_with_component_bridge(
    source_row: dict[str, Any],
    *,
    event_row_id: str | None = None,
    source_kind: str = "numeric_router_catalog_source_row",
    source_artifact: str | None = None,
    source_line_no: int | None = None,
    source_sha256: str | None = None,
    required_event_fields: list[str] | tuple[str, ...] | None = None,
    source_component_bridge: dict[str, str] | None = None,
) -> dict[str, Any]:
    event = numeric_router_catalog_event_from_source_row(
        source_row,
        event_row_id=event_row_id,
        source_kind=source_kind,
        source_artifact=source_artifact,
        source_line_no=source_line_no,
        source_sha256=source_sha256,
        required_event_fields=required_event_fields,
    )
    bridge = source_component_bridge or {}
    raw_candidates = [
        normalized(source_row.get(alias))
        for alias in NUMERIC_ROUTER_CATALOG_EVENT_FIELD_ALIASES["source_component"]
        if normalized(source_row.get(alias))
    ]
    explicit_component = normalized(source_row.get("source_component"))
    bridged_component = ""
    bridge_source_value = ""
    bridge_status = "SOURCE_COMPONENT_NOT_PRESENT"
    if explicit_component:
        bridged_component = explicit_component
        bridge_source_value = explicit_component
        bridge_status = "EXPLICIT_NUMERIC_ROUTER_SOURCE_COMPONENT_PRESENT"
    else:
        for value in raw_candidates:
            mapped = normalized(bridge.get(value))
            if mapped:
                bridged_component = mapped
                bridge_source_value = value
                bridge_status = "SOURCE_COMPONENT_BRIDGED_BY_EXPLICIT_MAP"
                break
        if not bridged_component and raw_candidates:
            bridge_source_value = raw_candidates[0]
            bridge_status = "SOURCE_COMPONENT_SEMANTIC_BRIDGE_REQUIRED"
    event["source_component"] = bridged_component
    event_sources = dict(event.get("event_field_sources") or {})
    if bridged_component:
        event_sources["source_component"] = "source_component" if explicit_component else f"bridge:{bridge_source_value}"
    else:
        event_sources.pop("source_component", None)
    required_fields = list(dict.fromkeys(required_event_fields or NUMERIC_ROUTER_CATALOG_EVENT_KEYS))
    missing_required_fields = [field for field in required_fields if not normalized(event.get(field))]
    event.update(
        {
            "event_field_sources": event_sources,
            "raw_source_component_candidates": raw_candidates,
            "source_component_bridge_source_value": bridge_source_value,
            "source_component_bridge_status": bridge_status,
            "missing_required_fields": missing_required_fields,
            "event_adapter_status": "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_COMPLETE"
            if not missing_required_fields
            else "NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT_INCOMPLETE",
        }
    )
    return event


def numeric_router_catalog_entry_matches_event(entry: dict[str, Any], event: dict[str, Any]) -> bool:
    for key in NUMERIC_ROUTER_CATALOG_EVENT_KEYS:
        required_value = normalized(entry.get(key))
        if required_value and normalized(event.get(key)) != required_value:
            return False
    return True


def summarize_numeric_router_catalog_event_contracts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_field_counts: Counter[str] = Counter()
    for row in rows:
        required_field_counts.update(row.get("required_event_fields") or [])
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "catalog_type_counts": dict(sorted(Counter(normalized(row.get("catalog_type")) for row in rows).items())),
        "catalog_priority_bucket_counts": dict(
            sorted(Counter(normalized(row.get("catalog_priority_bucket")) for row in rows).items())
        ),
        "required_event_field_counts": dict(sorted(required_field_counts.items())),
        "min_required_event_field_count": min((int(row.get("required_event_field_count") or 0) for row in rows), default=0),
        "max_required_event_field_count": max((int(row.get("required_event_field_count") or 0) for row in rows), default=0),
        "ready_contract_rows": sum(
            normalized(row.get("source_capture_contract_status"))
            == "READY_DEFAULT_OFF_NUMERIC_ROUTER_CATALOG_EVENT_CONTRACT"
            for row in rows
        ),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_catalog_source_capture_plan_for_adapter_spec(
    adapter_spec_row: dict[str, Any],
    *,
    plan_row_id: str,
    contract_rows_requiring_field: int = 0,
) -> dict[str, Any]:
    required_field = normalized(adapter_spec_row.get("required_event_field"))
    source_path = normalized(adapter_spec_row.get("source_path"))
    resolution = normalized(adapter_spec_row.get("adapter_resolution"))
    owner = NUMERIC_ROUTER_SOURCE_PRODUCER_OWNERS.get(source_path, {})

    if resolution == "DIRECT_FIELD_PRESENT":
        plan_status = "CURRENT_SOURCE_FIELD_DIRECTLY_ADAPTABLE"
        implementation_action = "copy_direct_field_into_default_off_catalog_event"
        source_capture_owner = "current_source_row"
        requires_code_or_upstream_capture = False
    elif resolution == "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING":
        plan_status = "CURRENT_SOURCE_FIELD_ALIAS_ADAPTABLE"
        implementation_action = "map_existing_alias_into_default_off_catalog_event"
        source_capture_owner = "current_source_row_alias"
        requires_code_or_upstream_capture = False
    elif required_field == "route_session":
        plan_status = "PRODUCER_ROUTE_SESSION_CAPTURE_PATCHED_OR_REQUIRED"
        implementation_action = "emit_route_session_from_candidate_session_tag_or_kill_zone_before_catalog_evaluator_use"
        source_capture_owner = owner.get("producer_owner") or "producer_route_session_capture"
        requires_code_or_upstream_capture = True
    elif required_field in NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS:
        plan_status = "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED"
        implementation_action = "attach_field_from_numeric_router_catalog_entry_or_source_capture_selection_scope"
        source_capture_owner = "numeric_router_catalog_entry_scope"
        requires_code_or_upstream_capture = True
    else:
        plan_status = "PRODUCER_FIELD_CAPTURE_REQUIRED"
        implementation_action = "add_upstream_capture_or_source_join_before_catalog_evaluator_use"
        source_capture_owner = owner.get("producer_owner") or "producer_field_capture"
        requires_code_or_upstream_capture = True

    return {
        "source_capture_plan_row_id": plan_row_id,
        "input_adapter_spec_row_id": adapter_spec_row.get("adapter_spec_row_id"),
        "source_path": source_path,
        "producer_owner": owner.get("producer_owner"),
        "producer_route_session_status": owner.get("route_session_status"),
        "source_exists": bool(adapter_spec_row.get("source_exists")),
        "source_rows_scanned": adapter_spec_row.get("source_rows_scanned"),
        "required_event_field": required_field,
        "contract_rows_requiring_field": contract_rows_requiring_field,
        "alias_candidates": adapter_spec_row.get("alias_candidates") or [],
        "alias_presence_counts": adapter_spec_row.get("alias_presence_counts") or {},
        "adapter_resolution": resolution,
        "source_capture_plan_status": plan_status,
        "source_capture_owner": source_capture_owner,
        "implementation_action": implementation_action,
        "requires_code_or_upstream_capture": requires_code_or_upstream_capture,
        "current_log_field_complete": resolution in {"DIRECT_FIELD_PRESENT", "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING"},
        "current_source_can_emit_complete_catalog_event": False,
        "historical_current_log_backfill_possible_without_catalog_scope": resolution
        in {"DIRECT_FIELD_PRESENT", "ALIAS_AVAILABLE_NEEDS_ADAPTER_MAPPING"},
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_catalog_source_capture_plans(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_source: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_source.setdefault(normalized(row.get("source_path")), []).append(row)
    source_summaries = {}
    for source_path, source_rows in sorted(by_source.items()):
        missing = [
            normalized(row.get("required_event_field"))
            for row in source_rows
            if not bool(row.get("current_log_field_complete"))
        ]
        source_summaries[source_path] = {
            "field_rows": len(source_rows),
            "current_log_complete_field_rows": sum(bool(row.get("current_log_field_complete")) for row in source_rows),
            "missing_or_catalog_scope_field_rows": len(missing),
            "missing_or_catalog_scope_fields": missing,
            "current_source_can_emit_complete_catalog_event": False,
            "producer_owner": source_rows[0].get("producer_owner") if source_rows else None,
        }
    return {
        "rows": len(rows),
        "source_count": len(by_source),
        "source_capture_plan_status_counts": dict(
            sorted(Counter(normalized(row.get("source_capture_plan_status")) for row in rows).items())
        ),
        "required_event_field_counts": dict(
            sorted(Counter(normalized(row.get("required_event_field")) for row in rows).items())
        ),
        "contract_rows_requiring_field_sum": sum(int(row.get("contract_rows_requiring_field") or 0) for row in rows),
        "current_log_complete_field_rows": sum(bool(row.get("current_log_field_complete")) for row in rows),
        "requires_code_or_upstream_capture_rows": sum(bool(row.get("requires_code_or_upstream_capture")) for row in rows),
        "current_source_complete_event_sources": sum(
            bool(summary.get("current_source_can_emit_complete_catalog_event"))
            for summary in source_summaries.values()
        ),
        "source_summaries": source_summaries,
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_catalog_scope_event_emitter_contract_for_source(
    *,
    source_path: str,
    source_plan_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    emitter_contract_id: str,
) -> dict[str, Any]:
    plan_by_field = {
        normalized(row.get("required_event_field")): row
        for row in source_plan_rows
        if normalized(row.get("required_event_field"))
    }
    required_counts: Counter[str] = Counter()
    for row in contract_rows:
        required_counts.update(row.get("required_event_fields") or [])
    source_adapter_fields = [
        field
        for field in ("symbol", "route_session", "source_component")
        if required_counts.get(field, 0) > 0
    ]
    catalog_scope_fields = [
        field
        for field in sorted(NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS)
        if required_counts.get(field, 0) > 0
    ]
    direct_fields: list[str] = []
    alias_fields: list[str] = []
    producer_patched_fields: list[str] = []
    missing_source_fields: list[str] = []
    source_adapter_status_by_field: dict[str, str] = {}
    for field in source_adapter_fields:
        plan = plan_by_field.get(field, {})
        status = normalized(plan.get("source_capture_plan_status"))
        source_adapter_status_by_field[field] = status
        if status == "CURRENT_SOURCE_FIELD_DIRECTLY_ADAPTABLE":
            direct_fields.append(field)
        elif status == "CURRENT_SOURCE_FIELD_ALIAS_ADAPTABLE":
            alias_fields.append(field)
        elif status == "PRODUCER_ROUTE_SESSION_CAPTURE_PATCHED_OR_REQUIRED":
            producer_patched_fields.append(field)
        else:
            missing_source_fields.append(field)
    catalog_scope_attachment_fields = [
        field
        for field in catalog_scope_fields
        if normalized(plan_by_field.get(field, {}).get("source_capture_plan_status"))
        == "NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_REQUIRED"
    ]
    source_adapter_prospectively_complete = not missing_source_fields
    historical_current_log_complete = source_adapter_prospectively_complete and not producer_patched_fields
    catalog_scope_attachment_complete = set(catalog_scope_fields).issubset(catalog_scope_attachment_fields)
    ready = source_adapter_prospectively_complete and catalog_scope_attachment_complete
    if ready:
        status = "READY_DEFAULT_OFF_CATALOG_SCOPE_EVENT_EMITTER_CONTRACT"
    elif not catalog_scope_attachment_complete:
        status = "BLOCKED_MISSING_CATALOG_SCOPE_ATTACHMENT_RULE"
    else:
        status = "BLOCKED_MISSING_SOURCE_ADAPTER_FIELD"
    return {
        "emitter_contract_id": emitter_contract_id,
        "schema_version": "main_orch48_numeric_router_catalog_scope_event_emitter_contract_v1",
        "source_path": normalized(source_path),
        "producer_owner": NUMERIC_ROUTER_SOURCE_PRODUCER_OWNERS.get(normalized(source_path), {}).get("producer_owner"),
        "input_source_plan_rows": len(source_plan_rows),
        "input_catalog_contract_rows": len(contract_rows),
        "catalog_contract_rows_requiring_scope_attachment": sum(
            any(field in NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS for field in (row.get("required_event_fields") or []))
            for row in contract_rows
        ),
        "source_adapter_fields": source_adapter_fields,
        "source_adapter_status_by_field": source_adapter_status_by_field,
        "direct_source_fields": direct_fields,
        "alias_source_fields": alias_fields,
        "producer_patched_source_fields": producer_patched_fields,
        "missing_source_adapter_fields": missing_source_fields,
        "catalog_scope_attachment_fields": catalog_scope_attachment_fields,
        "catalog_scope_attachment_field_counts": {
            field: int(required_counts.get(field, 0)) for field in catalog_scope_fields
        },
        "source_adapter_prospectively_complete": source_adapter_prospectively_complete,
        "historical_current_log_complete_after_catalog_attachment": historical_current_log_complete,
        "catalog_scope_attachment_complete": catalog_scope_attachment_complete,
        "event_emitter_contract_status": status,
        "event_emitter_action": "adapt_source_fields_then_attach_catalog_scope_fields_before_default_off_catalog_evaluator",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def numeric_router_catalog_event_from_source_row_with_catalog_attachment(
    source_row: dict[str, Any],
    contract_row: dict[str, Any],
    *,
    event_row_id: str | None = None,
    source_kind: str = "numeric_router_catalog_source_row",
    source_artifact: str | None = None,
    source_line_no: int | None = None,
    source_sha256: str | None = None,
) -> dict[str, Any]:
    required_fields = list(dict.fromkeys(contract_row.get("required_event_fields") or []))
    source_required_fields = [
        field for field in required_fields if field not in NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS
    ]
    event = numeric_router_catalog_event_from_source_row(
        source_row,
        event_row_id=event_row_id,
        source_kind=source_kind,
        source_artifact=source_artifact,
        source_line_no=source_line_no,
        source_sha256=source_sha256,
        required_event_fields=source_required_fields,
    )
    source_mismatches = []
    for field in source_required_fields:
        expected = normalized(contract_row.get(field))
        observed = normalized(event.get(field))
        if expected and observed and expected != observed:
            source_mismatches.append({"field": field, "source_value": observed, "catalog_contract_value": expected})
    attached_fields: list[str] = []
    attached_sources: dict[str, str] = {}
    if not event.get("missing_required_fields") and not source_mismatches:
        for field in sorted(NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS):
            if field not in required_fields:
                continue
            value = normalized(contract_row.get(field))
            if not value:
                continue
            event[field] = value
            attached_fields.append(field)
            attached_sources[field] = normalized(contract_row.get("contract_row_id"))
    missing_full_fields = [field for field in required_fields if not normalized(event.get(field))]
    if source_mismatches:
        status = "NUMERIC_ROUTER_CATALOG_EVENT_SOURCE_SCOPE_MISMATCH"
    elif missing_full_fields:
        status = "NUMERIC_ROUTER_CATALOG_EVENT_INCOMPLETE_AFTER_CATALOG_SCOPE_ATTACHMENT"
    else:
        status = "NUMERIC_ROUTER_CATALOG_EVENT_COMPLETE_AFTER_CATALOG_SCOPE_ATTACHMENT"
    event.update(
        {
            "input_contract_row_id": contract_row.get("contract_row_id"),
            "input_numeric_router_catalog_entry_id": contract_row.get("input_numeric_router_catalog_entry_id"),
            "source_required_fields": source_required_fields,
            "catalog_scope_attached_fields": attached_fields,
            "catalog_scope_attachment_field_sources": attached_sources,
            "source_contract_mismatches": source_mismatches,
            "required_event_fields": required_fields,
            "required_event_field_count": len(required_fields),
            "missing_required_fields": missing_full_fields,
            "event_adapter_status": status,
            "catalog_scope_attachment_status": status,
            "runtime_score_allowed": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": numeric_router_boundary(),
        }
    )
    return event


def summarize_numeric_router_catalog_scope_event_emitter_contracts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    catalog_scope_field_counts: Counter[str] = Counter()
    source_adapter_field_counts: Counter[str] = Counter()
    for row in rows:
        catalog_scope_field_counts.update(row.get("catalog_scope_attachment_fields") or [])
        source_adapter_field_counts.update(row.get("source_adapter_fields") or [])
    return {
        "rows": len(rows),
        "source_count": len({normalized(row.get("source_path")) for row in rows}),
        "input_catalog_contract_rows_max": max((int(row.get("input_catalog_contract_rows") or 0) for row in rows), default=0),
        "event_emitter_contract_status_counts": dict(
            sorted(Counter(normalized(row.get("event_emitter_contract_status")) for row in rows).items())
        ),
        "source_adapter_prospectively_complete_rows": sum(
            bool(row.get("source_adapter_prospectively_complete")) for row in rows
        ),
        "historical_current_log_complete_after_catalog_attachment_rows": sum(
            bool(row.get("historical_current_log_complete_after_catalog_attachment")) for row in rows
        ),
        "catalog_scope_attachment_complete_rows": sum(
            bool(row.get("catalog_scope_attachment_complete")) for row in rows
        ),
        "catalog_scope_attachment_field_source_rows": dict(sorted(catalog_scope_field_counts.items())),
        "source_adapter_field_source_rows": dict(sorted(source_adapter_field_counts.items())),
        "producer_patched_source_rows": sum(bool(row.get("producer_patched_source_fields")) for row in rows),
        "missing_source_adapter_field_rows": sum(bool(row.get("missing_source_adapter_fields")) for row in rows),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_contract_source_required_fields(contract_row: dict[str, Any]) -> list[str]:
    return [
        field
        for field in contract_row.get("required_event_fields") or []
        if field not in NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS
    ]


def numeric_router_catalog_event_emitter_dry_run_for_source_rows(
    *,
    source_path: str,
    source_rows: list[dict[str, Any]],
    contract_rows: list[dict[str, Any]],
    dry_run_row_id: str,
) -> dict[str, Any]:
    contract_index: dict[tuple[tuple[str, ...], tuple[str, ...]], list[dict[str, Any]]] = {}
    contracts_requiring_catalog_scope = 0
    for contract in contract_rows:
        required_fields = contract.get("required_event_fields") or []
        if any(field in NUMERIC_ROUTER_CATALOG_SCOPE_ATTACHMENT_FIELDS for field in required_fields):
            contracts_requiring_catalog_scope += 1
        source_fields = tuple(numeric_router_contract_source_required_fields(contract))
        values = tuple(normalized(contract.get(field)) for field in source_fields)
        if not source_fields or any(not value for value in values):
            continue
        contract_index.setdefault((source_fields, values), []).append(contract)

    fieldset_counts: Counter[str] = Counter()
    emitted_event_count = 0
    source_rows_with_contract_match = 0
    matched_contract_ids: set[str] = set()
    adapted_field_presence_counts: Counter[str] = Counter()
    source_rows_with_symbol = 0
    source_rows_with_route_session = 0
    source_rows_with_source_component = 0
    for source_row in source_rows:
        event = numeric_router_catalog_event_from_source_row(source_row, required_event_fields=[])
        for field in ("symbol", "route_session", "source_component"):
            if normalized(event.get(field)):
                adapted_field_presence_counts[field] += 1
        if normalized(event.get("symbol")):
            source_rows_with_symbol += 1
        if normalized(event.get("route_session")):
            source_rows_with_route_session += 1
        if normalized(event.get("source_component")):
            source_rows_with_source_component += 1
        row_match_count = 0
        for source_fields, values in contract_index:
            observed = tuple(normalized(event.get(field)) for field in source_fields)
            if observed != values:
                continue
            contracts = contract_index[(source_fields, values)]
            row_match_count += len(contracts)
            emitted_event_count += len(contracts)
            fieldset_counts["|".join(source_fields)] += len(contracts)
            matched_contract_ids.update(str(row.get("contract_row_id")) for row in contracts)
        if row_match_count:
            source_rows_with_contract_match += 1

    return {
        "dry_run_row_id": dry_run_row_id,
        "schema_version": "main_orch48_numeric_router_catalog_event_emitter_current_row_dry_run_v1",
        "source_path": normalized(source_path),
        "source_rows_scanned": len(source_rows),
        "input_catalog_contract_rows": len(contract_rows),
        "catalog_contracts_requiring_scope_attachment": contracts_requiring_catalog_scope,
        "contract_source_key_groups": len(contract_index),
        "adapted_field_presence_counts": dict(sorted(adapted_field_presence_counts.items())),
        "source_rows_with_symbol": source_rows_with_symbol,
        "source_rows_with_route_session": source_rows_with_route_session,
        "source_rows_with_source_component": source_rows_with_source_component,
        "source_rows_with_contract_match_after_catalog_attachment": source_rows_with_contract_match,
        "unique_contracts_matched_after_catalog_attachment": len(matched_contract_ids),
        "emitted_complete_catalog_event_count": emitted_event_count,
        "source_required_fieldset_match_counts": dict(sorted(fieldset_counts.items())),
        "dry_run_status": "CURRENT_ROWS_EMIT_COMPLETE_DEFAULT_OFF_CATALOG_EVENTS"
        if emitted_event_count
        else "CURRENT_ROWS_NO_CATALOG_CONTRACT_MATCH_AFTER_ATTACHMENT",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_catalog_event_emitter_dry_runs(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "source_count": len({normalized(row.get("source_path")) for row in rows}),
        "source_rows_scanned": sum(int(row.get("source_rows_scanned") or 0) for row in rows),
        "input_catalog_contract_rows_max": max((int(row.get("input_catalog_contract_rows") or 0) for row in rows), default=0),
        "dry_run_status_counts": dict(sorted(Counter(normalized(row.get("dry_run_status")) for row in rows).items())),
        "sources_with_contract_match_after_catalog_attachment": sum(
            int(row.get("source_rows_with_contract_match_after_catalog_attachment") or 0) > 0 for row in rows
        ),
        "source_rows_with_contract_match_after_catalog_attachment": sum(
            int(row.get("source_rows_with_contract_match_after_catalog_attachment") or 0) for row in rows
        ),
        "unique_contracts_matched_after_catalog_attachment_max": max(
            (int(row.get("unique_contracts_matched_after_catalog_attachment") or 0) for row in rows),
            default=0,
        ),
        "emitted_complete_catalog_event_count": sum(
            int(row.get("emitted_complete_catalog_event_count") or 0) for row in rows
        ),
        "source_rows_with_symbol": sum(int(row.get("source_rows_with_symbol") or 0) for row in rows),
        "source_rows_with_route_session": sum(int(row.get("source_rows_with_route_session") or 0) for row in rows),
        "source_rows_with_source_component": sum(int(row.get("source_rows_with_source_component") or 0) for row in rows),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_component_bridge_audit_for_source(
    *,
    source_path: str,
    current_source_component_counts: dict[str, int],
    catalog_source_component_counts: dict[str, int],
    bridge_audit_row_id: str,
) -> dict[str, Any]:
    current_values = {normalized(value) for value in current_source_component_counts if normalized(value)}
    catalog_values = {normalized(value) for value in catalog_source_component_counts if normalized(value)}
    exact_match_values = sorted(current_values & catalog_values)
    exact_match_source_rows = sum(int(current_source_component_counts.get(value, 0)) for value in exact_match_values)
    bridge_required_values = sorted(current_values - catalog_values)
    catalog_uncovered_values = sorted(catalog_values - current_values)
    if exact_match_values:
        status = "SOURCE_COMPONENT_HAS_EXACT_MATCHES_AND_REQUIRES_REVIEW_FOR_REMAINING_VALUES"
    else:
        status = "SOURCE_COMPONENT_SEMANTIC_BRIDGE_REQUIRED_BEFORE_EVENT_MATCH"
    return {
        "bridge_audit_row_id": bridge_audit_row_id,
        "schema_version": "main_orch48_numeric_router_source_component_bridge_audit_v1",
        "source_path": normalized(source_path),
        "current_source_component_counts": dict(sorted(current_source_component_counts.items())),
        "catalog_source_component_counts": dict(sorted(catalog_source_component_counts.items())),
        "current_source_component_distinct_count": len(current_values),
        "catalog_source_component_distinct_count": len(catalog_values),
        "exact_match_values": exact_match_values,
        "exact_match_value_count": len(exact_match_values),
        "exact_match_source_rows": exact_match_source_rows,
        "bridge_required_values": bridge_required_values,
        "bridge_required_value_count": len(bridge_required_values),
        "catalog_uncovered_values": catalog_uncovered_values,
        "catalog_uncovered_value_count": len(catalog_uncovered_values),
        "source_component_bridge_status": status,
        "bridge_action": "create_explicit_source_component_mapping_before_catalog_event_emission",
        "semantic_guardrail": "do_not_treat_framework_strategy_family_or_source_file_aliases_as_numeric_router_source_component_without_explicit_bridge",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_component_bridge_audits(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(normalized(row.get("source_component_bridge_status")) for row in rows)
    exact_values: set[str] = set()
    bridge_required_values: set[str] = set()
    catalog_uncovered_values: set[str] = set()
    for row in rows:
        exact_values.update(row.get("exact_match_values") or [])
        bridge_required_values.update(row.get("bridge_required_values") or [])
        catalog_uncovered_values.update(row.get("catalog_uncovered_values") or [])
    return {
        "rows": len(rows),
        "source_count": len({normalized(row.get("source_path")) for row in rows}),
        "source_component_bridge_status_counts": dict(sorted(status_counts.items())),
        "sources_requiring_semantic_bridge": sum(
            normalized(row.get("source_component_bridge_status"))
            == "SOURCE_COMPONENT_SEMANTIC_BRIDGE_REQUIRED_BEFORE_EVENT_MATCH"
            for row in rows
        ),
        "sources_with_exact_match_values": sum(bool(row.get("exact_match_values")) for row in rows),
        "global_exact_match_values": sorted(exact_values),
        "global_bridge_required_values": sorted(bridge_required_values),
        "global_catalog_uncovered_values": sorted(catalog_uncovered_values),
        "global_exact_match_value_count": len(exact_values),
        "global_bridge_required_value_count": len(bridge_required_values),
        "global_catalog_uncovered_value_count": len(catalog_uncovered_values),
        "exact_match_source_rows": sum(int(row.get("exact_match_source_rows") or 0) for row in rows),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_plan_kind(entry: dict[str, Any]) -> str:
    bucket = normalized(entry.get("catalog_priority_bucket"))
    if bucket == "P0_SOURCE_REPAIR_EXACT_R_GEOMETRY":
        return "broker_execution_geometry_exact_r_repair_plan"
    if bucket == "P0_SOURCE_REPAIR_JOIN_ABSENCE_PROOF":
        return "source_join_absence_proof_repair_plan"
    if bucket == "P0_SOURCE_REPAIR_SPREAD_GEOMETRY_ATTACHMENT":
        return "broker_spread_geometry_attachment_repair_plan"
    return "source_repair_manual_review_plan"


def numeric_router_source_repair_required_source_class(plan_kind: str) -> str:
    if plan_kind == "broker_execution_geometry_exact_r_repair_plan":
        return "broker_execution_geometry_fields"
    if plan_kind == "source_join_absence_proof_repair_plan":
        return "source_join_keys_or_original_packet_rows"
    if plan_kind == "broker_spread_geometry_attachment_repair_plan":
        return "broker_spread_or_quote_geometry_fields"
    return "manual_source_review"


def numeric_router_source_repair_offline_action(plan_kind: str) -> str:
    if plan_kind == "broker_execution_geometry_exact_r_repair_plan":
        return "join_existing_or_future_broker_execution_geometry_before_exact_r_reconstruction"
    if plan_kind == "source_join_absence_proof_repair_plan":
        return "repair_source_join_keys_or_preserve_absence_proof_until_source_packet_exists"
    if plan_kind == "broker_spread_geometry_attachment_repair_plan":
        return "attach_broker_spread_or_quote_geometry_before_exact_spread_proxy_use"
    return "manual_source_repair_review"


def numeric_router_source_repair_execution_plan_for_entry(
    entry: dict[str, Any],
    *,
    plan_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    plan_kind = numeric_router_source_repair_plan_kind(entry)
    return {
        "source_repair_plan_row_id": plan_row_id,
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_numeric_router_catalog_entry_id": entry.get("numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": entry.get("input_numeric_router_family_spec_id"),
        "catalog_priority_bucket": entry.get("catalog_priority_bucket"),
        "numeric_router_action": entry.get("numeric_router_action"),
        "implementation_target": entry.get("implementation_target"),
        "symbol": entry.get("symbol"),
        "route_session": entry.get("route_session"),
        "horizon_id": entry.get("horizon_id"),
        "source_component": entry.get("source_component"),
        "primitive_flag": entry.get("primitive_flag"),
        "proxy_r_class": entry.get("proxy_r_class"),
        "repair_action": entry.get("repair_action"),
        "missing_field_count": entry.get("missing_field_count"),
        "input_action_rows": entry.get("input_action_rows"),
        "source_locator_refs": entry.get("source_locator_refs") or [],
        "source_repair_plan_kind": plan_kind,
        "required_source_class": numeric_router_source_repair_required_source_class(plan_kind),
        "offline_repair_action": numeric_router_source_repair_offline_action(plan_kind),
        "plan_execution_status": "READY_OFFLINE_SOURCE_REPAIR_PLAN",
        "requires_source_join_before_exact_r": True,
        "requires_broker_operation_now": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_execution_plans(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "source_repair_plan_kind_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_plan_kind")) for row in rows).items())
        ),
        "source_repair_plan_kind_input_action_counts": dict(
            sorted(
                {
                    kind: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("source_repair_plan_kind")) == kind
                    )
                    for kind in {normalized(row.get("source_repair_plan_kind")) for row in rows}
                }.items()
            )
        ),
        "required_source_class_counts": dict(
            sorted(Counter(normalized(row.get("required_source_class")) for row in rows).items())
        ),
        "catalog_priority_bucket_counts": dict(
            sorted(Counter(normalized(row.get("catalog_priority_bucket")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "ready_plan_rows": sum(
            normalized(row.get("plan_execution_status")) == "READY_OFFLINE_SOURCE_REPAIR_PLAN" for row in rows
        ),
        "requires_broker_operation_now_rows": sum(bool(row.get("requires_broker_operation_now")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_slippage_join_status(plan: dict[str, Any]) -> str:
    required_source_class = normalized(plan.get("required_source_class"))
    if required_source_class in {"broker_execution_geometry_fields", "broker_spread_or_quote_geometry_fields"}:
        return "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT"
    if required_source_class == "source_join_keys_or_original_packet_rows":
        return "NOT_SLIPPAGE_JOIN_APPLICABLE_SOURCE_PACKET_REQUIRED"
    return "SOURCE_REPAIR_SLIPPAGE_JOIN_MANUAL_REVIEW_REQUIRED"


def numeric_router_source_repair_slippage_identity_key(row: dict[str, Any]) -> str:
    values = [normalized(row.get(field)) for field in NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_FIELDS]
    if not all(values):
        return ""
    return "|".join(values)


def _source_repair_slippage_value_present(value: Any) -> bool:
    return bool(str(value).strip()) if value is not None else False


def _source_repair_slippage_order_identity_present(value: Any) -> bool:
    if not _source_repair_slippage_value_present(value):
        return False
    try:
        return int(value) > 0
    except (TypeError, ValueError):
        return False


def numeric_router_source_repair_slippage_join_contract_for_plan(
    plan: dict[str, Any],
    *,
    contract_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    join_status = numeric_router_source_repair_slippage_join_status(plan)
    slippage_applicable = join_status == "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT"
    return {
        "slippage_join_contract_row_id": contract_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_join_contract_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_source_repair_plan_row_id": plan.get("source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": plan.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": plan.get("input_numeric_router_family_spec_id"),
        "source_repair_plan_kind": plan.get("source_repair_plan_kind"),
        "required_source_class": plan.get("required_source_class"),
        "catalog_priority_bucket": plan.get("catalog_priority_bucket"),
        "numeric_router_action": plan.get("numeric_router_action"),
        "symbol": plan.get("symbol"),
        "route_session": plan.get("route_session"),
        "horizon_id": plan.get("horizon_id"),
        "source_component": plan.get("source_component"),
        "primitive_flag": plan.get("primitive_flag"),
        "repair_action": plan.get("repair_action"),
        "missing_field_count": plan.get("missing_field_count"),
        "input_action_rows": plan.get("input_action_rows"),
        "slippage_join_contract_status": join_status,
        "slippage_row_identity_binding_required": slippage_applicable,
        "required_source_repair_identity_fields": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_FIELDS)
        if slippage_applicable
        else [],
        "required_order_identity_any_of": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_ORDER_IDENTITY_ANY_OF)
        if slippage_applicable
        else [],
        "required_slippage_geometry_fields": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_GEOMETRY_FIELDS)
        if slippage_applicable
        else [],
        "slippage_schema_contract_version": "numeric_router_source_repair_geometry_v1"
        if slippage_applicable
        else None,
        "source_repair_identity_key": numeric_router_source_repair_slippage_identity_key(
            {
                "source_repair_plan_row_id": plan.get("source_repair_plan_row_id"),
                "input_numeric_router_catalog_entry_id": plan.get("input_numeric_router_catalog_entry_id"),
                "input_numeric_router_family_spec_id": plan.get("input_numeric_router_family_spec_id"),
            }
        ),
        "current_historical_slippage_rows_bound_to_contract": 0,
        "exact_r_repaired_by_this_contract": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def numeric_router_source_repair_slippage_join_event_from_row(
    slippage_row: dict[str, Any],
    contract: dict[str, Any],
    *,
    event_row_id: str | None = None,
) -> dict[str, Any]:
    required_identity_fields = list(contract.get("required_source_repair_identity_fields") or [])
    missing_identity_fields = [
        field for field in required_identity_fields if not _source_repair_slippage_value_present(slippage_row.get(field))
    ]
    order_identity_any_of = list(contract.get("required_order_identity_any_of") or [])
    captured_order_identity_fields = [
        field for field in order_identity_any_of if _source_repair_slippage_order_identity_present(slippage_row.get(field))
    ]
    required_geometry_fields = list(contract.get("required_slippage_geometry_fields") or [])
    missing_geometry_fields = [
        field for field in required_geometry_fields if not _source_repair_slippage_value_present(slippage_row.get(field))
    ]
    row_identity_key = normalized(slippage_row.get("source_repair_identity_key"))
    if not row_identity_key:
        row_identity_key = numeric_router_source_repair_slippage_identity_key(slippage_row)
    expected_identity_key = normalized(contract.get("source_repair_identity_key"))

    identity_mismatch = bool(row_identity_key and expected_identity_key and row_identity_key != expected_identity_key)
    if normalized(contract.get("slippage_join_contract_status")) != "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT":
        status = "SOURCE_REPAIR_SLIPPAGE_JOIN_NOT_APPLICABLE_FOR_CONTRACT"
    elif identity_mismatch:
        status = "SOURCE_REPAIR_SLIPPAGE_JOIN_IDENTITY_MISMATCH"
    elif missing_identity_fields or not captured_order_identity_fields:
        status = "SOURCE_REPAIR_SLIPPAGE_JOIN_IDENTITY_INCOMPLETE"
    else:
        status = "SOURCE_REPAIR_SLIPPAGE_JOIN_IDENTITY_COMPLETE"

    return {
        "slippage_join_event_row_id": event_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_join_event_v1",
        "input_slippage_join_contract_row_id": contract.get("slippage_join_contract_row_id"),
        "input_source_repair_plan_row_id": contract.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": contract.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": contract.get("input_numeric_router_family_spec_id"),
        "source_repair_identity_key": row_identity_key,
        "expected_source_repair_identity_key": expected_identity_key,
        "missing_source_repair_identity_fields": missing_identity_fields,
        "required_order_identity_any_of": order_identity_any_of,
        "captured_order_identity_fields": captured_order_identity_fields,
        "missing_slippage_geometry_fields": missing_geometry_fields,
        "captured_slippage_geometry_field_count": len(required_geometry_fields) - len(missing_geometry_fields),
        "slippage_join_event_status": status,
        "exact_r_repaired_by_this_event": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_slippage_join_contracts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "slippage_join_contract_status_counts": dict(
            sorted(Counter(normalized(row.get("slippage_join_contract_status")) for row in rows).items())
        ),
        "slippage_join_contract_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("slippage_join_contract_status")) == status
                    )
                    for status in {normalized(row.get("slippage_join_contract_status")) for row in rows}
                }.items()
            )
        ),
        "source_repair_plan_kind_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_plan_kind")) for row in rows).items())
        ),
        "required_source_class_counts": dict(
            sorted(Counter(normalized(row.get("required_source_class")) for row in rows).items())
        ),
        "slippage_row_identity_binding_required_rows": sum(
            bool(row.get("slippage_row_identity_binding_required")) for row in rows
        ),
        "current_historical_slippage_rows_bound_to_contract": sum(
            int(row.get("current_historical_slippage_rows_bound_to_contract") or 0) for row in rows
        ),
        "exact_r_repaired_by_this_contract_rows": sum(bool(row.get("exact_r_repaired_by_this_contract")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_slippage_identity_adapter_for_contract(
    contract: dict[str, Any],
    *,
    adapter_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    contract_status = normalized(contract.get("slippage_join_contract_status"))
    payload = {
        "source_repair_plan_row_id": contract.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": contract.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": contract.get("input_numeric_router_family_spec_id"),
    }
    payload_key = numeric_router_source_repair_slippage_identity_key(payload)
    ready = (
        contract_status == "READY_PROSPECTIVE_SLIPPAGE_ROW_IDENTITY_JOIN_CONTRACT"
        and bool(payload_key)
        and bool(contract.get("slippage_row_identity_binding_required"))
    )
    if ready:
        adapter_status = "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD"
    elif contract_status == "NOT_SLIPPAGE_JOIN_APPLICABLE_SOURCE_PACKET_REQUIRED":
        adapter_status = "NOT_APPLICABLE_SOURCE_PACKET_REQUIRED"
    else:
        adapter_status = "SOURCE_REPAIR_IDENTITY_ADAPTER_MANUAL_REVIEW_REQUIRED"

    return {
        "slippage_identity_adapter_row_id": adapter_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_identity_adapter_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_slippage_join_contract_row_id": contract.get("slippage_join_contract_row_id"),
        "input_source_repair_plan_row_id": contract.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": contract.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": contract.get("input_numeric_router_family_spec_id"),
        "source_repair_identity_key": payload_key,
        "slippage_join_contract_status": contract_status,
        "slippage_identity_adapter_status": adapter_status,
        "source_repair_identity_payload": payload if ready else None,
        "trade_params_source_repair_identity_patch": {"source_repair_identity": payload} if ready else None,
        "requires_explicit_future_source_repair_row_selection": ready,
        "input_action_rows": contract.get("input_action_rows"),
        "required_order_identity_any_of": list(contract.get("required_order_identity_any_of") or []),
        "required_slippage_geometry_fields": list(contract.get("required_slippage_geometry_fields") or []),
        "exact_r_repaired_by_this_adapter": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def numeric_router_source_repair_slippage_identity_payload_from_adapter(
    adapter: dict[str, Any],
) -> dict[str, Any]:
    if normalized(adapter.get("slippage_identity_adapter_status")) != "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD":
        return {}
    payload = adapter.get("source_repair_identity_payload")
    if not isinstance(payload, dict):
        return {}
    if not numeric_router_source_repair_slippage_identity_key(payload):
        return {}
    return {
        "source_repair_plan_row_id": payload.get("source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": payload.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": payload.get("input_numeric_router_family_spec_id"),
    }


def summarize_numeric_router_source_repair_slippage_identity_adapters(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "slippage_identity_adapter_status_counts": dict(
            sorted(Counter(normalized(row.get("slippage_identity_adapter_status")) for row in rows).items())
        ),
        "slippage_identity_adapter_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("slippage_identity_adapter_status")) == status
                    )
                    for status in {normalized(row.get("slippage_identity_adapter_status")) for row in rows}
                }.items()
            )
        ),
        "payload_ready_rows": sum(
            normalized(row.get("slippage_identity_adapter_status"))
            == "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD"
            for row in rows
        ),
        "trade_params_patch_rows": sum(bool(row.get("trade_params_source_repair_identity_patch")) for row in rows),
        "requires_explicit_future_source_repair_row_selection_rows": sum(
            bool(row.get("requires_explicit_future_source_repair_row_selection")) for row in rows
        ),
        "exact_r_repaired_by_this_adapter_rows": sum(bool(row.get("exact_r_repaired_by_this_adapter")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_slippage_selection_event_from_adapter(
    adapter: dict[str, Any],
    selection_row: dict[str, Any],
    *,
    selection_event_row_id: str | None = None,
) -> dict[str, Any]:
    adapter_status = normalized(adapter.get("slippage_identity_adapter_status"))
    expected_key = normalized(adapter.get("source_repair_identity_key"))
    selected_key = normalized(selection_row.get("source_repair_identity_key"))
    if not selected_key:
        selected_key = numeric_router_source_repair_slippage_identity_key(selection_row)
    payload = numeric_router_source_repair_slippage_identity_payload_from_adapter(adapter)
    ready_adapter = adapter_status == "READY_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_PAYLOAD" and bool(payload)

    if adapter_status == "NOT_APPLICABLE_SOURCE_PACKET_REQUIRED":
        event_status = "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED"
    elif not ready_adapter:
        event_status = "SOURCE_REPAIR_SELECTION_ADAPTER_NOT_READY"
    elif not selected_key:
        event_status = "SOURCE_REPAIR_SELECTION_IDENTITY_MISSING"
    elif selected_key != expected_key:
        event_status = "SOURCE_REPAIR_SELECTION_IDENTITY_MISMATCH"
    else:
        event_status = "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH"

    patch = {"source_repair_identity": payload} if event_status == "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH" else None
    return {
        "slippage_selection_event_row_id": selection_event_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_selection_bridge_v1",
        "input_slippage_identity_adapter_row_id": adapter.get("slippage_identity_adapter_row_id"),
        "input_slippage_join_contract_row_id": adapter.get("input_slippage_join_contract_row_id"),
        "input_source_repair_plan_row_id": adapter.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": adapter.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": adapter.get("input_numeric_router_family_spec_id"),
        "expected_source_repair_identity_key": expected_key,
        "selected_source_repair_identity_key": selected_key,
        "slippage_selection_event_status": event_status,
        "trade_params_source_repair_identity_patch": patch,
        "requires_explicit_future_source_repair_row_selection": ready_adapter,
        "exact_r_repaired_by_this_selection_event": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_slippage_selection_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "slippage_selection_event_status_counts": dict(
            sorted(Counter(normalized(row.get("slippage_selection_event_status")) for row in rows).items())
        ),
        "trade_params_patch_rows": sum(bool(row.get("trade_params_source_repair_identity_patch")) for row in rows),
        "requires_explicit_future_source_repair_row_selection_rows": sum(
            bool(row.get("requires_explicit_future_source_repair_row_selection")) for row in rows
        ),
        "exact_r_repaired_by_this_selection_event_rows": sum(
            bool(row.get("exact_r_repaired_by_this_selection_event")) for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def _source_packet_direct_execution_identity_fields_present(
    *rows: dict[str, Any] | None,
) -> list[str]:
    present: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_DIRECT_EXECUTION_IDENTITY_FIELDS:
            if _source_repair_slippage_value_present(row.get(field)):
                present.add(field)
    return sorted(present)


def numeric_router_source_repair_source_packet_trace_for_proof_row(
    plan: dict[str, Any],
    proof_source_row: dict[str, Any],
    *,
    trace_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
    source_packet_id_field: str,
    original_packet_row: dict[str, Any] | None,
    original_packet_source_artifact: str | None = None,
    original_packet_source_line_no: int | None = None,
    original_packet_source_sha256: str | None = None,
    source_join_packet_row: dict[str, Any] | None,
    source_join_source_artifact: str | None = None,
    source_join_source_line_no: int | None = None,
    source_join_source_sha256: str | None = None,
) -> dict[str, Any]:
    original_found = isinstance(original_packet_row, dict)
    join_found = isinstance(source_join_packet_row, dict)
    identity_fields_present = _source_packet_direct_execution_identity_fields_present(
        original_packet_row,
        source_join_packet_row,
    )

    if not original_found:
        trace_status = "SOURCE_PACKET_TRACE_ORIGINAL_PACKET_MISSING"
    elif not join_found:
        trace_status = "SOURCE_PACKET_TRACE_JOIN_PACKET_MISSING"
    elif identity_fields_present:
        trace_status = "SOURCE_PACKET_TRACE_PACKET_FOUND_DIRECT_EXECUTION_IDENTITY_PRESENT"
    else:
        trace_status = "SOURCE_PACKET_TRACE_COMPLETE_PACKET_FOUND_EXECUTION_IDENTITY_ABSENT"

    source_row_id = proof_source_row.get("source_row_id")
    join_row = source_join_packet_row or {}
    original_row = original_packet_row or {}
    return {
        "source_packet_trace_row_id": trace_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_source_packet_trace_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_source_repair_plan_row_id": plan.get("source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": plan.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": plan.get("input_numeric_router_family_spec_id"),
        "input_numeric_router_source_repair_proof_row_id": proof_source_row.get("source_repair_proof_row_id"),
        "input_numeric_result_row_id": proof_source_row.get("input_numeric_result_row_id"),
        "input_source_repair_execution_row_id": proof_source_row.get("input_source_repair_execution_row_id"),
        "source_component": proof_source_row.get("source_component") or plan.get("source_component"),
        "symbol": proof_source_row.get("symbol") or plan.get("symbol"),
        "route_session": proof_source_row.get("route_session") if proof_source_row.get("route_session") is not None else plan.get("route_session"),
        "horizon_id": proof_source_row.get("horizon_id") or plan.get("horizon_id"),
        "primitive_flag": proof_source_row.get("primitive_flag") or plan.get("primitive_flag"),
        "source_row_id": source_row_id,
        "source_manifest_hash": proof_source_row.get("source_manifest_hash")
        or original_row.get("source_manifest_hash")
        or join_row.get("source_manifest_hash"),
        "source_packet_id_field": source_packet_id_field,
        "original_source_packet_found": original_found,
        "original_source_packet_row_id": original_row.get(source_packet_id_field) if original_found else None,
        "original_source_packet_source_artifact": original_packet_source_artifact,
        "original_source_packet_source_line_no": original_packet_source_line_no,
        "original_source_packet_source_sha256": original_packet_source_sha256,
        "source_join_packet_found": join_found,
        "source_join_packet_row_id": join_row.get(source_packet_id_field) if join_found else None,
        "source_join_packet_source_artifact": source_join_source_artifact,
        "source_join_packet_source_line_no": source_join_source_line_no,
        "source_join_packet_source_sha256": source_join_source_sha256,
        "route_candidate_id": join_row.get("route_candidate_id") or original_row.get("route_candidate_id"),
        "side": join_row.get("side") or original_row.get("side"),
        "target_stop_contract_id": join_row.get("target_stop_contract_id") or original_row.get("target_stop_contract_id"),
        "entry_variant": join_row.get("entry_variant") or original_row.get("entry_variant"),
        "source_entry_variant": join_row.get("source_entry_variant") or original_row.get("source_entry_variant"),
        "target_stop_result": join_row.get("target_stop_result") or original_row.get("target_stop_result"),
        "m1_source_status": join_row.get("m1_source_status") or original_row.get("m1_source_status"),
        "tick_source_status": join_row.get("tick_source_status") or original_row.get("tick_source_status"),
        "exact_spread_context_status": join_row.get("exact_spread_context_status")
        or original_row.get("exact_spread_context_status"),
        "nofill_geometry_context_status": join_row.get("nofill_geometry_context_status")
        or original_row.get("nofill_geometry_context_status"),
        "source_repair_system_decision": proof_source_row.get("source_repair_system_decision"),
        "source_repair_execution_status": proof_source_row.get("source_repair_execution_status"),
        "exact_missing_field_proof": proof_source_row.get("exact_missing_field_proof") or [],
        "direct_execution_identity_fields_present": identity_fields_present,
        "direct_execution_identity_missing_fields": [
            field
            for field in NUMERIC_ROUTER_SOURCE_REPAIR_SOURCE_PACKET_DIRECT_EXECUTION_IDENTITY_FIELDS
            if field not in identity_fields_present
        ],
        "source_packet_trace_status": trace_status,
        "source_packet_trace_repaired_source_absence_proof": original_found and join_found,
        "exact_r_repaired_by_this_trace": False,
        "slippage_join_repaired_by_this_trace": False,
        "requires_prospective_execution_identity_capture": True,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_source_packet_traces(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "source_packet_trace_status_counts": dict(
            sorted(Counter(normalized(row.get("source_packet_trace_status")) for row in rows).items())
        ),
        "source_packet_trace_status_input_rows": dict(
            sorted(
                {
                    status: sum(
                        1
                        for row in rows
                        if normalized(row.get("source_packet_trace_status")) == status
                    )
                    for status in {normalized(row.get("source_packet_trace_status")) for row in rows}
                }.items()
            )
        ),
        "plan_rows": len(
            {
                normalized(row.get("input_source_repair_plan_row_id"))
                for row in rows
                if normalized(row.get("input_source_repair_plan_row_id"))
            }
        ),
        "source_component_counts": dict(
            sorted(Counter(normalized(row.get("source_component")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "route_session_counts": dict(
            sorted(Counter(normalized(row.get("route_session")) for row in rows).items())
        ),
        "original_source_packet_found_rows": sum(bool(row.get("original_source_packet_found")) for row in rows),
        "source_join_packet_found_rows": sum(bool(row.get("source_join_packet_found")) for row in rows),
        "direct_execution_identity_found_rows": sum(
            bool(row.get("direct_execution_identity_fields_present")) for row in rows
        ),
        "source_absence_proof_repaired_rows": sum(
            bool(row.get("source_packet_trace_repaired_source_absence_proof")) for row in rows
        ),
        "exact_r_repaired_by_this_trace_rows": sum(bool(row.get("exact_r_repaired_by_this_trace")) for row in rows),
        "slippage_join_repaired_by_this_trace_rows": sum(bool(row.get("slippage_join_repaired_by_this_trace")) for row in rows),
        "requires_prospective_execution_identity_capture_rows": sum(
            bool(row.get("requires_prospective_execution_identity_capture")) for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_selector_surface_for_selection_event(
    selection_event: dict[str, Any],
    identity_adapter: dict[str, Any] | None,
    source_packet_plan_summary: dict[str, Any] | None,
    *,
    selector_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    selection_status = normalized(selection_event.get("slippage_selection_event_status"))
    adapter = identity_adapter if isinstance(identity_adapter, dict) else {}
    packet_summary = source_packet_plan_summary if isinstance(source_packet_plan_summary, dict) else {}
    packet_plan_status = normalized(packet_summary.get("source_packet_trace_plan_status"))
    trade_params_patch = selection_event.get("trade_params_source_repair_identity_patch")
    input_action_rows = int(adapter.get("input_action_rows") or packet_summary.get("input_action_rows") or 0)

    source_packet_context_payload = None
    if selection_status == "READY_DEFAULT_OFF_TRADE_PARAMS_SOURCE_REPAIR_IDENTITY_PATCH" and trade_params_patch:
        selector_status = "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR"
    elif (
        selection_status == "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED"
        and packet_plan_status == "SOURCE_PACKET_TRACE_PLAN_COMPLETE_EXECUTION_IDENTITY_ABSENT"
    ):
        selector_status = "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT"
        source_packet_context_payload = {
            "source_packet_context_type": "source_join_original_packet_context_without_execution_identity",
            "source_component": packet_summary.get("source_component"),
            "symbol": packet_summary.get("symbol"),
            "route_session": packet_summary.get("route_session"),
            "source_packet_id_field": packet_summary.get("source_packet_id_field"),
            "trace_rows": packet_summary.get("trace_rows"),
            "input_action_rows": packet_summary.get("input_action_rows"),
            "original_source_packet_artifact": packet_summary.get("original_source_packet_artifact"),
            "source_join_packet_artifact": packet_summary.get("source_join_packet_artifact"),
            "direct_execution_identity_found_rows": packet_summary.get("direct_execution_identity_found_rows"),
        }
    elif selection_status == "SOURCE_REPAIR_SELECTION_NOT_APPLICABLE_SOURCE_PACKET_REQUIRED":
        selector_status = "SOURCE_REPAIR_SELECTOR_SOURCE_PACKET_CONTEXT_MISSING"
    else:
        selector_status = "SOURCE_REPAIR_SELECTOR_NOT_READY"

    return {
        "source_repair_selector_surface_row_id": selector_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_selector_surface_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_slippage_selection_event_row_id": selection_event.get("slippage_selection_event_row_id"),
        "input_slippage_identity_adapter_row_id": selection_event.get("input_slippage_identity_adapter_row_id"),
        "input_slippage_join_contract_row_id": selection_event.get("input_slippage_join_contract_row_id"),
        "input_source_repair_plan_row_id": selection_event.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": selection_event.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": selection_event.get("input_numeric_router_family_spec_id"),
        "slippage_selection_event_status": selection_status,
        "slippage_identity_adapter_status": adapter.get("slippage_identity_adapter_status"),
        "source_packet_trace_plan_status": packet_summary.get("source_packet_trace_plan_status"),
        "input_action_rows": input_action_rows,
        "source_repair_selector_surface_status": selector_status,
        "trade_params_source_repair_identity_patch": (
            trade_params_patch
            if selector_status == "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR"
            else None
        ),
        "source_packet_context_payload": source_packet_context_payload,
        "source_repair_selector_payload_type": (
            "trade_params_source_repair_identity"
            if selector_status == "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR"
            else "source_packet_context_without_execution_identity"
            if selector_status == "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT"
            else None
        ),
        "requires_prospective_execution_identity_capture": selector_status
        == "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT",
        "exact_r_repaired_by_this_selector": False,
        "slippage_join_repaired_by_this_selector": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_selector_surfaces(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "source_repair_selector_surface_status_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_selector_surface_status")) for row in rows).items())
        ),
        "source_repair_selector_surface_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("source_repair_selector_surface_status")) == status
                    )
                    for status in {normalized(row.get("source_repair_selector_surface_status")) for row in rows}
                }.items()
            )
        ),
        "trade_params_source_repair_identity_patch_rows": sum(
            bool(row.get("trade_params_source_repair_identity_patch")) for row in rows
        ),
        "trade_params_source_repair_identity_patch_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("trade_params_source_repair_identity_patch")
        ),
        "source_packet_context_payload_rows": sum(bool(row.get("source_packet_context_payload")) for row in rows),
        "source_packet_context_payload_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("source_packet_context_payload")
        ),
        "requires_prospective_execution_identity_capture_rows": sum(
            bool(row.get("requires_prospective_execution_identity_capture")) for row in rows
        ),
        "requires_prospective_execution_identity_capture_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("requires_prospective_execution_identity_capture")
        ),
        "exact_r_repaired_by_this_selector_rows": sum(
            bool(row.get("exact_r_repaired_by_this_selector")) for row in rows
        ),
        "slippage_join_repaired_by_this_selector_rows": sum(
            bool(row.get("slippage_join_repaired_by_this_selector")) for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_selector_event_from_surface(
    selector_surface: dict[str, Any],
    catalog_entry: dict[str, Any] | None,
    *,
    event_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    selector_status = normalized(selector_surface.get("source_repair_selector_surface_status"))
    catalog = catalog_entry if isinstance(catalog_entry, dict) else {}
    expected_catalog_entry_id = normalized(selector_surface.get("input_numeric_router_catalog_entry_id"))
    expected_family_spec_id = normalized(selector_surface.get("input_numeric_router_family_spec_id"))
    catalog_entry_id = normalized(catalog.get("numeric_router_catalog_entry_id"))
    catalog_family_spec_id = normalized(catalog.get("input_numeric_router_family_spec_id"))
    catalog_entry_found = bool(catalog)
    catalog_entry_id_match = bool(expected_catalog_entry_id and catalog_entry_id == expected_catalog_entry_id)
    catalog_family_spec_id_match = bool(
        expected_family_spec_id and catalog_family_spec_id == expected_family_spec_id
    )
    packet_payload = selector_surface.get("source_packet_context_payload")
    packet_payload = packet_payload if isinstance(packet_payload, dict) else {}

    event = {key: catalog.get(key) for key in NUMERIC_ROUTER_CATALOG_EVENT_KEYS if normalized(catalog.get(key))}
    if not event:
        for field in ("symbol", "route_session", "source_component"):
            value = packet_payload.get(field)
            if normalized(value):
                event[field] = value

    if not expected_catalog_entry_id:
        event_status = "SOURCE_REPAIR_SELECTOR_EVENT_MISSING_CATALOG_ENTRY_ID"
    elif not catalog_entry_found or not catalog_entry_id_match:
        event_status = "SOURCE_REPAIR_SELECTOR_EVENT_CATALOG_ENTRY_NOT_FOUND_OR_MISMATCH"
    elif normalized(catalog.get("catalog_type")) != "source_repair_queue_entry":
        event_status = "SOURCE_REPAIR_SELECTOR_EVENT_CATALOG_ENTRY_NOT_SOURCE_REPAIR_QUEUE"
    elif (
        selector_status == "READY_DEFAULT_OFF_SOURCE_REPAIR_EXECUTION_IDENTITY_SELECTOR"
        and selector_surface.get("trade_params_source_repair_identity_patch")
    ):
        event_status = "SOURCE_REPAIR_SELECTOR_EVENT_READY_FOR_DEFAULT_OFF_ROUTER"
    elif selector_status == "READY_DEFAULT_OFF_SOURCE_PACKET_CONTEXT_SELECTOR_EXECUTION_IDENTITY_ABSENT":
        event_status = "SOURCE_REPAIR_SELECTOR_EVENT_PACKET_CONTEXT_READY_FOR_PROSPECTIVE_CAPTURE_ROUTER"
    else:
        event_status = "SOURCE_REPAIR_SELECTOR_EVENT_NOT_READY"

    event_routable = event_status in {
        "SOURCE_REPAIR_SELECTOR_EVENT_READY_FOR_DEFAULT_OFF_ROUTER",
        "SOURCE_REPAIR_SELECTOR_EVENT_PACKET_CONTEXT_READY_FOR_PROSPECTIVE_CAPTURE_ROUTER",
    }
    event.update(
        {
            "source_repair_selector_event_row_id": event_row_id,
            "schema_version": "main_orch48_numeric_router_source_repair_selector_event_v1",
            "source_artifact": source_artifact,
            "source_line_no": source_line_no,
            "source_sha256": source_sha256,
            "input_source_repair_selector_surface_row_id": selector_surface.get(
                "source_repair_selector_surface_row_id"
            ),
            "input_source_repair_plan_row_id": selector_surface.get("input_source_repair_plan_row_id"),
            "input_numeric_router_catalog_entry_id": selector_surface.get("input_numeric_router_catalog_entry_id"),
            "input_numeric_router_family_spec_id": selector_surface.get("input_numeric_router_family_spec_id"),
            "input_slippage_selection_event_row_id": selector_surface.get("input_slippage_selection_event_row_id"),
            "input_slippage_identity_adapter_row_id": selector_surface.get("input_slippage_identity_adapter_row_id"),
            "source_repair_selector_surface_status": selector_status,
            "source_repair_selector_payload_type": selector_surface.get("source_repair_selector_payload_type"),
            "source_repair_selector_event_status": event_status,
            "source_repair_selector_event_routable": event_routable,
            "catalog_entry_found": catalog_entry_found,
            "catalog_entry_id_match": catalog_entry_id_match,
            "catalog_family_spec_id_match": catalog_family_spec_id_match,
            "catalog_type": catalog.get("catalog_type"),
            "catalog_priority_bucket": catalog.get("catalog_priority_bucket"),
            "catalog_priority_rank": catalog.get("catalog_priority_rank"),
            "numeric_router_action": catalog.get("numeric_router_action"),
            "implementation_target": catalog.get("implementation_target"),
            "input_action_rows": selector_surface.get("input_action_rows"),
            "catalog_input_action_rows": catalog.get("input_action_rows"),
            "trade_params_source_repair_identity_patch": selector_surface.get(
                "trade_params_source_repair_identity_patch"
            ),
            "source_packet_context_payload": selector_surface.get("source_packet_context_payload"),
            "requires_prospective_execution_identity_capture": bool(
                selector_surface.get("requires_prospective_execution_identity_capture")
            ),
            "default_catalog_evaluation_would_skip_source_repair": True,
            "include_source_repair_required_for_catalog_evaluation": event_routable,
            "exact_r_repaired_by_this_event": False,
            "slippage_join_repaired_by_this_event": False,
            "runtime_score_allowed": False,
            "runtime_candidate_use_permitted": False,
            "candidate_use_allowed_now": False,
            "unconditional_scalar_use_allowed": False,
            "replay_r_reference_counted_as_new_main_result": False,
            "research_boundary": numeric_router_boundary(),
        }
    )
    return event


def summarize_numeric_router_source_repair_selector_events(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "source_repair_selector_event_status_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_selector_event_status")) for row in rows).items())
        ),
        "source_repair_selector_event_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("source_repair_selector_event_status")) == status
                    )
                    for status in {normalized(row.get("source_repair_selector_event_status")) for row in rows}
                }.items()
            )
        ),
        "source_repair_selector_surface_status_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_selector_surface_status")) for row in rows).items())
        ),
        "catalog_entry_found_rows": sum(bool(row.get("catalog_entry_found")) for row in rows),
        "catalog_entry_id_match_rows": sum(bool(row.get("catalog_entry_id_match")) for row in rows),
        "catalog_family_spec_id_match_rows": sum(bool(row.get("catalog_family_spec_id_match")) for row in rows),
        "event_routable_rows": sum(bool(row.get("source_repair_selector_event_routable")) for row in rows),
        "event_routable_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("source_repair_selector_event_routable")
        ),
        "trade_params_source_repair_identity_patch_rows": sum(
            bool(row.get("trade_params_source_repair_identity_patch")) for row in rows
        ),
        "source_packet_context_payload_rows": sum(bool(row.get("source_packet_context_payload")) for row in rows),
        "requires_prospective_execution_identity_capture_rows": sum(
            bool(row.get("requires_prospective_execution_identity_capture")) for row in rows
        ),
        "exact_r_repaired_by_this_event_rows": sum(bool(row.get("exact_r_repaired_by_this_event")) for row in rows),
        "slippage_join_repaired_by_this_event_rows": sum(
            bool(row.get("slippage_join_repaired_by_this_event")) for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_selector_route_for_event(
    selector_event: dict[str, Any],
    catalog_matches: list[dict[str, Any]],
    *,
    route_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    expected_catalog_entry_id = normalized(selector_event.get("input_numeric_router_catalog_entry_id"))
    source_repair_matches = [
        match for match in catalog_matches if normalized(match.get("catalog_type")) == "source_repair_queue_entry"
    ]
    expected_matches = [
        match
        for match in source_repair_matches
        if normalized(match.get("input_numeric_router_catalog_entry_id")) == expected_catalog_entry_id
    ]
    event_status = normalized(selector_event.get("source_repair_selector_event_status"))

    if event_status == "SOURCE_REPAIR_SELECTOR_EVENT_READY_FOR_DEFAULT_OFF_ROUTER" and expected_matches:
        route_status = "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE"
    elif (
        event_status == "SOURCE_REPAIR_SELECTOR_EVENT_PACKET_CONTEXT_READY_FOR_PROSPECTIVE_CAPTURE_ROUTER"
        and expected_matches
    ):
        route_status = "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
    elif not selector_event.get("source_repair_selector_event_routable"):
        route_status = "SOURCE_REPAIR_SELECTOR_EVENT_NOT_ROUTABLE"
    else:
        route_status = "SOURCE_REPAIR_SELECTOR_ROUTER_EXPECTED_CATALOG_MATCH_MISSING"

    route_ready = route_status in {
        "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE",
        "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE",
    }
    return {
        "source_repair_selector_route_row_id": route_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_selector_router_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_source_repair_selector_event_row_id": selector_event.get("source_repair_selector_event_row_id"),
        "input_source_repair_selector_surface_row_id": selector_event.get(
            "input_source_repair_selector_surface_row_id"
        ),
        "input_source_repair_plan_row_id": selector_event.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": selector_event.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": selector_event.get("input_numeric_router_family_spec_id"),
        "source_repair_selector_surface_status": selector_event.get("source_repair_selector_surface_status"),
        "source_repair_selector_event_status": event_status,
        "source_repair_selector_route_status": route_status,
        "source_repair_selector_payload_type": selector_event.get("source_repair_selector_payload_type"),
        "catalog_match_count": len(catalog_matches),
        "source_repair_queue_match_count": len(source_repair_matches),
        "expected_catalog_entry_match_count": len(expected_matches),
        "matched_catalog_entry_ids": [
            match.get("input_numeric_router_catalog_entry_id") for match in source_repair_matches
        ],
        "matched_numeric_router_actions": sorted(
            {normalized(match.get("numeric_router_action")) for match in source_repair_matches}
        ),
        "catalog_evaluation_include_source_repair": True,
        "default_catalog_evaluation_would_skip_source_repair": True,
        "router_path_ready_default_off": route_ready,
        "trade_params_source_repair_identity_patch": selector_event.get(
            "trade_params_source_repair_identity_patch"
        )
        if route_status == "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE"
        else None,
        "source_packet_context_payload": selector_event.get("source_packet_context_payload")
        if route_status == "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
        else None,
        "requires_prospective_execution_identity_capture": bool(
            selector_event.get("requires_prospective_execution_identity_capture")
        ),
        "input_action_rows": selector_event.get("input_action_rows"),
        "catalog_input_action_rows": selector_event.get("catalog_input_action_rows"),
        "exact_r_repaired_by_this_route": False,
        "slippage_join_repaired_by_this_route": False,
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_selector_routes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "source_repair_selector_route_status_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_selector_route_status")) for row in rows).items())
        ),
        "source_repair_selector_route_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("source_repair_selector_route_status")) == status
                    )
                    for status in {normalized(row.get("source_repair_selector_route_status")) for row in rows}
                }.items()
            )
        ),
        "router_path_ready_default_off_rows": sum(bool(row.get("router_path_ready_default_off")) for row in rows),
        "router_path_ready_default_off_input_action_rows": sum(
            int(row.get("input_action_rows") or 0) for row in rows if row.get("router_path_ready_default_off")
        ),
        "trade_params_source_repair_identity_patch_rows": sum(
            bool(row.get("trade_params_source_repair_identity_patch")) for row in rows
        ),
        "trade_params_source_repair_identity_patch_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("trade_params_source_repair_identity_patch")
        ),
        "source_packet_context_payload_rows": sum(bool(row.get("source_packet_context_payload")) for row in rows),
        "source_packet_context_payload_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("source_packet_context_payload")
        ),
        "requires_prospective_execution_identity_capture_rows": sum(
            bool(row.get("requires_prospective_execution_identity_capture")) for row in rows
        ),
        "requires_prospective_execution_identity_capture_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("requires_prospective_execution_identity_capture")
        ),
        "catalog_matched_rows": sum(int(row.get("catalog_match_count") or 0) > 0 for row in rows),
        "source_repair_queue_matched_rows": sum(
            int(row.get("source_repair_queue_match_count") or 0) > 0 for row in rows
        ),
        "expected_catalog_entry_matched_rows": sum(
            int(row.get("expected_catalog_entry_match_count") or 0) > 0 for row in rows
        ),
        "exact_r_repaired_by_this_route_rows": sum(bool(row.get("exact_r_repaired_by_this_route")) for row in rows),
        "slippage_join_repaired_by_this_route_rows": sum(
            bool(row.get("slippage_join_repaired_by_this_route")) for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def _numeric_router_source_repair_capture_patch_fields(
    capture_patch_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    fields: dict[str, dict[str, Any]] = {}
    for row in capture_patch_rows:
        field = normalized(row.get("missing_field"))
        if field:
            fields[field] = row
    return fields


def numeric_router_source_repair_execution_identity_capture_contract_for_route(
    selector_route: dict[str, Any],
    capture_patch_rows: list[dict[str, Any]],
    *,
    contract_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
    source_repair_queue_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    route_status = normalized(selector_route.get("source_repair_selector_route_status"))
    queue_entry = source_repair_queue_entry if isinstance(source_repair_queue_entry, dict) else {}
    capture_fields_by_name = _numeric_router_source_repair_capture_patch_fields(capture_patch_rows)
    required_geometry_fields = [
        field
        for field in NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_GEOMETRY_FIELDS
        if field in capture_fields_by_name
    ]
    missing_capture_schema_fields = [
        field
        for field in NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_GEOMETRY_FIELDS
        if field not in capture_fields_by_name
    ]

    patch = selector_route.get("trade_params_source_repair_identity_patch")
    patch = patch if isinstance(patch, dict) else {}
    payload = patch.get("source_repair_identity")
    payload = payload if isinstance(payload, dict) else {}
    source_repair_identity_key = numeric_router_source_repair_slippage_identity_key(payload)

    packet_payload = selector_route.get("source_packet_context_payload")
    packet_payload = packet_payload if isinstance(packet_payload, dict) else {}

    source_repair_queue_route_bound = bool(
        selector_route.get("router_path_ready_default_off")
        and int(selector_route.get("source_repair_queue_match_count") or 0) > 0
        and int(selector_route.get("expected_catalog_entry_match_count") or 0) > 0
    )
    capture_schema_bound = not missing_capture_schema_fields
    identity_route = route_status == "ROUTED_DEFAULT_OFF_SOURCE_REPAIR_IDENTITY_SELECTOR_TO_QUEUE"
    packet_route = (
        route_status == "ROUTED_SOURCE_PACKET_CONTEXT_SELECTOR_TO_PROSPECTIVE_EXECUTION_IDENTITY_CAPTURE_QUEUE"
    )

    if not capture_schema_bound:
        contract_status = "EXECUTION_IDENTITY_CAPTURE_CONTRACT_MISSING_CAPTURE_SCHEMA_FIELDS"
    elif identity_route and source_repair_identity_key and source_repair_queue_route_bound:
        contract_status = "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"
    elif packet_route and packet_payload and source_repair_queue_route_bound:
        contract_status = "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
    elif not source_repair_queue_route_bound:
        contract_status = "EXECUTION_IDENTITY_CAPTURE_CONTRACT_SOURCE_REPAIR_QUEUE_ROUTE_NOT_BOUND"
    else:
        contract_status = "EXECUTION_IDENTITY_CAPTURE_CONTRACT_ROUTE_NOT_READY"

    contract_ready = contract_status in {
        "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY",
        "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT",
    }
    input_action_rows = selector_route.get("input_action_rows")
    return {
        "execution_identity_capture_contract_row_id": contract_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_execution_identity_capture_contract_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_source_repair_selector_route_row_id": selector_route.get("source_repair_selector_route_row_id"),
        "input_source_repair_selector_event_row_id": selector_route.get("input_source_repair_selector_event_row_id"),
        "input_source_repair_selector_surface_row_id": selector_route.get(
            "input_source_repair_selector_surface_row_id"
        ),
        "input_source_repair_plan_row_id": selector_route.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": selector_route.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": selector_route.get("input_numeric_router_family_spec_id"),
        "source_repair_selector_route_status": route_status,
        "execution_identity_capture_contract_status": contract_status,
        "symbol": queue_entry.get("symbol") or packet_payload.get("symbol"),
        "route_session": queue_entry.get("route_session") or packet_payload.get("route_session"),
        "horizon_id": queue_entry.get("horizon_id"),
        "source_component": queue_entry.get("source_component") or packet_payload.get("source_component"),
        "repair_action": queue_entry.get("repair_action"),
        "numeric_router_action": queue_entry.get("numeric_router_action"),
        "catalog_priority_bucket": queue_entry.get("catalog_priority_bucket"),
        "source_repair_queue_route_bound": source_repair_queue_route_bound,
        "row_identity_bound_to_numeric_router_source_repair_queue": source_repair_queue_route_bound,
        "capture_patch_fields_bound_to_route": capture_schema_bound,
        "capture_patch_field_count": len(required_geometry_fields),
        "capture_patch_row_ids": [
            capture_fields_by_name[field].get("slippage_capture_patch_row_id")
            for field in required_geometry_fields
        ],
        "missing_capture_schema_fields": missing_capture_schema_fields,
        "required_source_repair_identity_fields": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_FIELDS),
        "required_order_identity_any_of": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_ORDER_IDENTITY_ANY_OF),
        "required_execution_geometry_fields": required_geometry_fields,
        "required_future_slippage_row_fields": list(
            dict.fromkeys(
                list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_FIELDS)
                + list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_ORDER_IDENTITY_ANY_OF)
                + required_geometry_fields
            )
        ),
        "source_repair_identity_key": source_repair_identity_key,
        "source_repair_identity_payload": payload if source_repair_identity_key else None,
        "trade_params_source_repair_identity_patch": patch if source_repair_identity_key else None,
        "source_packet_context_payload": packet_payload or None,
        "source_packet_route_requires_prospective_execution_identity_capture": bool(
            selector_route.get("requires_prospective_execution_identity_capture")
        ),
        "requires_execution_capture_row_for_exact_r": contract_ready,
        "current_historical_slippage_rows_bound_to_contract": 0,
        "exact_r_repaired_by_this_contract": False,
        "slippage_join_repaired_by_this_contract": False,
        "input_action_rows": input_action_rows,
        "materialization_result_scope": "prospective_execution_identity_capture_contract_not_historical_repair",
        "source_operation": "default_off_execution_identity_capture_contract_from_selector_route_and_slippage_schema",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "implementation_effect": {
            "default_off_capture_contract_available": contract_ready,
            "prospective_observability_schema_effect": capture_schema_bound,
            "runtime_logging_schema_effect_if_runtime_reenabled": capture_schema_bound,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_execution_identity_capture_contracts(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = {normalized(row.get("execution_identity_capture_contract_status")) for row in rows}
    geometry_counts = [int(row.get("capture_patch_field_count") or 0) for row in rows]
    return {
        "rows": len(rows),
        "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in rows),
        "execution_identity_capture_contract_status_counts": dict(
            sorted(Counter(normalized(row.get("execution_identity_capture_contract_status")) for row in rows).items())
        ),
        "execution_identity_capture_contract_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("execution_identity_capture_contract_status")) == status
                    )
                    for status in statuses
                }.items()
            )
        ),
        "source_repair_selector_route_status_counts": dict(
            sorted(Counter(normalized(row.get("source_repair_selector_route_status")) for row in rows).items())
        ),
        "source_repair_queue_route_bound_rows": sum(bool(row.get("source_repair_queue_route_bound")) for row in rows),
        "row_identity_bound_to_numeric_router_source_repair_queue_rows": sum(
            bool(row.get("row_identity_bound_to_numeric_router_source_repair_queue")) for row in rows
        ),
        "capture_patch_fields_bound_to_route_rows": sum(
            bool(row.get("capture_patch_fields_bound_to_route")) for row in rows
        ),
        "trade_params_source_repair_identity_patch_rows": sum(
            bool(row.get("trade_params_source_repair_identity_patch")) for row in rows
        ),
        "trade_params_source_repair_identity_patch_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("trade_params_source_repair_identity_patch")
        ),
        "source_repair_identity_key_rows": sum(bool(row.get("source_repair_identity_key")) for row in rows),
        "source_packet_context_payload_rows": sum(bool(row.get("source_packet_context_payload")) for row in rows),
        "source_packet_context_payload_input_action_rows": sum(
            int(row.get("input_action_rows") or 0)
            for row in rows
            if row.get("source_packet_context_payload")
        ),
        "source_packet_route_requires_prospective_execution_identity_capture_rows": sum(
            bool(row.get("source_packet_route_requires_prospective_execution_identity_capture")) for row in rows
        ),
        "requires_execution_capture_row_for_exact_r_rows": sum(
            bool(row.get("requires_execution_capture_row_for_exact_r")) for row in rows
        ),
        "required_execution_geometry_field_count_min": min(geometry_counts) if geometry_counts else 0,
        "required_execution_geometry_field_count_max": max(geometry_counts) if geometry_counts else 0,
        "required_execution_geometry_fields": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_GEOMETRY_FIELDS),
        "required_order_identity_any_of": list(NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_ORDER_IDENTITY_ANY_OF),
        "missing_capture_schema_field_rows": sum(bool(row.get("missing_capture_schema_fields")) for row in rows),
        "current_historical_slippage_rows_bound_to_contract": sum(
            int(row.get("current_historical_slippage_rows_bound_to_contract") or 0) for row in rows
        ),
        "exact_r_repaired_by_this_contract_rows": sum(
            bool(row.get("exact_r_repaired_by_this_contract")) for row in rows
        ),
        "slippage_join_repaired_by_this_contract_rows": sum(
            bool(row.get("slippage_join_repaired_by_this_contract")) for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def numeric_router_source_repair_execution_identity_capture_event_from_slippage_row(
    capture_contract: dict[str, Any],
    slippage_row: dict[str, Any],
    *,
    event_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
    slippage_source_artifact: str,
    slippage_source_line_no: int,
    slippage_source_sha256: str,
) -> dict[str, Any]:
    contract_status = normalized(capture_contract.get("execution_identity_capture_contract_status"))
    expected_identity_key = normalized(capture_contract.get("source_repair_identity_key"))
    row_identity_key = normalized(slippage_row.get("source_repair_identity_key"))
    if not row_identity_key:
        row_identity_key = numeric_router_source_repair_slippage_identity_key(slippage_row)

    required_identity_fields = list(capture_contract.get("required_source_repair_identity_fields") or [])
    missing_identity_fields = [
        field for field in required_identity_fields if not _source_repair_slippage_value_present(slippage_row.get(field))
    ]
    order_identity_any_of = list(capture_contract.get("required_order_identity_any_of") or [])
    captured_order_identity_fields = [
        field for field in order_identity_any_of if _source_repair_slippage_order_identity_present(slippage_row.get(field))
    ]
    required_geometry_fields = list(capture_contract.get("required_execution_geometry_fields") or [])
    missing_geometry_fields = [
        field for field in required_geometry_fields if not _source_repair_slippage_value_present(slippage_row.get(field))
    ]
    identity_mismatch = bool(row_identity_key and expected_identity_key and row_identity_key != expected_identity_key)

    if contract_status == "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT":
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
    elif contract_status != "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY":
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_NOT_READY"
    elif missing_identity_fields or not row_identity_key:
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_SOURCE_REPAIR_IDENTITY_MISSING"
    elif identity_mismatch:
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_SOURCE_REPAIR_IDENTITY_MISMATCH"
    elif not captured_order_identity_fields:
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_ORDER_IDENTITY_MISSING"
    elif missing_geometry_fields:
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_GEOMETRY_INCOMPLETE"
    else:
        event_status = "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_COMPLETE"

    slippage_row_bound = event_status == "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_COMPLETE"
    return {
        "execution_identity_capture_event_row_id": event_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_execution_identity_capture_event_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "slippage_source_artifact": slippage_source_artifact,
        "slippage_source_line_no": slippage_source_line_no,
        "slippage_source_sha256": slippage_source_sha256,
        "input_execution_identity_capture_contract_row_id": capture_contract.get(
            "execution_identity_capture_contract_row_id"
        ),
        "input_source_repair_selector_route_row_id": capture_contract.get(
            "input_source_repair_selector_route_row_id"
        ),
        "input_source_repair_plan_row_id": capture_contract.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": capture_contract.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": capture_contract.get("input_numeric_router_family_spec_id"),
        "input_action_rows": capture_contract.get("input_action_rows"),
        "execution_identity_capture_contract_status": contract_status,
        "execution_identity_capture_event_status": event_status,
        "expected_source_repair_identity_key": expected_identity_key,
        "slippage_row_source_repair_identity_key": row_identity_key,
        "missing_source_repair_identity_fields": missing_identity_fields,
        "required_order_identity_any_of": order_identity_any_of,
        "captured_order_identity_fields": captured_order_identity_fields,
        "missing_execution_geometry_fields": missing_geometry_fields,
        "captured_execution_geometry_field_count": len(required_geometry_fields) - len(missing_geometry_fields),
        "slippage_row_bound_to_contract": slippage_row_bound,
        "slippage_join_repaired_by_this_event": slippage_row_bound,
        "exact_r_repaired_by_this_event": False,
        "slippage_row_ticket": slippage_row.get("ticket"),
        "slippage_row_order_ticket": slippage_row.get("order_ticket") or slippage_row.get("mt5_order_id"),
        "slippage_row_deal_ticket": slippage_row.get("deal_ticket") or slippage_row.get("mt5_deal_id"),
        "slippage_row_symbol": slippage_row.get("symbol"),
        "slippage_event_type": slippage_row.get("slippage_event_type") or slippage_row.get("trigger"),
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_execution_identity_capture_events(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = {normalized(row.get("execution_identity_capture_event_status")) for row in rows}
    contract_ids = {normalized(row.get("input_execution_identity_capture_contract_row_id")) for row in rows}
    slippage_keys = {
        (
            normalized(row.get("slippage_source_artifact")),
            normalized(row.get("slippage_source_line_no")),
        )
        for row in rows
    }
    return {
        "rows": len(rows),
        "unique_contract_rows_checked": len({item for item in contract_ids if item}),
        "unique_slippage_rows_checked": len({item for item in slippage_keys if item[0] and item[1]}),
        "execution_identity_capture_event_status_counts": dict(
            sorted(Counter(normalized(row.get("execution_identity_capture_event_status")) for row in rows).items())
        ),
        "execution_identity_capture_event_status_unique_contract_counts": dict(
            sorted(
                {
                    status: len(
                        {
                            normalized(row.get("input_execution_identity_capture_contract_row_id"))
                            for row in rows
                            if normalized(row.get("execution_identity_capture_event_status")) == status
                        }
                    )
                    for status in statuses
                }.items()
            )
        ),
        "execution_identity_capture_contract_status_counts": dict(
            sorted(Counter(normalized(row.get("execution_identity_capture_contract_status")) for row in rows).items())
        ),
        "slippage_row_bound_to_contract_rows": sum(bool(row.get("slippage_row_bound_to_contract")) for row in rows),
        "slippage_join_repaired_by_this_event_rows": sum(
            bool(row.get("slippage_join_repaired_by_this_event")) for row in rows
        ),
        "exact_r_repaired_by_this_event_rows": sum(bool(row.get("exact_r_repaired_by_this_event")) for row in rows),
        "missing_source_repair_identity_event_rows": sum(
            normalized(row.get("execution_identity_capture_event_status"))
            == "EXECUTION_IDENTITY_CAPTURE_EVENT_SOURCE_REPAIR_IDENTITY_MISSING"
            for row in rows
        ),
        "packet_context_execution_identity_absent_event_rows": sum(
            normalized(row.get("execution_identity_capture_event_status"))
            == "EXECUTION_IDENTITY_CAPTURE_EVENT_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
            for row in rows
        ),
        "order_identity_missing_event_rows": sum(
            normalized(row.get("execution_identity_capture_event_status"))
            == "EXECUTION_IDENTITY_CAPTURE_EVENT_ORDER_IDENTITY_MISSING"
            for row in rows
        ),
        "geometry_incomplete_event_rows": sum(
            normalized(row.get("execution_identity_capture_event_status"))
            == "EXECUTION_IDENTITY_CAPTURE_EVENT_GEOMETRY_INCOMPLETE"
            for row in rows
        ),
        "contract_complete_event_rows": sum(
            normalized(row.get("execution_identity_capture_event_status"))
            == "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_COMPLETE"
            for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def _source_repair_future_execution_value_present(value: Any) -> bool:
    return _source_repair_slippage_value_present(value)


def numeric_router_source_repair_future_slippage_lifecycle_emitter_event_from_contract(
    capture_contract: dict[str, Any],
    execution_values: dict[str, Any],
    *,
    event_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    contract_status = normalized(capture_contract.get("execution_identity_capture_contract_status"))
    expected_identity_key = normalized(capture_contract.get("source_repair_identity_key"))
    identity_payload = capture_contract.get("source_repair_identity_payload")
    identity_payload = identity_payload if isinstance(identity_payload, dict) else {}
    identity_key = numeric_router_source_repair_slippage_identity_key(identity_payload)
    required_geometry_fields = list(capture_contract.get("required_execution_geometry_fields") or [])
    missing_geometry_fields = [
        field
        for field in required_geometry_fields
        if not _source_repair_future_execution_value_present(execution_values.get(field))
    ]
    order_identity_any_of = list(capture_contract.get("required_order_identity_any_of") or [])
    captured_order_identity_fields = [
        field
        for field in order_identity_any_of
        if _source_repair_slippage_order_identity_present(execution_values.get(field))
    ]
    required_identity_fields = list(capture_contract.get("required_source_repair_identity_fields") or [])
    missing_identity_fields = [
        field
        for field in required_identity_fields
        if not _source_repair_future_execution_value_present(identity_payload.get(field))
    ]

    packet_contract = contract_status == "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT"
    identity_contract = contract_status == "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY"

    if packet_contract:
        emitter_status = "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
    elif not identity_contract:
        emitter_status = "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_NOT_READY"
    elif missing_identity_fields or not identity_key or (expected_identity_key and identity_key != expected_identity_key):
        emitter_status = "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_SOURCE_REPAIR_IDENTITY_INCOMPLETE"
    elif not captured_order_identity_fields:
        emitter_status = "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_ORDER_IDENTITY_MISSING"
    elif missing_geometry_fields:
        emitter_status = "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_EXECUTION_GEOMETRY_INCOMPLETE"
    else:
        emitter_status = "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE"

    emitter_ready = (
        emitter_status == "READY_DEFAULT_OFF_FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_CONTRACT_COMPLETE"
    )
    entry_payload = None
    close_payload = None
    merged_payload = None
    if emitter_ready:
        entry_payload = {
            "slippage_event_type": "entry",
            "slippage_schema_version": "entry_slippage_shadow_v2",
            "source_repair_geometry_contract_version": "numeric_router_source_repair_geometry_v1",
            "source_repair_plan_row_id": identity_payload.get("source_repair_plan_row_id"),
            "input_numeric_router_catalog_entry_id": identity_payload.get("input_numeric_router_catalog_entry_id"),
            "input_numeric_router_family_spec_id": identity_payload.get("input_numeric_router_family_spec_id"),
            "source_repair_identity_key": identity_key,
            "source_repair_row_identity_status": "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE",
            "order_ticket": execution_values.get("order_ticket"),
            "deal_ticket": execution_values.get("deal_ticket"),
            "broker_fill_time_utc": execution_values.get("broker_fill_time_utc"),
            "executed_entry_price": execution_values.get("executed_entry_price"),
            "executed_stop_price": execution_values.get("executed_stop_price"),
            "executed_target_price": execution_values.get("executed_target_price"),
            "executed_lot_size": execution_values.get("executed_lot_size"),
            "partial_exit_lifecycle": "ENTRY_FULL_POSITION_OPENED",
            "slippage_price": execution_values.get("slippage_price"),
        }
        close_payload = {
            "slippage_event_type": "close",
            "slippage_schema_version": "close_slippage_shadow_v1",
            "source_repair_geometry_contract_version": "numeric_router_source_repair_geometry_v1",
            "order_ticket": execution_values.get("order_ticket"),
            "deal_ticket": execution_values.get("deal_ticket"),
            "broker_fill_time_utc": execution_values.get("broker_fill_time_utc"),
            "executed_entry_price": execution_values.get("executed_entry_price"),
            "executed_exit_price": execution_values.get("executed_exit_price"),
            "executed_stop_price": execution_values.get("executed_stop_price"),
            "executed_target_price": execution_values.get("executed_target_price"),
            "executed_lot_size": execution_values.get("executed_lot_size"),
            "commission": execution_values.get("commission"),
            "swap": execution_values.get("swap"),
            "partial_exit_lifecycle": execution_values.get("partial_exit_lifecycle"),
            "slippage_price": execution_values.get("slippage_price"),
        }
        merged_payload = {
            **identity_payload,
            "source_repair_identity_key": identity_key,
            **{field: execution_values.get(field) for field in required_geometry_fields},
        }

    preview_status = (
        "EXECUTION_IDENTITY_CAPTURE_EVENT_CONTRACT_COMPLETE" if emitter_ready else "EXECUTION_IDENTITY_CAPTURE_EVENT_NOT_EMITTED"
    )
    return {
        "future_slippage_lifecycle_emitter_event_row_id": event_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_future_slippage_lifecycle_emitter_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "input_execution_identity_capture_contract_row_id": capture_contract.get(
            "execution_identity_capture_contract_row_id"
        ),
        "input_source_repair_selector_route_row_id": capture_contract.get(
            "input_source_repair_selector_route_row_id"
        ),
        "input_source_repair_plan_row_id": capture_contract.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": capture_contract.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": capture_contract.get("input_numeric_router_family_spec_id"),
        "input_action_rows": capture_contract.get("input_action_rows"),
        "execution_identity_capture_contract_status": contract_status,
        "future_slippage_lifecycle_emitter_status": emitter_status,
        "future_execution_identity_capture_event_status_if_emitted": preview_status,
        "source_repair_identity_key": identity_key,
        "expected_source_repair_identity_key": expected_identity_key,
        "missing_source_repair_identity_fields": missing_identity_fields,
        "required_order_identity_any_of": order_identity_any_of,
        "captured_order_identity_fields": captured_order_identity_fields,
        "missing_execution_geometry_fields": missing_geometry_fields,
        "captured_execution_geometry_field_count": len(required_geometry_fields) - len(missing_geometry_fields),
        "future_entry_slippage_row_payload": entry_payload,
        "future_close_slippage_row_payload": close_payload,
        "future_merged_lifecycle_execution_identity_payload": merged_payload,
        "source_repair_identity_written_to_future_entry_payload": bool(entry_payload),
        "future_close_payload_joinable_by_order_ticket": bool(
            close_payload and _source_repair_slippage_order_identity_present(close_payload.get("order_ticket"))
        ),
        "future_slippage_row_bound_to_contract_if_emitted": emitter_ready,
        "slippage_join_repaired_by_this_emitter": False,
        "exact_r_repaired_by_this_emitter": False,
        "synthetic_schema_fixture_only": True,
        "materialization_result_scope": "future_lifecycle_slippage_emitter_contract_self_check_not_historical_repair",
        "source_operation": "default_off_future_slippage_lifecycle_emitter_from_execution_identity_contract",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "implementation_effect": {
            "default_off_future_slippage_lifecycle_emitter_contract_available": emitter_ready,
            "requires_future_execution_values": bool(identity_contract),
            "runtime_logging_schema_effect_if_runtime_reenabled": emitter_ready,
            "runtime_trading_or_live_broker_effect": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
        },
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_future_slippage_lifecycle_emitter_events(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = {normalized(row.get("future_slippage_lifecycle_emitter_status")) for row in rows}
    return {
        "rows": len(rows),
        "future_slippage_lifecycle_emitter_status_counts": dict(
            sorted(Counter(normalized(row.get("future_slippage_lifecycle_emitter_status")) for row in rows).items())
        ),
        "future_slippage_lifecycle_emitter_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("future_slippage_lifecycle_emitter_status")) == status
                    )
                    for status in statuses
                }.items()
            )
        ),
        "execution_identity_capture_contract_status_counts": dict(
            sorted(Counter(normalized(row.get("execution_identity_capture_contract_status")) for row in rows).items())
        ),
        "future_contract_complete_if_emitted_rows": sum(
            bool(row.get("future_slippage_row_bound_to_contract_if_emitted")) for row in rows
        ),
        "source_repair_identity_written_to_future_entry_payload_rows": sum(
            bool(row.get("source_repair_identity_written_to_future_entry_payload")) for row in rows
        ),
        "future_close_payload_joinable_by_order_ticket_rows": sum(
            bool(row.get("future_close_payload_joinable_by_order_ticket")) for row in rows
        ),
        "future_entry_slippage_row_payload_rows": sum(bool(row.get("future_entry_slippage_row_payload")) for row in rows),
        "future_close_slippage_row_payload_rows": sum(bool(row.get("future_close_slippage_row_payload")) for row in rows),
        "future_merged_lifecycle_execution_identity_payload_rows": sum(
            bool(row.get("future_merged_lifecycle_execution_identity_payload")) for row in rows
        ),
        "packet_context_execution_identity_absent_rows": sum(
            normalized(row.get("future_slippage_lifecycle_emitter_status"))
            == "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
            for row in rows
        ),
        "execution_geometry_incomplete_rows": sum(
            normalized(row.get("future_slippage_lifecycle_emitter_status"))
            == "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_EXECUTION_GEOMETRY_INCOMPLETE"
            for row in rows
        ),
        "order_identity_missing_rows": sum(
            normalized(row.get("future_slippage_lifecycle_emitter_status"))
            == "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_ORDER_IDENTITY_MISSING"
            for row in rows
        ),
        "source_repair_identity_incomplete_rows": sum(
            normalized(row.get("future_slippage_lifecycle_emitter_status"))
            == "FUTURE_SLIPPAGE_LIFECYCLE_EMITTER_SOURCE_REPAIR_IDENTITY_INCOMPLETE"
            for row in rows
        ),
        "slippage_join_repaired_by_this_emitter_rows": sum(
            bool(row.get("slippage_join_repaired_by_this_emitter")) for row in rows
        ),
        "exact_r_repaired_by_this_emitter_rows": sum(bool(row.get("exact_r_repaired_by_this_emitter")) for row in rows),
        "synthetic_schema_fixture_rows": sum(bool(row.get("synthetic_schema_fixture_only")) for row in rows),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def _source_repair_slippage_pair_ticket(row: dict[str, Any]) -> str:
    for field in ("ticket", "position_ticket", "entry_order_ticket"):
        value = row.get(field)
        if _source_repair_slippage_order_identity_present(value):
            return normalized(value)
    return ""


def numeric_router_source_repair_slippage_lifecycle_pairs(
    slippage_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: dict[str, dict[str, Any]] = {}
    closes: list[dict[str, Any]] = []
    for row in slippage_rows:
        event_type = normalized(row.get("slippage_event_type") or row.get("trigger")).lower()
        ticket = _source_repair_slippage_pair_ticket(row)
        if not ticket:
            continue
        if event_type == "entry" or normalized(row.get("trigger")) == "limit_fill":
            entries.setdefault(ticket, row)
        elif event_type == "close" or "close" in event_type:
            closes.append(row)

    pairs: list[dict[str, Any]] = []
    for close_row in closes:
        ticket = _source_repair_slippage_pair_ticket(close_row)
        entry_row = entries.get(ticket)
        if not entry_row:
            continue
        pairs.append(
            {
                "slippage_lifecycle_pair_id": f"SLIPPAGE-LIFECYCLE-PAIR-{len(pairs) + 1:08d}",
                "ticket": ticket,
                "entry_slippage_row": entry_row,
                "close_slippage_row": close_row,
            }
        )
    return pairs


def _first_present(*values: Any) -> Any:
    for value in values:
        if _source_repair_slippage_value_present(value):
            return value
    return None


def numeric_router_source_repair_execution_identity_lifecycle_join_event_from_pair(
    capture_contract: dict[str, Any],
    lifecycle_pair: dict[str, Any],
    *,
    event_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
    slippage_source_artifact: str,
    slippage_source_sha256: str,
) -> dict[str, Any]:
    entry_row = lifecycle_pair.get("entry_slippage_row")
    entry_row = entry_row if isinstance(entry_row, dict) else {}
    close_row = lifecycle_pair.get("close_slippage_row")
    close_row = close_row if isinstance(close_row, dict) else {}
    contract_status = normalized(capture_contract.get("execution_identity_capture_contract_status"))
    expected_identity_key = normalized(capture_contract.get("source_repair_identity_key"))

    identity_payload = {
        field: _first_present(entry_row.get(field), close_row.get(field))
        for field in NUMERIC_ROUTER_SOURCE_REPAIR_SLIPPAGE_IDENTITY_FIELDS
    }
    identity_key = normalized(entry_row.get("source_repair_identity_key") or close_row.get("source_repair_identity_key"))
    if not identity_key:
        identity_key = numeric_router_source_repair_slippage_identity_key(identity_payload)

    merged_payload = {
        **identity_payload,
        "source_repair_identity_key": identity_key,
        "broker_fill_time_utc": _first_present(close_row.get("broker_fill_time_utc"), entry_row.get("broker_fill_time_utc")),
        "commission": _first_present(close_row.get("commission"), entry_row.get("commission")),
        "deal_ticket": _first_present(
            close_row.get("deal_ticket"),
            close_row.get("mt5_deal_id"),
            entry_row.get("deal_ticket"),
        ),
        "executed_entry_price": _first_present(
            entry_row.get("executed_entry_price"),
            entry_row.get("fill_price"),
            close_row.get("executed_entry_price"),
        ),
        "executed_exit_price": _first_present(close_row.get("executed_exit_price"), close_row.get("fill_price")),
        "executed_lot_size": _first_present(
            close_row.get("executed_lot_size"),
            close_row.get("volume_closed"),
            entry_row.get("executed_lot_size"),
        ),
        "executed_stop_price": _first_present(entry_row.get("executed_stop_price"), close_row.get("executed_stop_price")),
        "executed_target_price": _first_present(
            entry_row.get("executed_target_price"),
            close_row.get("executed_target_price"),
        ),
        "order_ticket": _first_present(
            entry_row.get("order_ticket"),
            entry_row.get("ticket"),
            close_row.get("order_ticket"),
            close_row.get("ticket"),
        ),
        "partial_exit_lifecycle": _first_present(close_row.get("partial_exit_lifecycle"), entry_row.get("partial_exit_lifecycle")),
        "slippage_price": _first_present(close_row.get("slippage_price"), entry_row.get("slippage_price")),
        "swap": _first_present(close_row.get("swap"), entry_row.get("swap")),
    }
    required_identity_fields = list(capture_contract.get("required_source_repair_identity_fields") or [])
    missing_identity_fields = [
        field for field in required_identity_fields if not _source_repair_slippage_value_present(merged_payload.get(field))
    ]
    order_identity_any_of = list(capture_contract.get("required_order_identity_any_of") or [])
    captured_order_identity_fields = [
        field
        for field in order_identity_any_of
        if _source_repair_slippage_order_identity_present(merged_payload.get(field))
    ]
    required_geometry_fields = list(capture_contract.get("required_execution_geometry_fields") or [])
    missing_geometry_fields = [
        field for field in required_geometry_fields if not _source_repair_slippage_value_present(merged_payload.get(field))
    ]
    identity_mismatch = bool(identity_key and expected_identity_key and identity_key != expected_identity_key)

    if contract_status == "READY_DEFAULT_OFF_PACKET_CONTEXT_CAPTURE_CONTRACT_EXECUTION_IDENTITY_ABSENT":
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
    elif contract_status != "READY_DEFAULT_OFF_EXECUTION_IDENTITY_CAPTURE_CONTRACT_WITH_SOURCE_REPAIR_IDENTITY":
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_CONTRACT_NOT_READY"
    elif missing_identity_fields or not identity_key:
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_SOURCE_REPAIR_IDENTITY_MISSING"
    elif identity_mismatch:
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_SOURCE_REPAIR_IDENTITY_MISMATCH"
    elif not captured_order_identity_fields:
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_ORDER_IDENTITY_MISSING"
    elif missing_geometry_fields:
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_EXECUTION_GEOMETRY_INCOMPLETE"
    else:
        join_status = "SLIPPAGE_LIFECYCLE_JOIN_CONTRACT_COMPLETE"

    join_complete = join_status == "SLIPPAGE_LIFECYCLE_JOIN_CONTRACT_COMPLETE"
    return {
        "slippage_lifecycle_join_event_row_id": event_row_id,
        "schema_version": "main_orch48_numeric_router_source_repair_slippage_lifecycle_join_audit_v1",
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "slippage_source_artifact": slippage_source_artifact,
        "slippage_source_sha256": slippage_source_sha256,
        "input_execution_identity_capture_contract_row_id": capture_contract.get(
            "execution_identity_capture_contract_row_id"
        ),
        "input_source_repair_plan_row_id": capture_contract.get("input_source_repair_plan_row_id"),
        "input_numeric_router_catalog_entry_id": capture_contract.get("input_numeric_router_catalog_entry_id"),
        "input_numeric_router_family_spec_id": capture_contract.get("input_numeric_router_family_spec_id"),
        "input_action_rows": capture_contract.get("input_action_rows"),
        "input_slippage_lifecycle_pair_id": lifecycle_pair.get("slippage_lifecycle_pair_id"),
        "lifecycle_ticket": lifecycle_pair.get("ticket"),
        "entry_slippage_source_line_no": entry_row.get("_source_line_no"),
        "close_slippage_source_line_no": close_row.get("_source_line_no"),
        "execution_identity_capture_contract_status": contract_status,
        "slippage_lifecycle_join_status": join_status,
        "expected_source_repair_identity_key": expected_identity_key,
        "slippage_lifecycle_source_repair_identity_key": identity_key,
        "missing_source_repair_identity_fields": missing_identity_fields,
        "required_order_identity_any_of": order_identity_any_of,
        "captured_order_identity_fields": captured_order_identity_fields,
        "missing_execution_geometry_fields": missing_geometry_fields,
        "captured_execution_geometry_field_count": len(required_geometry_fields) - len(missing_geometry_fields),
        "merged_lifecycle_execution_identity_payload": merged_payload if join_complete else None,
        "slippage_lifecycle_pair_bound_to_contract": join_complete,
        "slippage_lifecycle_join_repaired_by_this_event": join_complete,
        "exact_r_repaired_by_this_lifecycle_join": False,
        "materialization_result_scope": "slippage_lifecycle_join_audit_not_exact_r_repair",
        "source_operation": "default_off_slippage_entry_close_lifecycle_join_against_execution_identity_contract",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": numeric_router_boundary(),
    }


def summarize_numeric_router_source_repair_slippage_lifecycle_join_events(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = {normalized(row.get("slippage_lifecycle_join_status")) for row in rows}
    return {
        "rows": len(rows),
        "unique_contract_rows_checked": len(
            {
                normalized(row.get("input_execution_identity_capture_contract_row_id"))
                for row in rows
                if normalized(row.get("input_execution_identity_capture_contract_row_id"))
            }
        ),
        "unique_slippage_lifecycle_pairs_checked": len(
            {
                normalized(row.get("input_slippage_lifecycle_pair_id"))
                for row in rows
                if normalized(row.get("input_slippage_lifecycle_pair_id"))
            }
        ),
        "slippage_lifecycle_join_status_counts": dict(
            sorted(Counter(normalized(row.get("slippage_lifecycle_join_status")) for row in rows).items())
        ),
        "slippage_lifecycle_join_status_unique_contract_counts": dict(
            sorted(
                {
                    status: len(
                        {
                            normalized(row.get("input_execution_identity_capture_contract_row_id"))
                            for row in rows
                            if normalized(row.get("slippage_lifecycle_join_status")) == status
                        }
                    )
                    for status in statuses
                }.items()
            )
        ),
        "slippage_lifecycle_join_status_input_action_counts": dict(
            sorted(
                {
                    status: sum(
                        int(row.get("input_action_rows") or 0)
                        for row in rows
                        if normalized(row.get("slippage_lifecycle_join_status")) == status
                    )
                    for status in statuses
                }.items()
            )
        ),
        "slippage_lifecycle_pair_bound_to_contract_rows": sum(
            bool(row.get("slippage_lifecycle_pair_bound_to_contract")) for row in rows
        ),
        "slippage_lifecycle_join_repaired_by_this_event_rows": sum(
            bool(row.get("slippage_lifecycle_join_repaired_by_this_event")) for row in rows
        ),
        "exact_r_repaired_by_this_lifecycle_join_rows": sum(
            bool(row.get("exact_r_repaired_by_this_lifecycle_join")) for row in rows
        ),
        "missing_source_repair_identity_lifecycle_rows": sum(
            normalized(row.get("slippage_lifecycle_join_status"))
            == "SLIPPAGE_LIFECYCLE_JOIN_SOURCE_REPAIR_IDENTITY_MISSING"
            for row in rows
        ),
        "packet_context_execution_identity_absent_lifecycle_rows": sum(
            normalized(row.get("slippage_lifecycle_join_status"))
            == "SLIPPAGE_LIFECYCLE_JOIN_PACKET_CONTEXT_EXECUTION_IDENTITY_ABSENT"
            for row in rows
        ),
        "execution_geometry_incomplete_lifecycle_rows": sum(
            normalized(row.get("slippage_lifecycle_join_status"))
            == "SLIPPAGE_LIFECYCLE_JOIN_EXECUTION_GEOMETRY_INCOMPLETE"
            for row in rows
        ),
        "runtime_score_allowed_rows": sum(bool(row.get("runtime_score_allowed")) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "unconditional_scalar_use_allowed_rows": sum(bool(row.get("unconditional_scalar_use_allowed")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


class NumericRouterImplementationCatalog:
    """Default-off evaluator over numeric-router implementation catalog entries."""

    def __init__(self, entries: list[dict[str, Any]]) -> None:
        self.entries = list(entries)

    @classmethod
    def from_jsonl_paths(cls, paths: list[Path | str] | tuple[Path | str, ...]) -> "NumericRouterImplementationCatalog":
        return cls(load_numeric_router_catalog_entries(paths))

    def evaluate_event(self, event: dict[str, Any], *, include_source_repair: bool = False) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []
        for entry in self.entries:
            if not include_source_repair and entry.get("catalog_type") == "source_repair_queue_entry":
                continue
            if not numeric_router_catalog_entry_matches_event(entry, event):
                continue
            matches.append(
                {
                    "numeric_router_catalog_match_id": f"MATCH-{len(matches) + 1:08d}",
                    "input_numeric_router_catalog_entry_id": entry.get("numeric_router_catalog_entry_id"),
                    "input_numeric_router_family_spec_id": entry.get("input_numeric_router_family_spec_id"),
                    "catalog_type": entry.get("catalog_type"),
                    "catalog_priority_bucket": entry.get("catalog_priority_bucket"),
                    "catalog_priority_rank": entry.get("catalog_priority_rank"),
                    "numeric_router_action": entry.get("numeric_router_action"),
                    "implementation_target": entry.get("implementation_target"),
                    "symbol": entry.get("symbol"),
                    "route_session": entry.get("route_session"),
                    "horizon_id": entry.get("horizon_id"),
                    "source_component": entry.get("source_component"),
                    "primitive_flag": entry.get("primitive_flag"),
                    "proxy_r_class": entry.get("proxy_r_class"),
                    "target_stop_order_class": entry.get("target_stop_order_class"),
                    "repair_action": entry.get("repair_action"),
                    "missing_field_count": entry.get("missing_field_count"),
                    "input_action_rows": entry.get("input_action_rows"),
                    "catalog_evaluation_status": "DEFAULT_OFF_NUMERIC_ROUTER_CATALOG_MATCH",
                    "runtime_score_allowed": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": False,
                    "unconditional_scalar_use_allowed": False,
                    "replay_r_reference_counted_as_new_main_result": False,
                    "research_boundary": numeric_router_boundary(),
                }
            )
        return matches

    def summarize_catalog(self) -> dict[str, Any]:
        return {
            "catalog_entries": len(self.entries),
            "input_action_rows": sum(int(row.get("input_action_rows") or 0) for row in self.entries),
            "catalog_type_counts": dict(
                sorted(Counter(normalized(row.get("catalog_type")) for row in self.entries).items())
            ),
            "catalog_priority_bucket_counts": dict(
                sorted(Counter(normalized(row.get("catalog_priority_bucket")) for row in self.entries).items())
            ),
            "source_repair_queue_entries": sum(
                normalized(row.get("catalog_type")) == "source_repair_queue_entry" for row in self.entries
            ),
            "runtime_candidate_use_permitted_rows": sum(
                bool(row.get("runtime_candidate_use_permitted")) for row in self.entries
            ),
            "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in self.entries),
        }


def summarize_system_recommendations(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "scope_system_decision_rows": sum(int(row.get("scope_system_decision_rows") or 0) for row in rows),
        "scorer_registry_surface_rows": sum(int(row.get("scorer_registry_surface_rows") or 0) for row in rows),
        "avoid_comparator_score_rows": sum(int(row.get("avoid_comparator_score_rows") or 0) for row in rows),
        "context_guard_input_rows": sum(int(row.get("context_guard_input_rows") or 0) for row in rows),
        "source_repair_proof_rows": sum(int(row.get("source_repair_proof_rows") or 0) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
        "live_effect_rows": sum(bool(row.get("live_effect")) for row in rows),
    }
