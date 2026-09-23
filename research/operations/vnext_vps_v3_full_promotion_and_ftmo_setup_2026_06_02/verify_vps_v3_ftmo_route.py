#!/usr/bin/env python3
"""Verify the VPS V3/FTMO route artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[2]
sys.path.insert(0, str(REPO))

from src.research.moonshot_v3_runtime_packages import load_v3_runtime_package_set
REQUIRED_STATUS_FIELDS = (
    "evidence_class",
    "production_change_status",
    "runtime_effect_boundary",
    "source_capture_status",
    "implementation_decision",
    "branch_decision",
    "exact_R_status",
    "proxy_R_status",
    "expectancy_status",
    "broker_operation_status",
    "live_trading_status",
    "remote_push_status",
)
REQUIRED_FILES = (
    "VPS_V3_FTMO_CONTEXT_ANCHOR.md",
    "VPS_V3_FTMO_SOURCE_INVENTORY.jsonl",
    "VPS_V3_FTMO_BRANCH_CONVERGENCE_LEDGER.jsonl",
    "VPS_V3_FTMO_PROFILE_VERIFICATION_LEDGER.jsonl",
    "VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl",
    "VPS_V3_FTMO_RUNTIME_WIRING_LEDGER.jsonl",
    "VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl",
    "VPS_V3_FTMO_EXECUTION_POLICY_LEDGER.jsonl",
    "VPS_V3_FTMO_NAMESPACE_AND_SUPERVISOR_LEDGER.jsonl",
    "VPS_V3_FTMO_PACKET_COMPLETENESS_LEDGER.jsonl",
    "VPS_V3_FTMO_ROLLBACK_AND_ACTIVATION_PLAN.md",
    "VPS_V3_FTMO_VERIFICATION_RESULT.json",
    "VPS_V3_FTMO_COMPLETION_AUDIT.json",
    "VPS_V3_FTMO_OUTPUT_MANIFEST.json",
    "VPS_V3_FTMO_MT5_READONLY_PROBE.json",
    "VPS_V3_FTMO_PROCESS_SNAPSHOT.json",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise AssertionError(f"{path}:{line_no} is not a JSON object")
            rows.append(row)
    return rows


def status_field_issues(row: dict[str, Any], *, path: Path, row_no: int | None = None) -> list[str]:
    where = f"{path.name}:{row_no}" if row_no is not None else path.name
    return [f"{where}:missing_status_field:{field}" for field in REQUIRED_STATUS_FIELDS if field not in row]


def profile(path: str) -> dict[str, Any]:
    return yaml.safe_load((REPO / path).read_text(encoding="utf-8")) or {}


def main() -> int:
    issues: list[str] = []
    checks: dict[str, Any] = {}

    for rel in REQUIRED_FILES:
        path = ROUTE_DIR / rel
        if not path.exists():
            issues.append(f"missing_required_file:{rel}")
        elif path.stat().st_size <= 0:
            issues.append(f"empty_required_file:{rel}")

    for path in ROUTE_DIR.glob("VPS_V3_FTMO_*.json"):
        data = read_json(path)
        issues.extend(status_field_issues(data, path=path))

    for path in ROUTE_DIR.glob("VPS_V3_FTMO_*.jsonl"):
        rows = read_jsonl(path)
        if not rows:
            issues.append(f"empty_jsonl:{path.name}")
        for idx, row in enumerate(rows, 1):
            issues.extend(status_field_issues(row, path=path, row_no=idx))

    probes = read_json(ROUTE_DIR / "VPS_V3_FTMO_MT5_READONLY_PROBE.json")["probes"]
    fn_probe = probes["redacted_account"]
    ftmo_probe = probes["operator_profile"]
    checks["redacted_account_probe_ok"] = fn_probe.get("initialize_ok") is True
    checks["ftmo_probe_ok"] = ftmo_probe.get("initialize_ok") is True
    checks["terminal_paths_distinct"] = (
        fn_probe.get("terminal_info", {}).get("path") != ftmo_probe.get("terminal_info", {}).get("path")
    )
    checks["terminal_data_paths_distinct"] = (
        fn_probe.get("terminal_info", {}).get("data_path") != ftmo_probe.get("terminal_info", {}).get("data_path")
    )
    checks["ftmo_flat"] = ftmo_probe.get("positions_total") == 0 and ftmo_probe.get("orders_total") == 0
    for key, value in checks.items():
        if key.endswith("_ok") or key in {"terminal_paths_distinct", "terminal_data_paths_distinct", "ftmo_flat"}:
            if value is not True:
                issues.append(f"check_failed:{key}")

    redacted_account = profile("config/profiles/redacted_account.yaml")
    ftmo = profile("config/profiles/operator_profile.yaml")
    if redacted_account.get("mt5", {}).get("terminal_path") != r"C:\Program Files\MetaTrader 5\terminal64.exe":
        issues.append("redacted_account_terminal_path_not_bound_to_normal_mt5")
    if ftmo.get("mt5", {}).get("terminal_path") != r"C:\MT5\FTMO\terminal64.exe":
        issues.append("ftmo_terminal_path_not_bound_to_portable_mt5")
    if redacted_account.get("runtime", {}).get("broker_account_namespace") == ftmo.get("runtime", {}).get("broker_account_namespace"):
        issues.append("broker_namespaces_not_distinct")

    package_rows = read_jsonl(ROUTE_DIR / "VPS_V3_FTMO_V3_PACKAGE_CONSUMPTION_LEDGER.jsonl")
    packages = load_v3_runtime_package_set(REPO)
    expected_sha = {package.provenance.package_role: package.provenance.sha256 for package in packages.values()}
    observed_sha = {
        row["package_key"]: row["provenance"]["sha256"]
        for row in package_rows
    }
    checks["package_sha_match"] = (
        observed_sha.get("selector_v3") == expected_sha["selector_v3"]
        and observed_sha.get("scheduler_v3") == expected_sha["scheduler_v3"]
        and observed_sha.get("execution_policy_v3") == expected_sha["execution_policy_v3"]
    )
    if not checks["package_sha_match"]:
        issues.append("package_sha_mismatch")

    packet_rows = read_jsonl(ROUTE_DIR / "VPS_V3_FTMO_PACKET_COMPLETENESS_LEDGER.jsonl")
    packet = packet_rows[0]["packet"]
    checks["packet_default_off_no_broker_effect"] = (
        packet.get("runtime_effect_now") is False
        and packet.get("broker_operation") is False
        and packet.get("order_calls") == 0
        and packet.get("paid_api_or_vendor_call") is False
    )
    if not checks["packet_default_off_no_broker_effect"]:
        issues.append("packet_has_runtime_or_broker_effect")

    risk_rows = read_jsonl(ROUTE_DIR / "VPS_V3_FTMO_RISK_SCHEDULER_LEDGER.jsonl")
    actions = {row["decision"]["action_class"] for row in risk_rows}
    checks["scheduler_action_coverage"] = {"require_source", "admit", "admit_reduced_risk", "reject"}.issubset(actions)
    if not checks["scheduler_action_coverage"]:
        issues.append("scheduler_action_coverage_missing")

    process = read_json(ROUTE_DIR / "VPS_V3_FTMO_PROCESS_SNAPSHOT.json")["process_snapshot"]
    checks["redacted_account_processes_active"] = process["redacted_account_run_agent_count"] == 24
    checks["ftmo_run_agent_not_active"] = process["ftmo_run_agent_count"] == 0
    if not checks["redacted_account_processes_active"]:
        issues.append("redacted_account_24_processes_not_active")
    if not checks["ftmo_run_agent_not_active"]:
        issues.append("ftmo_run_agent_process_unexpectedly_active")

    result_path = ROUTE_DIR / "VPS_V3_FTMO_VERIFICATION_RESULT.json"
    existing_result: dict[str, Any] = {}
    if result_path.exists():
        try:
            existing_result = read_json(result_path)
        except Exception:
            existing_result = {}
    result = {
        "schema_version": "vps_v3_ftmo_verification_result_v1",
        "route_id": "vnext_vps_v3_full_promotion_and_ftmo_setup_2026_06_02",
        "ok": not issues,
        "status": "ok" if not issues else "failed",
        "checks": checks,
        "issue_count": len(issues),
        "issues": issues,
        "evidence_class": "VPS production engineering, runtime integration, broker-profile verification, default-off package consumption, supervisor setup, rollback proof, and scoped deployment readiness",
        "production_change_status": "scoped_code_config_profile_verifier_artifact_changes_authorized_by_goal",
        "runtime_effect_boundary": "default_off_v3_package_consumption_no_live_process_reload_no_order_deal_position_mutation",
        "source_capture_status": "current_vps_disk_process_and_readonly_mt5_capture",
        "implementation_decision": "repair_profiles_add_default_off_v3_loader_verify_namespace_rollbacks",
        "branch_decision": "consume_origin_vnext_vps_ftmo_v3_clean_deploy_2026_06_02_preserve_vps_live_fixes",
        "exact_R_status": "not_applicable_to_this_production_engineering_goal_no_replay_scoring",
        "proxy_R_status": "not_applicable_to_this_production_engineering_goal_v3_proxy_values_are_package_provenance_only",
        "expectancy_status": "not_applicable_to_live_readiness_expectancy_values_are_package_provenance_only",
        "broker_operation_status": "read_only_mt5_profile_and_process_inspection_only_no_broker_mutation",
        "live_trading_status": "redacted_account_live_continues_existing_processes_ftmo_staged_no_activation",
        "remote_push_status": existing_result.get(
            "remote_push_status",
            "pending_until_scoped_commit_is_pushed",
        ),
    }
    if existing_result.get("verification_matrix"):
        result["verification_matrix"] = existing_result["verification_matrix"]
    result_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
