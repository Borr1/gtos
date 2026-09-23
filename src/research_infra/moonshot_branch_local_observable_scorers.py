"""Branch-local observable scorer module materialization helpers.

These helpers are research-only. They convert code integration candidate rows
into concrete scorer-module materialization records without touching live
trading logic.
"""

from __future__ import annotations

from typing import Any


SCORER_MODULE_SURFACE = "src/research_infra/moonshot_branch_local_observable_scorers.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_materialization_surface": SCORER_MODULE_SURFACE,
        "input_code_integration_status": row.get("code_integration_status"),
        "input_code_integration_decision": row.get("code_integration_decision"),
        "observable_scope_key": row.get("observable_scope_key"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "integration_priority_score": to_float(row.get("integration_priority_score")),
        "live_effect": False,
    }


def scorer_module_materialization(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("code_integration_status") or "")
    if status == "CODE_INTEGRATION_CONTROLLED_OBSERVABLE_SCORER_PATCH":
        materialization_status = "SCORER_MODULE_CONTROLLED_OBSERVABLE_PATCH_READY"
        decision = "MATERIALIZE_CONTROLLED_OBSERVABLE_SCORER"
        scorer_family = "CONTROLLED_OBSERVABLE"
        can_score_standalone = True
        guard_policy = "MATCHED_CONTROL_CONTEXT_REQUIRED_FOR_REPORTING"
    elif status == "CODE_INTEGRATION_GUARDED_SOURCE_PROXY_SCORER_PATCH":
        materialization_status = "SCORER_MODULE_GUARDED_SOURCE_PROXY_PATCH_READY"
        decision = "MATERIALIZE_SOURCE_PROXY_SCORER_WITH_SOURCE_GUARD"
        scorer_family = "GUARDED_SOURCE_PROXY"
        can_score_standalone = True
        guard_policy = "SOURCE_GUARD_REQUIRED"
    elif status == "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH":
        materialization_status = "SCORER_MODULE_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_PATCH_READY"
        decision = "MATERIALIZE_SOURCE_PROXY_SCORER_WITH_MANDATORY_CONTROL_GUARD"
        scorer_family = "AMBIGUOUS_SOURCE_PROXY"
        can_score_standalone = False
        guard_policy = "AMBIGUITY_CONTROL_GUARD_REQUIRED"
    else:
        materialization_status = "SCORER_MODULE_CONTEXT_ONLY"
        decision = "PRESERVE_SCORER_CONTEXT"
        scorer_family = "CONTEXT_ONLY"
        can_score_standalone = False
        guard_policy = "NO_SCORER_PATCH"
    return {
        **_base(row),
        "module_materialization_stage": "SCORER_MODULE_MATERIALIZATION",
        "module_materialization_status": materialization_status,
        "module_materialization_decision": decision,
        "scorer_family": scorer_family,
        "candidate_function_name": row.get("candidate_function_hint"),
        "can_score_standalone": can_score_standalone,
        "control_guard_required": bool(row.get("control_guard_required")),
        "guard_policy": guard_policy,
        "module_patch_ready": status in {
            "CODE_INTEGRATION_CONTROLLED_OBSERVABLE_SCORER_PATCH",
            "CODE_INTEGRATION_GUARDED_SOURCE_PROXY_SCORER_PATCH",
            "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH",
        },
        "branch_local_ready": status
        in {
            "CODE_INTEGRATION_CONTROLLED_OBSERVABLE_SCORER_PATCH",
            "CODE_INTEGRATION_GUARDED_SOURCE_PROXY_SCORER_PATCH",
            "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH",
        },
    }
