"""Main-side helpers for moonshot expanded-market final review decisions."""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


BOUNDARY_SCHEMA = "main_side_moonshot_expanded_market_final_review_execution_v1"
SURFACE = "src/research_infra/moonshot_expanded_market_final_review_execution.py"


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


def final_review_action(decision: str | None) -> str:
    text = normalized(decision)
    if text == "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL":
        return "KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE"
    if text == "REDESIGN_EXPANDED_MARKET_FINAL_REVIEW_CAPACITY_BLOCKED":
        return "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE"
    return "PRESERVE_FINAL_REVIEW_ROW_FOR_DECISION_REPAIR"


def final_review_integrity_status(final_review_row: dict[str, Any], main_candidate: dict[str, Any] | None) -> str:
    if not main_candidate:
        return "FINAL_REVIEW_MAIN_CANDIDATE_BINDING_REPAIR_REQUIRED"
    if normalized(final_review_row.get("final_review_evidence_status")) != "FINAL_REVIEW_EVIDENCE_COMPLETE":
        return "FINAL_REVIEW_EVIDENCE_REPAIR_REQUIRED"
    if int(final_review_row.get("final_review_evidence_rows") or 0) <= 0:
        return "FINAL_REVIEW_EVIDENCE_REPAIR_REQUIRED"
    recompute_delta = safe_float(final_review_row.get("average_selected_intrabar_cost_adjusted_recompute_delta"))
    if recompute_delta is None or abs(recompute_delta) > 1e-9:
        return "FINAL_REVIEW_RECOMPUTE_REPAIR_REQUIRED"
    return "FINAL_REVIEW_VERIFIED"


