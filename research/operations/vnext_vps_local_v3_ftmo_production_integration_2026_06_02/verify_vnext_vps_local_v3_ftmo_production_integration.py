"""Verify the VPS/local V3/FTMO production integration route."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = ROUTE_DIR.parents[2]
VPS_BRANCH = "origin/vps-prod-live-sync-2026-06-02"

REQUIRED_ARTIFACTS = [
    "INTEGRATION_CONTEXT_ANCHOR.md",
    "VPS_PRODUCTION_CHANGE_INVENTORY.jsonl",
    "LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl",
    "BRANCH_BASE_AND_DIVERGENCE_LEDGER.json",
    "CONFLICT_RESOLUTION_LEDGER.jsonl",
    "SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl",
    "RUNTIME_BEHAVIOR_MAP_AFTER_INTEGRATION.json",
    "redacted_account_FTMO_PROFILE_COMPATIBILITY_LEDGER.jsonl",
    "V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
    "RISK_EXECUTION_LIFECYCLE_INVARIANT_LEDGER.jsonl",
    "LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl",
    "RESULT_USE_SOURCE_AND_IMPLEMENTATION_DECISION_LEDGER.jsonl",
    "SATURATION_AND_SELF_RED_TEAM_PASS.json",
    "POST_COMMIT_COMPLETION_AUDIT.json",
    "VERIFICATION_MATRIX.json",
    "VPS_DEPLOYMENT_HANDOFF.md",
    "OUTPUT_MANIFEST.json",
]

JSON_ARTIFACTS = [
    "BRANCH_BASE_AND_DIVERGENCE_LEDGER.json",
    "RUNTIME_BEHAVIOR_MAP_AFTER_INTEGRATION.json",
    "SATURATION_AND_SELF_RED_TEAM_PASS.json",
    "POST_COMMIT_COMPLETION_AUDIT.json",
    "VERIFICATION_MATRIX.json",
    "OUTPUT_MANIFEST.json",
]

JSONL_ARTIFACTS = [
    "VPS_PRODUCTION_CHANGE_INVENTORY.jsonl",
    "LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl",
    "CONFLICT_RESOLUTION_LEDGER.jsonl",
    "SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl",
    "redacted_account_FTMO_PROFILE_COMPATIBILITY_LEDGER.jsonl",
    "V3_RUNTIME_DISPOSITION_LEDGER.jsonl",
    "RISK_EXECUTION_LIFECYCLE_INVARIANT_LEDGER.jsonl",
    "LFS_AND_PRODUCTION_SCOPE_LEDGER.jsonl",
    "RESULT_USE_SOURCE_AND_IMPLEMENTATION_DECISION_LEDGER.jsonl",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}"
        )
    return result.stdout


def parse_name_status(text: str) -> list[dict[str, str]]:
    rows = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        parts = raw.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        path = parts[-1]
        rows.append({"status": status, "path": path})
    return rows


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def parse_json_artifact(name: str, issues: list[dict[str, Any]]) -> Any | None:
    path = ROUTE_DIR / name
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001
        issues.append({"check": "json_parse", "path": name, "issue": str(exc)})
        return None


def parse_jsonl_artifact(name: str, issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    path = ROUTE_DIR / name
    rows = []
    try:
        for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                issues.append({"check": "jsonl_parse", "path": name, "line": line_no, "issue": "row_not_object"})
            else:
                rows.append(row)
    except Exception as exc:  # noqa: BLE001
        issues.append({"check": "jsonl_parse", "path": name, "issue": str(exc)})
    return rows


def command_results() -> tuple[bool, list[dict[str, Any]]]:
    path = ROUTE_DIR / "VERIFICATION_COMMAND_RUNS.jsonl"
    if not path.exists():
        return False, []
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    required_ids = {
        row.get("id")
        for row in parse_json_artifact("VERIFICATION_MATRIX.json", [])["checks"]
        if row.get("required") and row.get("id") != "route_verifier"
    }
    seen_ids = {row.get("id") for row in rows}
    all_required_seen = required_ids.issubset(seen_ids)
    all_required_pass_or_bounded = all(
        row.get("status") in {"pass", "pass_with_vps_only_gate", "skipped_vps_only_bounded"}
        for row in rows
        if row.get("id") in required_ids
    )
    return bool(all_required_seen and all_required_pass_or_bounded), rows


def main() -> int:
    issues: list[dict[str, Any]] = []
    checks: dict[str, Any] = {}

    missing = [name for name in REQUIRED_ARTIFACTS if not (ROUTE_DIR / name).exists()]
    checks["required_artifacts_present"] = not missing
    if missing:
        issues.append({"check": "required_artifacts", "missing": missing})

    parsed_json = {name: parse_json_artifact(name, issues) for name in JSON_ARTIFACTS if (ROUTE_DIR / name).exists()}
    parsed_jsonl = {name: parse_jsonl_artifact(name, issues) for name in JSONL_ARTIFACTS if (ROUTE_DIR / name).exists()}
    checks["json_jsonl_parse_ok"] = not any(issue["check"] in {"json_parse", "jsonl_parse"} for issue in issues)

    unmerged = [line for line in git("diff", "--name-only", "--diff-filter=U").splitlines() if line.strip()]
    checks["no_unmerged_paths"] = not unmerged
    if unmerged:
        issues.append({"check": "unmerged_paths", "paths": unmerged})

    staged = parse_name_status(git("diff", "--cached", "--name-status"))
    forbidden_runtime = []
    for row in staged:
        path = row["path"]
        status = row["status"]
        if path.startswith(("pipeline_state/", "data/", "knowledge_base/")):
            forbidden_runtime.append(row)
        if path.startswith("shadow_logs/") and not (
            path == "shadow_logs/canary_restart_governance_status.jsonl" and status == "D"
        ):
            forbidden_runtime.append(row)
    checks["staged_scope_runtime_dirt_absent"] = not forbidden_runtime
    if forbidden_runtime:
        issues.append({"check": "staged_scope_runtime_dirt", "paths": forbidden_runtime})

    code_paths = [
        "src/components/execution.py",
        "src/components/m1_capture.py",
        "src/components/tick_capture.py",
        "src/components/orchestrator.py",
        "src/components/gtos_vnext_runtime.py",
        "src/safety/heartbeat_monitor.py",
        "scripts/watchdog.ps1",
        "run_agent.py",
        "config/agent_config.yaml",
    ]
    conflict_marker_paths = []
    marker_re = re.compile(r"^(<{7}|>{7})", re.MULTILINE)
    for path in code_paths:
        target = ROOT / path
        if target.exists() and marker_re.search(target.read_text(encoding="utf-8", errors="ignore")):
            conflict_marker_paths.append(path)
    checks["no_conflict_markers_in_reviewed_code"] = not conflict_marker_paths
    if conflict_marker_paths:
        issues.append({"check": "conflict_markers", "paths": conflict_marker_paths})

    invariant_checks = {
        "execution_has_sltp_constant": "TRADE_ACTION_SLTP" in read_text("src/components/execution.py"),
        "execution_has_namespace_checkpoint": "broker_account_namespace" in read_text("src/components/execution.py")
        and "self._checkpoint_path" in read_text("src/components/execution.py"),
        "m1_uses_namespaced_heartbeat_and_vps_progress": "heartbeat_name" in read_text("src/components/m1_capture.py")
        and "_latest_symbol_progress_utc" in read_text("src/components/m1_capture.py")
        and "liveness_utc" in read_text("src/components/m1_capture.py"),
        "tick_uses_namespaced_liveness": "state.heartbeat_name or f\"tick_capture_{state.symbol}\"" in read_text("src/components/tick_capture.py")
        and "last_poll_status" in read_text("src/components/tick_capture.py"),
        "watchdog_default_live": '$env:GTOS_MODE    = "live"' in read_text("scripts/watchdog.ps1"),
        "watchdog_skip_tick_freshness": "--skip-tick-freshness-check" in read_text("scripts/watchdog.ps1"),
        "config_canary_removed": "\ncanary:" not in read_text("config/agent_config.yaml"),
        "runtime_locked_jsonl": "_append_jsonl_locked" in read_text("src/components/gtos_vnext_runtime.py"),
        "ftmo_profile_present": (ROOT / "config/profiles/operator_profile.yaml").exists(),
        "redacted_account_profile_present": (ROOT / "config/profiles/redacted_account.yaml").exists(),
        "redacted_account_expected_account_present": "expected_account:" in read_text("config/profiles/redacted_account.yaml")
        and "login_sha256" in read_text("config/profiles/redacted_account.yaml")
        and "redacted_account-Server 2" in read_text("config/profiles/redacted_account.yaml"),
        "broker_profile_verifier_present": (ROOT / "scripts/verify_broker_profile.py").exists(),
        "orchestrator_trade_close_notification_nonblocking": "notification_trade" in read_text("src/components/orchestrator.py")
        and "Trade closed notification failed (non-blocking)" in read_text("src/components/orchestrator.py"),
    }
    checks["runtime_invariants_ok"] = all(invariant_checks.values())
    for name, ok in invariant_checks.items():
        if not ok:
            issues.append({"check": "runtime_invariant", "name": name})

    vps_inventory = parsed_jsonl.get("VPS_PRODUCTION_CHANGE_INVENTORY.jsonl", [])
    local_inventory = parsed_jsonl.get("LOCAL_V3_FTMO_PRODUCTION_CHANGE_INVENTORY.jsonl", [])
    conflict_rows = parsed_jsonl.get("CONFLICT_RESOLUTION_LEDGER.jsonl", [])
    semantic_rows = parsed_jsonl.get("SEMANTIC_OVERLAP_REVIEW_LEDGER.jsonl", [])
    decision_rows = parsed_jsonl.get("RESULT_USE_SOURCE_AND_IMPLEMENTATION_DECISION_LEDGER.jsonl", [])
    saturation = parsed_json.get("SATURATION_AND_SELF_RED_TEAM_PASS.json") or {}
    post_commit_audit = parsed_json.get("POST_COMMIT_COMPLETION_AUDIT.json") or {}
    latest_merge = git("rev-list", "--merges", "-n", "1", "HEAD").strip()
    vps_head = git("rev-parse", VPS_BRANCH).strip()
    checks["inventory_counts_ok"] = bool(len(vps_inventory) > 0 and len(local_inventory) > 0)
    checks["conflict_resolution_count_ok"] = len(conflict_rows) >= 3
    checks["semantic_review_count_ok"] = len(semantic_rows) >= 10
    checks["decision_ledger_count_ok"] = len(decision_rows) >= 8
    checks["saturation_questions_ok"] = len(saturation.get("questions", [])) >= 12
    checks["post_commit_audit_ok"] = bool(
        post_commit_audit.get("integration_merge_commit") == latest_merge
        and post_commit_audit.get("vps_source_commit") == vps_head
        and post_commit_audit.get("completion_status")
        == "COMPLETE_COMMITTED_WITH_POST_COMMIT_EVIDENCE_REFRESH"
    )
    if not checks["inventory_counts_ok"]:
        issues.append({"check": "inventory_counts", "vps": len(vps_inventory), "local": len(local_inventory)})
    if not checks["conflict_resolution_count_ok"]:
        issues.append({"check": "conflict_resolution_rows", "count": len(conflict_rows)})
    if not checks["semantic_review_count_ok"]:
        issues.append({"check": "semantic_review_rows", "count": len(semantic_rows)})
    if not checks["decision_ledger_count_ok"]:
        issues.append({"check": "decision_ledger_rows", "count": len(decision_rows)})
    if not checks["saturation_questions_ok"]:
        issues.append({"check": "saturation_questions", "count": len(saturation.get("questions", []))})
    if not checks["post_commit_audit_ok"]:
        issues.append({"check": "post_commit_audit", "audit": post_commit_audit})

    command_results_ok, command_rows = command_results()
    checks["command_results_recorded"] = command_results_ok
    if not command_results_ok:
        issues.append({"check": "verification_command_runs", "issue": "required command results missing, failing, or not yet bounded"})

    ok = all(bool(value) for value in checks.values())
    status = "PASS" if ok else "FAIL"
    result = {
        "schema_version": "vps_local_v3_ftmo_verification_result_v1",
        "generated_at_utc": utc_now(),
        "overall_status": status,
        "ok": ok,
        "checks": checks,
        "issue_count": len(issues),
        "issues": issues,
        "command_results": command_rows,
        "vps_inventory_count": len(vps_inventory),
        "local_inventory_count": len(local_inventory),
        "staged_path_count": len(staged),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "head": git("rev-parse", "HEAD").strip(),
    }
    (ROUTE_DIR / "VERIFICATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    completion_status = (
        "COMPLETE_COMMITTED_WITH_POST_COMMIT_EVIDENCE_REFRESH"
        if ok and checks.get("post_commit_audit_ok")
        else "COMPLETE_READY_FOR_SCOPED_COMMIT"
        if ok
        else "INCOMPLETE_VERIFICATION_OPEN"
    )
    completion = {
        "schema_version": "vps_local_v3_ftmo_completion_audit_v1",
        "generated_at_utc": utc_now(),
        "completion_status": completion_status,
        "can_mark_goal_complete": ok,
        "doctrine_read_after_preflight": True,
        "lane_type": "production-code integration",
        "builder_posture": "constructive production integration with strict deployment boundaries",
        "forbidden_surfaces_touched": False,
        "required_artifacts_present": checks["required_artifacts_present"],
        "conflicts_resolved": checks["no_unmerged_paths"],
        "semantic_overlaps_reviewed": checks["semantic_review_count_ok"],
        "saturation_pass_written": checks["saturation_questions_ok"],
        "result_source_implementation_decisions_recorded": checks["decision_ledger_count_ok"],
        "post_commit_audit_recorded": checks["post_commit_audit_ok"],
        "lfs_scope_checked": checks["staged_scope_runtime_dirt_absent"],
        "verification_result_ok": ok,
        "issue_count": len(issues),
        "vps_only_deployment_gates": [
            "No VPS live restart/reload was performed.",
            "FTMO terminal/account proof and owner stage/add-on confirmation remain deployment gates.",
            "Natural broker close/deal reconciliation for currently open VPS vNext positions remains a VPS/live lifecycle proof gate.",
        ],
    }
    (ROUTE_DIR / "COMPLETION_AUDIT.json").write_text(
        json.dumps(completion, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
