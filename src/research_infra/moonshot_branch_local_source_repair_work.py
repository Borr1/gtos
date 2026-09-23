"""Branch-local source and control repair work-order materialization helpers."""

from __future__ import annotations

from typing import Any


REPAIR_MODULE_SURFACE = "src/research_infra/moonshot_branch_local_source_repair_work.py"


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_materialization_surface": REPAIR_MODULE_SURFACE,
        "input_code_integration_status": row.get("code_integration_status"),
        "input_code_integration_decision": row.get("code_integration_decision"),
        "observable_scope_key": row.get("observable_scope_key"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "live_effect": False,
    }


def source_repair_work_materialization(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("code_integration_status") or "")
    if status == "CODE_INTEGRATION_EXACT_SOURCE_REPAIR_WORK_ORDER":
        materialization_status = "REPAIR_MODULE_EXACT_SOURCE_WORK_ORDER_OPEN"
        decision = "EXECUTE_EXACT_SOURCE_REPAIR_OR_ACQUISITION"
        repair_family = "EXACT_SOURCE_REPAIR"
        fail_if_negative = False
    elif status == "CODE_INTEGRATION_HORIZON_REBUILD_RESCORE_WORK_ORDER":
        materialization_status = "REPAIR_MODULE_HORIZON_REBUILD_RESCORE_WORK_ORDER_OPEN"
        decision = "EXECUTE_HORIZON_REBUILD_AND_RESCORE"
        repair_family = "HORIZON_REBUILD_RESCORE"
        fail_if_negative = False
    elif status == "CODE_INTEGRATION_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER":
        materialization_status = "REPAIR_MODULE_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER_OPEN"
        decision = "EXECUTE_HORIZON_REBUILD_AND_KILL_CHECK"
        repair_family = "HORIZON_REBUILD_KILL_CHECK"
        fail_if_negative = True
    else:
        materialization_status = "REPAIR_MODULE_CONTEXT_ONLY"
        decision = "PRESERVE_REPAIR_CONTEXT"
        repair_family = "CONTEXT_ONLY"
        fail_if_negative = False
    return {
        **_base(row),
        "module_materialization_stage": "SOURCE_REPAIR_MODULE_MATERIALIZATION",
        "module_materialization_status": materialization_status,
        "module_materialization_decision": decision,
        "repair_family": repair_family,
        "candidate_function_name": row.get("candidate_function_hint"),
        "repair_work_order_open": status
        in {
            "CODE_INTEGRATION_EXACT_SOURCE_REPAIR_WORK_ORDER",
            "CODE_INTEGRATION_HORIZON_REBUILD_RESCORE_WORK_ORDER",
            "CODE_INTEGRATION_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER",
        },
        "fail_if_negative_persists": bool(row.get("fail_if_negative_persists") or fail_if_negative),
        "branch_local_ready": False,
    }


def exact_control_work_materialization(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_base(row),
        "module_materialization_stage": "EXACT_CONTROL_WORK_ORDER_MATERIALIZATION",
        "module_materialization_status": "REPAIR_MODULE_EXACT_CONTROL_BUILD_WORK_ORDER_OPEN",
        "module_materialization_decision": "EXECUTE_EXACT_CONTROL_SCOPE_BUILD",
        "repair_family": "EXACT_CONTROL_BUILD",
        "candidate_function_name": row.get("candidate_function_hint"),
        "repair_work_order_open": True,
        "exact_control_build_required": True,
        "exact_build_source_requirement": row.get("exact_build_source_requirement"),
        "branch_local_ready": False,
    }


def horizon_sidecar_work_materialization(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_base(row),
        "module_materialization_stage": "HORIZON_REPAIR_SIDECAR_MATERIALIZATION",
        "module_materialization_status": str(row.get("code_integration_status") or "HORIZON_REPAIR_CONTEXT_ONLY").replace(
            "CODE_INTEGRATION_", "REPAIR_MODULE_"
        ),
        "module_materialization_decision": "PRESERVE_HORIZON_REPAIR_SIDECAR_CONTEXT",
        "repair_family": "HORIZON_REPAIR_SIDECAR",
        "repair_work_order_open": False,
        "branch_local_ready": False,
    }