def compact_final_review_row(
    final_review_row: dict[str, Any],
    implementation_candidate_row: dict[str, Any] | None,
    main_candidate: dict[str, Any] | None,
    *,
    final_review_source_artifact: str,
    final_review_source_line_no: int,
    final_review_source_sha256: str,
    implementation_candidate_source_artifact: str | None,
    implementation_candidate_source_line_no: int | None,
    implementation_candidate_source_sha256: str | None,
    output_row_id: str,
) -> dict[str, Any]:
    decision = normalized(final_review_row.get("keep_kill_redesign_implement_decision"))
    integrity = final_review_integrity_status(final_review_row, main_candidate)
    return {
        "final_review_overlay_row_id": output_row_id,
        "final_review_source_artifact": final_review_source_artifact,
        "final_review_source_line_no": final_review_source_line_no,
        "final_review_source_sha256": final_review_source_sha256,
        "implementation_candidate_source_artifact": implementation_candidate_source_artifact,
        "implementation_candidate_source_line_no": implementation_candidate_source_line_no,
        "implementation_candidate_source_sha256": implementation_candidate_source_sha256,
        "source_final_review_row_id": final_review_row.get("final_review_row_id"),
        "source_input_deconcentration_row_id": final_review_row.get("input_deconcentration_row_id"),
        "source_input_final_branch_artifact_row_id": final_review_row.get("input_final_branch_artifact_row_id"),
        "source_input_implementation_candidate_row_id": final_review_row.get("input_implementation_candidate_row_id"),
        "source_input_reduced_surface_execution_row_id": (implementation_candidate_row or {}).get(
            "input_reduced_surface_execution_row_id"
        ),
        "main_candidate_row_id": (main_candidate or {}).get("candidate_row_id"),
        "main_candidate_bound": bool(main_candidate),
        "artifact_family": final_review_row.get("artifact_family"),
        "artifact_function_name": final_review_row.get("artifact_function_name"),
        "artifact_scope_sha256": final_review_row.get("artifact_scope_sha256"),
        "candidate_surface_scope_sha256": (main_candidate or {}).get("surface_scope_sha256"),
        "symbol": final_review_row.get("symbol"),
        "source_symbol": final_review_row.get("source_symbol"),
        "market_timeframe": final_review_row.get("market_timeframe"),
        "route_session": final_review_row.get("route_session"),
        "horizon_id": final_review_row.get("horizon_id"),
        "source_component": final_review_row.get("source_component"),
        "selected_side": final_review_row.get("selected_side"),
        "source_path": final_review_row.get("source_path"),
        "source_file_sha256": final_review_row.get("source_file_sha256"),
        "branch_local_code_expression": final_review_row.get("branch_local_code_expression"),
        "capacity_blocking_dimensions": final_review_row.get("capacity_blocking_dimensions") or [],
        "capacity_selected_input": bool(final_review_row.get("capacity_selected_input")),
        "base_selected_input": bool(final_review_row.get("base_selected_input")),
        "final_review_evidence_rows": int(final_review_row.get("final_review_evidence_rows") or 0),
        "evidence_execution_rows_claimed": int(final_review_row.get("evidence_execution_rows_claimed") or 0),
        "evidence_effective_n_sum": safe_float(final_review_row.get("evidence_effective_n_sum")),
        "matched_effective_n_sum": safe_float(final_review_row.get("matched_effective_n_sum")),
        "deconcentration_score": safe_float(final_review_row.get("deconcentration_score")),
        "final_review_score": safe_float(final_review_row.get("final_review_score")),
        "max_capacity_utilization": safe_float(final_review_row.get("max_capacity_utilization")),
        "row_average_selected_intrabar_cost_adjusted_simulated_r": safe_float(
            final_review_row.get("row_average_selected_intrabar_cost_adjusted_simulated_r")
        ),
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r": safe_float(
            final_review_row.get("recomputed_average_selected_intrabar_cost_adjusted_simulated_r")
        ),
        "row_average_selected_minus_rejected_intrabar_cost_adjusted_r": safe_float(
            final_review_row.get("row_average_selected_minus_rejected_intrabar_cost_adjusted_r")
        ),
        "recomputed_average_selected_minus_rejected_intrabar_cost_adjusted_r": safe_float(
            final_review_row.get("recomputed_average_selected_minus_rejected_intrabar_cost_adjusted_r")
        ),
        "average_selected_intrabar_cost_adjusted_recompute_delta": safe_float(
            final_review_row.get("average_selected_intrabar_cost_adjusted_recompute_delta")
        ),
        "target_first_share": safe_float(final_review_row.get("target_first_share")),
        "stop_first_share": safe_float(final_review_row.get("stop_first_share")),
        "target_first_minus_stop_first_share": safe_float(final_review_row.get("target_first_minus_stop_first_share")),
        "source_final_review_decision": decision,
        "main_compiler_final_review_action": final_review_action(decision),
        "final_review_integrity_status": integrity,
        "branch_local_candidate_status_after_final_review": "READY_DEFAULT_OFF_FINAL_REVIEW_CANDIDATE"
        if integrity == "FINAL_REVIEW_VERIFIED" and decision == "IMPLEMENT_EXPANDED_MARKET_FINAL_REVIEW_BRANCH_LOCAL"
        else "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CANDIDATE",
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "replay_r_reference_counted_as_new_main_result": False,
        "research_boundary": research_boundary(),
        "expanded_market_final_review_execution_surface": SURFACE,
    }


