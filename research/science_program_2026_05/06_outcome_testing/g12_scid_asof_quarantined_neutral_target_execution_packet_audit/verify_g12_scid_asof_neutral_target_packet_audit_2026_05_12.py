#!/usr/bin/env python3
"""Standalone verifier for the G12 SCID neutral target packet audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_ASOF_NEUTRAL_TARGET_PACKET_AUDIT"
ROUTE_ID = "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT"
EVIDENCE_CLASS = "G12_SCID_ASOF_QUARANTINED_NEUTRAL_TARGET_EXECUTION_PACKET_AUDIT_ONLY"
ACCEPT_DECISION = "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY"
RESULT_PATH = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
FORBIDDEN_RAW_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "run_agent.py", "scripts/canary")

REQUIRED_FILES = [
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.json",
    f"{PREFIX}_CONTEXT_ANCHOR_{DATE_TAG}.md",
    f"{PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_SOURCE_HASH_INPUT_BINDING_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_TERMINAL_GRID_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_ROW_TARGET_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_NOT_COMPUTABLE_REASON_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_AGGREGATE_MATRIX_RECOMPUTATION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_NOLEAK_EVIDENCE_CLASS_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_DIRTY_STATE_RAW_BLOB_LIVE_SURFACE_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_SATURATION_SELF_REDTEAM_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
    f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.md",
    f"{PREFIX}_NEXT_G0_SYNTHESIS_CONTROL_PROMPT_PACK_{DATE_TAG}.md",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.md",
    f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
    "build_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py",
    "verify_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py",
    "test_g12_scid_asof_neutral_target_packet_audit_2026_05_12.py",
]
REQUIRED_JSON = [name for name in REQUIRED_FILES if name.endswith(".json")]


def repo_path(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_file(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def git_staged_files() -> list[str]:
    proc = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True, capture_output=True, check=False)
    return [line.replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()]


def refresh_manifest() -> None:
    manifest_path = ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json"
    if not manifest_path.exists() or not RESULT_PATH.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    artifacts = [item for item in manifest.get("artifacts", []) if item.get("path") != repo_path(RESULT_PATH)]
    artifacts.append({"path": repo_path(RESULT_PATH), "sha256": sha256_file(RESULT_PATH), "size_bytes": RESULT_PATH.stat().st_size})
    artifacts.sort(key=lambda item: item["path"])
    manifest["artifacts"] = artifacts
    manifest["artifact_count"] = len(artifacts)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    false_flags = [
        "validation_safe",
        "outcome_review_opened",
        "live_effect",
        "strategy_result_scoring_opened",
        "changes_live_trading_behavior",
        "credentials_touched",
        "opens_ai_api",
        "opens_broker_account_order_history_deal_position_evidence",
        "opens_live_trading_behavior",
        "opens_live_restart",
        "opens_paid_or_vendor_access",
        "opens_prompt_config_risk_safety_execution_canary_selector_edit",
        "opens_raw_market_data_blob_commit",
        "opens_registry_edit",
        "opens_remote_push",
        "opens_result_scoring",
        "opens_validation",
    ]
    return (
        payload.get("route_id") == ROUTE_ID
        and payload.get("evidence_class") == EVIDENCE_CLASS
        and payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and all(payload.get(key) is False for key in false_flags)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    checks: dict[str, bool] = {}
    required_paths = [ROUTE_DIR / name for name in REQUIRED_FILES]
    checks["required_files_exist"] = all(path.exists() for path in required_paths)
    if not checks["required_files_exist"]:
        issues.append(f"missing required files: {[repo_path(path) for path in required_paths if not path.exists()]}")

    parsed: dict[str, dict[str, Any]] = {}
    for name in REQUIRED_JSON:
        path = ROUTE_DIR / name
        if not path.exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            issues.append(f"JSON parse failed for {repo_path(path)}: {exc}")
    checks["json_parse_ok"] = not any(issue.startswith("JSON parse failed") for issue in issues)
    checks["safe_flags_closed"] = all(safe_flags_closed(payload) for payload in parsed.values())

    prerequisite = parsed.get(f"{PREFIX}_PREREQUISITE_ACCEPTANCE_AUDIT_{DATE_TAG}.json", {})
    source = parsed.get(f"{PREFIX}_SOURCE_HASH_INPUT_BINDING_AUDIT_{DATE_TAG}.json", {})
    terminal = parsed.get(f"{PREFIX}_TERMINAL_GRID_RECOMPUTATION_AUDIT_{DATE_TAG}.json", {})
    row_target = parsed.get(f"{PREFIX}_ROW_TARGET_RECOMPUTATION_AUDIT_{DATE_TAG}.json", {})
    not_audit = parsed.get(f"{PREFIX}_NOT_COMPUTABLE_REASON_AUDIT_{DATE_TAG}.json", {})
    aggregate = parsed.get(f"{PREFIX}_AGGREGATE_MATRIX_RECOMPUTATION_AUDIT_{DATE_TAG}.json", {})
    noleak = parsed.get(f"{PREFIX}_NOLEAK_EVIDENCE_CLASS_AUDIT_{DATE_TAG}.json", {})
    denominator = parsed.get(f"{PREFIX}_DUPLICATE_CONCENTRATION_DENOMINATOR_AUDIT_{DATE_TAG}.json", {})
    dirty = parsed.get(f"{PREFIX}_DIRTY_STATE_RAW_BLOB_LIVE_SURFACE_AUDIT_{DATE_TAG}.json", {})
    decision = parsed.get(f"{PREFIX}_DECISION_LEDGER_{DATE_TAG}.json", {})
    completion = parsed.get(f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json", {})
    manifest = parsed.get(f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json", {})

    checks["terminal_decision_accepts_control_evidence_only"] = decision.get("terminal_decision") == ACCEPT_DECISION
    checks["completion_can_mark_goal_complete"] = completion.get("can_mark_goal_complete") is True
    checks["prerequisites_accepted"] = prerequisite.get("all_prerequisites_accepted") is True
    checks["source_artifact_hashes_match"] = source.get("all_input_artifact_hashes_match_target_binding") is True
    checks["scid_segments_rehashed"] = source.get("accepted_scid_segments_rehashed") is True
    checks["manifest_hashes_match"] = (
        source.get("candidate_rows_sha256_matches_manifest") is True
        and source.get("bar_rows_sha256_matches_manifest") is True
    )
    checks["terminal_grid_full"] = (
        terminal.get("full_terminal_grid_pass") is True
        and terminal.get("recomputed_terminal_statuses") == 24112
        and terminal.get("target_packet_terminal_statuses") == 24112
    )
    checks["row_targets_recomputed"] = (
        row_target.get("full_row_hash_recomputation_pass") is True
        and row_target.get("target_row_hash_mismatch_count") == 0
        and row_target.get("target_value_mismatch_count") == 0
    )
    checks["not_computable_fail_closed"] = (
        not_audit.get("reason_counts_match_target") is True
        and not_audit.get("reason_counts_match_completion_and_failure") is True
        and not_audit.get("not_computable_rows_have_target_values") == 0
    )
    checks["aggregates_match"] = (
        aggregate.get("availability_summary_matches") is True
        and aggregate.get("aggregate_matrices_hash_match") is True
        and aggregate.get("partition_symbol_session_matrix_hash_match") is True
        and aggregate.get("positive_return_fraction_label_present_and_neutral") is True
    )
    checks["noleak_passes"] = noleak.get("all_noleak_checks_pass") is True
    checks["denominator_passes"] = denominator.get("all_denominator_checks_pass") is True
    checks["dirty_raw_live_surface_passes"] = dirty.get("all_dirty_state_checks_pass") is True
    manifest_paths = {item.get("path") for item in manifest.get("artifacts", [])}
    required_manifest_paths = {
        repo_path(ROUTE_DIR / name)
        for name in REQUIRED_FILES
        if not name.endswith("OUTPUT_MANIFEST_2026-05-12.json")
    }
    checks["manifest_has_required_artifacts"] = required_manifest_paths.issubset(manifest_paths)
    route_files = [path for path in ROUTE_DIR.rglob("*") if path.is_file()]
    checks["route_has_no_raw_blobs"] = not any(path.suffix.lower() in FORBIDDEN_RAW_EXTENSIONS for path in route_files)
    staged = git_staged_files()
    checks["staged_files_have_no_forbidden_live_surface"] = not any(path.startswith(FORBIDDEN_LIVE_PREFIXES) for path in staged)
    checks["staged_files_have_no_raw_market_blobs"] = not any(Path(path).suffix.lower() in FORBIDDEN_RAW_EXTENSIONS for path in staged)

    for key, value in checks.items():
        if not value:
            issues.append(f"check failed: {key}")

    output = {
        "schema_version": "g12_scid_asof_neutral_target_packet_audit_verifier_v1",
        "route_id": ROUTE_ID,
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "strategy_result_scoring_opened": False,
        "changes_live_trading_behavior": False,
        "credentials_touched": False,
        "opens_ai_api": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_or_vendor_access": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "opens_result_scoring": False,
        "opens_validation": False,
        "ok": not issues,
        "issues": issues,
        "checks": checks,
        "terminal_decision": decision.get("terminal_decision"),
        "git_status_short_informational": git_status_short(),
        "can_mark_goal_complete_after_scoped_commit_and_closeout": not issues,
    }
    if not args.no_write:
        RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        refresh_manifest()
    print(json.dumps({"ok": output["ok"], "issues": issues}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
