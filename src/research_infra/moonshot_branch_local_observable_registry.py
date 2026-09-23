"""Branch-local observable registry materialization helpers.

The functions here produce research-only registry records from code integration
candidate rows. They intentionally do not wire into the live orchestrator.
"""

from __future__ import annotations

from typing import Any


REGISTRY_MODULE_SURFACE = "src/research_infra/moonshot_branch_local_observable_registry.py"


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "module_materialization_surface": REGISTRY_MODULE_SURFACE,
        "input_code_integration_status": row.get("code_integration_status"),
        "input_code_integration_decision": row.get("code_integration_decision"),
        "observable_scope_key": row.get("observable_scope_key"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "live_effect": False,
    }


def registry_module_materialization(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("code_integration_status") or "")
    if status == "CODE_INTEGRATION_DENOMINATOR_GUARDED_OBSERVABLE_REGISTRY_PATCH":
        materialization_status = "REGISTRY_MODULE_DENOMINATOR_GUARDED_OBSERVABLE_READY"
        decision = "MATERIALIZE_OBSERVABLE_REGISTRY_ENTRY"
        registry_family = "DENOMINATOR_GUARDED_OBSERVABLE"
        guard_required = True
        ready = True
    elif status in {
        "CODE_INTEGRATION_SYMBOL_PROXY_CONTROL_GUARD_PATCH",
        "CODE_INTEGRATION_SESSION_PROXY_CONTROL_GUARD_PATCH",
    }:
        materialization_status = "REGISTRY_MODULE_PROXY_CONTROL_GUARD_READY"
        decision = "MATERIALIZE_PROXY_CONTROL_GUARD_ENTRY"
        registry_family = "PROXY_CONTROL_GUARD"
        guard_required = True
        ready = True
    elif status == "CODE_INTEGRATION_EXACT_CONTROL_BUILDER_WORK_ORDER":
        materialization_status = "REGISTRY_MODULE_EXACT_CONTROL_BUILD_PLACEHOLDER"
        decision = "PRESERVE_EXACT_CONTROL_BUILD_PLACEHOLDER"
        registry_family = "EXACT_CONTROL_BUILD_REQUIRED"
        guard_required = True
        ready = False
    elif status == "CODE_INTEGRATION_CONTROL_COMPARATOR_REGISTRY_PATCH":
        materialization_status = "REGISTRY_MODULE_CONTROL_COMPARATOR_READY"
        decision = "MATERIALIZE_CONTROL_COMPARATOR_ENTRY"
        registry_family = "CONTROL_COMPARATOR"
        guard_required = False
        ready = True
    elif status == "CODE_INTEGRATION_CONTROL_CONTEXT_ONLY":
        materialization_status = "REGISTRY_MODULE_CONTROL_CONTEXT_ONLY"
        decision = "PRESERVE_CONTROL_CONTEXT"
        registry_family = "CONTROL_CONTEXT"
        guard_required = False
        ready = False
    elif status == "CODE_INTEGRATION_DENOMINATOR_GUARD_PATCH":
        materialization_status = "REGISTRY_MODULE_DENOMINATOR_GUARD_READY"
        decision = "MATERIALIZE_DENOMINATOR_GUARD_ENTRY"
        registry_family = "DENOMINATOR_GUARD"
        guard_required = True
        ready = True
    else:
        materialization_status = "REGISTRY_MODULE_CONTEXT_ONLY"
        decision = "PRESERVE_REGISTRY_CONTEXT"
        registry_family = "CONTEXT_ONLY"
        guard_required = False
        ready = False
    return {
        **_base(row),
        "module_materialization_stage": "REGISTRY_MODULE_MATERIALIZATION",
        "module_materialization_status": materialization_status,
        "module_materialization_decision": decision,
        "registry_family": registry_family,
        "candidate_function_name": row.get("candidate_function_hint"),
        "registry_key": row.get("observable_scope_key") or row.get("source_code_candidate_id"),
        "guard_required": guard_required,
        "module_patch_ready": ready,
        "branch_local_ready": ready,
    }


def coverage_sidecar_registry_materialization(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_base(row),
        "module_materialization_stage": "COVERAGE_REGISTRY_SIDECAR_MATERIALIZATION",
        "module_materialization_status": str(row.get("code_integration_status") or "COVERAGE_REGISTRY_CONTEXT_ONLY").replace(
            "CODE_INTEGRATION_", "REGISTRY_MODULE_"
        ),
        "module_materialization_decision": "PRESERVE_FULL_PRIMITIVE_COVERAGE_REGISTRY_CONTEXT",
        "registry_family": "PRIMITIVE_COVERAGE_SIDECAR",
        "registry_key": row.get("observable_scope_key") or row.get("source_code_candidate_id"),
        "guard_required": False,
        "module_patch_ready": False,
        "branch_local_ready": False,
    }
