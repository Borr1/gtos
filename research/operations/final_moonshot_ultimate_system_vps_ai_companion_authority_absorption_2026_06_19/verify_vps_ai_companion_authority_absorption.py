#!/usr/bin/env python3
"""Verify VPS AI companion authority absorption artifacts."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
BASE_HEAD = "435d7d083611d11d986a02ee3bc688e952eb360a"
VPS_TRACKING_REF = "origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18"
REQUIRED_FLOOR = "b112d22c351b13e2af045bb8feb82f1e235246f4"
AUTHORITY_VERIFICATION_PATH = (
    "research/operations/vps_runtime_ai_companion_authority_deployment_2026_06_19/"
    "VERIFICATION_RESULT.json"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(name: str) -> Any:
    return json.loads((ROUTE / name).read_text(encoding="utf-8"))


def read_jsonl(name: str) -> list[dict[str, Any]]:
    return [json.loads(line) for line in (ROUTE / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(name: str, data: Any) -> None:
    (ROUTE / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_output(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def main() -> int:
    now = utc_now()
    issues: list[str] = []
    required = [
        "build_vps_ai_companion_authority_absorption.py",
        "verify_vps_ai_companion_authority_absorption.py",
        "VPS_AI_COMPANION_AUTHORITY_ABSORPTION_SUMMARY.json",
        "VPS_AI_COMPANION_REMOTE_COMMIT_LEDGER.jsonl",
        "VPS_AI_COMPANION_CODE_IMPACT_LEDGER.jsonl",
        "VPS_AI_COMPANION_ROUTE_ARTIFACT_POINTER_LEDGER.jsonl",
        "VPS_AI_COMPANION_RUNTIME_BOUNDARY_LEDGER.jsonl",
        "VPS_AI_COMPANION_SOURCE_ACCESS_LEDGER.jsonl",
        "DECISION_LEDGER.jsonl",
        "REPAIR_LEDGER.jsonl",
        "COMPLETION_AUDIT.json",
        "FOCUSED_TEST_RESULT.json",
        "SATURATION_SELF_RED_TEAM.md",
        "NEXT_PROMPT.md",
        "OUTPUT_MANIFEST.json",
    ]
    for name in required:
        if not (ROUTE / name).exists():
            issues.append(f"missing_required:{name}")

    summary = read_json("VPS_AI_COMPANION_AUTHORITY_ABSORPTION_SUMMARY.json")
    commits = read_jsonl("VPS_AI_COMPANION_REMOTE_COMMIT_LEDGER.jsonl")
    paths = read_jsonl("VPS_AI_COMPANION_CODE_IMPACT_LEDGER.jsonl")
    pointers = read_jsonl("VPS_AI_COMPANION_ROUTE_ARTIFACT_POINTER_LEDGER.jsonl")
    boundaries = read_jsonl("VPS_AI_COMPANION_RUNTIME_BOUNDARY_LEDGER.jsonl")
    sources = read_jsonl("VPS_AI_COMPANION_SOURCE_ACCESS_LEDGER.jsonl")
    decisions = read_jsonl("DECISION_LEDGER.jsonl")
    repairs = read_jsonl("REPAIR_LEDGER.jsonl")
    completion = read_json("COMPLETION_AUDIT.json")
    manifest = read_json("OUTPUT_MANIFEST.json")

    current_head = git_output(["git", "rev-parse", VPS_TRACKING_REF])
    expected_commit_rows = int(git_output(["git", "rev-list", "--count", f"{BASE_HEAD}..{current_head}"]))
    expected_changed_paths = {
        line for line in git_output(["git", "diff", "--name-only", f"{BASE_HEAD}..{current_head}"]).splitlines() if line
    }
    current_authority_verification = json.loads(
        git_output(["git", "show", f"{current_head}:{AUTHORITY_VERIFICATION_PATH}"])
    )
    floor_ok = subprocess.run(
        ["git", "merge-base", "--is-ancestor", REQUIRED_FLOOR, current_head],
        cwd=ROOT,
        check=False,
    ).returncode == 0
    if summary.get("status") != "latest_vps_package_guard_absorbed_current_remote_snapshot":
        issues.append("summary_status_mismatch")
    if summary.get("base_local_vps_head") != BASE_HEAD:
        issues.append("base_head_mismatch")
    if summary.get("remote_probe_head") != current_head:
        issues.append("remote_probe_head_mismatch")
    if summary.get("source_snapshot_head") != current_head:
        issues.append("source_snapshot_head_mismatch")
    if summary.get("local_origin_head_after_fetch") != current_head:
        issues.append("local_origin_head_after_fetch_mismatch")
    if summary.get("source_snapshot_verified") is not True:
        issues.append("source_snapshot_not_verified")
    if summary.get("remote_probe_matches_source_snapshot") is not True:
        issues.append("remote_probe_not_source_snapshot")
    if summary.get("local_origin_floor_or_newer") is not True or not floor_ok:
        issues.append("local_origin_floor_not_ok")
    if summary.get("main_worktree_fetch_status") not in {"not_required_current", "passed"}:
        issues.append("main_fetch_status_unexpected")
    if summary.get("commit_rows") != len(commits) or len(commits) != expected_commit_rows:
        issues.append("commit_row_count_mismatch")
    if summary.get("changed_path_rows") != len(paths) or {row.get("path") for row in paths} != expected_changed_paths:
        issues.append("changed_path_count_mismatch")
    if summary.get("package_relevant_changed_path_rows") != sum(bool(row.get("package_relevance")) for row in paths):
        issues.append("package_relevant_changed_path_count_mismatch")
    if not summary.get("package_relevant_changed_path_rows"):
        issues.append("package_relevant_changed_paths_missing")
    if summary.get("authority_verification_ok") is not True:
        issues.append("authority_verification_not_ok")
    if summary.get("micro_observation_verification_ok") is not True:
        issues.append("micro_observation_verification_not_ok")
    if summary.get("authority_level") != "protective":
        issues.append("authority_level_not_protective")
    if summary.get("ai_companion_enabled") is not True:
        issues.append("ai_companion_not_enabled_in_vps_evidence")
    if summary.get("active_control_count") != 0:
        issues.append("unexpected_active_control_count")
    if summary.get("proposal_count") != current_authority_verification.get("active_control_summary", {}).get("proposal_count"):
        issues.append("proposal_count_not_current_snapshot")
    if summary.get("local_runtime_code_imported") is not False:
        issues.append("local_runtime_code_imported")
    for field in ["final_package_selected", "model_training_allowed", "deployment_readiness_claim", "broker_runtime_change_status", "direct_broker_mutation_by_this_route"]:
        if summary.get(field) is not False:
            issues.append(f"terminal_boundary_not_false:{field}")
    if any(value is not False for value in summary.get("forbidden_surface_status", {}).values()):
        issues.append("forbidden_surface_crossed")

    subjects = {row.get("subject") for row in commits}
    for expected in {
        "vps: capture ai companion micro observation",
        "context: record ai companion micro observation",
        "vps: deploy ai companion protective authority",
        "context: record ai companion authority deployment",
        "vps: surface execution manager companion advisories",
        "vps: enrich companion execution manager advisories",
    }:
        if expected not in subjects:
            issues.append(f"missing_commit_subject:{expected}")

    classifications = {row.get("classification") for row in paths}
    for expected in {
        "new_ai_companion_runtime_code",
        "ultimate_book_runtime_integration",
        "execution_lifecycle_runtime_code",
        "broker_profile_or_market_data_runtime",
        "runtime_supervision_or_reconciliation",
        "shadow_intelligence_boundary_artifact",
        "runtime_config",
        "focused_tests",
        "vps_authority_deployment_artifact",
        "vps_micro_observation_artifact",
    }:
        if expected not in classifications:
            issues.append(f"missing_path_classification:{expected}")
    if not all(row.get("exists_in_source_snapshot") is True for row in pointers):
        issues.append("pointer_missing_in_source_snapshot")
    boundary_statuses = {row.get("control"): row.get("status") for row in boundaries}
    for allowed in ["pause_new_entries", "symbol_sleeve_cooldown", "risk_multiplier_reduce_only"]:
        if boundary_statuses.get(allowed) != "allowed_reduce_or_protect_only":
            issues.append(f"allowed_boundary_missing:{allowed}")
    for forbidden in ["order_placement", "risk_increase", "hard_gate_override", "broker_account_order_deal_position_mutation", "credential_mutation"]:
        if boundary_statuses.get(forbidden) != "forbidden":
            issues.append(f"forbidden_boundary_missing:{forbidden}")
    source_status = {row.get("source_id"): row.get("status") for row in sources}
    if source_status.get("main_worktree_fetch") != summary.get("main_worktree_fetch_status"):
        issues.append("source_main_fetch_status_mismatch")
    if source_status.get("remote_head_probe") != "readable":
        issues.append("source_remote_probe_not_readable")
    if source_status.get("immutable_remote_tracking_snapshot") != "readable_immutable_remote_tracking_snapshot":
        issues.append("source_snapshot_not_readable")
    if source_status.get("local_remote_tracking_ref") != "latest_remote_observed":
        issues.append("source_local_remote_status_mismatch")
    if completion.get("goal_completion_claim") is not False:
        issues.append("completion_claim_not_false")
    if len(decisions) < 2 or not all(row.get("status") == "selected" for row in decisions):
        issues.append("decision_ledger_invalid")
    if len(repairs) < 2:
        issues.append("repair_ledger_too_low")
    coverage = completion.get("instruction_coverage", {})
    for key in ["live_state_regenerated", "same_evidence_class_repair_pursued", "no_arbitrary_top_n", "full_changed_path_ledger_preserved", "full_commit_ledger_preserved"]:
        if coverage.get(key) is not True:
            issues.append(f"instruction_coverage_missing:{key}")
    if not all(item.get("exists") is True for item in manifest.get("files", [])):
        issues.append("manifest_file_missing")

    result = {
        "schema": "gtos.final_moonshot.vps_ai_companion_authority_absorption.verification_result.v1",
        "verified_utc": now,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "remote_probe_head": summary.get("remote_probe_head"),
        "source_snapshot_head": summary.get("source_snapshot_head"),
        "source_snapshot_verified": summary.get("source_snapshot_verified"),
        "main_worktree_fetch_status": summary.get("main_worktree_fetch_status"),
        "commit_rows": len(commits),
        "changed_path_rows": len(paths),
        "authority_verification_ok": summary.get("authority_verification_ok"),
        "micro_observation_verification_ok": summary.get("micro_observation_verification_ok"),
        "authority_level": summary.get("authority_level"),
        "active_control_count": summary.get("active_control_count"),
        "proposal_count": summary.get("proposal_count"),
        "package_relevant_changed_path_rows": summary.get("package_relevant_changed_path_rows"),
        "final_package_selected": summary.get("final_package_selected"),
        "model_training_allowed": summary.get("model_training_allowed"),
        "deployment_readiness_claim": summary.get("deployment_readiness_claim"),
    }
    write_json("VERIFICATION_RESULT.json", result)
    focused = read_json("FOCUSED_TEST_RESULT.json")
    focused["status"] = "passed" if result["ok"] else "failed"
    focused["verification_result"] = {"ok": result["ok"], "issue_count": result["issue_count"], "verified_utc": now}
    write_json("FOCUSED_TEST_RESULT.json", focused)
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