def summarize_final_review_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [
        value
        for row in rows
        if (value := safe_float(row.get("recomputed_average_selected_intrabar_cost_adjusted_simulated_r"))) is not None
    ]
    return {
        "rows": len(rows),
        "main_candidate_bound_rows": sum(bool(row.get("main_candidate_bound")) for row in rows),
        "main_compiler_final_review_action_counts": dict(
            sorted(Counter(normalized(row.get("main_compiler_final_review_action")) for row in rows).items())
        ),
        "final_review_integrity_status_counts": dict(
            sorted(Counter(normalized(row.get("final_review_integrity_status")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "final_review_evidence_rows": sum(int(row.get("final_review_evidence_rows") or 0) for row in rows),
        "evidence_execution_rows_claimed": sum(int(row.get("evidence_execution_rows_claimed") or 0) for row in rows),
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_rows": len(values),
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_sum_reference": rounded(sum(values)),
        "recomputed_average_selected_intrabar_cost_adjusted_simulated_r_mean_reference": rounded(
            sum(values) / len(values) if values else None
        ),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }


def apply_final_review_overlay_to_rollups(
    rollups: list[dict[str, Any]],
    final_review_overlays: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    overlay_by_candidate = {
        normalized(row.get("main_candidate_row_id")): row for row in final_review_overlays
    }
    rows: list[dict[str, Any]] = []
    for rollup in rollups:
        candidate_id = normalized(rollup.get("candidate_row_id"))
        overlay = overlay_by_candidate.get(candidate_id, {})
        action = normalized(overlay.get("main_compiler_final_review_action"))
        if action == "KEEP_DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_CANDIDATE":
            adjusted_status = "DEFAULT_OFF_FINAL_REVIEW_IMPLEMENT_READY"
        elif action == "REDESIGN_DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_CANDIDATE":
            adjusted_status = "DEFAULT_OFF_FINAL_REVIEW_CAPACITY_BLOCKED_REDESIGN"
        else:
            adjusted_status = "DEFAULT_OFF_FINAL_REVIEW_BINDING_REPAIR_REQUIRED"
        rows.append(
            {
                **rollup,
                "final_review_overlay_bound": bool(overlay),
                "source_final_review_row_id": overlay.get("source_final_review_row_id"),
                "source_final_review_decision": overlay.get("source_final_review_decision"),
                "main_compiler_final_review_action": action,
                "final_review_integrity_status": overlay.get("final_review_integrity_status"),
                "branch_local_candidate_status_after_final_review": overlay.get(
                    "branch_local_candidate_status_after_final_review"
                ),
                "capacity_blocking_dimensions": overlay.get("capacity_blocking_dimensions") or [],
                "final_review_score": overlay.get("final_review_score"),
                "max_capacity_utilization": overlay.get("max_capacity_utilization"),
                "final_review_evidence_rows": overlay.get("final_review_evidence_rows"),
                "final_review_adjusted_rollup_status": adjusted_status,
                "runtime_candidate_use_permitted": False,
                "candidate_use_allowed_now": False,
                "replay_r_reference_counted_as_new_main_result": False,
                "research_boundary": research_boundary(),
            }
        )
    return rows


def summarize_final_review_adjusted_rollups(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "final_review_overlay_bound_rows": sum(bool(row.get("final_review_overlay_bound")) for row in rows),
        "final_review_adjusted_rollup_status_counts": dict(
            sorted(Counter(normalized(row.get("final_review_adjusted_rollup_status")) for row in rows).items())
        ),
        "main_compiler_final_review_action_counts": dict(
            sorted(Counter(normalized(row.get("main_compiler_final_review_action")) for row in rows).items())
        ),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "event_registry_match_rows": sum(int(row.get("event_registry_match_rows") or 0) for row in rows),
        "expected_candidate_event_rows": sum(int(row.get("expected_candidate_event_rows") or 0) for row in rows),
        "duplicate_scope_event_match_rows": sum(int(row.get("duplicate_scope_event_match_rows") or 0) for row in rows),
        "final_review_evidence_rows": sum(int(row.get("final_review_evidence_rows") or 0) for row in rows),
        "runtime_candidate_use_permitted_rows": sum(bool(row.get("runtime_candidate_use_permitted")) for row in rows),
        "candidate_use_allowed_now_rows": sum(bool(row.get("candidate_use_allowed_now")) for row in rows),
        "replay_r_reference_counted_as_new_main_result_rows": sum(
            bool(row.get("replay_r_reference_counted_as_new_main_result")) for row in rows
        ),
    }
