"""Verifier for the G12 local data catalog source-control audit route."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import build_g12_gtos_local_research_data_catalog_source_control_audit_2026_05_10 as builder


ROUTE_DIR = builder.ROUTE_DIR
PREFIX = builder.PREFIX
DATE = builder.DATE
RESULT_NAME = f"{PREFIX}_VERIFICATION_RESULT_{DATE}.json"
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|unknown|maybe|later)\b|unresolved vague", re.I)

REQUIRED_FAMILIES = {
    "context_anchor",
    "decision_ledger",
    "root_resolver_config_schema_audit",
    "catalog_row_count_schema_audit",
    "search_result_missing_window_routing_audit",
    "acquisition_manifest_classification_audit",
    "hash_large_file_deferral_audit",
    "forbidden_route_noleak_audit",
    "integration_guide_usability_audit",
    "saturation_self_redteam_ledger",
    "repair_followup_source_request_ledger",
    "target_verifier_nonwriting_audit",
    "completion_audit",
    "output_manifest",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return builder.rel(path)


def safe_flag_issues(value: Any, path: str = "$") -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in builder.SAFE_FALSE_KEYS and item is not False:
                issues.append({"path": child, "value": item})
            if key == "promotion_verdict" and item != builder.PROMOTION_VERDICT:
                issues.append({"path": child, "value": item})
            issues.extend(safe_flag_issues(item, child))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            issues.extend(safe_flag_issues(item, f"{path}[{idx}]"))
    return issues


def parse_artifacts() -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    payloads: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for path in sorted(ROUTE_DIR.glob("*.json")):
        if path.name == RESULT_NAME:
            continue
        try:
            payload = load_json(path)
            payloads[path.name] = payload
            issues = safe_flag_issues(payload, path.name)
            if issues:
                failures.append({"check": "safe_flags", "file": path.name, "issues": issues[:20]})
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": path.name, "error": str(exc)})
    for path in sorted(ROUTE_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in ("NO_PROMOTION_VERDICT", "validation_safe=false", "outcome_review_opened=false", "live_effect=false"):
            if token not in text:
                failures.append({"check": "markdown_control_tokens", "file": path.name, "missing": token})
        for token in ("validation_safe=true", "outcome_review_opened=true", "live_effect=true"):
            if token in text:
                failures.append({"check": "markdown_true_safe_flag", "file": path.name, "token": token})
        hit = PLACEHOLDER_RE.search(text)
        if hit:
            failures.append({"check": "placeholder_scan", "file": path.name, "fragment": hit.group(0)})
    return payloads, failures


def verify_required_artifacts(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    families = {payload.get("artifact_family") for payload in payloads.values()}
    failures: list[dict[str, Any]] = []
    missing = REQUIRED_FAMILIES - families
    if missing:
        failures.append({"check": "required_artifact_families", "missing": sorted(missing)})
    for script in (
        "build_g12_gtos_local_research_data_catalog_source_control_audit_2026_05_10.py",
        "verify_g12_gtos_local_research_data_catalog_source_control_audit_2026_05_10.py",
        "test_g12_gtos_local_research_data_catalog_source_control_audit_2026_05_10.py",
    ):
        if not (ROUTE_DIR / script).exists():
            failures.append({"check": "route_tooling_exists", "missing": script})
    return failures


def payload_by_family(payloads: dict[str, dict[str, Any]], family: str) -> dict[str, Any]:
    for payload in payloads.values():
        if payload.get("artifact_family") == family:
            return payload
    return {}


def verify_audits(payloads: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    expected = builder.EXPECTED
    decision = payload_by_family(payloads, "decision_ledger")
    if decision.get("terminal_decision") != builder.TERMINAL_DECISION:
        failures.append({"check": "terminal_decision", "value": decision.get("terminal_decision")})
    if decision.get("can_use_tooling_with_conditions") is not True:
        failures.append({"check": "decision_acceptance", "value": decision})

    root = payload_by_family(payloads, "root_resolver_config_schema_audit")
    if root.get("audit_passed") is not True:
        failures.append({"check": "root_audit_passed", "value": root})
    if root.get("persisted_current_worktree_path_mismatch_count", 0) < 1:
        failures.append({"check": "root_snapshot_staleness_detected", "value": root.get("persisted_current_worktree_path_mismatch_count")})
    if root.get("runtime_current_worktree_paths_match_active_repo") is not True:
        failures.append({"check": "runtime_current_worktree_paths", "value": root})

    catalog = payload_by_family(payloads, "catalog_row_count_schema_audit")
    if catalog.get("audit_passed") is not True or catalog.get("expected_counts_reconciled") is not True:
        failures.append({"check": "catalog_audit_passed", "value": catalog})
    if catalog.get("persisted_catalog_row_count") != expected["catalog_rows"]:
        failures.append({"check": "catalog_row_count", "value": catalog.get("persisted_catalog_row_count")})
    if catalog.get("persisted_small_hash_rows") != expected["small_hash_rows"]:
        failures.append({"check": "small_hash_rows", "value": catalog.get("persisted_small_hash_rows")})
    if catalog.get("persisted_large_file_deferral_rows") != expected["large_file_deferrals"]:
        failures.append({"check": "large_deferral_rows", "value": catalog.get("persisted_large_file_deferral_rows")})
    persisted_hash = catalog.get("persisted_hash_recompute", {})
    if persisted_hash.get("persisted_small_hash_mismatch_count") != 0:
        failures.append({"check": "persisted_hash_mismatch", "value": persisted_hash})
    if persisted_hash.get("persisted_small_hash_missing_count", 0) < 1:
        failures.append({"check": "persisted_missing_hash_rows_detected", "value": persisted_hash.get("persisted_small_hash_missing_count")})

    search = payload_by_family(payloads, "search_result_missing_window_routing_audit")
    if search.get("audit_passed") is not True:
        failures.append({"check": "search_missing_audit_passed", "value": search})
    if search.get("query_count") != expected["search_queries"]:
        failures.append({"check": "query_count", "value": search.get("query_count")})
    if search.get("recoverable_market_data_count") != expected["recoverable_market_data_windows"]:
        failures.append({"check": "recoverable_count", "value": search.get("recoverable_market_data_count")})
    if search.get("non_generatable_source_state_count") != expected["non_generatable_source_state_gaps"]:
        failures.append({"check": "non_generatable_count", "value": search.get("non_generatable_source_state_count")})

    acquisition = payload_by_family(payloads, "acquisition_manifest_classification_audit")
    if acquisition.get("audit_passed") is not True or acquisition.get("request_count") != expected["acquisition_requests"]:
        failures.append({"check": "acquisition_audit_passed", "value": acquisition})
    if acquisition.get("non_manifest_execution_count") != 0 or acquisition.get("nonzero_cost_cap_count") != 0:
        failures.append({"check": "acquisition_manifest_only_zero_cost", "value": acquisition})

    hash_audit = payload_by_family(payloads, "hash_large_file_deferral_audit")
    if hash_audit.get("audit_passed") is not True:
        failures.append({"check": "hash_deferral_audit_passed", "value": hash_audit})
    if hash_audit.get("runtime_recomputed_hashes_verified") != expected["small_hash_rows"]:
        failures.append({"check": "runtime_recomputed_hashes", "value": hash_audit.get("runtime_recomputed_hashes_verified")})

    noleak = payload_by_family(payloads, "forbidden_route_noleak_audit")
    if noleak.get("audit_passed") is not True:
        failures.append({"check": "noleak_audit_passed", "value": noleak})
    if noleak.get("diff_scope", {}).get("forbidden_live_surface_paths") != []:
        failures.append({"check": "forbidden_live_surface_diff", "value": noleak.get("diff_scope")})

    integration = payload_by_family(payloads, "integration_guide_usability_audit")
    if integration.get("audit_passed") is not True:
        failures.append({"check": "integration_audit_passed", "value": integration})

    verifier = payload_by_family(payloads, "target_verifier_nonwriting_audit")
    if verifier.get("audit_passed") is not True:
        failures.append({"check": "target_verifier_nonwriting", "value": verifier})

    completion = payload_by_family(payloads, "completion_audit")
    if completion.get("completion_standard_satisfied") is not True or completion.get("can_mark_goal_complete") is not True:
        failures.append({"check": "completion_audit", "value": completion})
    if completion.get("missing_incomplete_or_weak_requirements") != []:
        failures.append({"check": "completion_missing_requirements", "value": completion.get("missing_incomplete_or_weak_requirements")})

    repair = payload_by_family(payloads, "repair_followup_source_request_ledger")
    if repair.get("followup_count", 0) < 2 or repair.get("lazy_blockers_remaining") != []:
        failures.append({"check": "repair_followup_exactness", "value": repair})
    return failures


def verify_python_syntax() -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in ROUTE_DIR.glob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append({"check": "python_ast_syntax", "file": path.name, "error": str(exc)})
    return failures


def verify() -> dict[str, Any]:
    payloads, failures = parse_artifacts()
    failures.extend(verify_required_artifacts(payloads))
    failures.extend(verify_audits(payloads))
    failures.extend(verify_python_syntax())
    diff_scope = builder.git_diff_scope()
    if not diff_scope["ok"]:
        failures.append({"check": "forbidden_live_surface_diff", "paths": diff_scope["forbidden_live_surface_paths"]})
    return builder.with_safe_flags(
        {
            "artifact_family": "verification_result",
            "route_id": builder.ROUTE_ID,
            "schema_version": f"{builder.SCHEMA_VERSION}_verifier_v1",
            "terminal_decision": builder.TERMINAL_DECISION,
            "ok": failures == [],
            "can_mark_goal_complete": failures == [],
            "failure_count": len(failures),
            "failures": failures,
            "json_artifact_count": len(payloads),
            "diff_scope": diff_scope,
        }
    )


def main() -> int:
    result = verify()
    (ROUTE_DIR / RESULT_NAME).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
