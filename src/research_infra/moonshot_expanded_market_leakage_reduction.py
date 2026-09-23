"""Main-side helpers for moonshot expanded-market leakage-reduced scopes.

The weekend moonshot worktree emits branch-local leakage-reduction rows after
expanded-market code-candidate execution.  This module gives main a small,
testable surface for consuming those rows without importing the whole moonshot
runtime.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Any


SURFACE = "src/research_infra/moonshot_expanded_market_leakage_reduction.py"
BOUNDARY_SCHEMA = "main_side_moonshot_expanded_market_leakage_reduction_v1"
BASE_SCOPE_KEYS = (
    "horizon_id",
    "market_timeframe",
    "route_session",
    "selected_side",
    "source_component",
    "source_symbol",
    "symbol",
)
NARROW_NUMERIC_FIELDS = (
    "selected_intrabar_cost_adjusted_simulated_r",
    "selected_minus_rejected_intrabar_cost_adjusted_r",
    "temporal_winner_consistency_share",
    "temporal_positive_winner_fold_share",
)


def research_boundary() -> dict[str, Any]:
    """Return the no-live-effect boundary for consumed moonshot rows."""
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


def decision_family(decision: str | None) -> str:
    text = normalized(decision)
    if text.startswith("IMPLEMENT"):
        return "implement"
    if "AVOID" in text:
        return "avoid"
    if text.startswith("KILL"):
        return "kill"
    if text.startswith("REDESIGN"):
        return "redesign"
    return "missing"


def main_action_class(decision: str | None, follow_class: str | None = None) -> str:
    text = normalized(decision)
    if text == "IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED":
        return "IMPLEMENT_DEFAULT_OFF_PRESERVED"
    if text == "IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE":
        return "IMPLEMENT_DEFAULT_OFF_LEAKAGE_REDUCED"
    if normalized(follow_class) == "avoid":
        return "AVOID_INTELLIGENCE"
    if text.startswith("REDESIGN"):
        return "REDESIGN"
    return "REVIEW"


def extract_scope(row: dict[str, Any]) -> dict[str, Any]:
    scope = row.get("reduction_scope")
    if isinstance(scope, dict) and scope:
        return dict(scope)

    rebuilt = {key: normalized(row.get(key)) for key in BASE_SCOPE_KEYS}
    if row.get("source_path") is not None:
        rebuilt["source_path"] = normalized(row.get("source_path"))
    if row.get("source_file_sha256") is not None:
        rebuilt["source_file_sha256"] = normalized(row.get("source_file_sha256"))
    thresholds: dict[str, float] = {}
    for source_field, threshold_field in (
        ("target_selected_intrabar_cost_adjusted_simulated_r", "selected_intrabar_cost_adjusted_simulated_r"),
        ("target_selected_minus_rejected_intrabar_cost_adjusted_r", "selected_minus_rejected_intrabar_cost_adjusted_r"),
        ("target_temporal_winner_consistency_share", "temporal_winner_consistency_share"),
        ("target_temporal_positive_winner_fold_share", "temporal_positive_winner_fold_share"),
    ):
        value = safe_float(row.get(source_field))
        if value is not None:
            thresholds[threshold_field] = rounded(value)
    if thresholds:
        rebuilt["numeric_thresholds"] = thresholds
    return rebuilt


def event_matches_reduction_scope(event: dict[str, Any], scope: dict[str, Any]) -> bool:
    """Return whether an event/selection row is inside a leakage-reduced scope."""
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


def compact_leakage_reduction_row(
    row: dict[str, Any],
    *,
    intake_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    decision = normalized(row.get("keep_kill_redesign_implement_decision"))
    scope = extract_scope(row)
    target_r = safe_float(row.get("target_selected_intrabar_cost_adjusted_simulated_r"))
    avg_r = safe_float(row.get("average_selected_intrabar_cost_adjusted_simulated_r"))
    selected_minus_rejected = safe_float(row.get("target_selected_minus_rejected_intrabar_cost_adjusted_r"))

    output = {
        "intake_row_id": intake_row_id,
        "source_artifact": source_artifact,
        "source_line_no": source_line_no,
        "source_sha256": source_sha256,
        "source_leakage_reduction_row_id": row.get("leakage_reduction_row_id"),
        "input_code_candidate_execution_row_id": row.get("input_code_candidate_execution_row_id"),
        "input_code_candidate_row_id": row.get("input_code_candidate_row_id"),
        "input_implementation_selection_row_id": row.get("input_implementation_selection_row_id"),
        "candidate_function_name": row.get("candidate_function_name"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "selected_side": row.get("selected_side"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "reduction_scope": scope,
        "reduction_scope_sha256": row.get("reduction_scope_sha256") or stable_hash(scope),
        "matched_selection_rows": int(row.get("matched_selection_rows") or 0),
        "matched_implement_rows": int(row.get("matched_implement_rows") or 0),
        "matched_nonimplement_rows": int(row.get("matched_nonimplement_rows") or 0),
        "matched_avoid_rows": int(row.get("matched_avoid_rows") or 0),
        "matched_kill_rows": int(row.get("matched_kill_rows") or 0),
        "matched_redesign_rows": int(row.get("matched_redesign_rows") or 0),
        "selection_precision": safe_float(row.get("selection_precision")),
        "target_selected_intrabar_cost_adjusted_simulated_r": target_r,
        "average_selected_intrabar_cost_adjusted_simulated_r": avg_r,
        "target_selected_minus_rejected_intrabar_cost_adjusted_r": selected_minus_rejected,
        "target_temporal_winner_consistency_share": safe_float(row.get("target_temporal_winner_consistency_share")),
        "target_temporal_positive_winner_fold_share": safe_float(
            row.get("target_temporal_positive_winner_fold_share")
        ),
        "target_effective_n": safe_float(row.get("target_effective_n")),
        "target_selected_intrabar_target_first_count": int(row.get("target_selected_intrabar_target_first_count") or 0),
        "target_selected_intrabar_stop_first_count": int(row.get("target_selected_intrabar_stop_first_count") or 0),
        "target_selected_intrabar_neither_count": int(row.get("target_selected_intrabar_neither_count") or 0),
        "target_selected_intrabar_ambiguous_count": int(row.get("target_selected_intrabar_ambiguous_count") or 0),
        "source_decision": decision,
        "main_action_class": main_action_class(decision, row.get("follow_inverse_default_off_avoid_class")),
        "main_compiler_action": (
            "REGISTER_DEFAULT_OFF_LEAKAGE_REDUCED_SIDE_FILTER_SCOPE"
            if decision == "IMPLEMENT_EXPANDED_MARKET_LEAKAGE_REDUCED_CODE_CANDIDATE"
            else "REGISTER_DEFAULT_OFF_PRESERVED_SIDE_FILTER_SCOPE"
            if decision == "IMPLEMENT_EXPANDED_MARKET_CODE_CANDIDATE_EXECUTION_PRESERVED"
            else "PRESERVE_FOR_REDESIGN_OR_SCOPE_REPAIR"
        ),
        "proxy_r_reference_counted_as_result": False,
        "replay_r_reference_field": "target_selected_intrabar_cost_adjusted_simulated_r",
        "research_boundary": research_boundary(),
        "expanded_market_leakage_reduction_surface": SURFACE,
    }
    return output


def summarize_leakage_reduction_intake(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_values = [
        value
        for row in rows
        if (value := safe_float(row.get("target_selected_intrabar_cost_adjusted_simulated_r"))) is not None
    ]
    average_values = [
        value
        for row in rows
        if (value := safe_float(row.get("average_selected_intrabar_cost_adjusted_simulated_r"))) is not None
    ]
    return {
        "rows": len(rows),
        "main_action_class_counts": dict(sorted(Counter(normalized(row.get("main_action_class")) for row in rows).items())),
        "main_compiler_action_counts": dict(
            sorted(Counter(normalized(row.get("main_compiler_action")) for row in rows).items())
        ),
        "source_decision_counts": dict(sorted(Counter(normalized(row.get("source_decision")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(normalized(row.get("symbol")) for row in rows).items())),
        "market_timeframe_counts": dict(sorted(Counter(normalized(row.get("market_timeframe")) for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(normalized(row.get("route_session")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(normalized(row.get("source_component")) for row in rows).items())),
        "selected_side_counts": dict(sorted(Counter(normalized(row.get("selected_side")) for row in rows).items())),
        "target_selected_intrabar_cost_adjusted_simulated_r_rows": len(target_values),
        "target_selected_intrabar_cost_adjusted_simulated_r_sum_reference": rounded(sum(target_values)),
        "target_selected_intrabar_cost_adjusted_simulated_r_mean_reference": rounded(
            sum(target_values) / len(target_values) if target_values else None
        ),
        "average_selected_intrabar_cost_adjusted_simulated_r_rows": len(average_values),
        "average_selected_intrabar_cost_adjusted_simulated_r_mean_reference": rounded(
            sum(average_values) / len(average_values) if average_values else None
        ),
        "matched_selection_rows": sum(int(row.get("matched_selection_rows") or 0) for row in rows),
        "matched_implement_rows": sum(int(row.get("matched_implement_rows") or 0) for row in rows),
        "matched_nonimplement_rows": sum(int(row.get("matched_nonimplement_rows") or 0) for row in rows),
        "matched_redesign_rows": sum(int(row.get("matched_redesign_rows") or 0) for row in rows),
        "proxy_r_reference_counted_as_result_rows": sum(
            row.get("proxy_r_reference_counted_as_result") is True for row in rows
        ),
        "runtime_candidate_use_permitted_rows": sum(
            bool((row.get("research_boundary") or {}).get("runtime_candidate_use_permitted")) for row in rows
        ),
    }
